import hashlib
import json
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import signing
from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction
from django.http import FileResponse, Http404, JsonResponse
from django.db.models import Max, Q
from django.shortcuts import redirect
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .ai_service import chat_with_ai, analyze_spending_with_ai, get_ai_status, parse_purchase_plan_with_ai, parse_transaction_with_ai
from .card_repository import fetch_card, fetch_cards
from .models import AIAnalysisRecord, AuthSession, CommunityComment, CommunityPost, CommunityPostLike, OwnedCard, PurchasePlan, SocialAccount, Transaction
from .seed_data import PURCHASE_PLANS, TRANSACTIONS


MERCHANT_HINTS = [
    ('컴포즈커피', '카페', '☕'),
    ('스타벅스', '카페', '☕'),
    ('투썸', '카페', '☕'),
    ('메가커피', '카페', '☕'),
    ('샐러디', '식비', '🥗'),
    ('쿠팡', '쇼핑', '📦'),
    ('무신사', '쇼핑', '🛍️'),
    ('마켓컬리', '쇼핑', '📦'),
    ('GS25', '편의점', '🏪'),
    ('CU', '편의점', '🏪'),
    ('세븐일레븐', '편의점', '🏪'),
    ('스포애니', '헬스', '🏋️'),
    ('올리브영', '뷰티', '💄'),
    ('이마트', '마트', '🛒'),
    ('홈플러스', '마트', '🛒'),
    ('맥도날드', '식비', '🍔'),
    ('배달의민족', '식비', '🍕'),
    ('요기요', '식비', '🍕'),
    ('카카오택시', '교통', '🚕'),
    ('카카오T', '교통', '🚕'),
    ('택시', '교통', '🚕'),
    ('CGV', '문화', '🎬'),
    ('넷플릭스', '구독', '📺'),
    ('네이버플러스', '구독', '📱'),
    ('토익스피킹', '교육', '📚'),
    ('링글', '교육', '🗣️'),
    ('교보문고', '교육', '📖'),
]

CARD_HINTS = [
    ('LOCA LIKIT Eat', '10106'),
    ('LIKIT Eat', '10106'),
    ('리킷 Eat', '10106'),
    ('LOCA LIKIT Shop', '10107'),
    ('LIKIT Shop', '10107'),
    ('LOCA 100', '10029'),
    ('SHOPPER', '10612'),
    ('카드의정석', '10612'),
    ('우리', '10612'),
    ('로카', '10029'),
]

DEFAULT_OWNED_CARD_IDS = ['10106', '10612', '10029']
LEGACY_DEFAULT_OWNED_CARD_ID_SETS = [
    {'10029', '10612', '10609'},
    {'10033', '10612', '10607'},
]
DEMO_USER_EMAIL = 'demo@carch.local'
DEMO_USER_NAME = '남주현'


def json_response(payload, status=200):
    return JsonResponse(
        payload,
        status=status,
        safe=isinstance(payload, dict),
        json_dumps_params={'ensure_ascii': False},
    )


def health(request):
    return json_response({'ok': True, 'service': 'carch-api'})


def _token_hash(token):
    return hashlib.sha256(str(token).encode('utf-8')).hexdigest()


def serialize_user(user):
    initials = (user.first_name or user.username or user.email or 'C')[:1]
    return {
        'id': user.id,
        'email': user.email,
        'name': user.first_name or user.username or user.email,
        'initials': initials.upper(),
    }


def _create_auth_session(user, provider='email'):
    raw_token = secrets.token_urlsafe(32)
    session = AuthSession.objects.create(
        user=user,
        token_hash=_token_hash(raw_token),
        provider=provider,
        expires_at=timezone.now() + timedelta(days=settings.AUTH_SESSION_DAYS),
    )
    return raw_token, session


def _auth_payload(user, token, provider='email'):
    return {
        'ok': True,
        'token': token,
        'provider': provider,
        'user': serialize_user(user),
    }


def get_request_user(request):
    header = request.headers.get('Authorization', '')
    if not header.lower().startswith('bearer '):
        return None
    token = header.split(' ', 1)[1].strip()
    if not token:
        return None
    session = (
        AuthSession.objects.select_related('user')
        .filter(token_hash=_token_hash(token), expires_at__gt=timezone.now())
        .first()
    )
    if not session:
        return None
    session.last_used_at = timezone.now()
    session.save(update_fields=['last_used_at'])
    return session.user


def get_demo_user():
    User = get_user_model()
    user = User.objects.filter(email__iexact=DEMO_USER_EMAIL).first()
    if user:
        return user
    user = User.objects.create_user(
        username=_unique_username('demo'),
        email=DEMO_USER_EMAIL,
        first_name=DEMO_USER_NAME,
    )
    user.set_unusable_password()
    user.save(update_fields=['password'])
    return user


def get_dev_admin_user():
    User = get_user_model()
    email = settings.DEV_ADMIN_EMAIL
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        user = User.objects.create_user(
            username=_unique_username(email.split('@')[0] or 'admin'),
            email=email,
            password=settings.DEV_ADMIN_PASSWORD,
            first_name=settings.DEV_ADMIN_NAME[:30],
        )
        changed_fields = []
    elif not user.has_usable_password():
        user.set_password(settings.DEV_ADMIN_PASSWORD)
        changed_fields = ['password']
    else:
        changed_fields = []

    if user.first_name != settings.DEV_ADMIN_NAME[:30]:
        user.first_name = settings.DEV_ADMIN_NAME[:30]
        changed_fields.append('first_name')
    if not user.is_staff:
        user.is_staff = True
        changed_fields.append('is_staff')
    if not user.is_superuser:
        user.is_superuser = True
        changed_fields.append('is_superuser')
    if not user.is_active:
        user.is_active = True
        changed_fields.append('is_active')
    if user.has_usable_password() and not user.check_password(settings.DEV_ADMIN_PASSWORD):
        # Keep an existing custom password intact. Auto-login issues a token directly.
        pass
    if changed_fields:
        user.save(update_fields=changed_fields)
    elif user.pk:
        user.save()
    return user


def get_effective_user(request):
    return get_request_user(request) or get_demo_user()


def auth_required_response():
    return json_response({'detail': '로그인이 필요합니다.'}, status=401)


def forbidden_response():
    return json_response({'detail': '권한이 없습니다.'}, status=403)


def require_request_user(request):
    user = get_request_user(request)
    if not user:
        return None, auth_required_response()
    return user, None


def user_display_name(user):
    return (user.first_name or user.username or user.email or 'CARCH 사용자')[:30]


def user_avatar(user):
    return user_display_name(user)[:1] or 'C'


def _find_user_by_email(email):
    if not email:
        return None
    User = get_user_model()
    return User.objects.filter(email__iexact=email).first()


def _unique_username(seed):
    User = get_user_model()
    base = re.sub(r'[^a-zA-Z0-9_]+', '', str(seed or 'carch_user'))[:24] or 'carch_user'
    username = base
    suffix = 1
    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f'{base[:20]}{suffix}'
    return username


def _oauth_frontend_redirect(path='', **params):
    safe_path = path if str(path or '').startswith('/') else '/cards'
    query = urllib.parse.urlencode({key: value for key, value in params.items() if value not in {None, ''}})
    url = f'{settings.FRONTEND_URL}{safe_path}'
    return redirect(f'{url}?{query}' if query else url)


OAUTH_PROVIDER_CONFIG = {
    'kakao': {
        'label': '카카오',
        'client_id_setting': 'KAKAO_CLIENT_ID',
        'client_secret_setting': 'KAKAO_CLIENT_SECRET',
        'authorize_url': 'https://kauth.kakao.com/oauth/authorize',
        'token_url': 'https://kauth.kakao.com/oauth/token',
        'profile_url': 'https://kapi.kakao.com/v2/user/me',
        'scope': 'profile_nickname account_email',
    },
    'naver': {
        'label': '네이버',
        'client_id_setting': 'NAVER_CLIENT_ID',
        'client_secret_setting': 'NAVER_CLIENT_SECRET',
        'authorize_url': 'https://nid.naver.com/oauth2.0/authorize',
        'token_url': 'https://nid.naver.com/oauth2.0/token',
        'profile_url': 'https://openapi.naver.com/v1/nid/me',
        'scope': '',
    },
}


def _oauth_config(provider):
    config = OAUTH_PROVIDER_CONFIG.get(provider)
    if not config:
        return None
    return {
        **config,
        'client_id': getattr(settings, config['client_id_setting'], ''),
        'client_secret': getattr(settings, config['client_secret_setting'], ''),
    }


def _oauth_redirect_uri(request, provider):
    return request.build_absolute_uri(f'/api/auth/oauth/{provider}/callback/')


def _post_form(url, payload, headers=None):
    body = urllib.parse.urlencode(payload).encode('utf-8')
    request = urllib.request.Request(
        url,
        data=body,
        headers={'Content-Type': 'application/x-www-form-urlencoded', **(headers or {})},
        method='POST',
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode('utf-8'))


def _get_json(url, headers=None):
    request = urllib.request.Request(url, headers=headers or {}, method='GET')
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode('utf-8'))


def _extract_oauth_profile(provider, raw_profile):
    if provider == 'kakao':
        account = raw_profile.get('kakao_account') or {}
        profile = account.get('profile') or {}
        provider_user_id = str(raw_profile.get('id') or '')
        return {
            'providerUserId': provider_user_id,
            'email': account.get('email') or '',
            'name': profile.get('nickname') or account.get('email') or '카카오 사용자',
            'avatarUrl': profile.get('profile_image_url') or '',
        }
    if provider == 'naver':
        response = raw_profile.get('response') or {}
        provider_user_id = str(response.get('id') or '')
        return {
            'providerUserId': provider_user_id,
            'email': response.get('email') or '',
            'name': response.get('name') or response.get('nickname') or response.get('email') or '네이버 사용자',
            'avatarUrl': response.get('profile_image') or '',
        }
    return {}


def _get_or_create_social_user(provider, profile, raw_profile):
    provider_user_id = profile.get('providerUserId')
    email = profile.get('email') or ''
    name = profile.get('name') or ''
    if not provider_user_id:
        raise ValueError('소셜 계정 식별값을 확인할 수 없습니다.')

    account = SocialAccount.objects.select_related('user').filter(
        provider=provider,
        provider_user_id=provider_user_id,
    ).first()
    if account:
        account.email = email
        account.name = name
        account.avatar_url = profile.get('avatarUrl') or ''
        account.raw_profile = raw_profile
        account.save(update_fields=['email', 'name', 'avatar_url', 'raw_profile', 'updated_at'])
        return account.user

    User = get_user_model()
    user = _find_user_by_email(email) if email else None
    if not user:
        username_seed = email.split('@')[0] if email else f'{provider}_{provider_user_id}'
        user = User.objects.create_user(
            username=_unique_username(username_seed),
            email=email,
            password=None,
            first_name=name[:30],
        )
        user.set_unusable_password()
        user.save(update_fields=['password'])
    elif name and not user.first_name:
        user.first_name = name[:30]
        user.save(update_fields=['first_name'])

    SocialAccount.objects.create(
        user=user,
        provider=provider,
        provider_user_id=provider_user_id,
        email=email,
        name=name,
        avatar_url=profile.get('avatarUrl') or '',
        raw_profile=raw_profile,
    )
    return user


def auth_providers(request):
    providers = []
    for provider, config in OAUTH_PROVIDER_CONFIG.items():
        client_id = getattr(settings, config['client_id_setting'], '')
        client_secret = getattr(settings, config['client_secret_setting'], '')
        providers.append(
            {
                'id': provider,
                'label': config['label'],
                'enabled': bool(client_id and (provider != 'naver' or client_secret)),
                'requiresSecret': provider == 'naver',
                'startUrl': f'/api/auth/oauth/{provider}/start/',
            }
        )
    return json_response(
        {
            'email': {'enabled': settings.EMAIL_AUTH_ENABLED},
            'devLogin': {
                'enabled': bool(settings.DEBUG and settings.DEV_AUTO_LOGIN_ENABLED),
                'email': settings.DEV_ADMIN_EMAIL,
                'name': settings.DEV_ADMIN_NAME,
            },
            'providers': providers,
            'frontendUrl': settings.FRONTEND_URL,
        }
    )


@csrf_exempt
def dev_login(request):
    if request.method != 'POST':
        return json_response({'detail': 'POST 요청만 지원합니다.'}, status=405)
    if not (settings.DEBUG and settings.DEV_AUTO_LOGIN_ENABLED):
        return json_response({'detail': '개발용 자동 로그인이 비활성화되어 있습니다.'}, status=403)

    user = get_dev_admin_user()
    token, _ = _create_auth_session(user, 'dev-admin')
    payload = _auth_payload(user, token, 'dev-admin')
    payload['devAutoLogin'] = True
    return json_response(payload)


@csrf_exempt
def email_signup(request):
    if request.method != 'POST':
        return json_response({'detail': 'POST 요청만 지원합니다.'}, status=405)
    if not settings.EMAIL_AUTH_ENABLED:
        return json_response({'detail': '이메일 가입이 비활성화되어 있습니다.'}, status=403)
    payload, error = parse_request_body(request)
    if error:
        return error
    email = str(payload.get('email') or '').strip().lower()
    password = str(payload.get('password') or '')
    name = str(payload.get('name') or email.split('@')[0] or 'CARCH 사용자').strip()
    if not email or '@' not in email:
        return json_response({'detail': '이메일을 확인해 주세요.'}, status=400)
    if len(password) < 8:
        return json_response({'detail': '비밀번호는 8자 이상이어야 합니다.'}, status=400)

    User = get_user_model()
    user = _find_user_by_email(email)
    if user and user.has_usable_password():
        return json_response({'detail': '이미 가입된 이메일입니다.'}, status=409)
    if not user:
        user = User(username=_unique_username(email.split('@')[0]), email=email, first_name=name[:30])
    else:
        user.first_name = user.first_name or name[:30]
    try:
        validate_password(password, user)
    except ValidationError as exc:
        return json_response({'detail': ' '.join(exc.messages)}, status=400)
    user.set_password(password)
    user.save()
    token, _ = _create_auth_session(user, 'email')
    return json_response(_auth_payload(user, token, 'email'), status=201)


@csrf_exempt
def email_login(request):
    if request.method != 'POST':
        return json_response({'detail': 'POST 요청만 지원합니다.'}, status=405)
    payload, error = parse_request_body(request)
    if error:
        return error
    email = str(payload.get('email') or '').strip().lower()
    password = str(payload.get('password') or '')
    user = _find_user_by_email(email)
    if not user:
        return json_response({'detail': '이메일 또는 비밀번호를 확인해 주세요.'}, status=401)
    authenticated = authenticate(request, username=user.username, password=password)
    if not authenticated:
        return json_response({'detail': '이메일 또는 비밀번호를 확인해 주세요.'}, status=401)
    token, _ = _create_auth_session(authenticated, 'email')
    return json_response(_auth_payload(authenticated, token, 'email'))


def auth_me(request):
    user = get_request_user(request)
    if not user:
        return json_response({'authenticated': False}, status=401)
    return json_response({'authenticated': True, 'user': serialize_user(user)})


@csrf_exempt
def auth_logout(request):
    if request.method != 'POST':
        return json_response({'detail': 'POST 요청만 지원합니다.'}, status=405)
    header = request.headers.get('Authorization', '')
    if header.lower().startswith('bearer '):
        AuthSession.objects.filter(token_hash=_token_hash(header.split(' ', 1)[1].strip())).delete()
    return json_response({'ok': True})


def oauth_start(request, provider):
    config = _oauth_config(provider)
    if not config:
        return json_response({'detail': '지원하지 않는 로그인 방식입니다.'}, status=404)
    if not config['client_id'] or (provider == 'naver' and not config['client_secret']):
        return json_response({'detail': f'{config["label"]} 로그인 키가 설정되어 있지 않습니다.'}, status=400)

    next_path = request.GET.get('next') or '/cards'
    state = signing.dumps(
        {
            'provider': provider,
            'next': next_path if next_path.startswith('/') else '/cards',
            'nonce': secrets.token_urlsafe(8),
        },
        salt='carch-oauth',
        compress=True,
    )
    params = {
        'response_type': 'code',
        'client_id': config['client_id'],
        'redirect_uri': _oauth_redirect_uri(request, provider),
        'state': state,
    }
    if config.get('scope'):
        params['scope'] = config['scope']
    return redirect(f'{config["authorize_url"]}?{urllib.parse.urlencode(params)}')


