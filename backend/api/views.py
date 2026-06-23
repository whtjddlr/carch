import json
import re
from collections import defaultdict
from datetime import datetime, timedelta

from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse
from django.db.models import Max
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .ai_service import chat_with_ai, analyze_spending_with_ai, get_ai_status, parse_purchase_plan_with_ai, parse_transaction_with_ai
from .card_repository import fetch_card, fetch_cards
from .models import AIAnalysisRecord, CommunityComment, CommunityPost, OwnedCard, PurchasePlan, Transaction
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
    ('LOCA 100', '10029'),
    ('로카', '10029'),
    ('롯데', '10029'),
    ('SHOPPER', '10612'),
    ('카드의정석', '10612'),
    ('우리', '10612'),
    ('이마트 신한', '10609'),
    ('신한', '10609'),
]

DEFAULT_OWNED_CARD_IDS = ['10029', '10612', '10609']


def json_response(payload, status=200):
    return JsonResponse(
        payload,
        status=status,
        safe=isinstance(payload, dict),
        json_dumps_params={'ensure_ascii': False},
    )


def health(request):
    return json_response({'ok': True, 'service': 'carch-api'})


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


def serialize_transaction(transaction):
    approved_at = timezone.localtime(transaction.approved_at)
    approved_at_text = approved_at.isoformat()
    amount = int(transaction.amount)
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


def ensure_transactions_seeded():
    if Transaction.objects.exists():
        return

    rows = []
    for item in TRANSACTIONS:
        rows.append(
            Transaction(
                public_id=item['id'],
                card_id=str(item['cardId']),
                merchant_name=item['merchantName'],
                category=item['category'],
                amount=int(item['amount']),
                approved_at=parse_approved_at(item['approvedAt']),
                icon=item.get('icon') or '💳',
                address=item.get('address') or '-',
            )
        )
    Transaction.objects.bulk_create(rows, ignore_conflicts=True)