def oauth_callback(request, provider):
    config = _oauth_config(provider)
    if not config:
        return _oauth_frontend_redirect('/login', auth_error='unsupported_provider')
    state_value = request.GET.get('state') or ''
    try:
        state = signing.loads(state_value, salt='carch-oauth', max_age=600)
    except signing.BadSignature:
        return _oauth_frontend_redirect('/login', auth_error='invalid_state')
    if state.get('provider') != provider:
        return _oauth_frontend_redirect('/login', auth_error='provider_mismatch')
    if request.GET.get('error'):
        return _oauth_frontend_redirect('/login', auth_error=request.GET.get('error'))
    code = request.GET.get('code')
    if not code:
        return _oauth_frontend_redirect('/login', auth_error='missing_code')

    token_payload = {
        'grant_type': 'authorization_code',
        'client_id': config['client_id'],
        'redirect_uri': _oauth_redirect_uri(request, provider),
        'code': code,
    }
    if config['client_secret']:
        token_payload['client_secret'] = config['client_secret']
    if provider == 'naver':
        token_payload['state'] = state_value
    try:
        token_data = _post_form(config['token_url'], token_payload)
        access_token = token_data.get('access_token')
        if not access_token:
            raise ValueError('access_token missing')
        raw_profile = _get_json(
            config['profile_url'],
            headers={'Authorization': f'Bearer {access_token}'},
        )
        profile = _extract_oauth_profile(provider, raw_profile)
        user = _get_or_create_social_user(provider, profile, raw_profile)
        auth_token, _ = _create_auth_session(user, provider)
    except (urllib.error.URLError, ValueError, KeyError) as exc:
        return _oauth_frontend_redirect('/login', auth_error='oauth_failed', detail=str(exc)[:80])

    return _oauth_frontend_redirect(
        '/login/callback',
        token=auth_token,
        provider=provider,
        next=state.get('next') or '/cards',
    )


def ai_status(request):
    return json_response(get_ai_status())


def parse_request_body(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}'), None
    except json.JSONDecodeError:
        return None, json_response({'detail': 'JSON 형식이 올바르지 않습니다.'}, status=400)


def normalize_tags(value):
    if isinstance(value, list):
        tags = value
    elif isinstance(value, str):
        tags = re.split(r'[,#\s]+', value)
    else:
        tags = []
    normalized = []
    for tag in tags:
        clean = str(tag).strip().lstrip('#')
        if clean and clean not in normalized:
            normalized.append(clean)
    return normalized[:5]


def parse_approved_at(value):
    if not value:
        return timezone.localtime().replace(second=0, microsecond=0)

    if isinstance(value, datetime):
        approved_at = value
    else:
        normalized = str(value).strip().replace('Z', '+00:00')
        if len(normalized) == 10:
            now = timezone.localtime()
            normalized = f'{normalized}T{now.hour:02d}:{now.minute:02d}:00+09:00'
        elif 'T' not in normalized and ' ' in normalized:
            normalized = normalized.replace(' ', 'T', 1)
        approved_at = parse_datetime(normalized)

    if approved_at is None:
        return timezone.localtime().replace(second=0, microsecond=0)
    if timezone.is_naive(approved_at):
        approved_at = timezone.make_aware(approved_at, timezone.get_current_timezone())
    return timezone.localtime(approved_at).replace(second=0, microsecond=0)


PAYMENT_TYPE_LUMP_SUM = 'lump_sum'
PAYMENT_TYPE_INSTALLMENT = 'installment'


def _coerce_boolish(value, fallback=False):
    if isinstance(value, bool):
        return value
    if value in (None, ''):
        return fallback
    if isinstance(value, (int, float)):
        return bool(value)
    lowered = str(value).strip().lower()
    if lowered in {'true', '1', 'yes', 'y', 'on', 'interest_free'}:
        return True
    if lowered in {'false', '0', 'no', 'n', 'off'}:
        return False
    return fallback


def normalize_payment_terms(payload=None, text=''):
    payload = payload or {}
    source_text = str(
        text
        or payload.get('sourceText')
        or payload.get('source_text')
        or payload.get('rawText')
        or payload.get('text')
        or ''
    )
    search_text = source_text.replace(' ', '')

    raw_payment_type = str(
        payload.get('paymentType')
        or payload.get('payment_type')
        or payload.get('payType')
        or ''
    ).strip().lower()
    raw_months = (
        payload.get('installmentMonths')
        or payload.get('installment_months')
        or payload.get('months')
        or 0
    )
    try:
        installment_months = int(raw_months or 0)
    except (TypeError, ValueError):
        installment_months = 0

    month_match = re.search(r'(\d{1,2})\s*(?:개월|month|months)', source_text, re.IGNORECASE)
    if month_match:
        installment_months = max(installment_months, int(month_match.group(1)))

    is_interest_free = _coerce_boolish(
        payload.get('isInterestFreeInstallment')
        if 'isInterestFreeInstallment' in payload
        else payload.get('is_interest_free_installment'),
        fallback=False,
    ) or '무이자' in search_text

    is_installment = (
        raw_payment_type in {PAYMENT_TYPE_INSTALLMENT, 'installment', 'installments', '할부'}
        or installment_months > 1
        or '할부' in search_text
        or is_interest_free
    )
    if raw_payment_type in {PAYMENT_TYPE_LUMP_SUM, 'lump', 'single', '일시불'} and not ('할부' in search_text or is_interest_free):
        is_installment = False

    if is_installment:
        installment_months = max(installment_months, 2)
        payment_type = PAYMENT_TYPE_INSTALLMENT
    else:
        installment_months = 0
        is_interest_free = False
        payment_type = PAYMENT_TYPE_LUMP_SUM

    return {
        'paymentType': payment_type,
        'payment_type': payment_type,
        'installmentMonths': installment_months,
        'installment_months': installment_months,
        'isInterestFreeInstallment': bool(is_interest_free),
        'is_interest_free_installment': bool(is_interest_free),
    }


def serialize_transaction(transaction):
    approved_at = timezone.localtime(transaction.approved_at)
    approved_at_text = approved_at.isoformat()
    amount = int(transaction.amount)
    payment_terms = normalize_payment_terms(
        {
            'paymentType': getattr(transaction, 'payment_type', PAYMENT_TYPE_LUMP_SUM),
            'installmentMonths': getattr(transaction, 'installment_months', 0),
            'isInterestFreeInstallment': getattr(transaction, 'is_interest_free_installment', False),
        }
    )
    return {
        'id': transaction.public_id,
        'rawId': transaction.id,
        'cardId': str(transaction.card_id),
        'card_id': str(transaction.card_id),
        'merchant': transaction.merchant_name,
        'merchantName': transaction.merchant_name,
        'merchant_name': transaction.merchant_name,
        'category': transaction.category,
        'cat': transaction.category,
        'amount': amount,
        'amt': amount,
        'approvedAt': approved_at_text,
        'approved_at': approved_at_text,
        **payment_terms,
        'date': approved_at.date().isoformat(),
        'time': approved_at.strftime('%H:%M'),
        'icon': transaction.icon or '💳',
        'address': transaction.address or '-',
        'addr': transaction.address or '-',
        'sourceText': transaction.source_text,
        'isCancelled': transaction.is_cancelled,
        'is_cancelled': transaction.is_cancelled,
        'createdAt': timezone.localtime(transaction.created_at).isoformat(),
        'updatedAt': timezone.localtime(transaction.updated_at).isoformat(),
    }


def seed_public_transaction_id(user, source_id):
    return f'u{user.id}-{source_id}'


def cleanup_legacy_seed_transactions(user):
    legacy_ids = []
    for item in TRANSACTIONS:
        legacy_id = str(item['id'])
        current_id = seed_public_transaction_id(user, legacy_id)
        if legacy_id == current_id:
            continue
        if Transaction.objects.filter(user=user, public_id=current_id).exists():
            legacy_ids.append(legacy_id)
    if legacy_ids:
        Transaction.objects.filter(user=user, public_id__in=legacy_ids).delete()


def ensure_transactions_seeded(user=None):
    user = user or get_demo_user()
    cleanup_legacy_seed_transactions(user)
    existing_ids = set(Transaction.objects.values_list('public_id', flat=True))
    rows = []
    for item in TRANSACTIONS:
        public_id = seed_public_transaction_id(user, item['id'])
        if public_id in existing_ids:
            continue
        rows.append(
            Transaction(
                user=user,
                public_id=public_id,
                card_id=str(item['cardId']),
                merchant_name=item['merchantName'],
                category=item['category'],
                amount=int(item['amount']),
                approved_at=parse_approved_at(item['approvedAt']),
                payment_type=item.get('paymentType') or PAYMENT_TYPE_LUMP_SUM,
                installment_months=int(item.get('installmentMonths') or 0),
                is_interest_free_installment=bool(item.get('isInterestFreeInstallment') or False),
                icon=item.get('icon') or '💳',
                address=item.get('address') or '-',
            )
        )
    if rows:
        Transaction.objects.bulk_create(rows, ignore_conflicts=True)


def ensure_purchase_plans_seeded(user=None):
    user = user or get_demo_user()
    existing_seed_titles = set(
        PurchasePlan.objects.filter(user=user).values_list('title', flat=True)
    )

    for item in PURCHASE_PLANS:
        if item['title'] in existing_seed_titles:
            continue
        PurchasePlan.objects.create(
            user=user,
            title=item['title'][:120],
            plan_type=item.get('type', '큰 지출')[:40],
            expense_mode=item.get('expenseMode', 'planned-extra')[:40],
            total_budget=int(item.get('totalBudget') or 0),
            start_month=item.get('startMonth', '2026-07')[:7],
            end_month=item.get('endMonth', '2026-08')[:7],
            status=item.get('status', '선택 완료')[:30],
            selected_scenario_id=item.get('selectedScenarioId') or '',
            progress=int(item.get('progress') or 0),
            items=item.get('items') or [],
            scenarios=item.get('scenarios') or [],
        )


def transaction_queryset(request=None, user=None):
    user = user or (get_effective_user(request) if request is not None else get_demo_user())
    ensure_transactions_seeded(user)
    return Transaction.objects.filter(user=user)


def _month_key_from_transaction(item):
    date_text = str(item.get('date') or item.get('approvedAt') or item.get('approved_at') or '')
    return date_text[:7] if len(date_text) >= 7 else ''


def _shift_month(month_key, delta):
    try:
        year, month = [int(part) for part in str(month_key).split('-')[:2]]
    except (TypeError, ValueError):
        now = timezone.localtime()
        year, month = now.year, now.month
    month_index = year * 12 + month - 1 + int(delta)
    shifted_year = month_index // 12
    shifted_month = month_index % 12 + 1
    return f'{shifted_year:04d}-{shifted_month:02d}'


def _median(values):
    clean = sorted(_as_int(value) for value in values)
    if not clean:
        return 0
    middle = len(clean) // 2
    if len(clean) % 2:
        return clean[middle]
    return round((clean[middle - 1] + clean[middle]) / 2)


def _pct_change(current, base):
    current = _as_int(current)
    base = _as_int(base)
    if base <= 0:
        return None
    return round(((current - base) / base) * 100)


def _parse_category_overrides(request):
    raw_values = request.GET.getlist('recurringCategory')
    raw_values.extend((request.GET.get('recurringCategories') or '').split(','))
    return {
        value.strip()
        for value in raw_values
        if value and value.strip()
    }


def _build_spending_trend(transactions, recurring_overrides=None):
    recurring_overrides = set(recurring_overrides or [])
    expenses = [item for item in transactions if _as_int(item.get('amount')) < 0]
    months = sorted({month for month in (_month_key_from_transaction(item) for item in expenses) if month})
    current_month = months[-1] if months else timezone.localtime().strftime('%Y-%m')
    previous_month = _shift_month(current_month, -1)
    baseline_months = [_shift_month(current_month, -index) for index in range(1, 7)]

    by_month_category = defaultdict(int)
    by_month_total = defaultdict(int)
    for item in expenses:
        month = _month_key_from_transaction(item)
        if not month:
            continue
        amount = abs(_as_int(item.get('amount')))
        category = item.get('category') or item.get('cat') or '기타'
        by_month_category[(month, category)] += amount
        by_month_total[month] += amount

    categories = sorted({category for _, category in by_month_category.keys()})
    category_changes = []
    adjusted_total = 0

    for category in categories:
        current_amount = by_month_category[(current_month, category)]
        previous_amount = by_month_category[(previous_month, category)]
        baseline_values = [by_month_category[(month, category)] for month in baseline_months]
        baseline_average = round(sum(baseline_values) / len(baseline_values)) if baseline_values else 0
        baseline_median = _median(baseline_values)
        baseline_reference = max(baseline_median, baseline_average)
        delta_from_previous = current_amount - previous_amount
        delta_from_baseline = current_amount - baseline_reference
        detected_one_time = (
            current_amount >= 50000
            and (
                (baseline_reference > 0 and current_amount >= baseline_reference * 1.75 and delta_from_baseline >= 35000)
                or (baseline_reference == 0 and current_amount >= 80000)
            )
        )
        one_time = detected_one_time and category not in recurring_overrides
        if one_time:
            adjusted_amount = min(current_amount, round(max(baseline_reference, current_amount * 0.45)))
            status = 'one-time'
        elif detected_one_time and category in recurring_overrides:
            adjusted_amount = current_amount
            status = 'recurring-confirmed'
        elif delta_from_baseline >= 30000 and baseline_reference > 0:
            adjusted_amount = current_amount
            status = 'increase'
        elif delta_from_baseline <= -30000 and baseline_reference > 0:
            adjusted_amount = current_amount
            status = 'decrease'
        else:
            adjusted_amount = current_amount
            status = 'stable'
        adjusted_total += adjusted_amount
        category_changes.append(
            {
                'category': category,
                'currentAmount': current_amount,
                'previousAmount': previous_amount,
                'baselineAverage': baseline_average,
                'baselineMedian': baseline_median,
                'baselineReference': baseline_reference,
                'deltaFromPrevious': delta_from_previous,
                'deltaFromBaseline': delta_from_baseline,
                'changeRateFromBaseline': _pct_change(current_amount, baseline_reference),
                'adjustedAmount': adjusted_amount,
                'recommendationWeight': round(adjusted_amount / current_amount, 2) if current_amount else 0,
                'status': status,
                'oneTimeCandidate': one_time,
                'detectedOneTimeCandidate': detected_one_time,
                'userConfirmedRecurring': category in recurring_overrides,
            }
        )

    category_changes.sort(key=lambda item: abs(item['deltaFromBaseline']), reverse=True)
    current_total = by_month_total[current_month]
    previous_total = by_month_total[previous_month]
    baseline_totals = [by_month_total[month] for month in baseline_months]
    baseline_total_average = round(sum(baseline_totals) / len(baseline_totals)) if baseline_totals else 0

    return {
        'currentMonth': current_month,
        'previousMonth': previous_month,
        'baselineMonths': baseline_months,
        'basisLabel': '최근 6개월 기준',
        'total': {
            'current': current_total,
            'previous': previous_total,
            'baselineAverage': baseline_total_average,
            'deltaFromPrevious': current_total - previous_total,
            'deltaFromBaseline': current_total - baseline_total_average,
            'adjustedForRecommendation': adjusted_total,
        },
        'categoryChanges': category_changes,
        'oneTimeCandidates': [item for item in category_changes if item['oneTimeCandidate']][:4],
        'reviewCandidates': [item for item in category_changes if item['detectedOneTimeCandidate']][:4],
        'recurringOverrides': sorted(recurring_overrides),
        'recurringCategories': [item for item in category_changes if not item['oneTimeCandidate'] and item['currentAmount'] > 0][:5],
    }


def get_transaction_or_404(request, transaction_id):
    try:
        return transaction_queryset(request).get(public_id=str(transaction_id))
    except Transaction.DoesNotExist:
        raise Http404('거래내역을 찾을 수 없습니다.')


def create_transaction_from_payload(payload, user=None):
    data = build_transaction(payload)
    return Transaction.objects.create(
        user=user,
        public_id=data['id'],
        card_id=data['cardId'],
        merchant_name=data['merchantName'],
        category=data['category'],
        amount=data['amount'],
        approved_at=parse_approved_at(data['approvedAt']),
        payment_type=data['paymentType'],
        installment_months=data['installmentMonths'],
        is_interest_free_installment=data['isInterestFreeInstallment'],
        icon=data.get('icon') or '💳',
        address=data.get('address') or '직접 입력',
        source_text=payload.get('sourceText') or payload.get('source_text') or '',
    )


def ensure_community_seeded():
    if CommunityPost.objects.exists():
        return

    demo_user = get_demo_user()
    seed_posts = [
        {
            'title': 'LOCA LIKIT Eat vs 카드의정석2 SHOPPER 비교 후기',
            'body': '6개월 사용 후 솔직한 후기입니다. LIKIT Eat는 식비와 카페 결제 관리가 편하고, 카드의정석2 SHOPPER는 쇼핑 혜택이 매력적이에요.',
            'author': '이승민',
            'avatar': '이',
            'tags': ['카드비교', '생활카드', '우리카드'],
            'likes': 47,
            'liked': False,
            'comments': [
                {'author': '남주현', 'avatar': '남', 'body': 'SHOPPER 전월 실적 채우는 게 생각보다 괜찮나요?'},
                {'author': '박서연', 'avatar': '박', 'body': '쇼핑몰 자주 쓰면 체감 혜택이 꽤 있어요.'},
            ],
        },
        {
            'title': '월 30만원으로 카드 혜택 최대화하는 법',
            'body': '실적 채우기 어려운 분들을 위한 가이드입니다. 필수 지출 항목부터 카드 혜택을 최대로 누리는 방법을 공유합니다.',
            'author': '박서연',
            'avatar': '박',
            'tags': ['카드전략', '혜택최대화'],
            'likes': 89,
            'liked': True,
            'comments': [{'author': '최민준', 'avatar': '최', 'body': '교통비랑 구독 먼저 묶는 팁 좋네요.'}],
        },
        {
            'title': 'LOCA 100을 보조 카드로 두는 방식',
            'body': '주력 할인 카드가 애매한 결제는 LOCA 100 같은 기본 할인 카드로 받쳐두는 방식이 깔끔했습니다.',
            'author': '최민준',
            'avatar': '최',
            'tags': ['롯데카드', '생활'],
            'likes': 34,
            'liked': False,
            'comments': [],
        },
    ]

    for item in seed_posts:
        comments = item.pop('comments')
        post = CommunityPost.objects.create(user=demo_user, **item)
        for comment in comments:
            CommunityComment.objects.create(user=demo_user, post=post, **comment)


def serialize_comment(comment, viewer=None):
    created_at = timezone.localtime(comment.created_at)
    return {
        'id': f'cm{comment.id}',
        'rawId': comment.id,
        'editable': bool(viewer and comment.user_id == viewer.id),
        'author': comment.author,
        'avatar': comment.avatar,
        'body': comment.body,
        'text': comment.body,
        'date': created_at.date().isoformat(),
        'createdAt': created_at.isoformat(),
    }


def viewer_liked_post(post, viewer=None):
    if not viewer:
        return False
    if hasattr(post, '_viewer_liked'):
        return bool(post._viewer_liked)
    return CommunityPostLike.objects.filter(post=post, user=viewer).exists()


def serialize_community_post(post, include_comments=False, viewer=None):
    created_at = timezone.localtime(post.created_at)
    payload = {
        'id': f'c{post.id}',
        'rawId': post.id,
        'editable': bool(viewer and post.user_id == viewer.id),
        'title': post.title,
        'body': post.body,
        'author': post.author,
        'avatar': post.avatar,
        'date': created_at.date().isoformat(),
        'createdAt': created_at.isoformat(),
        'updatedAt': timezone.localtime(post.updated_at).isoformat(),
        'likes': post.likes,
        'liked': viewer_liked_post(post, viewer),
        'comments': post.comment_set.count(),
        'commentCount': post.comment_set.count(),
        'tags': post.tags or [],
    }
    if include_comments:
        payload['commentItems'] = [serialize_comment(comment, viewer=viewer) for comment in post.comment_set.all()]
    return payload


def serialize_analysis_record(record):
    created_at = timezone.localtime(record.created_at)
    return {
        'id': f'a{record.id}',
        'rawId': record.id,
        'analysisType': record.analysis_type,
        'cacheKey': record.cache_key,
        'title': record.title,
        'inputPayload': record.input_payload,
        'resultPayload': record.result_payload,
        'aiMode': record.ai_mode,
        'confidence': record.confidence,
        'createdAt': created_at.isoformat(),
        'date': created_at.date().isoformat(),
    }