def ensure_purchase_plans_seeded():
    if PurchasePlan.objects.exists():
        return

    for item in PURCHASE_PLANS:
        PurchasePlan.objects.create(
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


def transaction_queryset():
    ensure_transactions_seeded()
    return Transaction.objects.all()


def get_transaction_or_404(transaction_id):
    try:
        return transaction_queryset().get(public_id=str(transaction_id))
    except Transaction.DoesNotExist:
        raise Http404('거래내역을 찾을 수 없습니다.')


def create_transaction_from_payload(payload):
    data = build_transaction(payload)
    return Transaction.objects.create(
        public_id=data['id'],
        card_id=data['cardId'],
        merchant_name=data['merchantName'],
        category=data['category'],
        amount=data['amount'],
        approved_at=parse_approved_at(data['approvedAt']),
        icon=data.get('icon') or '💳',
        address=data.get('address') or '직접 입력',
        source_text=payload.get('sourceText') or payload.get('source_text') or '',
    )


def ensure_community_seeded():
    if CommunityPost.objects.exists():
        return

    seed_posts = [
        {
            'title': 'LOCA 100 vs 카드의정석2 SHOPPER 비교 후기',
            'body': '6개월 사용 후 솔직한 후기입니다. LOCA 100은 일상 할인 폭이 안정적이고, 카드의정석2 SHOPPER는 쇼핑 혜택이 매력적이에요.',
            'author': '이승민',
            'avatar': '이',
            'tags': ['카드비교', '롯데카드', '우리카드'],
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
            'title': '이마트 신한카드 이 혜택 아셨나요?',
            'body': '많은 분들이 모르고 있는 이마트 신한카드의 마트 혜택과 기본 적립 조건을 소개합니다.',
            'author': '최민준',
            'avatar': '최',
            'tags': ['신한카드', '마트'],
            'likes': 34,
            'liked': False,
            'comments': [],
        },
    ]

    for item in seed_posts:
        comments = item.pop('comments')
        post = CommunityPost.objects.create(**item)
        for comment in comments:
            CommunityComment.objects.create(post=post, **comment)


def serialize_comment(comment):
    created_at = timezone.localtime(comment.created_at)
    return {
        'id': f'cm{comment.id}',
        'rawId': comment.id,
        'author': comment.author,
        'avatar': comment.avatar,
        'body': comment.body,
        'text': comment.body,
        'date': created_at.date().isoformat(),
        'createdAt': created_at.isoformat(),
    }


def serialize_community_post(post, include_comments=False):
    created_at = timezone.localtime(post.created_at)
    payload = {
        'id': f'c{post.id}',
        'rawId': post.id,
        'title': post.title,
        'body': post.body,
        'author': post.author,
        'avatar': post.avatar,
        'date': created_at.date().isoformat(),
        'createdAt': created_at.isoformat(),
        'updatedAt': timezone.localtime(post.updated_at).isoformat(),
        'likes': post.likes,
        'liked': post.liked,
        'comments': post.comment_set.count(),
        'commentCount': post.comment_set.count(),
        'tags': post.tags or [],
    }
    if include_comments:
        payload['commentItems'] = [serialize_comment(comment) for comment in post.comment_set.all()]
    return payload


def serialize_analysis_record(record):
    created_at = timezone.localtime(record.created_at)
    return {
        'id': f'a{record.id}',
        'rawId': record.id,
        'analysisType': record.analysis_type,
        'title': record.title,
        'inputPayload': record.input_payload,
        'resultPayload': record.result_payload,
        'aiMode': record.ai_mode,
        'confidence': record.confidence,
        'createdAt': created_at.isoformat(),
        'date': created_at.date().isoformat(),
    }


def save_analysis_record(analysis_type, title, input_payload, result_payload):
    confidence = result_payload.get('confidence') if isinstance(result_payload, dict) else None
    try:
        confidence = float(confidence) if confidence is not None else None
    except (TypeError, ValueError):
        confidence = None

    return AIAnalysisRecord.objects.create(
        analysis_type=analysis_type,
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


def get_purchase_plan_or_404(plan_id):
    try:
        return PurchasePlan.objects.get(id=normalize_plan_id(plan_id))
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
        items.append(
            {
                'id': str(item.get('id') or f'i{index}'),
                'name': str(item.get('name') or f'구매 항목 {index}').strip()[:80],
                'category': str(item.get('category') or '기타').strip()[:40],
                'amount': amount,
                'targetMonth': str(item.get('targetMonth') or item.get('target_month') or '')[:7],
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


def create_purchase_plan_from_payload(payload):
    items = normalize_plan_items(payload.get('items') or [])
    return PurchasePlan.objects.create(
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
            'card': 'LOCA 100',
            'benefit': min(int(item.get('amount') or 0) // 100, 30000),
            'note': '월 실적과 기본 할인 혜택을 함께 고려한 배정입니다.',
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
            'reasons': ['보유 카드 혜택을 우선 배정했습니다.', '전월 실적 충족 가능성을 함께 고려했습니다.'],
            'warning': None,
            'monthlyPlan': [
                {'month': plan.start_month, 'items': first_month_items},
                {'month': plan.end_month, 'items': last_month_items},
            ],
            'cardSummary': [
                {'cardName': 'LOCA 100', 'totalAmount': sum(int(item.get('amount') or 0) for item in items[:2]), 'benefit': 45000, 'achieved': True, 'remainingLimit': 100000, 'itemCount': len(items[:2])},
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


def ensure_owned_cards_seeded():
    if OwnedCard.objects.exists():
        return
    OwnedCard.objects.bulk_create(
        [
            OwnedCard(card_id=card_id, display_order=index)
            for index, card_id in enumerate(DEFAULT_OWNED_CARD_IDS)
        ],
        ignore_conflicts=True,
    )


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
    ensure_owned_cards_seeded()

    if request.method == 'GET':
        cards = []
        for owned_card in OwnedCard.objects.all():
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

        max_order = OwnedCard.objects.aggregate(value=Max('display_order'))['value']
        owned_card, created = OwnedCard.objects.get_or_create(
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
    ensure_owned_cards_seeded()

    raw_id = str(card_id).strip()
    try:
        if raw_id.startswith('oc') and raw_id[2:].isdigit():
            owned_card = OwnedCard.objects.get(id=int(raw_id[2:]))
        else:
            owned_card = OwnedCard.objects.get(card_id=raw_id)
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
    if request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            return json_response({'detail': 'JSON 형식이 올바르지 않습니다.'}, status=400)
        transaction = create_transaction_from_payload(payload)
        return json_response(serialize_transaction(transaction), status=201)

    card_id = request.GET.get('cardId') or request.GET.get('card_id')
    category = request.GET.get('category')
    transactions = transaction_queryset()
    if card_id:
        transactions = transactions.filter(card_id=str(card_id))
    if category:
        transactions = transactions.filter(category=category)
    rows = [serialize_transaction(item) for item in transactions]
    return json_response({'count': len(rows), 'results': rows})


def transaction_detail(request, transaction_id):
    transaction = get_transaction_or_404(transaction_id)
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
    return {
        'id': public_id,
        'cardId': str(payload.get('cardId') or payload.get('card_id') or '10029'),
        'merchantName': payload.get('merchantName') or payload.get('merchant_name') or payload.get('merchant') or '가맹점 미확인',
        'category': payload.get('category') or payload.get('cat') or '기타',
        'amount': amount,
        'approvedAt': approved_at,
        'icon': payload.get('icon') or '💳',
        'address': payload.get('address') or payload.get('addr') or '직접 입력',
    }


@csrf_exempt
def parse_transaction(request):
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
        )
        return json_response(ai_parsed)

    merchant, category, icon = infer_merchant(text)
    parsed = {
        'cardId': infer_card_id(text),
        'merchantName': merchant,
        'category': category,
        'amount': infer_amount(text),
        'approvedAt': infer_approved_at(text),
        'icon': icon,
        'address': '직접 입력',
        'sourceText': text,
        'aiMode': 'mock',
        'confidence': 0.82 if merchant != '가맹점 미확인' and infer_amount(text) != 0 else 0.58,
        'reviewFields': ['merchantName', 'amount', 'approvedAt', 'cardId'],
    }
    save_analysis_record(
        'transaction_parse',
        '결제내역 입력 보정',
        {'rawText': text},
        parsed,
    )
    return json_response(parsed)


def spending_summary(request):
    transactions = [serialize_transaction(item) for item in transaction_queryset()]
    expense_rows = [item for item in transactions if item['amount'] < 0]
    by_category = defaultdict(int)
    by_card = defaultdict(int)
    for item in expense_rows:
        amount = abs(item['amount'])
        by_category[item['category']] += amount
        by_card[item['cardId']] += amount

    summary = {
        'totalExpense': sum(abs(item['amount']) for item in expense_rows),
        'totalIncome': sum(item['amount'] for item in transactions if item['amount'] > 0),
        'byCategory': [{'category': key, 'amount': value} for key, value in by_category.items()],
        'byCard': [{'cardId': key, 'amount': value} for key, value in by_card.items()],
    }

    include_ai = request.GET.get('ai') in {'1', 'true', 'yes'}
    refresh_ai = request.GET.get('refresh') in {'1', 'true', 'yes'} or request.GET.get('force') in {'1', 'true', 'yes'}

    if include_ai:
        latest_record = AIAnalysisRecord.objects.filter(analysis_type='spending_summary').first()
        if latest_record and not refresh_ai:
            summary['aiAnalysis'] = latest_record.result_payload or fallback_spending_analysis(summary)
            summary['aiAnalysisRecordId'] = f'a{latest_record.id}'
            summary['aiAnalysisCached'] = True
            summary['aiAnalysisCreatedAt'] = timezone.localtime(latest_record.created_at).isoformat()
            return json_response(summary)

        if not refresh_ai:
            summary['aiAnalysisStatus'] = 'empty'
            summary['aiAnalysisCached'] = False
            return json_response(summary)

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
        }
        summary['aiAnalysis'] = analyze_spending_with_ai(summary, transactions, cards) or fallback_spending_analysis(summary)
        record = save_analysis_record(
            'spending_summary',
            summary['aiAnalysis'].get('summaryTitle') or '카드 소비 분석',
            {
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
            },
            summary['aiAnalysis'],
        )
        summary['aiAnalysisRecordId'] = f'a{record.id}'
        summary['aiAnalysisCached'] = False
        summary['aiAnalysisCreatedAt'] = timezone.localtime(record.created_at).isoformat()

    return json_response(summary)


def fallback_spending_analysis(summary):
    top_category = max(summary['byCategory'], key=lambda item: item['amount'], default={'category': '기타', 'amount': 0})
    return {
        'summaryTitle': '이번 달 소비 요약',
        'headline': f"{top_category['category']} 지출 비중이 가장 높습니다.",
        'savingOpportunities': [
            {
                'title': f"{top_category['category']} 예산 점검",
                'amount': 0,
                'reason': 'AI 호출 실패 시 기본 규칙으로 만든 안내입니다.',
                'action': '상위 지출 카테고리의 반복 결제를 확인하세요.',
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
        'nextActions': ['상위 지출 카테고리 확인', '추천 카드와 혜택 비교'],
        'aiMode': 'mock',
        'confidence': 0.55,
    }


def analysis_record_list(request):
    if request.method != 'GET':
        return json_response({'detail': 'GET 요청만 지원합니다.'}, status=405)

    records = AIAnalysisRecord.objects.all()
    analysis_type = (request.GET.get('type') or request.GET.get('analysisType') or '').strip()
    if analysis_type:
        records = records.filter(analysis_type=analysis_type)

    try:
        limit = min(max(int(request.GET.get('limit', 20)), 1), 100)
    except (TypeError, ValueError):
        limit = 20

    rows = [serialize_analysis_record(record) for record in records[:limit]]
    return json_response({'count': records.count(), 'results': rows})


def build_chat_context(request):
    transactions = [serialize_transaction(item) for item in transaction_queryset()]
    expense_rows = [item for item in transactions if item['amount'] < 0]
    by_category = defaultdict(int)
    by_card = defaultdict(int)
    for item in expense_rows:
        amount = abs(item['amount'])
        by_category[item['category']] += amount
        by_card[item['cardId']] += amount

    summary = {
        'totalExpense': sum(abs(item['amount']) for item in expense_rows),
        'totalIncome': sum(item['amount'] for item in transactions if item['amount'] > 0),
        'byCategory': [{'category': key, 'amount': value} for key, value in by_category.items()],
        'byCard': [{'cardId': key, 'amount': value} for key, value in by_card.items()],
    }

    cards = []
    card_ids = [*by_card.keys(), '10029', '10612', '10609']
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
        'transactions': transactions,
        'cards': cards[:6],
        'communityPosts': community_posts,
    }


def fallback_chat_response(message, context):
    summary = context.get('summary') or {}
    top_category = max(summary.get('byCategory') or [], key=lambda item: item['amount'], default={'category': '기타', 'amount': 0})
    text = str(message or '')

    if '추천' in text or '카드' in text:
        reply = '현재 데이터 기준으로는 자주 쓰는 카테고리와 전월실적 조건을 같이 보는 카드 추천이 좋아요. 추천 화면에서 보유 카드와 후보 카드의 혜택 요약을 비교해볼 수 있습니다.'
        route = '/recommendations/new'
        quick_replies = ['내 소비에 맞는 카드 추천', '전월실적 확인해줘', '소비 분석해줘']
    elif '결제' in text or '내역' in text or '추가' in text:
        reply = '결제내역은 직접 추가하고, AI가 문구를 가맹점/금액/카테고리로 보정하는 흐름이 가장 안전합니다. 카드사 실데이터 자동 수집 없이도 시연 완성도가 좋아요.'
        route = '/transactions/new'
        quick_replies = ['결제내역 추가할래', '최근 거래 보여줘', '카테고리 분석해줘']
    elif '계획' in text or '구매' in text:
        reply = '예정된 큰 지출은 목적과 시점을 먼저 나눈 뒤 카드 혜택 조건에 맞춰 배치하면 좋습니다. 취업 준비, 여행, 전자기기처럼 항목이 섞인 계획도 월별 초안으로 정리할 수 있습니다.'
        route = '/plans/new'
        quick_replies = ['큰 지출 계획 만들기', '취업 준비 예시', '카드 추천해줘']
    else:
        reply = f"현재 데이터에서는 {top_category['category']} 지출이 가장 크게 보여요. 먼저 상위 카테고리를 확인하고, 자주 쓰는 카드가 그 지출에 맞는 혜택을 주는지 비교해보면 좋겠습니다."
        route = '/analytics/cards'
        quick_replies = ['이번 달 소비 분석해줘', '카드 추천해줘', '결제내역 추가할래']

    return {
        'reply': reply,
        'quickReplies': quick_replies,
        'relatedRoute': route,
        'aiMode': 'mock',
        'confidence': 0.55,
    }


@csrf_exempt
def chat_message(request):
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
    )
    ai_response['analysisRecordId'] = f'a{record.id}'
    return json_response(ai_response)


def card_recommendations(request):
    cards = fetch_cards(request, limit=12, active_only=True)
    shopping_keywords = ('쇼핑', '마트', '온라인', '생활')

    ranked = []
    for card in cards:
        text = ' '.join([card.get('benefitSummary') or '', card.get('titleDescription') or '', *card.get('benefits', [])])
        score = 78
        if any(keyword in text for keyword in shopping_keywords):
            score += 12
        if card.get('previousMonthMinSpend') and card['previousMonthMinSpend'] <= 500000:
            score += 5
        ranked.append(
            {
                **card,
                'match': min(score, 96),
                'reason': '최근 쇼핑/생활 지출 비중과 전월실적 조건을 함께 반영했습니다.',
                'highlights': card.get('benefits', []),
            }
        )
    ranked.sort(key=lambda item: item['match'], reverse=True)
    return json_response({'count': min(len(ranked), 3), 'results': ranked[:3]})


@csrf_exempt
def community_post_list(request):
    ensure_community_seeded()

    if request.method == 'POST':
        payload, error_response = parse_request_body(request)
        if error_response:
            return error_response

        title = (payload.get('title') or '').strip()
        body = (payload.get('body') or payload.get('content') or '').strip()
        if not title:
            return json_response({'detail': '제목을 입력해 주세요.'}, status=400)
        if not body:
            return json_response({'detail': '본문을 입력해 주세요.'}, status=400)

        author = (payload.get('author') or '남주현').strip()
        post = CommunityPost.objects.create(
            title=title[:120],
            body=body,
            author=author[:30],
            avatar=(payload.get('avatar') or author[:1] or '남')[:2],
            tags=normalize_tags(payload.get('tags')),
        )
        return json_response(serialize_community_post(post, include_comments=True), status=201)

    if request.method != 'GET':
        return json_response({'detail': '지원하지 않는 요청입니다.'}, status=405)

    posts = CommunityPost.objects.all()
    search = (request.GET.get('search') or '').strip()
    if search:
        posts = posts.filter(title__icontains=search)
    return json_response({'count': posts.count(), 'results': [serialize_community_post(post) for post in posts]})


@csrf_exempt
def community_post_detail(request, post_id):
    ensure_community_seeded()
    post = get_community_post_or_404(post_id)

    if request.method == 'GET':
        return json_response(serialize_community_post(post, include_comments=True))

    if request.method in {'PATCH', 'PUT'}:
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
        return json_response(serialize_community_post(post, include_comments=True))

    if request.method == 'DELETE':
        post.delete()
        return json_response({'ok': True})

    return json_response({'detail': '지원하지 않는 요청입니다.'}, status=405)


@csrf_exempt
def community_post_like(request, post_id):
    ensure_community_seeded()
    if request.method != 'POST':
        return json_response({'detail': 'POST 요청만 지원합니다.'}, status=405)

    post = get_community_post_or_404(post_id)
    post.liked = not post.liked
    if post.liked:
        post.likes += 1
    else:
        post.likes = max(post.likes - 1, 0)
    post.save(update_fields=['liked', 'likes', 'updated_at'])
    return json_response(serialize_community_post(post, include_comments=True))


@csrf_exempt
def community_comment_list(request, post_id):
    ensure_community_seeded()
    post = get_community_post_or_404(post_id)

    if request.method == 'GET':
        return json_response({'count': post.comment_set.count(), 'results': [serialize_comment(comment) for comment in post.comment_set.all()]})

    if request.method == 'POST':
        payload, error_response = parse_request_body(request)
        if error_response:
            return error_response
        body = (payload.get('body') or payload.get('text') or payload.get('content') or '').strip()
        if not body:
            return json_response({'detail': '댓글을 입력해 주세요.'}, status=400)
        author = (payload.get('author') or '남주현').strip()
        comment = CommunityComment.objects.create(
            post=post,
            body=body,
            author=author[:30],
            avatar=(payload.get('avatar') or author[:1] or '남')[:2],
        )
        return json_response(serialize_comment(comment), status=201)

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
        comment.delete()
        return json_response({'ok': True})
    return json_response({'detail': '지원하지 않는 요청입니다.'}, status=405)


def ai_contract(request):
    return json_response(
        {
            'when': '카드/결제내역 API 연결 후 실제 AI 호출을 붙입니다.',
            'input': {
                'rawPrompt': '다음 달 큰 지출 예산 80만 원을 관리하고 싶어요.',
                'transactions': '최근 결제내역 배열',
                'cards': '보유/추천 카드 배열',
            },
            'parseOutput': {
                'title': '취업 준비 지출 계획',
                'type': '취업 준비',
                'totalBudget': 800000,
                'startMonth': '2026-07',
                'endMonth': '2026-08',
                'items': [
                    {
                        'name': '정장 셔츠·슬랙스',
                        'category': '쇼핑',
                        'amount': 210000,
                        'targetMonth': '2026-07',
                        'required': True,
                        'flexible': False,
                    }
                ],
            },
        }
    )


@csrf_exempt
def purchase_plan_list(request):
    if request.method == 'GET':
        ensure_purchase_plans_seeded()
        plans = [serialize_purchase_plan(plan) for plan in PurchasePlan.objects.all()]
        return json_response(plans)

    if request.method == 'POST':
        payload, error_response = parse_request_body(request)
        if error_response:
            return error_response
        plan = create_purchase_plan_from_payload(payload)
        return json_response(serialize_purchase_plan(plan), status=201)

    return json_response({'detail': '지원하지 않는 요청입니다.'}, status=405)


@csrf_exempt
def purchase_plan_detail(request, plan_id):
    plan = get_purchase_plan_or_404(plan_id)

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

    plan = get_purchase_plan_or_404(plan_id)
    plan.scenarios = build_plan_scenarios(plan)
    plan.status = '계산 완료'
    plan.save(update_fields=['scenarios', 'status', 'updated_at'])
    return json_response(plan.scenarios)


@csrf_exempt
def purchase_plan_select(request, plan_id):
    if request.method != 'POST':
        return json_response({'detail': 'POST 요청만 지원합니다.'}, status=405)

    payload, error_response = parse_request_body(request)
    if error_response:
        return error_response
    plan = get_purchase_plan_or_404(plan_id)
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
    )
    plan['analysisRecordId'] = f'a{record.id}'
    return json_response(plan)

def fallback_spending_analysis(summary):
    top_category = max(summary['byCategory'], key=lambda item: item['amount'], default={'category': '기타', 'amount': 0})
    top_category_name = top_category.get('category') or '기타'
    top_category_amount = int(top_category.get('amount') or 0)
    total_expense = int(summary.get('totalExpense') or 0)
    return {
        'schemaVersion': 'spending-analysis-v2',
        'summaryTitle': '이번 달 소비 진단',
        'headline': f'{top_category_name} 지출 비중이 가장 높아 먼저 점검하면 좋아요.',
        'narrative': 'AI 호출이 실패해 기본 규칙으로 만든 분석입니다. 최근 거래 기준의 상위 지출부터 확인하세요.',
        'primaryInsight': {
            'label': '기본 진단',
            'title': f'{top_category_name} 지출 집중',
            'body': '현재 저장된 거래 기준으로 가장 큰 지출 항목입니다.',
            'severity': 'info',
            'metricLabel': '점검 금액',
            'metricValue': top_category_amount,
        },
        'summaryCards': [
            {
                'label': '총 지출',
                'value': f'{total_expense:,}원',
                'caption': '저장된 거래 기준',
                'tone': 'navy',
            },
            {
                'label': '우선 점검',
                'value': str(top_category_name),
                'caption': '가장 큰 카테고리',
                'tone': 'teal',
            },
        ],
        'savingOpportunities': [
            {
                'title': f'{top_category_name} 지출 점검',
                'amount': 0,
                'reason': 'AI 호출 실패 시 기본 규칙으로 만든 안내입니다.',
                'action': '상위 지출 카테고리의 반복 결제를 확인하세요.',
                'severity': 'info',
                'route': '/analytics/cards',
            }
        ],
        'categoryInsights': [
            {
                'category': top_category_name,
                'amount': top_category_amount,
                'shareLabel': '상위 지출',
                'insight': '현재 데이터에서 가장 큰 지출 항목입니다.',
            }
        ],
        'cardInsights': [],
        'warnings': ['실제 카드 혜택과 전월 실적 조건은 카드사 안내를 최종 확인해야 합니다.'],
        'nextActions': ['상위 지출 확인', '카드 혜택 비교'],
        'actionButtons': [
            {'label': '소비 분석 보기', 'route': '/analytics/cards', 'intent': 'open-analysis'},
            {'label': '카드 추천 보기', 'route': '/recommendations/new', 'intent': 'recommendation'},
        ],
        'aiMode': 'mock',
        'confidence': 0.55,
    }


def fallback_chat_response(message, context):
    summary = context.get('summary') or {}
    top_category = max(summary.get('byCategory') or [], key=lambda item: item['amount'], default={'category': '기타', 'amount': 0})
    top_category_name = top_category.get('category') or '기타'
    text = str(message or '')

    if '추천' in text or '카드' in text:
        reply = '현재 데이터 기준으로는 자주 쓰는 카테고리와 전월 실적 조건을 함께 보는 카드 추천 흐름이 좋아요. 추천 화면에서 보유 카드와 후보 카드의 혜택 요약을 비교해보세요.'
        route = '/recommendations/new'
        message_type = 'card-recommendation'
        quick_replies = ['내 소비에 맞는 카드 추천', '전월 실적 확인해줘', '소비 분석해줘']
        chips = [{'label': '추천 기준', 'value': '소비 카테고리', 'tone': 'teal'}]
    elif '결제' in text or '내역' in text or '추가' in text:
        reply = '결제내역은 직접 추가하고 AI가 문장을 가맹점, 금액, 카테고리로 보정하는 흐름이 가장 안전해요. 자동 수집 없이도 시연 완성도가 좋아집니다.'
        route = '/transactions/new'
        message_type = 'transaction-help'
        quick_replies = ['결제내역 추가할래', '최근 거래 보여줘', '카테고리 분석해줘']
        chips = [{'label': '추천 입력', 'value': '문장 보정', 'tone': 'blue'}]
    elif '계획' in text or '구매' in text:
        reply = '큰 지출은 월 예산 안에서 관리할지, 별도 예정 지출로 볼지 먼저 선택하는 게 좋아요. 취업 준비, 여행, 전자기기처럼 목적이 다른 지출도 품목과 월별 배치로 정리할 수 있습니다.'
        route = '/plans/new'
        message_type = 'purchase-plan'
        quick_replies = ['큰 지출 계획 만들기', '취업 준비 예시', '카드 추천해줘']
        chips = [{'label': '관리 방식', 'value': '선택 가능', 'tone': 'gold'}]
    else:
        reply = f'현재 데이터에서는 {top_category_name} 지출이 가장 크게 보여요. 먼저 상위 지출을 확인하고, 자주 쓰는 카드가 그 소비에 맞는 혜택을 주는지 비교하면 좋습니다.'
        route = '/analytics/cards'
        message_type = 'spending-analysis'
        quick_replies = ['이번 달 소비 분석해줘', '카드 추천해줘', '결제내역 추가할래']
        chips = [{'label': '우선 확인', 'value': str(top_category_name), 'tone': 'teal'}]

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
                        'cardId': '10029',
                        'merchantName': '컴포즈커피 역삼센터필드점',
                        'category': '카페',
                        'amount': -3800,
                        'approvedAt': '2026-06-23T09:30:00+09:00',
                        'displayTitle': '컴포즈커피 결제',
                        'displaySubtitle': '카페 · 3,800원 · LOCA 100',
                        'corrections': [],
                        'confidence': 0.85,
                        'reviewFields': ['amount', 'approvedAt'],
                    },
                },
                'spendingAnalysis': {
                    'output': {
                        'schemaVersion': 'spending-analysis-v2',
                        'summaryTitle': '이번 달 소비 진단',
                        'headline': '쇼핑과 마트 지출 비중이 높아 카드 혜택 점검 여지가 있어요.',
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
                        'reply': '최근 소비를 기준으로 다음 행동을 추천합니다.',
                        'summaryChips': [],
                        'quickReplies': [],
                        'actionButtons': [],
                        'relatedRoute': '/analytics/cards',
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
    '구독': ['구독', '넷플릭스', '스트리밍', 'subscription'],
}


def _as_int(value, fallback=0):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return fallback


def _krw(value):
    return f'{_as_int(value):,}원'


def _category_keywords(category):
    return CARD_RECOMMENDATION_CATEGORY_KEYWORDS.get(str(category), [str(category)])


def _build_spending_profile():
    transactions = [serialize_transaction(item) for item in transaction_queryset()]
    expenses = [item for item in transactions if _as_int(item.get('amount')) < 0]
    by_category = defaultdict(int)
    by_card = defaultdict(int)
    by_category_card = defaultdict(lambda: {'amount': 0, 'merchants': []})

    for item in expenses:
        amount = abs(_as_int(item.get('amount')))
        category = item.get('category') or item.get('cat') or '기타'
        card_id = str(item.get('cardId') or item.get('card_id') or '')
        by_category[category] += amount
        by_card[card_id] += amount
        category_card = by_category_card[(category, card_id)]
        category_card['amount'] += amount
        merchant = item.get('merchantName') or item.get('merchant') or ''
        if merchant and merchant not in category_card['merchants']:
            category_card['merchants'].append(merchant)

    category_rows = sorted(
        [{'category': key, 'amount': value} for key, value in by_category.items()],
        key=lambda item: item['amount'],
        reverse=True,
    )
    total_expense = sum(row['amount'] for row in category_rows)
    top_category = category_rows[0]['category'] if category_rows else '기타'

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

    return {
        'totalExpense': total_expense,
        'categoryRows': category_rows,
        'byCard': [{'cardId': key, 'amount': value} for key, value in by_card.items()],
        'categoryCardRows': sorted(
            [
                {
                    'category': category,
                    'cardId': card_id,
                    'amount': value['amount'],
                    'merchantExamples': value['merchants'][:3],
                }
                for (category, card_id), value in by_category_card.items()
            ],
            key=lambda item: item['amount'],
            reverse=True,
        ),
        'topCategory': top_category,
        'styleTags': style_tags[:3],
    }


def _benefit_rate_for_category(card, category):
    keywords = [keyword.lower() for keyword in _category_keywords(category)]
    benefit_items = card.get('benefitItems') or []
    best_rate = 0.0
    best_limit = None
    best_label = ''

    for item in benefit_items:
        label = ' '.join(
            str(value or '')
            for value in [item.get('label'), item.get('scope'), item.get('type')]
        ).lower()
        if not any(keyword in label for keyword in keywords):
            continue
        rate = item.get('ratePercent')
        if rate is None and item.get('type') in {'discount_rate', 'point_rate'}:
            rate = item.get('benefitValue') or item.get('benefit_value')
        try:
            rate = float(rate or 0)
        except (TypeError, ValueError):
            rate = 0
        if rate > best_rate:
            best_rate = rate
            best_limit = item.get('monthlyBenefitLimitKrw')
            best_label = item.get('label') or item.get('scope') or ''

    if best_rate:
        return best_rate, _as_int(best_limit, 0) or None, best_label

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
    if '전가맹' in text or '국내' in text or '언제나' in text:
        basic_matches = re.findall(
            r'(?:전가맹|국내외?|가맹점|언제나)[^%]{0,40}?(\d+(?:\.\d+)?)\s*%',
            text,
        )
        percent_values = [float(match) for match in basic_matches]
        if not percent_values:
            percent_values = [float(match) for match in re.findall(r'(\d+(?:\.\d+)?)\s*%\s*(?:적립|할인)', text)]
        return min(percent_values or [0.5], default=0.5), None, '기본 혜택'
    return 0.2, None, '기본 추정'


def _estimate_card_value(card, profile, owned=False):
    annual_fee = _as_int(card.get('annualFee') or card.get('domesticAnnualFee') or card.get('domestic_annual_fee'))
    monthly_annual_fee = round(annual_fee / 12)
    min_spend = _as_int(card.get('previousMonthMinSpend') or card.get('previous_month_min_spend'))
    total_spend = _as_int(profile.get('totalExpense'))
    eligible_ratio = 1
    remaining_spend = 0
    if min_spend and total_spend < min_spend:
        eligible_ratio = max(0.25, total_spend / min_spend) if total_spend else 0.25
        remaining_spend = min_spend - total_spend

    category_breakdown = []
    gross_benefit = 0
    matched_categories = []
    for row in profile.get('categoryRows') or []:
        amount = _as_int(row.get('amount'))
        if amount <= 0:
            continue
        rate, limit, label = _benefit_rate_for_category(card, row.get('category'))
        estimated = round(amount * rate / 100)
        if limit is not None:
            estimated = min(estimated, limit)
        estimated = round(estimated * eligible_ratio)
        gross_benefit += estimated
        if estimated > 0:
            matched_categories.append(row.get('category'))
        category_breakdown.append(
            {
                'category': row.get('category'),
                'amount': amount,
                'rate': round(rate, 2),
                'estimatedBenefit': estimated,
                'benefitLabel': label,
            }
        )

    monthly_net = gross_benefit - monthly_annual_fee
    annual_net = monthly_net * 12
    return {
        'expectedMonthlyBenefit': gross_benefit,
        'monthlyAnnualFee': monthly_annual_fee,
        'monthlyNetBenefit': monthly_net,
        'annualNetBenefit': annual_net,
        'annualFee': annual_fee,
        'previousMonthMinSpend': min_spend,
        'remainingSpendForBenefit': remaining_spend,
        'eligibleRatio': round(eligible_ratio, 2),
        'matchedCategories': list(dict.fromkeys(matched_categories))[:4],
        'categoryBreakdown': category_breakdown[:8],
        'owned': owned,
    }


def _recommendation_reason(card, value, profile, monthly_delta):
    top_category = profile.get('topCategory') or '주요 소비'
    if monthly_delta > 0:
        return f'{top_category} 지출 기준으로 연회비를 반영해도 현재 카드보다 월 {_krw(monthly_delta)} 정도 더 유리해요.'
    if value.get('remainingSpendForBenefit'):
        return f'혜택 조건까지 {_krw(value["remainingSpendForBenefit"])} 정도 남아 있어, 실적을 채우면 후보가 될 수 있어요.'
    return f'{top_category} 소비와 일부 혜택이 맞지만 현재 보유 카드 대비 순혜택은 크지 않아요.'


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


def _estimate_category_benefit(card, category, amount):
    rate, limit, label = _benefit_rate_for_category(card, category)
    estimated = round(_as_int(amount) * rate / 100)
    if limit is not None:
        estimated = min(estimated, _as_int(limit))
    return {
        'rate': round(rate, 2),
        'benefitLabel': label,
        'estimatedBenefit': estimated,
    }


def _build_routing_suggestions(profile, owned_values, result_cards, owned_ids):
    cards_by_id = {}
    destinations = []
    for item in owned_values:
        card = item.get('card') or {}
        card_id = _card_id(card)
        if card_id:
            cards_by_id[card_id] = card
            destinations.append({'card': card, 'rank': 99, 'monthlyDelta': 0})
    for index, card in enumerate(result_cards):
        card_id = _card_id(card)
        if card_id:
            cards_by_id.setdefault(card_id, card)
            destinations.append(
                {
                    'card': card,
                    'rank': index,
                    'monthlyDelta': _as_int((card.get('economics') or {}).get('monthlyDelta')),
                }
            )

    suggestions = []
    seen = set()
    for row in profile.get('categoryCardRows') or []:
        source_card_id = str(row.get('cardId') or '')
        source_card = cards_by_id.get(source_card_id)
        amount = _as_int(row.get('amount'))
        category = row.get('category') or '기타'
        if not source_card or amount <= 0:
            continue

        source_estimate = _estimate_category_benefit(source_card, category, amount)
        for destination_item in destinations:
            destination = destination_item['card']
            target_card_id = _card_id(destination)
            if not target_card_id or target_card_id == source_card_id:
                continue

            target_estimate = _estimate_category_benefit(destination, category, amount)
            monthly_gain = target_estimate['estimatedBenefit'] - source_estimate['estimatedBenefit']
            if monthly_gain < 1000:
                continue

            key = (category, source_card_id, target_card_id)
            if key in seen:
                continue
            seen.add(key)

            target_name = _card_name(destination)
            source_name = _card_name(source_card)
            owned_target = target_card_id in owned_ids
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
                    'merchantExamples': row.get('merchantExamples') or [],
                    'scope': 'owned' if owned_target else 'candidate',
                    'scopeLabel': '보유 카드 조정' if owned_target else '추천 카드 검토',
                    'destinationRank': destination_item['rank'],
                    'destinationMonthlyDelta': destination_item['monthlyDelta'],
                    'title': f'{category}{_topic_particle(category)} {target_name}',
                    'body': f'{source_name}의 {category} 결제를 {target_name}로 옮기면 월 {_krw(monthly_gain)} 더 남습니다.',
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
    profile = _build_spending_profile()
    ensure_owned_cards_seeded()
    owned_ids = {str(item.card_id) for item in OwnedCard.objects.all()}

    owned_values = []
    for card_id in owned_ids:
        if card_id.isdigit():
            card = fetch_card(int(card_id), request)
            if card:
                owned_values.append({'card': card, **_estimate_card_value(card, profile, owned=True)})

    baseline = max(owned_values, key=lambda item: item['monthlyNetBenefit'], default=None)
    current_monthly_net = _as_int(baseline.get('monthlyNetBenefit')) if baseline else 0

    candidates = fetch_cards(request, limit=36, active_only=True)
    ranked = []
    for card in candidates:
        detailed = fetch_card(int(card['cardAdId']), request) or card
        value = _estimate_card_value(detailed, profile, owned=str(detailed.get('cardAdId')) in owned_ids)
        monthly_delta = value['monthlyNetBenefit'] - current_monthly_net
        annual_delta = monthly_delta * 12
        annual_fee_delta = max(0, value['annualFee'] - _as_int((baseline or {}).get('annualFee')))
        payback_months = None
        if monthly_delta > 0 and annual_fee_delta > 0:
            payback_months = max(1, round(annual_fee_delta / monthly_delta))

        match = 70
        match += min(18, max(0, monthly_delta) // 1000)
        match += min(8, len(value['matchedCategories']) * 3)
        if value['remainingSpendForBenefit']:
            match -= 8
        if value['owned']:
            match -= 6
        match = max(45, min(98, match))
        notification = annual_delta >= 30000 and monthly_delta > 0 and (payback_months is None or payback_months <= 8)

        ranked.append(
            {
                **detailed,
                'match': match,
                'reason': _recommendation_reason(detailed, value, profile, monthly_delta),
                'highlights': detailed.get('benefits', []),
                'spendingFit': {
                    'styleTags': profile['styleTags'],
                    'topCategory': profile['topCategory'],
                    'matchedCategories': value['matchedCategories'],
                    'categoryBreakdown': value['categoryBreakdown'],
                },
                'economics': {
                    **value,
                    'currentMonthlyNetBenefit': current_monthly_net,
                    'monthlyDelta': monthly_delta,
                    'annualDelta': annual_delta,
                    'paybackMonths': payback_months,
                    'annualFeeDelta': annual_fee_delta,
                },
                'notification': {
                    'show': notification,
                    'title': '카드 교체로 혜택이 늘 수 있어요',
                    'body': f'현재 소비 기준 월 {_krw(max(0, monthly_delta))} 정도 순혜택 차이가 예상돼요.',
                    'severity': 'attention' if notification else 'info',
                },
            }
        )

    ranked.sort(key=lambda item: (item['economics']['monthlyDelta'], item['economics']['monthlyNetBenefit'], item['match']), reverse=True)
    results = ranked[:5]
    top = results[0] if results else None
    alert = (top or {}).get('notification') or {'show': False}
    routing_suggestions = _build_routing_suggestions(profile, owned_values, results, owned_ids)

    return json_response(
        {
            'count': len(results),
            'profile': profile,
            'baseline': {
                'cardId': str((baseline or {}).get('card', {}).get('cardAdId') or ''),
                'cardName': (baseline or {}).get('card', {}).get('name') or '',
                'monthlyNetBenefit': current_monthly_net,
                'expectedMonthlyBenefit': _as_int((baseline or {}).get('expectedMonthlyBenefit')),
                'monthlyAnnualFee': _as_int((baseline or {}).get('monthlyAnnualFee')),
            },
            'alert': alert,
            'routingSuggestions': routing_suggestions,
            'results': results,
        }
    )


# Create your views here.