def analysis_cache_key(payload):
    encoded = json.dumps(payload or {}, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(encoded.encode('utf-8')).hexdigest()


def save_analysis_record(analysis_type, title, input_payload, result_payload, cache_key='', user=None):
    confidence = result_payload.get('confidence') if isinstance(result_payload, dict) else None
    try:
        confidence = float(confidence) if confidence is not None else None
    except (TypeError, ValueError):
        confidence = None

    return AIAnalysisRecord.objects.create(
        user=user,
        analysis_type=analysis_type,
        cache_key=(cache_key or '')[:80],
        title=(title or '')[:120],
        input_payload=input_payload or {},
        result_payload=result_payload or {},
        ai_mode=str((result_payload or {}).get('aiMode') or '')[:20],
        confidence=confidence,
    )


def public_plan_id(plan):
    return f'p{plan.id}'


def normalize_plan_id(plan_id):
    raw_id = str(plan_id).lstrip('p')
    if not raw_id.isdigit():
        raise Http404('소비 계획을 찾을 수 없습니다.')
    return int(raw_id)


def get_purchase_plan_or_404(request, plan_id):
    try:
        return PurchasePlan.objects.get(id=normalize_plan_id(plan_id), user=get_effective_user(request))
    except PurchasePlan.DoesNotExist:
        raise Http404('소비 계획을 찾을 수 없습니다.')


def normalize_plan_items(value):
    if not isinstance(value, list):
        return []

    items = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            continue
        try:
            amount = abs(int(item.get('amount') or 0))
        except (TypeError, ValueError):
            amount = 0
        payment_terms = normalize_payment_terms(item)
        items.append(
            {
                'id': str(item.get('id') or f'i{index}'),
                'name': str(item.get('name') or f'구매 항목 {index}').strip()[:80],
                'category': str(item.get('category') or '기타').strip()[:40],
                'amount': amount,
                'targetMonth': str(item.get('targetMonth') or item.get('target_month') or '')[:7],
                'paymentType': payment_terms['paymentType'],
                'installmentMonths': payment_terms['installmentMonths'],
                'isInterestFreeInstallment': payment_terms['isInterestFreeInstallment'],
                'required': bool(item.get('required', True)),
                'flexible': bool(item.get('flexible', True)),
            }
        )
    return items[:20]


def serialize_purchase_plan(plan):
    return {
        'id': public_plan_id(plan),
        'rawId': plan.id,
        'title': plan.title,
        'type': plan.plan_type,
        'expenseMode': plan.expense_mode,
        'totalBudget': plan.total_budget,
        'startMonth': plan.start_month,
        'endMonth': plan.end_month,
        'status': plan.status,
        'selectedScenarioId': plan.selected_scenario_id,
        'createdAt': timezone.localtime(plan.created_at).date().isoformat(),
        'updatedAt': timezone.localtime(plan.updated_at).isoformat(),
        'progress': plan.progress,
        'items': plan.items or [],
        'scenarios': plan.scenarios or [],
        'analysisRecordId': f'a{plan.analysis_record_id}' if plan.analysis_record_id else '',
    }


def create_purchase_plan_from_payload(payload, user=None):
    items = normalize_plan_items(payload.get('items') or [])
    return PurchasePlan.objects.create(
        user=user,
        title=(payload.get('title') or '새 소비 계획')[:120],
        plan_type=(payload.get('type') or payload.get('planType') or '기타')[:40],
        expense_mode=(payload.get('expenseMode') or payload.get('expense_mode') or 'planned-extra')[:40],
        total_budget=abs(int(payload.get('totalBudget') or payload.get('budget') or 0)),
        start_month=(payload.get('startMonth') or payload.get('start_month') or '2026-07')[:7],
        end_month=(payload.get('endMonth') or payload.get('end_month') or '2026-09')[:7],
        status=(payload.get('status') or '작성 중')[:30],
        selected_scenario_id=payload.get('selectedScenarioId') or '',
        items=items,
        scenarios=payload.get('scenarios') if isinstance(payload.get('scenarios'), list) else [],
    )


def build_plan_scenarios(plan):
    items = plan.items or []
    total_amount = sum(int(item.get('amount') or 0) for item in items)
    budget_diff = int(plan.total_budget or 0) - total_amount
    first_month_items = [
        {
            'name': item.get('name'),
            'amount': item.get('amount'),
            'card': 'LOCA LIKIT Eat',
            'benefit': min(int(item.get('amount') or 0) // 100, 30000),
            'note': '식비와 카페 생활권 혜택을 함께 고려한 배정입니다.',
            'status': '구매 예정',
        }
        for item in items[:2]
    ]
    last_month_items = [
        {
            'name': item.get('name'),
            'amount': item.get('amount'),
            'card': '카드의정석2 SHOPPER',
            'benefit': min(int(item.get('amount') or 0) // 120, 25000),
            'note': '쇼핑/생활 혜택 카드에 지출을 분산했습니다.',
            'status': '구매 예정',
        }
        for item in items[2:]
    ]
    max_monthly_spend = max([int(item.get('amount') or 0) for item in items] or [0])
    return [
        {
            'id': 'sc1',
            'type': '혜택 최대화',
            'recommended': True,
            'totalAmount': total_amount,
            'totalBenefit': 75000,
            'budgetDiff': budget_diff,
            'maxMonthlySpend': max_monthly_spend,
            'achievedCards': 2,
            'reasons': ['보유 카드 혜택을 우선 배정했습니다.', '다음 달 혜택 조건 가능성을 함께 고려했습니다.'],
            'warning': None,
            'monthlyPlan': [
                {'month': plan.start_month, 'items': first_month_items},
                {'month': plan.end_month, 'items': last_month_items},
            ],
            'cardSummary': [
                {'cardName': 'LOCA LIKIT Eat', 'totalAmount': sum(int(item.get('amount') or 0) for item in items[:2]), 'benefit': 45000, 'achieved': True, 'remainingLimit': 100000, 'itemCount': len(items[:2])},
                {'cardName': '카드의정석2 SHOPPER', 'totalAmount': sum(int(item.get('amount') or 0) for item in items[2:]), 'benefit': 30000, 'achieved': True, 'remainingLimit': 50000, 'itemCount': len(items[2:])},
            ],
            'aiExplanation': '입력한 품목을 월별로 나누고 보유 카드 혜택이 큰 카드부터 배정했습니다.',
        },
        {
            'id': 'sc2',
            'type': '예산 안정',
            'recommended': False,
            'totalAmount': total_amount,
            'totalBenefit': 55000,
            'budgetDiff': budget_diff,
            'maxMonthlySpend': (total_amount + 2) // 3 if total_amount else 0,
            'achievedCards': 1,
            'reasons': ['월별 지출 쏠림을 줄였습니다.', '예산 초과 위험을 낮추는 배치입니다.'],
            'warning': None if budget_diff >= 0 else '총 구매 금액이 예산을 초과합니다.',
            'monthlyPlan': [],
            'cardSummary': [],
            'aiExplanation': '혜택보다 현금 흐름 안정성을 우선한 시나리오입니다.',
        },
        {
            'id': 'sc3',
            'type': '실적 균형',
            'recommended': False,
            'totalAmount': total_amount,
            'totalBenefit': 65000,
            'budgetDiff': budget_diff,
            'maxMonthlySpend': max_monthly_spend,
            'achievedCards': 2,
            'reasons': ['카드별 실적을 고르게 채우도록 배정했습니다.', '혜택 한도 소진 가능성을 줄였습니다.'],
            'warning': None,
            'monthlyPlan': [],
            'cardSummary': [],
            'aiExplanation': '여러 카드의 실적 조건을 함께 달성하는 방향입니다.',
        },
    ]


def get_community_post_or_404(post_id):
    raw_id = str(post_id).lstrip('c')
    if not raw_id.isdigit():
        raise Http404('게시글을 찾을 수 없습니다.')
    try:
        return CommunityPost.objects.get(id=int(raw_id))
    except CommunityPost.DoesNotExist:
        raise Http404('게시글을 찾을 수 없습니다.')


def card_image(request, filename):
    safe_name = filename.split('/')[-1].split('\\')[-1]
    path = settings.CARD_IMAGE_DIR / safe_name
    if not path.exists() or not path.is_file():
        raise Http404('카드 이미지를 찾을 수 없습니다.')
    return FileResponse(path.open('rb'))


def search_limit(request, default=8, maximum=50):
    try:
        value = int(request.GET.get('limit', default))
    except (TypeError, ValueError):
        value = default
    return max(1, min(value, maximum))


def compact_search_text(*values):
    return ' '.join(str(value or '').strip() for value in values if str(value or '').strip())


def join_search_parts(*values):
    return ' · '.join(str(value or '').strip() for value in values if str(value or '').strip())


def search_score(query, *values):
    if not query:
        return 1

    normalized_query = query.casefold()
    tokens = [token for token in normalized_query.split() if token]
    score = 0
    for index, value in enumerate(values):
        text = str(value or '').casefold()
        if not text:
            continue
        weight = max(1, 4 - index)
        if text == normalized_query:
            score += 120 * weight
        elif text.startswith(normalized_query):
            score += 80 * weight
        elif normalized_query in text:
            score += 45 * weight
        score += sum(10 * weight for token in tokens if token in text)
    return score


def clip_search_items(items, query, limit):
    if query:
        items.sort(key=lambda item: item.get('_score', 0), reverse=True)
    clipped = []
    for item in items[:limit]:
        clipped.append({key: value for key, value in item.items() if key != '_score'})
    return clipped


def build_card_search_item(card, query, owned_ids):
    card_id = str(card.get('id') or card.get('cardAdId') or card.get('card_ad_id') or '')
    title = card.get('name') or card.get('cardName') or card.get('card_name') or '카드'
    issuer = card.get('issuer') or card.get('issuerName') or card.get('issuer_name') or ''
    benefit = card.get('benefitSummary') or card.get('titleDescription') or card.get('title_description') or ''
    owned = card_id in owned_ids
    return {
        'id': card_id,
        'type': 'card',
        'title': title,
        'description': join_search_parts(issuer, benefit),
        'path': f'/cards/{card_id}' if owned else f'/cards/apply/{card_id}',
        'badge': '보유중' if owned else '',
        'imageUrl': card.get('imageUrl') or card.get('image_url') or '',
        'meta': {
            'issuer': issuer,
            'benefitSummary': benefit,
            'owned': owned,
        },
        '_score': search_score(query, title, issuer, benefit, card_id) + (90 if owned else 0),
    }


def build_transaction_search_item(tx, query):
    amount = int(tx.get('amount') or tx.get('amt') or 0)
    title = tx.get('merchant') or tx.get('merchantName') or '거래내역'
    category = tx.get('category') or tx.get('cat') or ''
    date = tx.get('date') or ''
    amount_text = f'{abs(amount):,}원'
    direction = '입금' if amount > 0 else '결제'
    return {
        'id': tx.get('id'),
        'type': 'transaction',
        'title': title,
        'description': join_search_parts(category, date, amount_text),
        'path': f"/transactions/{tx.get('id')}",
        'badge': direction,
        'meta': {
            'category': category,
            'date': date,
            'amount': amount,
        },
        '_score': search_score(query, title, category, date, amount_text, tx.get('address') or tx.get('addr')),
    }


def build_community_search_item(post, query):
    tags = post.get('tags') or []
    tag_text = ' '.join(tags)
    title = post.get('title') or '커뮤니티 글'
    body = post.get('body') or ''
    author = post.get('author') or ''
    return {
        'id': post.get('id'),
        'type': 'community',
        'title': title,
        'description': compact_search_text(author, body[:45]),
        'path': f"/community/{post.get('id')}",
        'badge': f"댓글 {post.get('comments') or post.get('commentCount') or 0}",
        'meta': {
            'author': author,
            'tags': tags,
        },
        '_score': search_score(query, title, body, author, tag_text),
    }


def search_items(request):
    user, error_response = require_request_user(request)
    if error_response:
        return error_response
    query = (request.GET.get('q') or request.GET.get('search') or '').strip()
    search_type = (request.GET.get('type') or 'all').strip()
    if search_type not in {'all', 'card', 'transaction', 'community'}:
        search_type = 'all'

    limit = search_limit(request, default=12 if search_type == 'all' else 24)
    per_section_limit = limit if search_type != 'all' else min(5, limit)
    card_section_limit = limit if search_type == 'card' else min(8, limit)
    sections = []
    items = []

    owned_cards = list(owned_card_queryset(request))
    owned_ids = {str(item.card_id) for item in owned_cards}

    if search_type in {'all', 'card'}:
        card_candidates = []
        if query:
            card_candidates = fetch_cards(request, limit=max(card_section_limit * 4, 36), search=query)
            for owned_card in owned_cards:
                already_included = any(
                    str(card.get('cardAdId') or card.get('id')) == str(owned_card.card_id)
                    for card in card_candidates
                )
                if already_included or not str(owned_card.card_id).isdigit():
                    continue
                card = fetch_card(int(owned_card.card_id), request)
                if card and search_score(query, card.get('cardName'), card.get('issuerName'), card.get('benefitSummary')) > 0:
                    card_candidates.append(card)
        else:
            card_candidates = fetch_cards(
                request,
                limit=max(card_section_limit * 3, 36),
                active_only=search_type == 'all',
            )

        card_items = clip_search_items(
            [build_card_search_item(card, query, owned_ids) for card in card_candidates],
            query,
            card_section_limit,
        )
        sections.append({'type': 'card', 'title': '카드', 'count': len(card_items), 'items': card_items})
        items.extend(card_items)

    if search_type in {'all', 'transaction'}:
        tx_queryset = transaction_queryset(request)
        if query:
            tx_queryset = tx_queryset.filter(
                Q(merchant_name__icontains=query)
                | Q(category__icontains=query)
                | Q(address__icontains=query)
                | Q(source_text__icontains=query)
                | Q(card_id__icontains=query)
            )
        tx_rows = [serialize_transaction(tx) for tx in tx_queryset[: limit * 3]]
        tx_items = clip_search_items(
            [build_transaction_search_item(tx, query) for tx in tx_rows],
            query,
            per_section_limit,
        )
        sections.append({'type': 'transaction', 'title': '거래', 'count': len(tx_items), 'items': tx_items})
        items.extend(tx_items)

    if search_type in {'all', 'community'}:
        ensure_community_seeded()
        posts = CommunityPost.objects.all()
        if query:
            posts = posts.filter(Q(title__icontains=query) | Q(body__icontains=query) | Q(author__icontains=query))
        post_rows = [serialize_community_post(post) for post in posts[: limit * 3]]
        community_items = clip_search_items(
            [build_community_search_item(post, query) for post in post_rows],
            query,
            per_section_limit,
        )
        sections.append({'type': 'community', 'title': '커뮤니티', 'count': len(community_items), 'items': community_items})
        items.extend(community_items)

    return json_response(
        {
            'query': query,
            'type': search_type,
            'count': len(items),
            'sections': [section for section in sections if section['items']],
            'results': items[:limit],
        }
    )


def card_list(request):
    ids = [value.strip() for value in request.GET.get('ids', '').split(',') if value.strip()]
    if ids:
        cards = []
        for raw_id in ids:
            if not raw_id.isdigit():
                continue
            card = fetch_card(int(raw_id), request)
            if card:
                cards.append(card)
        return json_response({'count': len(cards), 'results': cards})

    limit = min(int(request.GET.get('limit', 30)), 100)
    cards = fetch_cards(
        request,
        limit=limit,
        search=request.GET.get('search', '').strip(),
        issuer=request.GET.get('issuer', '').strip(),
        active_only=request.GET.get('active') == '1',
    )
    return json_response({'count': len(cards), 'results': cards})


def card_detail(request, card_ad_id):
    card = fetch_card(card_ad_id, request)
    if not card:
        return json_response({'detail': '카드를 찾을 수 없습니다.'}, status=404)
    return json_response(card)


def ensure_owned_cards_seeded(user=None):
    user = user or get_demo_user()
    existing = list(OwnedCard.objects.filter(user=user).order_by('display_order', 'id'))
    if existing:
        existing_ids = {str(card.card_id) for card in existing}
        if any(existing_ids == legacy_ids and len(existing) == len(legacy_ids) for legacy_ids in LEGACY_DEFAULT_OWNED_CARD_ID_SETS):
            OwnedCard.objects.filter(user=user).delete()
        else:
            return
    if OwnedCard.objects.filter(user=user).exists():
        return
    OwnedCard.objects.bulk_create(
        [
            OwnedCard(user=user, card_id=card_id, display_order=index)
            for index, card_id in enumerate(DEFAULT_OWNED_CARD_IDS)
        ],
        ignore_conflicts=True,
    )


def owned_card_queryset(request=None, user=None):
    user = user or (get_effective_user(request) if request is not None else get_demo_user())
    ensure_owned_cards_seeded(user)
    return OwnedCard.objects.filter(user=user)


def serialize_owned_card(owned_card, request):
    if not str(owned_card.card_id).isdigit():
        return None
    card = fetch_card(int(owned_card.card_id), request)
    if not card:
        return None
    card['ownedCardId'] = f'oc{owned_card.id}'
    card['owned_card_id'] = owned_card.id
    card['nickname'] = owned_card.nickname
    card['displayOrder'] = owned_card.display_order
    card['display_order'] = owned_card.display_order
    card['ownedAt'] = timezone.localtime(owned_card.created_at).isoformat()
    return card


@csrf_exempt
def owned_card_list(request):
    user, error_response = require_request_user(request)
    if error_response:
        return error_response
    owned_cards = owned_card_queryset(user=user)

    if request.method == 'GET':
        cards = []
        for owned_card in owned_cards:
            card = serialize_owned_card(owned_card, request)
            if card:
                cards.append(card)
        return json_response({'count': len(cards), 'results': cards})

    if request.method == 'POST':
        payload, error_response = parse_request_body(request)
        if error_response:
            return error_response

        raw_card_id = payload.get('cardId') or payload.get('cardAdId') or payload.get('card_ad_id') or payload.get('id')
        card_id = str(raw_card_id or '').strip()
        if not card_id.isdigit():
            return json_response({'detail': '추가할 카드 ID가 필요합니다.'}, status=400)

        card = fetch_card(int(card_id), request)
        if not card:
            return json_response({'detail': '카드를 찾을 수 없습니다.'}, status=404)

        max_order = owned_cards.aggregate(value=Max('display_order'))['value']
        owned_card, created = OwnedCard.objects.get_or_create(
            user=user,
            card_id=card_id,
            defaults={
                'nickname': (payload.get('nickname') or '')[:80],
                'display_order': 0 if max_order is None else max_order + 1,
            },
        )
        if not created and 'nickname' in payload:
            owned_card.nickname = (payload.get('nickname') or '')[:80]
            owned_card.save(update_fields=['nickname', 'updated_at'])
        return json_response(serialize_owned_card(owned_card, request), status=201 if created else 200)

    return json_response({'detail': '지원하지 않는 요청입니다.'}, status=405)


@csrf_exempt
def owned_card_detail(request, card_id):
    user, error_response = require_request_user(request)
    if error_response:
        return error_response
    owned_cards = owned_card_queryset(user=user)

    raw_id = str(card_id).strip()
    try:
        if raw_id.startswith('oc') and raw_id[2:].isdigit():
            owned_card = owned_cards.get(id=int(raw_id[2:]))
        else:
            owned_card = owned_cards.get(card_id=raw_id)
    except OwnedCard.DoesNotExist:
        return json_response({'detail': '보유 카드가 아닙니다.'}, status=404)

    if request.method == 'DELETE':
        owned_card.delete()
        return json_response({'ok': True})

    if request.method in {'PATCH', 'PUT'}:
        payload, error_response = parse_request_body(request)
        if error_response:
            return error_response
        if 'nickname' in payload:
            owned_card.nickname = (payload.get('nickname') or '')[:80]
        if 'displayOrder' in payload or 'display_order' in payload:
            try:
                owned_card.display_order = max(0, int(payload.get('displayOrder') or payload.get('display_order') or 0))
            except (TypeError, ValueError):
                return json_response({'detail': '표시 순서가 올바르지 않습니다.'}, status=400)
        owned_card.save()
        return json_response(serialize_owned_card(owned_card, request))

    return json_response({'detail': '지원하지 않는 요청입니다.'}, status=405)


@csrf_exempt
def transaction_list(request):
    user, error_response = require_request_user(request)
    if error_response:
        return error_response
    if request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return json_response({'detail': 'JSON 형식이 올바르지 않습니다.'}, status=400)
        transaction = create_transaction_from_payload(payload, user=user)
        return json_response(serialize_transaction(transaction), status=201)

    card_id = request.GET.get('cardId') or request.GET.get('card_id')
    category = request.GET.get('category')
    transactions = transaction_queryset(user=user)
    if card_id:
        transactions = transactions.filter(card_id=str(card_id))
    if category:
        transactions = transactions.filter(category=category)
    rows = [serialize_transaction(item) for item in transactions]
    return json_response({'count': len(rows), 'results': rows})


def transaction_detail(request, transaction_id):
    user, error_response = require_request_user(request)
    if error_response:
        return error_response
    transaction = get_transaction_or_404(request, transaction_id)
    return json_response(serialize_transaction(transaction))


def infer_merchant(text):
    compact = text.replace(' ', '')
    for keyword, category, icon in MERCHANT_HINTS:
        if keyword.replace(' ', '') in compact:
            full_match = re.search(rf'([가-힣A-Za-z0-9&().\- ]*{re.escape(keyword)}[가-힣A-Za-z0-9&().\- ]*?)(?:에서| 승인| 결제|\s+[\d,]+원)', text)
            merchant = full_match.group(1).strip() if full_match else keyword
            merchant = re.sub(r'^(오늘|어제|방금|카드|신한카드|우리카드|롯데카드)\s+', '', merchant).strip()
            return merchant or keyword, category, icon

    candidates = re.findall(r'([가-힣A-Za-z0-9&().\- ]{2,30})(?:에서| 승인| 결제|\s+[\d,]+원)', text)
    if candidates:
        merchant = candidates[-1].strip()
        merchant = re.sub(r'^(오늘|어제|방금|카드|신한카드|우리카드|롯데카드)\s+', '', merchant).strip()
        return merchant or '가맹점 미확인', '기타', '💳'
    return '가맹점 미확인', '기타', '💳'


def infer_card_id(text):
    compact = text.replace(' ', '').upper()
    for keyword, card_id in CARD_HINTS:
        if keyword.replace(' ', '').upper() in compact:
            return card_id
    return '10029'


def infer_amount(text):
    matches = re.findall(r'([0-9][0-9,]*)\s*(?:원|KRW|₩)', text, re.IGNORECASE)
    if not matches:
        matches = re.findall(r'([0-9][0-9,]{2,})', text)
    if not matches:
        return 0
    return -abs(int(matches[-1].replace(',', '')))


def infer_approved_at(text):
    now = timezone.localtime()
    month_day = re.search(r'(\d{1,2})[./월-]\s*(\d{1,2})\s*(?:일)?', text)
    time_match = re.search(r'(\d{1,2})[:시]\s*(\d{2})', text)
    hour = int(time_match.group(1)) if time_match else now.hour
    minute = int(time_match.group(2)) if time_match else now.minute

    if '어제' in text:
        base = now - timedelta(days=1)
        return base.replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()
    if month_day:
        month, day = int(month_day.group(1)), int(month_day.group(2))
        return now.replace(month=month, day=day, hour=hour, minute=minute, second=0, microsecond=0).isoformat()
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()


def build_transaction(payload):
    approved_at = payload.get('approvedAt') or payload.get('approved_at') or timezone.localtime().replace(second=0, microsecond=0).isoformat()
    amount = int(payload.get('amount') or payload.get('amt') or 0)
    if amount > 0 and payload.get('category') != '수입':
        amount = -amount
    public_id = payload.get('id') or f'u{int(datetime.now().timestamp() * 1000)}'
    if Transaction.objects.filter(public_id=public_id).exists():
        public_id = f'u{int(datetime.now().timestamp() * 1000)}'
    payment_terms = normalize_payment_terms(payload)
    return {
        'id': public_id,
        'cardId': str(payload.get('cardId') or payload.get('card_id') or '10029'),
        'merchantName': payload.get('merchantName') or payload.get('merchant_name') or payload.get('merchant') or '가맹점 미확인',
        'category': payload.get('category') or payload.get('cat') or '기타',
        'amount': amount,
        'approvedAt': approved_at,
        **payment_terms,
        'icon': payload.get('icon') or '💳',
        'address': payload.get('address') or payload.get('addr') or '직접 입력',
    }


@csrf_exempt
def parse_transaction(request):
    user, error_response = require_request_user(request)
    if error_response:
        return error_response
    if request.method != 'POST':
        return json_response({'detail': 'POST 요청만 지원합니다.'}, status=405)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return json_response({'detail': 'JSON 형식이 올바르지 않습니다.'}, status=400)

    text = (payload.get('rawText') or payload.get('text') or payload.get('rawPrompt') or '').strip()
    if not text:
        return json_response({'detail': '분석할 결제 문구가 필요합니다.'}, status=400)

    ai_parsed = parse_transaction_with_ai(text)
    if ai_parsed:
        save_analysis_record(
            'transaction_parse',
            '결제내역 입력 보정',
            {'rawText': text},
            ai_parsed,
            user=user,
        )
        return json_response(ai_parsed)

    merchant, category, icon = infer_merchant(text)
    payment_terms = normalize_payment_terms(text=text)
    parsed = {
        'cardId': infer_card_id(text),
        'merchantName': merchant,
        'category': category,
        'amount': infer_amount(text),
        'approvedAt': infer_approved_at(text),
        **payment_terms,
        'icon': icon,
        'address': '직접 입력',
        'sourceText': text,
        'aiMode': 'mock',
        'confidence': 0.82 if merchant != '가맹점 미확인' and infer_amount(text) != 0 else 0.58,
        'reviewFields': ['merchantName', 'amount', 'approvedAt', 'cardId', 'paymentType'],
    }
    save_analysis_record(
        'transaction_parse',
        '결제내역 입력 보정',
        {'rawText': text},
        parsed,
        user=user,
    )
    return json_response(parsed)


def spending_summary(request):
    user, error_response = require_request_user(request)
    if error_response:
        return error_response
    transactions = [serialize_transaction(item) for item in transaction_queryset(user=user)]
    spending_trend = _build_spending_trend(transactions, _parse_category_overrides(request))
    current_month = spending_trend['currentMonth']
    expense_rows = [
        item
        for item in transactions
        if item['amount'] < 0 and _month_key_from_transaction(item) == current_month
    ]
    income_rows = [
        item
        for item in transactions
        if item['amount'] > 0 and _month_key_from_transaction(item) == current_month
    ]
    by_category = defaultdict(int)
    by_card = defaultdict(int)
    for item in expense_rows:
        amount = abs(item['amount'])
        by_category[item['category']] += amount
        by_card[item['cardId']] += amount

    summary = {
        'totalExpense': sum(abs(item['amount']) for item in expense_rows),
        'totalIncome': sum(item['amount'] for item in income_rows),
        'byCategory': [{'category': key, 'amount': value} for key, value in by_category.items()],
        'byCard': [{'cardId': key, 'amount': value} for key, value in by_card.items()],
        'period': {
            'currentMonth': current_month,
            'previousMonth': spending_trend['previousMonth'],
            'baselineMonths': spending_trend['baselineMonths'],
        },
        'spendingTrend': spending_trend,
    }

    include_ai = request.GET.get('ai') in {'1', 'true', 'yes'}
    refresh_ai = request.GET.get('refresh') in {'1', 'true', 'yes'} or request.GET.get('force') in {'1', 'true', 'yes'}
    cards = []
    for card_id in by_card.keys():
        if str(card_id).isdigit():
            card = fetch_card(int(card_id), request)
            if card:
                cards.append(card)
    input_summary = {
        'totalExpense': summary['totalExpense'],
        'totalIncome': summary['totalIncome'],
        'byCategory': summary['byCategory'],
        'byCard': summary['byCard'],
        'spendingTrend': spending_trend,
    }
    analysis_input = {
        'summary': input_summary,
        'transactions': transactions[:30],
        'cards': [
            {
                'id': card.get('id') or card.get('cardAdId') or card.get('card_ad_id'),
                'name': card.get('name') or card.get('cardName') or card.get('card_name'),
                'issuer': card.get('issuer') or card.get('issuerName') or card.get('issuer_name'),
            }
            for card in cards
        ],
    }
    cache_key = analysis_cache_key(analysis_input)

    if include_ai:
        latest_record = AIAnalysisRecord.objects.filter(
            user=user,
            analysis_type='spending_summary',
            cache_key=cache_key,
        ).first()
        if latest_record and not refresh_ai:
            summary['aiAnalysis'] = latest_record.result_payload or fallback_spending_analysis(summary)
            summary['aiAnalysisRecordId'] = f'a{latest_record.id}'
            summary['aiAnalysisCached'] = True
            summary['aiAnalysisCreatedAt'] = timezone.localtime(latest_record.created_at).isoformat()
            summary['aiAnalysisCacheKey'] = cache_key
            return json_response(summary)

        if not refresh_ai:
            summary['aiAnalysis'] = fallback_spending_analysis(summary)
            summary['aiAnalysisStatus'] = 'local'
            summary['aiAnalysisCached'] = False
            summary['aiAnalysisCacheKey'] = cache_key
            return json_response(summary)

        summary['aiAnalysis'] = analyze_spending_with_ai(input_summary, transactions, cards) or fallback_spending_analysis(summary)
        record = save_analysis_record(
            'spending_summary',
            summary['aiAnalysis'].get('summaryTitle') or '카드 소비 분석',
            analysis_input,
            summary['aiAnalysis'],
            cache_key=cache_key,
            user=user,
        )
        summary['aiAnalysisRecordId'] = f'a{record.id}'
        summary['aiAnalysisCached'] = False
        summary['aiAnalysisCreatedAt'] = timezone.localtime(record.created_at).isoformat()
        summary['aiAnalysisCacheKey'] = cache_key

    return json_response(summary)


def fallback_spending_analysis(summary):
    top_category = max(summary['byCategory'], key=lambda item: item['amount'], default={'category': '기타', 'amount': 0})
    trend = summary.get('spendingTrend') or {}
    one_time = (trend.get('oneTimeCandidates') or [None])[0]
    recurring = (trend.get('recurringCategories') or [None])[0]
    headline = f"{top_category['category']} 지출 비중이 가장 높습니다."
    if one_time:
        headline = f"{one_time['category']} 지출은 평소보다 높습니다."
    elif recurring:
        headline = f"반복 소비는 {recurring['category']} 중심으로 안정적으로 이어지고 있습니다."
    return {
        'schemaVersion': 'spending-analysis-v2',
        'summaryTitle': '이번 달 소비 요약',
        'headline': headline,
        'narrative': '최근 6개월 흐름과 이번 달 소비를 함께 반영했습니다.',
        'primaryInsight': {
            'label': '핵심 진단',
            'title': one_time['category'] if one_time else top_category['category'],
            'body': '일시적인 지출은 평소 소비와 분리해 카드 추천에 반영했습니다.' if one_time else '가장 큰 지출 항목을 기준으로 카드 혜택을 비교합니다.',
            'severity': 'attention' if one_time else 'info',
            'metricLabel': '대상 금액',
            'metricValue': one_time['currentAmount'] if one_time else top_category['amount'],
        },
        'summaryCards': [
            {'label': '이번 달', 'value': _krw((trend.get('total') or {}).get('current')), 'tone': 'blue'},
            {'label': '6개월 평균', 'value': _krw((trend.get('total') or {}).get('baselineAverage')), 'tone': 'gray'},
            {'label': '추천 기준', 'value': _krw((trend.get('total') or {}).get('adjustedForRecommendation')), 'tone': 'teal'},
        ],
        'savingOpportunities': [
            {
                'title': f"{top_category['category']} 지출 확인",
                'amount': 0,
                'reason': '최근 6개월 기준선과 이번 달 소비를 비교했습니다.',
                'action': '일시적인 지출은 평소 소비와 분리해 확인합니다.',
                'severity': 'info',
                'route': '/recommendations/new',
            }
        ],
        'categoryInsights': [
            {
                'category': top_category['category'],
                'amount': top_category['amount'],
                'insight': '현재 데이터에서 가장 큰 지출 항목입니다.',
            }
        ],
        'cardInsights': [],
        'warnings': ['실제 카드 혜택과 한도는 카드사 약관 확인이 필요합니다.'],
        'nextActions': ['상위 지출 확인', '카드 혜택 비교'],
        'actionButtons': [
            {'label': '카드 추천 보기', 'route': '/recommendations/new', 'intent': 'recommendation'},
        ],
        'aiMode': 'mock',
        'confidence': 0.55,
    }


def analysis_record_list(request):
    if request.method != 'GET':
        return json_response({'detail': 'GET 요청만 지원합니다.'}, status=405)

    user, error_response = require_request_user(request)
    if error_response:
        return error_response
    records = AIAnalysisRecord.objects.filter(user=user)
    analysis_type = (request.GET.get('type') or request.GET.get('analysisType') or '').strip()
    if analysis_type:
        records = records.filter(analysis_type=analysis_type)
    cache_key = (request.GET.get('cacheKey') or request.GET.get('cache_key') or '').strip()
    if cache_key:
        records = records.filter(cache_key=cache_key)

    try:
        limit = min(max(int(request.GET.get('limit', 20)), 1), 100)
    except (TypeError, ValueError):
        limit = 20

    rows = [serialize_analysis_record(record) for record in records[:limit]]
    return json_response({'count': records.count(), 'results': rows})


def build_chat_context(request):
    transactions = [serialize_transaction(item) for item in transaction_queryset(request)]
    spending_trend = _build_spending_trend(transactions, _parse_category_overrides(request))
    current_month = spending_trend['currentMonth']
    current_transactions = [
        item for item in transactions if _month_key_from_transaction(item) == current_month
    ]
    expense_rows = [item for item in current_transactions if item['amount'] < 0]
    income_rows = [item for item in current_transactions if item['amount'] > 0]
    by_category = defaultdict(int)
    by_card = defaultdict(int)
    for item in expense_rows:
        amount = abs(item['amount'])
        by_category[item['category']] += amount
        by_card[item['cardId']] += amount

    summary = {
        'totalExpense': sum(abs(item['amount']) for item in expense_rows),
        'totalIncome': sum(item['amount'] for item in income_rows),
        'byCategory': [{'category': key, 'amount': value} for key, value in by_category.items()],
        'byCard': [{'cardId': key, 'amount': value} for key, value in by_card.items()],
        'period': {
            'currentMonth': current_month,
            'previousMonth': spending_trend['previousMonth'],
            'baselineMonths': spending_trend['baselineMonths'],
        },
        'spendingTrend': spending_trend,
    }

    cards = []
    card_ids = [*by_card.keys(), '10106', '10612', '10029']
    for raw_id in dict.fromkeys(str(card_id) for card_id in card_ids):
        if raw_id.isdigit():
            card = fetch_card(int(raw_id), request)
            if card:
                cards.append(card)

    ensure_community_seeded()
    community_posts = [
        {
            'title': post.title,
            'tags': post.tags or [],
            'likes': post.likes,
            'commentCount': post.comment_set.count(),
        }
        for post in CommunityPost.objects.all()[:3]
    ]

    return {
        'today': timezone.localtime().date().isoformat(),
        'summary': summary,
        'transactions': current_transactions,
        'cards': cards[:6],
        'communityPosts': community_posts,
    }


def fallback_chat_response(message, context):
    summary = context.get('summary') or {}
    top_category = max(summary.get('byCategory') or [], key=lambda item: item['amount'], default={'category': '기타', 'amount': 0})
    text = str(message or '')

    if '추천' in text or '카드' in text:
        reply = '현재 소비 흐름과 전월 실적 조건을 함께 반영해 비교할 수 있습니다. 추천 화면에서 보유 카드와 비교 카드를 함께 확인하시기 바랍니다.'
        route = '/recommendations/new'
        message_type = 'card-recommendation'
        quick_replies = ['카드 추천 보기', '전월 실적 확인', '소비 분석 보기']
        chips = [{'label': '기준', 'value': '소비 흐름', 'tone': 'teal'}]
    elif '결제' in text or '내역' in text or '추가' in text:
        reply = '결제내역을 입력하면 가맹점, 금액, 카테고리를 정리합니다. 저장 전 내용을 확인한 뒤 반영할 수 있습니다.'
        route = '/transactions/new'
        message_type = 'transaction-help'
        quick_replies = ['결제내역 추가', '최근 거래 보기', '카테고리 분석']
        chips = [{'label': '입력', 'value': '결제내역', 'tone': 'blue'}]
    elif '계획' in text or '구매' in text:
        reply = '예정된 큰 지출은 목적과 시점을 먼저 나눈 뒤 카드 혜택 조건에 맞춰 배치하는 것이 유리합니다. 월별 계획으로 정리해 드릴 수 있습니다.'
        route = '/plans/new'
        message_type = 'purchase-plan'
        quick_replies = ['목표 지출 만들기', '예시 보기', '카드 추천 보기']
        chips = [{'label': '계획', 'value': '목표 지출', 'tone': 'gold'}]
    else:
        reply = f"현재 데이터에서는 {top_category['category']} 지출이 가장 큽니다. 상위 지출과 카드 혜택 조건을 함께 확인하시기 바랍니다."
        route = '/analytics'
        message_type = 'spending-analysis'
        quick_replies = ['소비 분석 보기', '카드 추천 보기', '결제내역 추가']
        chips = [{'label': '우선 확인', 'value': str(top_category['category']), 'tone': 'teal'}]

    return {
        'schemaVersion': 'chat-response-v2',
        'messageType': message_type,
        'reply': reply,
        'summaryChips': chips,
        'quickReplies': quick_replies,
        'actionButtons': [{'label': '관련 화면 보기', 'route': route, 'intent': 'navigation'}],
        'relatedRoute': route,
        'aiMode': 'mock',
        'confidence': 0.55,
    }


@csrf_exempt
def chat_message(request):
    user, error_response = require_request_user(request)
    if error_response:
        return error_response
    if request.method != 'POST':
        return json_response({'detail': 'POST 요청만 지원합니다.'}, status=405)

    payload, error_response = parse_request_body(request)
    if error_response:
        return error_response

    message = (payload.get('message') or payload.get('text') or '').strip()
    if not message:
        return json_response({'detail': '질문을 입력해 주세요.'}, status=400)

    history = payload.get('history')
    if not isinstance(history, list):
        history = []

    context = build_chat_context(request)
    ai_response = chat_with_ai(message, history, context) or fallback_chat_response(message, context)
    record = save_analysis_record(
        'chat',
        message[:80],
        {
            'message': message,
            'history': history[-8:],
            'summary': context.get('summary') or {},
        },
        ai_response,
        user=user,
    )
    ai_response['analysisRecordId'] = f'a{record.id}'
    return json_response(ai_response)

@csrf_exempt
def community_post_list(request):
    ensure_community_seeded()
    viewer = get_request_user(request)

    if request.method == 'POST':
        user, error_response = require_request_user(request)
        if error_response:
            return error_response
        payload, error_response = parse_request_body(request)
        if error_response:
            return error_response

        title = (payload.get('title') or '').strip()
        body = (payload.get('body') or payload.get('content') or '').strip()
        if not title:
            return json_response({'detail': '제목을 입력해 주세요.'}, status=400)
        if not body:
            return json_response({'detail': '본문을 입력해 주세요.'}, status=400)

        author = user_display_name(user)
        post = CommunityPost.objects.create(
            user=user,
            title=title[:120],
            body=body,
            author=author[:30],
            avatar=user_avatar(user)[:2],
            tags=normalize_tags(payload.get('tags')),
        )
        return json_response(serialize_community_post(post, include_comments=True, viewer=user), status=201)

    if request.method != 'GET':
        return json_response({'detail': '지원하지 않는 요청입니다.'}, status=405)

    posts = CommunityPost.objects.all()
    search = (request.GET.get('search') or '').strip()
    if search:
        posts = posts.filter(title__icontains=search)
    return json_response({'count': posts.count(), 'results': [serialize_community_post(post, viewer=viewer) for post in posts]})


@csrf_exempt
def community_post_detail(request, post_id):
    ensure_community_seeded()
    post = get_community_post_or_404(post_id)
    viewer = get_request_user(request)

    if request.method == 'GET':
        return json_response(serialize_community_post(post, include_comments=True, viewer=viewer))

    if request.method in {'PATCH', 'PUT'}:
        user, error_response = require_request_user(request)
        if error_response:
            return error_response
        if post.user_id != user.id:
            return forbidden_response()
        payload, error_response = parse_request_body(request)
        if error_response:
            return error_response

        if 'title' in payload:
            title = (payload.get('title') or '').strip()
            if not title:
                return json_response({'detail': '제목을 입력해 주세요.'}, status=400)
            post.title = title[:120]
        if 'body' in payload or 'content' in payload:
            body = (payload.get('body') or payload.get('content') or '').strip()
            if not body:
                return json_response({'detail': '본문을 입력해 주세요.'}, status=400)
            post.body = body
        if 'tags' in payload:
            post.tags = normalize_tags(payload.get('tags'))
        post.save()
        return json_response(serialize_community_post(post, include_comments=True, viewer=user))

    if request.method == 'DELETE':
        user, error_response = require_request_user(request)
        if error_response:
            return error_response
        if post.user_id != user.id:
            return forbidden_response()
        post.delete()
        return json_response({'ok': True})

    return json_response({'detail': '지원하지 않는 요청입니다.'}, status=405)


@csrf_exempt
def community_post_like(request, post_id):
    ensure_community_seeded()
    if request.method != 'POST':
        return json_response({'detail': 'POST 요청만 지원합니다.'}, status=405)
    user, error_response = require_request_user(request)
    if error_response:
        return error_response

    post = get_community_post_or_404(post_id)
    with db_transaction.atomic():
        post = CommunityPost.objects.select_for_update().get(id=post.id)
        existing_like = CommunityPostLike.objects.filter(post=post, user=user).first()
        if existing_like:
            existing_like.delete()
            post.likes = max(post.likes - 1, 0)
            liked = False
        else:
            CommunityPostLike.objects.create(post=post, user=user)
            post.likes += 1
            liked = True
        post.save(update_fields=['likes', 'updated_at'])
        post._viewer_liked = liked
    return json_response(serialize_community_post(post, include_comments=True, viewer=user))


@csrf_exempt
def community_comment_list(request, post_id):
    ensure_community_seeded()
    post = get_community_post_or_404(post_id)
    viewer = get_request_user(request)

    if request.method == 'GET':
        return json_response({'count': post.comment_set.count(), 'results': [serialize_comment(comment, viewer=viewer) for comment in post.comment_set.all()]})

    if request.method == 'POST':
        user, error_response = require_request_user(request)
        if error_response:
            return error_response
        payload, error_response = parse_request_body(request)
        if error_response:
            return error_response
        body = (payload.get('body') or payload.get('text') or payload.get('content') or '').strip()
        if not body:
            return json_response({'detail': '댓글을 입력해 주세요.'}, status=400)
        author = user_display_name(user)
        comment = CommunityComment.objects.create(
            user=user,
            post=post,
            body=body,
            author=author[:30],
            avatar=user_avatar(user)[:2],
        )
        return json_response(serialize_comment(comment, viewer=user), status=201)

    return json_response({'detail': '지원하지 않는 요청입니다.'}, status=405)


@csrf_exempt
def community_comment_detail(request, comment_id):
    ensure_community_seeded()
    raw_id = str(comment_id).lstrip('cm')
    if not raw_id.isdigit():
        raise Http404('댓글을 찾을 수 없습니다.')
    try:
        comment = CommunityComment.objects.get(id=int(raw_id))
    except CommunityComment.DoesNotExist:
        raise Http404('댓글을 찾을 수 없습니다.')

    if request.method == 'DELETE':
        user, error_response = require_request_user(request)
        if error_response:
            return error_response
        if comment.user_id != user.id:
            return forbidden_response()
        comment.delete()
        return json_response({'ok': True})
    return json_response({'detail': '지원하지 않는 요청입니다.'}, status=405)

@csrf_exempt
def purchase_plan_list(request):
    user, error_response = require_request_user(request)
    if error_response:
        return error_response
    if request.method == 'GET':
        ensure_purchase_plans_seeded(user)
        plans = [serialize_purchase_plan(plan) for plan in PurchasePlan.objects.filter(user=user)]
        return json_response(plans)

    if request.method == 'POST':
        payload, error_response = parse_request_body(request)
        if error_response:
            return error_response
        plan = create_purchase_plan_from_payload(payload, user=user)
        return json_response(serialize_purchase_plan(plan), status=201)

    return json_response({'detail': '지원하지 않는 요청입니다.'}, status=405)


@csrf_exempt
def purchase_plan_detail(request, plan_id):
    user, error_response = require_request_user(request)
    if error_response:
        return error_response
    plan = get_purchase_plan_or_404(request, plan_id)

    if request.method == 'GET':
        return json_response(serialize_purchase_plan(plan))

    if request.method in {'PATCH', 'PUT'}:
        payload, error_response = parse_request_body(request)
        if error_response:
            return error_response
        if 'title' in payload:
            plan.title = (payload.get('title') or '새 소비 계획')[:120]
        if 'type' in payload or 'planType' in payload:
            plan.plan_type = (payload.get('type') or payload.get('planType') or '기타')[:40]
        if 'expenseMode' in payload or 'expense_mode' in payload:
            plan.expense_mode = (payload.get('expenseMode') or payload.get('expense_mode') or 'planned-extra')[:40]
        if 'totalBudget' in payload or 'budget' in payload:
            plan.total_budget = abs(int(payload.get('totalBudget') or payload.get('budget') or 0))
        if 'startMonth' in payload or 'start_month' in payload:
            plan.start_month = (payload.get('startMonth') or payload.get('start_month') or plan.start_month)[:7]
        if 'endMonth' in payload or 'end_month' in payload:
            plan.end_month = (payload.get('endMonth') or payload.get('end_month') or plan.end_month)[:7]
        if 'status' in payload:
            plan.status = (payload.get('status') or plan.status)[:30]
        if 'selectedScenarioId' in payload:
            plan.selected_scenario_id = payload.get('selectedScenarioId') or ''
        if 'items' in payload:
            plan.items = normalize_plan_items(payload.get('items'))
        if 'scenarios' in payload and isinstance(payload.get('scenarios'), list):
            plan.scenarios = payload.get('scenarios')
        plan.save()
        return json_response(serialize_purchase_plan(plan))

    if request.method == 'DELETE':
        plan.delete()
        return json_response({'ok': True})

    return json_response({'detail': '지원하지 않는 요청입니다.'}, status=405)


@csrf_exempt
def purchase_plan_scenarios(request, plan_id):
    if request.method != 'POST':
        return json_response({'detail': 'POST 요청만 지원합니다.'}, status=405)
    user, error_response = require_request_user(request)
    if error_response:
        return error_response

    plan = get_purchase_plan_or_404(request, plan_id)
    plan.scenarios = build_plan_scenarios(plan)
    plan.status = '계산 완료'
    plan.save(update_fields=['scenarios', 'status', 'updated_at'])
    return json_response(plan.scenarios)


@csrf_exempt
def purchase_plan_select(request, plan_id):
    if request.method != 'POST':
        return json_response({'detail': 'POST 요청만 지원합니다.'}, status=405)
    user, error_response = require_request_user(request)
    if error_response:
        return error_response

    payload, error_response = parse_request_body(request)
    if error_response:
        return error_response
    plan = get_purchase_plan_or_404(request, plan_id)
    scenario_id = payload.get('scenarioId') or payload.get('scenario_id') or ''
    scenario_ids = {str(scenario.get('id')) for scenario in (plan.scenarios or []) if isinstance(scenario, dict)}
    if scenario_ids and scenario_id not in scenario_ids:
        return json_response({'detail': '선택할 시나리오를 찾을 수 없습니다.'}, status=404)
    plan.selected_scenario_id = scenario_id
    plan.status = '선택 완료'
    plan.progress = 100
    plan.save(update_fields=['selected_scenario_id', 'status', 'progress', 'updated_at'])
    return json_response(serialize_purchase_plan(plan))


@csrf_exempt
def parse_purchase_plan(request):
    user, error_response = require_request_user(request)
    if error_response:
        return error_response
    if request.method != 'POST':
        return json_response({'detail': 'POST 요청만 지원합니다.'}, status=405)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return json_response({'detail': 'JSON 형식이 올바르지 않습니다.'}, status=400)

    text = payload.get('rawPrompt') or payload.get('prompt') or ''
    ai_plan = parse_purchase_plan_with_ai(payload)
    if ai_plan:
        record = save_analysis_record(
            'purchase_plan',
            ai_plan.get('title') or '소비 계획 분석',
            payload,
            ai_plan,
            user=user,
        )
        ai_plan['analysisRecordId'] = f'a{record.id}'
        return json_response(ai_plan)

    plan_type = '큰 지출'
    if '이사' in text:
        plan_type = '이사'
    elif '여행' in text:
        plan_type = '여행'
    elif '출산' in text or '육아' in text:
        plan_type = '육아'
    elif '혼수' in text or '결혼' in text:
        plan_type = '결혼 준비'
    elif any(keyword in text for keyword in ['면접', '취업', '정장', '토익']):
        plan_type = '취업 준비'
    elif any(keyword in text for keyword in ['기념일', '데이트', '선물']):
        plan_type = '기념일'
    elif any(keyword in text for keyword in ['헬스', '운동', 'PT', '보충제']):
        plan_type = '운동'
    elif any(keyword in text for keyword in ['노트북', '태블릿', '맥북']):
        plan_type = '전자기기'

    start_month = payload.get('startMonth') or '2026-07'
    end_month = payload.get('endMonth') or '2026-08'
    item_templates = {
        '여행': [
            ('항공권', '항공', 1600000),
            ('숙박', '숙박', 1800000),
            ('여행자보험', '보험', 200000),
            ('현지 교통', '교통', 400000),
        ],
        '이사': [
            ('이사 비용', '이사', 350000),
            ('침대', '가구', 600000),
            ('수납장', '가구', 240000),
            ('생활용품', '생활', 180000),
        ],
        '취업 준비': [
            ('정장 셔츠·슬랙스', '쇼핑', 210000),
            ('구두', '쇼핑', 160000),
            ('증명사진', '취업', 50000),
            ('어학 응시료', '교육', 84000),
        ],
        '기념일': [
            ('식사 예약', '식비', 180000),
            ('영화·전시', '문화', 50000),
            ('선물', '쇼핑', 180000),
            ('이동비', '교통', 40000),
        ],
        '운동': [
            ('헬스장 3개월권', '헬스', 180000),
            ('보충제', '쇼핑', 70000),
            ('운동복', '쇼핑', 80000),
            ('인바디·관리비', '헬스', 20000),
        ],
        '전자기기': [
            ('노트북', '전자기기', 1200000),
            ('보호 파우치', '쇼핑', 40000),
            ('마우스·허브', '전자기기', 90000),
            ('AS 보증', '서비스', 70000),
        ],
    }
    templates = item_templates.get(plan_type) or item_templates['취업 준비']
    plan = {
        'title': '새 목표 지출 계획' if plan_type == '큰 지출' else f'{plan_type} 지출 계획',
        'type': plan_type,
        'totalBudget': int(payload.get('budget') or 800000),
        'startMonth': start_month,
        'endMonth': end_month,
        'items': [
            {
                'id': f'i{index + 1}',
                'name': name,
                'category': category,
                'amount': amount,
                'targetMonth': start_month if index < 2 else end_month,
                'paymentType': PAYMENT_TYPE_LUMP_SUM,
                'installmentMonths': 0,
                'isInterestFreeInstallment': False,
                'required': index < 3,
                'flexible': index != 0,
            }
            for index, (name, category, amount) in enumerate(templates)
        ],
        'aiMode': 'mock',
    }
    record = save_analysis_record(
        'purchase_plan',
        plan['title'],
        payload,
        plan,
        user=user,
    )
    plan['analysisRecordId'] = f'a{record.id}'
    return json_response(plan)
def ai_contract(request):
    return json_response(
        {
            'version': 'carch-ai-contract-v2',
            'provider': 'GMS OpenAI-compatible chat completions',
            'stored': 'AIAnalysisRecord.result_payload',
            'features': {
                'transactionParse': {
                    'input': {'rawText': '오늘 컴포즈커피 역삼센터필드점 3,800원 결제'},
                    'output': {
                        'schemaVersion': 'transaction-parse-v2',
                        'cardId': '10106',
                        'merchantName': '컴포즈커피 역삼센터필드점',
                        'category': '카페',
                        'amount': -3800,
                        'approvedAt': '2026-06-23T09:30:00+09:00',
                        'displayTitle': '컴포즈커피 결제',
                        'displaySubtitle': '카페 · 3,800원 · LOCA LIKIT Eat',
                        'corrections': [],
                        'confidence': 0.85,
                        'reviewFields': ['amount', 'approvedAt'],
                    },
                },
                'spendingAnalysis': {
                    'output': {
                        'schemaVersion': 'spending-analysis-v2',
                        'summaryTitle': '이번 달 소비 진단',
                        'headline': '상위 지출 변화에 맞춰 카드 혜택 확인이 필요합니다.',
                        'primaryInsight': {
                            'label': '핵심 진단',
                            'title': '쇼핑 지출 집중',
                            'severity': 'attention',
                            'metricValue': 89000,
                        },
                        'summaryCards': [],
                        'savingOpportunities': [],
                        'actionButtons': [],
                        'confidence': 0.78,
                    },
                },
                'chat': {
                    'output': {
                        'schemaVersion': 'chat-response-v2',
                        'messageType': 'spending-analysis',
                        'reply': '최근 소비를 기준으로 다음 단계를 제안합니다.',
                        'summaryChips': [],
                        'quickReplies': [],
                        'actionButtons': [],
                        'relatedRoute': '/analytics',
                        'confidence': 0.78,
                    },
                },
            },
        }
    )


CARD_RECOMMENDATION_CATEGORY_KEYWORDS = {
    '쇼핑': ['쇼핑', '온라인', '쿠팡', '마켓', '백화점', 'mall', 'shopping'],
    '마트': ['마트', '이마트', '홈플러스', '롯데마트', 'grocery', 'market'],
    '카페': ['카페', '커피', '스타벅스', 'coffee', 'cafe'],
    '식비': ['식비', '외식', '음식', '배달', '푸드', 'dining', 'food'],
    '편의점': ['편의점', 'gs25', 'cu', '세븐일레븐'],
    '뷰티': ['뷰티', '화장품', '올리브영', 'beauty'],
    '교통': ['교통', '버스', '지하철', '택시', '주유', 'transport', 'fuel'],
    '문화': ['문화', '영화', '공연', 'cgv', 'movie'],
    '구독': ['구독', '넷플릭스', '유튜브', '스트리밍', 'subscription'],
    '교육': ['교육', '학원', '강의', '인강', '스터디', '대학', '면접', 'education'],
    '헬스': ['헬스', '피트니스', '운동', '짐', '스포애니', 'gym', 'fitness'],
}


COLD_START_CATEGORY_ROWS = [
    {'category': '식비', 'amount': 320000},
    {'category': '쇼핑', 'amount': 220000},
    {'category': '카페', 'amount': 70000},
    {'category': '교통', 'amount': 90000},
    {'category': '편의점', 'amount': 60000},
]


def _as_int(value, fallback=0):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return fallback


def _krw(value):
    return f'{_as_int(value):,}원'


def _category_keywords(category):
    return CARD_RECOMMENDATION_CATEGORY_KEYWORDS.get(str(category), [str(category)])


def _payment_context_from_mapping(mapping=None):
    terms = normalize_payment_terms(mapping or {})
    return {
        'paymentType': terms['paymentType'],
        'installmentMonths': terms['installmentMonths'],
        'isInterestFreeInstallment': terms['isInterestFreeInstallment'],
    }


def _payment_context_label(context):
    if (context or {}).get('paymentType') != PAYMENT_TYPE_INSTALLMENT:
        return '일시불'
    months = _as_int((context or {}).get('installmentMonths'), 0)
    prefix = f'{months}개월 ' if months else ''
    return f'{prefix}무이자 할부' if (context or {}).get('isInterestFreeInstallment') else f'{prefix}할부'


def _benefit_item_excludes_payment(item, payment_context=None):
    context = payment_context or {}
    if context.get('paymentType') != PAYMENT_TYPE_INSTALLMENT:
        return False

    excluded_methods = set(item.get('excludedPaymentMethods') or [])
    rules = item.get('paymentMethodRules') or {}
    if 'installment' in excluded_methods or rules.get('installmentBenefitEligible') is False:
        return True
    if context.get('isInterestFreeInstallment') and (
        'interest_free_installment' in excluded_methods
        or rules.get('interestFreeInstallmentEligible') is False
    ):
        return True
    return False


def _is_general_benefit_label(label):
    general_terms = [
        '전가맹점',
        '전 가맹점',
        '모든 가맹점',
        '전체 가맹점',
        '국내외 가맹점',
        '국내 가맹점',
        '해외 가맹점',
        '일상 영역',
        '일상 결제',
        '전체 결제',
    ]
    return any(term in label for term in general_terms)


def _build_spending_profile(request=None, adjusted_for_recommendation=False, recurring_overrides=None):
    transactions = [serialize_transaction(item) for item in transaction_queryset(request)]
    spending_trend = _build_spending_trend(transactions, recurring_overrides)
    current_month = spending_trend['currentMonth']
    previous_month = spending_trend['previousMonth']
    expenses = [
        item
        for item in transactions
        if _as_int(item.get('amount')) < 0 and _month_key_from_transaction(item) == current_month
    ]
    previous_expenses = [
        item
        for item in transactions
        if _as_int(item.get('amount')) < 0 and _month_key_from_transaction(item) == previous_month
    ]
    adjustments = {
        item['category']: _as_int(item.get('adjustedAmount'))
        for item in spending_trend.get('categoryChanges') or []
    }
    actual_by_category = defaultdict(int)
    for item in expenses:
        actual_by_category[item.get('category') or item.get('cat') or '기타'] += abs(_as_int(item.get('amount')))

    by_category = defaultdict(int)
    by_card = defaultdict(int)
    actual_by_card = defaultdict(int)
    previous_by_card = defaultdict(int)
    by_category_payment = defaultdict(int)
    by_category_card = defaultdict(lambda: {'amount': 0, 'actualAmount': 0, 'merchants': []})

    for item in previous_expenses:
        previous_by_card[str(item.get('cardId') or item.get('card_id') or '')] += abs(_as_int(item.get('amount')))

    for item in expenses:
        raw_amount = abs(_as_int(item.get('amount')))
        category = item.get('category') or item.get('cat') or '기타'
        card_id = str(item.get('cardId') or item.get('card_id') or '')
        payment_context = _payment_context_from_mapping(item)
        actual_by_card[card_id] += raw_amount
        category_actual = actual_by_category[category] or raw_amount
        if adjusted_for_recommendation:
            category_adjusted = adjustments.get(category, category_actual)
            scale = category_adjusted / category_actual if category_actual else 1
            amount = round(raw_amount * scale)
        else:
            amount = raw_amount
        by_category[category] += amount
        by_card[card_id] += amount
        by_category_payment[
            (
                category,
                payment_context['paymentType'],
                payment_context['installmentMonths'],
                payment_context['isInterestFreeInstallment'],
            )
        ] += amount
        category_card = by_category_card[
            (
                category,
                card_id,
                payment_context['paymentType'],
                payment_context['installmentMonths'],
                payment_context['isInterestFreeInstallment'],
            )
        ]
        category_card['amount'] += amount
        category_card['actualAmount'] += raw_amount
        merchant = item.get('merchantName') or item.get('merchant') or ''
        if merchant and merchant not in category_card['merchants']:
            category_card['merchants'].append(merchant)

    category_rows = sorted(
        [{'category': key, 'amount': value} for key, value in by_category.items()],
        key=lambda item: item['amount'],
        reverse=True,
    )
    data_source = 'transactions'
    if not category_rows:
        category_rows = [dict(row) for row in COLD_START_CATEGORY_ROWS]
        data_source = 'cold_start_defaults'
    benefit_evaluation_rows = sorted(
        [
            {
                'category': category,
                'amount': amount,
                'paymentType': payment_type,
                'installmentMonths': installment_months,
                'isInterestFreeInstallment': is_interest_free,
                'paymentLabel': _payment_context_label(
                    {
                        'paymentType': payment_type,
                        'installmentMonths': installment_months,
                        'isInterestFreeInstallment': is_interest_free,
                    }
                ),
            }
            for (category, payment_type, installment_months, is_interest_free), amount in by_category_payment.items()
        ],
        key=lambda item: item['amount'],
        reverse=True,
    )
    if not benefit_evaluation_rows:
        benefit_evaluation_rows = [
            {
                **row,
                'paymentType': PAYMENT_TYPE_LUMP_SUM,
                'installmentMonths': 0,
                'isInterestFreeInstallment': False,
                'paymentLabel': '일시불',
            }
            for row in category_rows
        ]
    total_expense = sum(row['amount'] for row in category_rows)
    top_category = category_rows[0]['category'] if category_rows else '기타'
    recurring_category_set = {
        item.get('category')
        for item in spending_trend.get('categoryChanges') or []
        if item.get('status') != 'one-time' and _as_int(item.get('currentAmount')) > 0
    }
    one_time_category_set = {
        item.get('category')
        for item in spending_trend.get('categoryChanges') or []
        if item.get('status') == 'one-time' and _as_int(item.get('currentAmount')) > 0
    }
    recommendation_rows = [
        row for row in category_rows if row.get('category') in recurring_category_set
    ] or category_rows
    recommendation_top_category = recommendation_rows[0]['category'] if recommendation_rows else top_category

    style_tags = []
    if total_expense >= 700000:
        style_tags.append('고소비형')
    elif total_expense >= 300000:
        style_tags.append('생활비 관리형')
    else:
        style_tags.append('소액 반복형')
    if top_category in {'쇼핑', '마트', '카페', '식비', '교통', '구독'}:
        style_tags.append(f'{top_category} 집중형')
    if len(category_rows) >= 4:
        style_tags.append('분산 소비형')
    if data_source == 'cold_start_defaults':
        style_tags = ['학습 초기', '조건부 추천', f'{top_category} 가정']

    return {
        'totalExpense': total_expense,
        'categoryRows': category_rows,
        'benefitEvaluationRows': benefit_evaluation_rows,
        'byCard': [{'cardId': key, 'amount': value} for key, value in by_card.items()],
        'currentByCard': [{'cardId': key, 'amount': value} for key, value in actual_by_card.items()],
        'previousByCard': [{'cardId': key, 'amount': value} for key, value in previous_by_card.items()],
        'categoryCardRows': sorted(
            [
                {
                    'category': category,
                    'cardId': card_id,
                    'paymentType': payment_type,
                    'installmentMonths': installment_months,
                    'isInterestFreeInstallment': is_interest_free,
                    'paymentLabel': _payment_context_label(
                        {
                            'paymentType': payment_type,
                            'installmentMonths': installment_months,
                            'isInterestFreeInstallment': is_interest_free,
                        }
                    ),
                    'amount': value['amount'],
                    'actualAmount': value['actualAmount'],
                    'merchantExamples': value['merchants'][:3],
                }
                for (category, card_id, payment_type, installment_months, is_interest_free), value in by_category_card.items()
            ],
            key=lambda item: item['amount'],
            reverse=True,
        ),
        'topCategory': top_category,
        'recommendationTopCategory': recommendation_top_category,
        'oneTimeCategories': list(one_time_category_set),
        'recurringCategories': list(recurring_category_set),
        'styleTags': style_tags[:3],
        'period': {
            'currentMonth': current_month,
            'previousMonth': spending_trend['previousMonth'],
            'baselineMonths': spending_trend['baselineMonths'],
        },
        'spendingTrend': spending_trend,
        'actualTotalExpense': sum(actual_by_category.values()),
        'adjustedForRecommendation': adjusted_for_recommendation,
        'dataSource': data_source,
        'transactionCount': len(transactions),
        'expenseTransactionCount': len(expenses),
        'activeMonthCount': len(
            {
                _month_key_from_transaction(item)
                for item in transactions
                if _as_int(item.get('amount')) < 0 and _month_key_from_transaction(item)
            }
        ),
    }


def _recommendation_data_readiness(profile, owned_ids):
    transaction_count = _as_int(profile.get('expenseTransactionCount'))
    active_months = _as_int(profile.get('activeMonthCount'))
    has_owned_cards = bool(owned_ids)
    data_source = profile.get('dataSource') or 'transactions'

    if not has_owned_cards and transaction_count == 0:
        stage, confidence = 'empty', 0.25
        label = '학습 전'
        message = '보유 카드와 첫 소비 계획을 입력하면 조건부 추천부터 시작할 수 있어요.'
    elif data_source == 'cold_start_defaults' or transaction_count == 0:
        stage, confidence = 'cold_start', 0.42
        label = '학습 초기'
        message = '거래 데이터가 부족해 일반 생활비 패턴으로 조건부 추천합니다.'
    elif active_months < 2 or transaction_count < 8:
        stage, confidence = 'warming_up', 0.62
        label = '학습 중'
        message = '최근 거래가 적어 예상 혜택을 보수적으로 계산합니다.'
    elif active_months < 3 or transaction_count < 20:
        stage, confidence = 'developing', 0.76
        label = '패턴 확인 중'
        message = '소비 패턴이 보이기 시작했지만 일부 추천은 조건부로 봐야 합니다.'
    else:
        stage, confidence = 'learned', 0.92
        label = '패턴 기반'
        message = '반복 소비 패턴을 기준으로 추천합니다.'

    return {
        'stage': stage,
        'label': label,
        'confidence': confidence,
        'message': message,
        'transactionCount': transaction_count,
        'activeMonthCount': active_months,
        'dataSource': data_source,
        'recommendationMode': 'conditional' if confidence < 0.75 else 'calculated',
    }


def _benefit_rule_quality(card):
    status = card.get('benefitDataStatus') or {}
    status_key = status.get('status')
    total = _as_int(status.get('totalBenefitCount'))
    verified = _as_int(status.get('verifiedBenefitCount'))
    verified_ratio = verified / total if total else 0

    if status_key == 'verified':
        confidence = 1.0
    elif status_key == 'partial':
        confidence = 0.68 + min(0.18, verified_ratio * 0.18)
    elif status_key == 'needs_input':
        confidence = 0.5
    elif status_key == 'missing':
        confidence = 0.35
    elif card.get('benefitItems'):
        confidence = 1.0
    else:
        confidence = 0.48

    missing_fields = set(status.get('missingRuleFields') or [])
    if {'benefitValue', 'monthlyLimit'} & missing_fields:
        confidence -= 0.12
    if 'previousMonthSpend' in missing_fields:
        confidence -= 0.08

    confidence = max(0.25, min(1.0, confidence))
    default_label = {
        'verified': '검증 완료',
        'partial': '일부 보완 필요',
        'needs_input': '정보 보완 필요',
        'missing': '혜택 데이터 없음',
    }.get(status_key, '혜택 데이터 확인 필요')
    return {
        'status': status_key or 'unknown',
        'label': status.get('label') or default_label,
        'confidence': round(confidence, 2),
        'verifiedBenefitCount': verified,
        'totalBenefitCount': total,
        'missingRuleFields': sorted(missing_fields),
        'manualInputAvailable': bool(status.get('manualInputAvailable', status_key != 'verified')),
    }


def _benefit_rate_for_category(card, category, payment_context=None):
    keywords = [keyword.lower() for keyword in _category_keywords(category)]
    benefit_items = card.get('benefitItems') or []
    best_rate = 0.0
    best_limit = None
    best_label = ''
    broad_rate = 0.0
    broad_limit = None
    broad_label = ''
    skipped_for_payment = 0

    for item in benefit_items:
        if _benefit_item_excludes_payment(item, payment_context):
            skipped_for_payment += 1
            continue
        label = ' '.join(
            str(value or '')
            for value in [item.get('label'), item.get('scope'), item.get('type')]
        ).lower()
        rate = item.get('ratePercent')
        if rate is None and item.get('type') in {'discount_rate', 'point_rate'}:
            rate = item.get('benefitValue') or item.get('benefit_value')
        try:
            rate = float(rate or 0)
        except (TypeError, ValueError):
            rate = 0
        limit = item.get('monthlyBenefitLimitKrw')
        label_text = item.get('label') or item.get('scope') or ''
        if any(keyword in label for keyword in keywords) and rate > best_rate:
            best_rate = rate
            best_limit = limit
            best_label = label_text
        if _is_general_benefit_label(label) and rate > broad_rate:
            broad_rate = rate
            broad_limit = limit
            broad_label = label_text or '기본 혜택'

    if best_rate:
        return best_rate, _as_int(best_limit, 0) or None, best_label
    if broad_rate:
        return broad_rate, _as_int(broad_limit, 0) or None, broad_label or '기본 혜택'
    if benefit_items and skipped_for_payment == len(benefit_items):
        return 0.0, None, f'{_payment_context_label(payment_context)} 혜택 제외'
    if benefit_items:
        return 0.0, None, '해당 카테고리 혜택 없음'

    text = ' '.join(
        str(value or '')
        for value in [
            card.get('name'),
            card.get('benefitSummary'),
            card.get('titleDescription'),
            *(card.get('benefits') or []),
        ]
    ).lower()
    if any(keyword in text for keyword in keywords):
        percent_values = [float(match) for match in re.findall(r'(\d+(?:\.\d+)?)\s*%', text)]
        return min(max(percent_values or [1.0]), 15.0), None, f'{category} 관련 혜택'
    if _is_general_benefit_label(text) or '전가맹' in text or '언제나' in text:
        basic_matches = re.findall(
            r'(?:전가맹|국내외?\s*가맹점|모든\s*가맹점|전체\s*가맹점|언제나)[^%]{0,40}?(\d+(?:\.\d+)?)\s*%',
            text,
        )
        percent_values = [float(match) for match in basic_matches]
        if not percent_values:
            percent_values = [float(match) for match in re.findall(r'(\d+(?:\.\d+)?)\s*%\s*(?:적립|할인)', text)]
        return min(percent_values or [0.5], default=0.5), None, '기본 혜택'
    return 0.0, None, '해당 카테고리 혜택 없음'


def _estimate_raw_category_benefit(card, category, amount, payment_context=None):
    rate, limit, label = _benefit_rate_for_category(card, category, payment_context=payment_context)
    estimated = round(_as_int(amount) * rate / 100)
    if limit is not None:
        estimated = min(estimated, limit)
    return {
        'rate': round(rate, 2),
        'estimatedBenefit': estimated,
        'benefitLabel': label,
        'limit': limit,
    }


def _apply_monthly_limit(raw, limit_usage=None):
    limit = raw.get('limit')
    if limit is None:
        return raw
    key = (raw.get('benefitLabel') or '', _as_int(limit))
    used = _as_int((limit_usage or {}).get(key))
    available = max(_as_int(limit) - used, 0)
    capped = min(_as_int(raw.get('estimatedBenefit')), available)
    if limit_usage is not None:
        limit_usage[key] = used + capped
    return {
        **raw,
        'estimatedBenefit': capped,
        'limitRemainingAfter': max(available - capped, 0),
        'limitUsageKey': f'{key[0]}:{key[1]}',
    }


def _card_evaluation_spend(card, profile, fallback_to_total=True):
    card_id = _card_id(card)
    for row in profile.get('byCard') or []:
        if str(row.get('cardId')) == card_id:
            return _as_int(row.get('amount'))
    return _as_int(profile.get('totalExpense')) if fallback_to_total else 0


def _card_fee(card):
    annual_fee = _as_int(card.get('annualFee') or card.get('domesticAnnualFee') or card.get('domestic_annual_fee'))
    return annual_fee, round(annual_fee / 12)


def _card_min_spend(card):
    return _as_int(card.get('previousMonthMinSpend') or card.get('previous_month_min_spend'))


def _estimate_card_value(
    card,
    profile,
    owned=False,
    evaluation_spend=None,
    benefit_eligibility_spend=None,
    performance_spend=None,
):
    annual_fee = _as_int(card.get('annualFee') or card.get('domesticAnnualFee') or card.get('domestic_annual_fee'))
    monthly_annual_fee = round(annual_fee / 12)
    min_spend = _as_int(card.get('previousMonthMinSpend') or card.get('previous_month_min_spend'))
    total_spend = _as_int(profile.get('totalExpense'))
    evaluation_spend = total_spend if evaluation_spend is None else _as_int(evaluation_spend)
    benefit_eligibility_spend = evaluation_spend if benefit_eligibility_spend is None else _as_int(benefit_eligibility_spend)
    performance_spend = evaluation_spend if performance_spend is None else _as_int(performance_spend)
    eligible_for_benefit = not min_spend or benefit_eligibility_spend >= min_spend
    next_month_eligible = not min_spend or performance_spend >= min_spend
    eligible_ratio = 1 if eligible_for_benefit else 0
    remaining_spend = 0
    if min_spend and not eligible_for_benefit:
        remaining_spend = min_spend - benefit_eligibility_spend
    remaining_current_spend = max(min_spend - performance_spend, 0) if min_spend else 0

    category_breakdown = []
    gross_benefit = 0
    potential_gross_benefit = 0
    matched_categories = []
    recurring_matched_categories = []
    one_time_categories = set(profile.get('oneTimeCategories') or [])
    limit_usage = {}
    for row in profile.get('benefitEvaluationRows') or profile.get('categoryRows') or []:
        amount = _as_int(row.get('amount'))
        if amount <= 0:
            continue
        category = row.get('category')
        payment_context = _payment_context_from_mapping(row)
        raw = _apply_monthly_limit(
            _estimate_raw_category_benefit(card, category, amount, payment_context=payment_context),
            limit_usage,
        )
        potential_estimated = raw['estimatedBenefit']
        estimated = potential_estimated if eligible_for_benefit else 0
        potential_gross_benefit += potential_estimated
        gross_benefit += estimated
        if potential_estimated > 0:
            matched_categories.append(category)
            if category not in one_time_categories:
                recurring_matched_categories.append(category)
        category_breakdown.append(
            {
                'category': category,
                'amount': amount,
                'rate': raw['rate'],
                'estimatedBenefit': estimated,
                'potentialBenefit': potential_estimated,
                'benefitLabel': raw['benefitLabel'],
                'paymentType': payment_context['paymentType'],
                'installmentMonths': payment_context['installmentMonths'],
                'isInterestFreeInstallment': payment_context['isInterestFreeInstallment'],
                'paymentLabel': _payment_context_label(payment_context),
            }
        )

    benefit_rule_quality = _benefit_rule_quality(card)
    rule_confidence = benefit_rule_quality['confidence']
    raw_gross_benefit = gross_benefit
    raw_potential_gross_benefit = potential_gross_benefit
    gross_benefit = round(gross_benefit * rule_confidence)
    potential_gross_benefit = round(potential_gross_benefit * rule_confidence)
    monthly_net = gross_benefit - monthly_annual_fee
    annual_net = monthly_net * 12
    return {
        'expectedMonthlyBenefit': gross_benefit,
        'rawExpectedMonthlyBenefit': raw_gross_benefit,
        'monthlyAnnualFee': monthly_annual_fee,
        'monthlyNetBenefit': monthly_net,
        'annualNetBenefit': annual_net,
        'annualFee': annual_fee,
        'previousMonthMinSpend': min_spend,
        'evaluationSpend': evaluation_spend,
        'benefitEligibilitySpend': benefit_eligibility_spend,
        'currentMonthPerformanceSpend': performance_spend,
        'eligibleForBenefit': eligible_for_benefit,
        'nextMonthEligibleForBenefit': next_month_eligible,
        'remainingSpendForBenefit': remaining_spend,
        'remainingCurrentSpendForNextMonthBenefit': remaining_current_spend,
        'eligibleRatio': round(eligible_ratio, 2),
        'potentialMonthlyBenefit': potential_gross_benefit,
        'rawPotentialMonthlyBenefit': raw_potential_gross_benefit,
        'potentialMonthlyNetBenefit': potential_gross_benefit - monthly_annual_fee,
        'benefitRuleQuality': benefit_rule_quality,
        'benefitRuleConfidence': rule_confidence,
        'matchedCategories': list(dict.fromkeys(matched_categories))[:4],
        'recurringMatchedCategories': list(dict.fromkeys(recurring_matched_categories))[:4],
        'primaryMatchedCategory': (
            list(dict.fromkeys(recurring_matched_categories))
            or list(dict.fromkeys(matched_categories))
            or [profile.get('recommendationTopCategory') or profile.get('topCategory') or '주요 소비']
        )[0],
        'categoryBreakdown': category_breakdown[:8],
        'owned': owned,
    }


def _recommendation_reason(card, value, profile, monthly_delta):
    top_category = value.get('primaryMatchedCategory') or profile.get('recommendationTopCategory') or profile.get('topCategory') or '주요 소비'
    if value.get('benefitRuleConfidence', 1) < 0.65:
        return f'{top_category} 지출과 맞지만 혜택 조건 검수가 필요해 보수적으로 계산했습니다.'
    if value.get('benefitTiming') == 'future_after_performance' and monthly_delta > 0:
        return f'{top_category} 소비 패턴상 전월실적을 채운 뒤 월 {_krw(monthly_delta)}의 순혜택 개선이 예상됩니다.'
    if monthly_delta > 0:
        return f'{top_category} 소비 기준으로 월 {_krw(monthly_delta)}의 순혜택 개선이 예상됩니다.'
    if value.get('remainingSpendForBenefit'):
        return f'혜택 조건까지 {_krw(value["remainingSpendForBenefit"])} 남아 있어 실적 충족 후 비교가 필요합니다.'
    return f'{top_category} 소비와 일부 혜택이 맞지만 현재 기준의 개선 폭은 제한적입니다.'


def _card_id(card):
    return str(card.get('cardAdId') or card.get('card_ad_id') or card.get('id') or '')


def _card_name(card):
    return card.get('name') or card.get('cardName') or card.get('card_name') or '추천 카드'


def _issuer_name(card):
    return card.get('issuer') or card.get('issuerName') or card.get('issuer_name') or ''


def _card_image_url(card):
    return card.get('imageUrl') or card.get('image_url') or ''


def _topic_particle(text):
    word = str(text or '').strip()
    if not word:
        return '는'
    last = word[-1]
    code = ord(last)
    if 0xAC00 <= code <= 0xD7A3:
        return '은' if (code - 0xAC00) % 28 else '는'
    return '은'


def _estimate_category_benefit(
    card,
    category,
    amount,
    evaluation_spend=None,
    payment_context=None,
    limit_usage=None,
):
    min_spend = _card_min_spend(card)
    evaluation_spend = _as_int(evaluation_spend)
    eligible = not min_spend or evaluation_spend >= min_spend
    payment_context = _payment_context_from_mapping(payment_context)
    raw = _apply_monthly_limit(
        _estimate_raw_category_benefit(card, category, amount, payment_context=payment_context),
        limit_usage,
    )
    rule_confidence = _benefit_rule_quality(card)['confidence']
    raw_estimated = raw['estimatedBenefit'] if eligible else 0
    estimated = round(raw_estimated * rule_confidence)
    potential = round(raw['estimatedBenefit'] * rule_confidence)
    return {
        'rate': raw['rate'],
        'benefitLabel': raw['benefitLabel'],
        'estimatedBenefit': estimated,
        'rawEstimatedBenefit': raw_estimated,
        'potentialBenefit': potential,
        'rawPotentialBenefit': raw['estimatedBenefit'],
        'benefitRuleConfidence': rule_confidence,
        'eligibleForBenefit': eligible,
        'paymentType': payment_context['paymentType'],
        'installmentMonths': payment_context['installmentMonths'],
        'isInterestFreeInstallment': payment_context['isInterestFreeInstallment'],
        'paymentLabel': _payment_context_label(payment_context),
    }


def _profile_card_spend_map(profile, key='byCard'):
    return {
        str(item.get('cardId') or ''): _as_int(item.get('amount'))
        for item in profile.get(key) or []
    }


def _estimate_current_portfolio_value(profile, cards_by_id, owned_ids):
    card_spend = _profile_card_spend_map(profile)
    current_card_spend = _profile_card_spend_map(profile, 'currentByCard') or card_spend
    previous_card_spend = _profile_card_spend_map(profile, 'previousByCard')
    gross_benefit = 0
    potential_benefit = 0
    breakdown = []
    limit_usage_by_card = defaultdict(dict)

    for row in profile.get('categoryCardRows') or []:
        card_id = str(row.get('cardId') or '')
        card = cards_by_id.get(card_id)
        amount = _as_int(row.get('amount'))
        if not card or amount <= 0:
            continue
        estimate = _estimate_category_benefit(
            card,
            row.get('category') or '기타',
            amount,
            evaluation_spend=previous_card_spend.get(card_id, 0),
            payment_context=row,
            limit_usage=limit_usage_by_card[card_id],
        )
        gross_benefit += estimate['estimatedBenefit']
        potential_benefit += estimate['potentialBenefit']
        breakdown.append(
            {
                'cardId': card_id,
                'cardName': _card_name(card),
                'category': row.get('category') or '기타',
                'amount': amount,
                **estimate,
            }
        )

    used_card_ids = {card_id for card_id, amount in card_spend.items() if amount > 0}
    fee_card_ids = used_card_ids or set(str(card_id) for card_id in owned_ids)
    monthly_fee = 0
    annual_fee = 0
    for card_id in fee_card_ids:
        card = cards_by_id.get(str(card_id))
        if not card:
            continue
        card_annual_fee, card_monthly_fee = _card_fee(card)
        annual_fee += card_annual_fee
        monthly_fee += card_monthly_fee

    monthly_net = gross_benefit - monthly_fee
    return {
        'cardId': 'current-portfolio',
        'cardName': '현재 사용 조합',
        'monthlyNetBenefit': monthly_net,
        'expectedMonthlyBenefit': gross_benefit,
        'potentialMonthlyBenefit': potential_benefit,
        'monthlyAnnualFee': monthly_fee,
        'annualFee': annual_fee,
        'annualNetBenefit': monthly_net * 12,
        'currentMonthPerformanceByCard': current_card_spend,
        'previousMonthPerformanceByCard': previous_card_spend,
        'breakdown': breakdown[:8],
    }


def _build_routing_suggestions(profile, owned_values, result_cards, owned_ids):
    cards_by_id = {}
    destinations = []
    card_spend = _profile_card_spend_map(profile)
    previous_card_spend = _profile_card_spend_map(profile, 'previousByCard')
    one_time_categories = {
        item.get('category')
        for item in (profile.get('spendingTrend') or {}).get('categoryChanges') or []
        if item.get('status') == 'one-time'
    }
    for item in owned_values:
        card = item.get('card') or {}
        card_id = _card_id(card)
        if card_id:
            cards_by_id[card_id] = card
            destinations.append({'card': card, 'rank': 99, 'monthlyDelta': 0})

    suggestions = []
    seen = set()
    for row in profile.get('categoryCardRows') or []:
        source_card_id = str(row.get('cardId') or '')
        source_card = cards_by_id.get(source_card_id)
        amount = _as_int(row.get('amount'))
        category = row.get('category') or '기타'
        if not source_card or amount <= 0 or category in one_time_categories:
            continue

        source_estimate = _estimate_category_benefit(
            source_card,
            category,
            amount,
            evaluation_spend=previous_card_spend.get(source_card_id, 0),
            payment_context=row,
        )
        for destination_item in destinations:
            destination = destination_item['card']
            target_card_id = _card_id(destination)
            if not target_card_id or target_card_id == source_card_id:
                continue

            owned_target = target_card_id in owned_ids
            target_evaluation_spend = previous_card_spend.get(target_card_id, 0)
            target_estimate = _estimate_category_benefit(
                destination,
                category,
                amount,
                evaluation_spend=target_evaluation_spend,
                payment_context=row,
            )
            monthly_gain = target_estimate['estimatedBenefit'] - source_estimate['estimatedBenefit']
            if monthly_gain < 1000:
                continue

            key = (
                category,
                source_card_id,
                target_card_id,
                row.get('paymentType') or PAYMENT_TYPE_LUMP_SUM,
                row.get('installmentMonths') or 0,
                bool(row.get('isInterestFreeInstallment')),
            )
            if key in seen:
                continue
            seen.add(key)

            target_name = _card_name(destination)
            source_name = _card_name(source_card)
            suggestions.append(
                {
                    'id': f'route-{category}-{source_card_id}-{target_card_id}',
                    'category': category,
                    'amount': amount,
                    'monthlyGain': monthly_gain,
                    'fromCardId': source_card_id,
                    'fromCardName': source_name,
                    'fromIssuer': _issuer_name(source_card),
                    'fromRate': source_estimate['rate'],
                    'fromBenefit': source_estimate['estimatedBenefit'],
                    'toCardId': target_card_id,
                    'toCardName': target_name,
                    'toIssuer': _issuer_name(destination),
                    'toImageUrl': _card_image_url(destination),
                    'toRate': target_estimate['rate'],
                    'toBenefit': target_estimate['estimatedBenefit'],
                    'benefitLabel': target_estimate['benefitLabel'],
                    'paymentType': row.get('paymentType') or PAYMENT_TYPE_LUMP_SUM,
                    'installmentMonths': _as_int(row.get('installmentMonths')),
                    'isInterestFreeInstallment': bool(row.get('isInterestFreeInstallment')),
                    'paymentLabel': row.get('paymentLabel') or _payment_context_label(row),
                    'merchantExamples': row.get('merchantExamples') or [],
                    'scope': 'owned',
                    'scopeLabel': '보유 카드 조정',
                    'destinationRank': destination_item['rank'],
                    'destinationMonthlyDelta': destination_item['monthlyDelta'],
                    'title': f'{category}{_topic_particle(category)} {target_name}',
                    'body': f'{category} 결제를 {target_name}로 조정하면 월 {_krw(monthly_gain)}의 추가 혜택이 예상됩니다.',
                }
            )

    suggestions.sort(
        key=lambda item: (
            item['destinationMonthlyDelta'],
            item['monthlyGain'],
            item['scope'] == 'owned',
            -item['destinationRank'],
        ),
        reverse=True,
    )
    unique_categories = []
    used_categories = set()
    for item in suggestions:
        if item['category'] in used_categories:
            continue
        used_categories.add(item['category'])
        unique_categories.append(item)
        if len(unique_categories) >= 4:
            break
    return unique_categories


def card_recommendations(request):
    user, error_response = require_request_user(request)
    if error_response:
        return error_response
    profile = _build_spending_profile(
        request,
        adjusted_for_recommendation=True,
        recurring_overrides=_parse_category_overrides(request),
    )
    owned_ids = {str(item.card_id) for item in owned_card_queryset(request)}
    data_readiness = _recommendation_data_readiness(profile, owned_ids)
    current_card_spend = _profile_card_spend_map(profile, 'currentByCard')
    previous_card_spend = _profile_card_spend_map(profile, 'previousByCard')

    owned_values = []
    owned_cards_by_id = {}
    for card_id in owned_ids:
        if card_id.isdigit():
            card = fetch_card(int(card_id), request)
            if card:
                normalized_card_id = str(_card_id(card))
                owned_cards_by_id[normalized_card_id] = card
                owned_values.append(
                    {
                        'card': card,
                        **_estimate_card_value(
                            card,
                            profile,
                            owned=True,
                            evaluation_spend=previous_card_spend.get(normalized_card_id, 0),
                            benefit_eligibility_spend=previous_card_spend.get(normalized_card_id, 0),
                            performance_spend=current_card_spend.get(normalized_card_id, 0),
                        ),
                    }
                )

    baseline = _estimate_current_portfolio_value(profile, owned_cards_by_id, owned_ids)
    current_monthly_net = _as_int(baseline.get('monthlyNetBenefit'))
    current_monthly_gross = _as_int(baseline.get('expectedMonthlyBenefit'))

    candidates = fetch_cards(request, limit=36, active_only=True)
    ranked = []
    for card in candidates:
        detailed = fetch_card(int(card['cardAdId']), request) or card
        is_owned = str(detailed.get('cardAdId')) in owned_ids
        if is_owned:
            continue
        value = _estimate_card_value(
            detailed,
            profile,
            owned=False,
            evaluation_spend=_as_int(profile.get('totalExpense')),
            benefit_eligibility_spend=_as_int(profile.get('totalExpense')),
            performance_spend=0,
        )
        value['benefitTiming'] = 'future_after_performance'
        comparison_monthly_net = value['expectedMonthlyBenefit'] - value['monthlyAnnualFee']
        monthly_delta = comparison_monthly_net - current_monthly_gross
        annual_delta = monthly_delta * 12
        annual_fee_delta = value['annualFee']
        payback_months = None
        if monthly_delta > 0 and annual_fee_delta > 0:
            payback_months = max(1, round(annual_fee_delta / monthly_delta))

        match = 70
        match += min(18, max(0, monthly_delta) // 1000)
        match += min(8, len(value['matchedCategories']) * 3)
        if value['remainingSpendForBenefit']:
            match -= 8
        if value.get('benefitRuleConfidence', 1) < 0.75:
            match -= round((0.75 - value['benefitRuleConfidence']) * 20)
        if data_readiness['confidence'] < 0.75:
            match -= round((0.75 - data_readiness['confidence']) * 18)
        match = max(45, min(98, match))
        notification = (
            data_readiness['confidence'] >= 0.6
            and value.get('benefitRuleConfidence', 1) >= 0.55
            and annual_delta >= 30000
            and monthly_delta > 0
            and (payback_months is None or payback_months <= 8)
        )
        recommendation_confidence = round(
            min(data_readiness['confidence'], value.get('benefitRuleConfidence', 1)),
            2,
        )
        ranking_gain = round(monthly_delta * recommendation_confidence)

        ranked.append(
            {
                **detailed,
                'match': match,
                'reason': _recommendation_reason(detailed, value, profile, monthly_delta),
                'highlights': detailed.get('benefits', []),
                'spendingFit': {
                    'styleTags': profile['styleTags'],
                    'topCategory': profile['topCategory'],
                    'recommendationTopCategory': profile.get('recommendationTopCategory'),
                    'matchedCategories': value['matchedCategories'],
                    'categoryBreakdown': value['categoryBreakdown'],
                    'dataReadiness': data_readiness,
                },
                'economics': {
                    **value,
                    'currentMonthlyNetBenefit': current_monthly_net,
                    'currentMonthlyGrossBenefit': current_monthly_gross,
                    'comparisonMonthlyNetBenefit': comparison_monthly_net,
                    'monthlyDelta': monthly_delta,
                    'annualDelta': annual_delta,
                    'paybackMonths': payback_months,
                    'annualFeeDelta': annual_fee_delta,
                },
                'recommendationConfidence': recommendation_confidence,
                'recommendationMode': data_readiness['recommendationMode'],
                'rankingGain': ranking_gain,
                'notification': {
                    'show': notification,
                    'title': (
                        '조건을 확인하면 추천 정확도가 올라갑니다'
                        if data_readiness['recommendationMode'] == 'conditional'
                        else '카드 사용 조정으로 혜택이 개선될 수 있습니다'
                    ),
                    'body': (
                        data_readiness['message']
                        if data_readiness['recommendationMode'] == 'conditional'
                        else f'현재 소비 기준 월 {_krw(max(0, monthly_delta))}의 순혜택 개선이 예상됩니다.'
                    ),
                    'severity': 'attention' if notification else 'info',
                },
            }
        )

    ranked.sort(
        key=lambda item: (
            item['rankingGain'] > 0,
            item['rankingGain'],
            item['recommendationConfidence'] >= 0.55,
            item['recommendationConfidence'],
            item['economics']['monthlyDelta'],
            item['match'],
            item['economics']['monthlyNetBenefit'],
        ),
        reverse=True,
    )
    results = ranked[:5]
    top = results[0] if results else None
    alert = (top or {}).get('notification') or {'show': False}
    routing_suggestions = _build_routing_suggestions(profile, owned_values, results, owned_ids)

    return json_response(
        {
            'count': len(results),
            'profile': profile,
            'dataReadiness': data_readiness,
            'baseline': {
                'cardId': baseline.get('cardId'),
                'cardName': baseline.get('cardName'),
                'monthlyNetBenefit': current_monthly_net,
                'expectedMonthlyBenefit': _as_int(baseline.get('expectedMonthlyBenefit')),
                'potentialMonthlyBenefit': _as_int(baseline.get('potentialMonthlyBenefit')),
                'monthlyAnnualFee': _as_int(baseline.get('monthlyAnnualFee')),
                'annualFee': _as_int(baseline.get('annualFee')),
                'breakdown': baseline.get('breakdown') or [],
            },
            'alert': alert,
            'routingSuggestions': routing_suggestions,
            'results': results,
            'warnings': [
                data_readiness['message'],
                '혜택 규칙이 검증되지 않은 카드는 예상 혜택을 보수적으로 반영했습니다.',
            ],
        }
    )


# Create your views here.
