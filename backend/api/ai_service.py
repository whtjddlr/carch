import json
import re
from datetime import datetime

import requests
from django.conf import settings
from django.utils import timezone

from . import ai_prompts


OPENAI_COMPATIBLE_MODES = {'gms', 'openai'}

CATEGORY_ICONS = {
    '카페': '☕',
    '쇼핑': '🛍',
    '편의점': '🏪',
    '뷰티': '💄',
    '마트': '🛒',
    '식비': '🍽',
    '교통': '🚇',
    '문화': '🎟',
    '구독': '📺',
    '수입': '💰',
    '기타': '💳',
}

KNOWN_CARDS = {
    '10029': 'LOCA 100',
    '10612': '카드의정석 SHOPPER',
    '10609': '이마트 신한카드',
}

ALLOWED_AI_ROUTES = {
    '/cards',
    '/transactions',
    '/transactions/new',
    '/budget',
    '/recommendations/new',
    '/analytics',
    '/community',
    '/plans',
    '/plans/new',
}

ALLOWED_TONES = {'navy', 'teal', 'blue', 'gray', 'gold', 'danger'}
ALLOWED_SEVERITIES = {'info', 'attention', 'warning'}
ALLOWED_MESSAGE_TYPES = {
    'general',
    'spending-analysis',
    'card-recommendation',
    'transaction-help',
    'purchase-plan',
    'navigation',
}


def get_ai_status():
    return {
        'configured': bool(settings.GMS_API_KEY) and settings.AI_MODE in OPENAI_COMPATIBLE_MODES,
        'mode': settings.AI_MODE,
        'provider': 'gms-openai-compatible',
        'model': settings.GMS_MODEL,
        'fallbackModel': settings.GMS_FALLBACK_MODEL,
        'baseUrl': settings.GMS_BASE_URL,
        'timeoutSeconds': settings.GMS_TIMEOUT_SECONDS,
        'maxOutputTokens': settings.GMS_MAX_OUTPUT_TOKENS,
        'keyLoaded': bool(settings.GMS_API_KEY),
    }


def parse_transaction_with_ai(raw_text):
    if not raw_text or not get_ai_status()['configured']:
        return None

    prompt = ai_prompts.build_transaction_prompt(
        raw_text,
        today=timezone.localtime().date().isoformat(),
        cards=KNOWN_CARDS,
        categories=CATEGORY_ICONS.keys(),
    )
    try:
        payload = request_gms_json(prompt, ai_prompts.TRANSACTION_DEVELOPER_PROMPT)
        parsed = extract_json_object(extract_output_text(payload))
        if not parsed:
            return None
        return normalize_transaction(parsed, raw_text)
    except (OSError, ValueError, requests.RequestException):
        return None


def parse_purchase_plan_with_ai(payload):
    raw_text = (payload.get('rawPrompt') or payload.get('prompt') or '').strip()
    if not raw_text or not get_ai_status()['configured']:
        return None

    prompt = ai_prompts.build_purchase_plan_prompt(
        payload,
        today=timezone.localtime().date().isoformat(),
    )
    try:
        response_payload = request_gms_json(prompt, ai_prompts.PURCHASE_PLAN_DEVELOPER_PROMPT)
        parsed = extract_json_object(extract_output_text(response_payload))
        if not parsed:
            return None
        return normalize_purchase_plan(parsed, payload)
    except (OSError, ValueError, requests.RequestException):
        return None


def analyze_spending_with_ai(summary, transactions, cards):
    if not get_ai_status()['configured']:
        return None

    prompt = ai_prompts.build_spending_analysis_prompt(summary, transactions, cards)
    try:
        response_payload = request_gms_json(prompt, ai_prompts.SPENDING_ANALYSIS_DEVELOPER_PROMPT)
        parsed = extract_json_object(extract_output_text(response_payload))
        if not parsed:
            return None
        return normalize_spending_analysis(parsed)
    except (OSError, ValueError, requests.RequestException):
        return None


def chat_with_ai(message, history, context):
    message = str(message or '').strip()
    if not message or not get_ai_status()['configured']:
        return None

    prompt = ai_prompts.build_chat_prompt(message, history, context)
    try:
        response_payload = request_gms_json(prompt, ai_prompts.CHAT_DEVELOPER_PROMPT)
        parsed = extract_json_object(extract_output_text(response_payload))
        if not parsed:
            return None
        return normalize_chat_response(parsed)
    except (OSError, ValueError, requests.RequestException):
        return None


def request_gms_chat_completion(prompt):
    return request_gms_json(prompt, ai_prompts.TRANSACTION_DEVELOPER_PROMPT)


def request_gms_json(prompt, developer_prompt):
    url = f'{settings.GMS_BASE_URL}/chat/completions'
    models = [settings.GMS_MODEL]
    if settings.GMS_FALLBACK_MODEL and settings.GMS_FALLBACK_MODEL not in models:
        models.append(settings.GMS_FALLBACK_MODEL)

    last_error = None
    for model in models:
        body = {
            'model': model,
            'messages': [
                {'role': 'developer', 'content': developer_prompt},
                {'role': 'user', 'content': prompt},
            ],
            'response_format': {'type': 'json_object'},
        }
        if model.startswith('gpt-5') or model.startswith('o'):
            body['reasoning_effort'] = 'low'
            body['max_completion_tokens'] = settings.GMS_MAX_OUTPUT_TOKENS
        else:
            body['max_tokens'] = settings.GMS_MAX_OUTPUT_TOKENS
        try:
            response = requests.post(
                url,
                json=body,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {settings.GMS_API_KEY}',
                },
                timeout=settings.GMS_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
            if extract_output_text(payload).strip():
                return payload
            finish_reason = ((payload.get('choices') or [{}])[0] or {}).get('finish_reason')
            last_error = ValueError(f'Empty GMS output: {finish_reason or "unknown"}')
        except requests.Timeout as error:
            last_error = error
            continue
        except requests.RequestException as error:
            last_error = error
    if last_error:
        raise last_error
    raise ValueError('No GMS model configured')


def extract_output_text(payload):
    if isinstance(payload.get('output_text'), str):
        return payload['output_text']

    chunks = []
    for item in payload.get('output', []):
        for content in item.get('content', []):
            if isinstance(content.get('text'), str):
                chunks.append(content['text'])
    if chunks:
        return ''.join(chunks)

    choices = payload.get('choices') or []
    if choices:
        message = choices[0].get('message') or {}
        content = message.get('content')
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and isinstance(item.get('text'), str):
                    chunks.append(item['text'])
            if chunks:
                return ''.join(chunks)

    return ''


def extract_json_object(text):
    if not text:
        return None
    cleaned = re.sub(r'^```(?:json)?|```$', '', text.strip(), flags=re.IGNORECASE | re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start == -1 or end == -1 or end <= start:
            return None
        return json.loads(cleaned[start : end + 1])


def normalize_transaction(parsed, source_text):
    card_id = str(parsed.get('cardId') or parsed.get('card_id') or '10029')
    if card_id not in KNOWN_CARDS:
        card_id = '10029'

    category = str(parsed.get('category') or '기타').strip()
    if category not in CATEGORY_ICONS:
        category = '기타'

    amount = coerce_amount(parsed.get('amount') or parsed.get('amt'))
    merchant = str(
        parsed.get('merchantName')
        or parsed.get('merchant_name')
        or parsed.get('merchant')
        or '가맹점 미확인'
    ).strip()

    review_fields = normalize_string_list(parsed.get('reviewFields') or parsed.get('review_fields'))

    return {
        'schemaVersion': str(parsed.get('schemaVersion') or 'transaction-parse-v2'),
        'cardId': card_id,
        'merchantName': merchant or '가맹점 미확인',
        'category': category,
        'amount': amount,
        'approvedAt': normalize_approved_at(parsed.get('approvedAt') or parsed.get('approved_at')),
        'icon': parsed.get('icon') or CATEGORY_ICONS[category],
        'address': parsed.get('address') or parsed.get('addr') or '직접 입력',
        'displayTitle': truncate(parsed.get('displayTitle') or merchant or '결제내역 확인', 80),
        'displaySubtitle': truncate(
            parsed.get('displaySubtitle') or f'{category} · {abs(amount):,}원 · {KNOWN_CARDS.get(card_id, card_id)}',
            120,
        ),
        'corrections': normalize_corrections(parsed.get('corrections')),
        'sourceText': source_text,
        'aiMode': 'gms',
        'confidence': clamp_confidence(parsed.get('confidence'), 0.75),
        'reviewFields': review_fields or ['merchantName', 'amount', 'approvedAt', 'cardId'],
    }


def normalize_purchase_plan(parsed, fallback_payload):
    fallback_budget = fallback_payload.get('budget') or fallback_payload.get('totalBudget') or 7000000
    start_month = normalize_month(parsed.get('startMonth') or fallback_payload.get('startMonth'), '2026-07')
    end_month = normalize_month(parsed.get('endMonth') or fallback_payload.get('endMonth'), '2026-09')
    items = []
    for index, item in enumerate(parsed.get('items') or [], start=1):
        if not isinstance(item, dict):
            continue
        name = str(item.get('name') or f'구매 항목 {index}').strip()
        items.append(
            {
                'id': str(item.get('id') or f'i{index}'),
                'name': name,
                'category': str(item.get('category') or '기타').strip(),
                'amount': coerce_positive_int(item.get('amount'), 0),
                'targetMonth': normalize_month(item.get('targetMonth'), start_month),
                'required': coerce_bool(item.get('required'), True),
                'flexible': coerce_bool(item.get('flexible'), True),
                'priority': normalize_choice(item.get('priority'), {'high', 'medium', 'low'}, 'medium'),
                'reason': truncate(item.get('reason') or '', 160),
            }
        )

    if not items:
        return None

    plan_type = truncate(parsed.get('type') or '기타', 30)
    title = truncate(parsed.get('title') or f'{plan_type} 구매 계획', 80)
    expense_mode = normalize_choice(
        parsed.get('expenseModeRecommendation') or parsed.get('expenseMode') or fallback_payload.get('expenseMode'),
        {'monthly-budget', 'planned-extra', 'mixed'},
        fallback_payload.get('expenseMode') or 'planned-extra',
    )

    return {
        'schemaVersion': str(parsed.get('schemaVersion') or 'purchase-plan-parse-v2'),
        'title': title,
        'type': plan_type,
        'summary': truncate(parsed.get('summary') or '', 240),
        'expenseModeRecommendation': expense_mode,
        'totalBudget': coerce_positive_int(parsed.get('totalBudget'), coerce_positive_int(fallback_budget, 7000000)),
        'startMonth': start_month,
        'endMonth': end_month,
        'items': items[:10],
        'reviewCards': normalize_summary_cards(parsed.get('reviewCards')),
        'riskNotes': normalize_string_list(parsed.get('riskNotes'))[:4],
        'nextActions': normalize_string_list(parsed.get('nextActions'))[:5],
        'aiMode': 'gms',
        'confidence': clamp_confidence(parsed.get('confidence'), 0.75),
        'reviewFields': normalize_string_list(parsed.get('reviewFields') or parsed.get('review_fields')),
    }


def normalize_spending_analysis(parsed):
    saving_opportunities = normalize_saving_opportunities(parsed.get('savingOpportunities'))
    category_insights = normalize_category_insights(parsed.get('categoryInsights'))
    card_insights = normalize_card_insights(parsed.get('cardInsights'))
    next_actions = normalize_string_list(parsed.get('nextActions'))[:5]

    return {
        'schemaVersion': str(parsed.get('schemaVersion') or 'spending-analysis-v2'),
        'summaryTitle': truncate(parsed.get('summaryTitle') or '이번 달 소비 진단', 80),
        'headline': truncate(parsed.get('headline') or '최근 소비 패턴을 기준으로 점검 포인트를 찾았어요.', 180),
        'narrative': truncate(parsed.get('narrative') or '', 420),
        'primaryInsight': normalize_primary_insight(parsed.get('primaryInsight')),
        'summaryCards': normalize_summary_cards(parsed.get('summaryCards')),
        'savingOpportunities': saving_opportunities,
        'categoryInsights': category_insights,
        'cardInsights': card_insights,
        'warnings': normalize_string_list(parsed.get('warnings'))[:5],
        'nextActions': next_actions,
        'actionButtons': normalize_action_buttons(parsed.get('actionButtons')),
        'aiMode': 'gms',
        'confidence': clamp_confidence(parsed.get('confidence'), 0.75),
    }


def normalize_chat_response(parsed):
    reply = str(parsed.get('reply') or parsed.get('answer') or '').strip()
    if not reply:
        return None

    quick_replies = normalize_string_list(parsed.get('quickReplies') or parsed.get('quick_replies'))[:4]
    if not quick_replies:
        quick_replies = ['이번 달 소비 분석해줘', '카드 추천해줘', '결제내역 추가할래']

    return {
        'schemaVersion': str(parsed.get('schemaVersion') or 'chat-response-v2'),
        'messageType': normalize_choice(parsed.get('messageType'), ALLOWED_MESSAGE_TYPES, 'general'),
        'reply': truncate(reply, 1200),
        'summaryChips': normalize_summary_chips(parsed.get('summaryChips')),
        'quickReplies': quick_replies,
        'actionButtons': normalize_action_buttons(parsed.get('actionButtons')),
        'relatedRoute': normalize_route(parsed.get('relatedRoute') or parsed.get('related_route')),
        'aiMode': 'gms',
        'confidence': clamp_confidence(parsed.get('confidence'), 0.75),
    }


def coerce_amount(value):
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        compact = re.sub(r'[^0-9-]', '', value)
        if compact and compact != '-':
            return int(compact)
    return 0


def coerce_positive_int(value, fallback):
    amount = coerce_amount(value)
    if amount:
        return abs(amount)
    return abs(int(fallback or 0))


def coerce_bool(value, fallback=False):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {'true', 'yes', '1', 'y'}:
            return True
        if lowered in {'false', 'no', '0', 'n'}:
            return False
    return fallback


def clamp_confidence(value, fallback=0.75):
    try:
        return max(0, min(1, float(value)))
    except (TypeError, ValueError):
        return fallback


def normalize_choice(value, allowed, fallback):
    normalized = str(value or '').strip()
    return normalized if normalized in allowed else fallback


def normalize_route(value):
    route = str(value or '').strip()
    return route if route in ALLOWED_AI_ROUTES else ''


def normalize_tone(value, fallback='gray'):
    return normalize_choice(value, ALLOWED_TONES, fallback)


def normalize_severity(value, fallback='info'):
    return normalize_choice(value, ALLOWED_SEVERITIES, fallback)


def normalize_month(value, fallback):
    if isinstance(value, str):
        match = re.search(r'(\d{4})[-./\s년]*(\d{1,2})', value)
        if match:
            return f'{int(match.group(1)):04d}-{int(match.group(2)):02d}'
    return fallback


def normalize_string_list(value):
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def normalize_object_list(value, fields):
    if not isinstance(value, list):
        return []
    normalized = []
    for item in value:
        if not isinstance(item, dict):
            continue
        row = {}
        for field, default in fields.items():
            raw_value = item.get(field, default)
            if isinstance(default, int):
                row[field] = coerce_positive_int(raw_value, default)
            else:
                row[field] = str(raw_value or default).strip()
        normalized.append(row)
    return normalized[:8]


def normalize_summary_cards(value):
    if not isinstance(value, list):
        return []
    cards = []
    for item in value:
        if not isinstance(item, dict):
            continue
        label = truncate(item.get('label') or '', 24)
        card_value = truncate(item.get('value') or '', 32)
        if not label or not card_value:
            continue
        cards.append(
            {
                'label': label,
                'value': card_value,
                'caption': truncate(item.get('caption') or '', 48),
                'tone': normalize_tone(item.get('tone'), 'gray'),
            }
        )
    return cards[:4]


def normalize_summary_chips(value):
    if not isinstance(value, list):
        return []
    chips = []
    for item in value:
        if not isinstance(item, dict):
            continue
        label = truncate(item.get('label') or '', 24)
        chip_value = truncate(item.get('value') or '', 36)
        if not label or not chip_value:
            continue
        chips.append({'label': label, 'value': chip_value, 'tone': normalize_tone(item.get('tone'), 'gray')})
    return chips[:3]


def normalize_primary_insight(value):
    if not isinstance(value, dict):
        value = {}
    return {
        'label': truncate(value.get('label') or '핵심 진단', 24),
        'title': truncate(value.get('title') or '소비 점검', 80),
        'body': truncate(value.get('body') or '최근 거래를 기준으로 확인할 점이 있습니다.', 220),
        'severity': normalize_severity(value.get('severity'), 'info'),
        'metricLabel': truncate(value.get('metricLabel') or '', 32),
        'metricValue': coerce_positive_int(value.get('metricValue'), 0),
    }


def normalize_saving_opportunities(value):
    if not isinstance(value, list):
        return []
    opportunities = []
    for item in value:
        if not isinstance(item, dict):
            continue
        opportunities.append(
            {
                'title': truncate(item.get('title') or '소비 점검', 80),
                'amount': coerce_positive_int(item.get('amount'), 0),
                'reason': truncate(item.get('reason') or '', 220),
                'action': truncate(item.get('action') or '', 160),
                'severity': normalize_severity(item.get('severity'), 'info'),
                'route': normalize_route(item.get('route')),
            }
        )
    return opportunities[:6]


def normalize_category_insights(value):
    if not isinstance(value, list):
        return []
    insights = []
    for item in value:
        if not isinstance(item, dict):
            continue
        insights.append(
            {
                'category': truncate(item.get('category') or '기타', 30),
                'amount': coerce_positive_int(item.get('amount'), 0),
                'shareLabel': truncate(item.get('shareLabel') or '', 32),
                'insight': truncate(item.get('insight') or '', 220),
            }
        )
    return insights[:8]


def normalize_card_insights(value):
    if not isinstance(value, list):
        return []
    insights = []
    for item in value:
        if not isinstance(item, dict):
            continue
        insights.append(
            {
                'cardId': str(item.get('cardId') or item.get('card_id') or '').strip(),
                'cardName': truncate(item.get('cardName') or item.get('card_name') or '', 60),
                'amount': coerce_positive_int(item.get('amount'), 0),
                'fit': truncate(item.get('fit') or '', 24),
                'insight': truncate(item.get('insight') or '', 220),
                'action': truncate(item.get('action') or '', 120),
            }
        )
    return insights[:6]


def normalize_action_buttons(value):
    if not isinstance(value, list):
        return []
    buttons = []
    for item in value:
        if not isinstance(item, dict):
            continue
        route = normalize_route(item.get('route'))
        label = truncate(item.get('label') or '', 32)
        if not label or not route:
            continue
        buttons.append({'label': label, 'route': route, 'intent': truncate(item.get('intent') or '', 32)})
    return buttons[:4]


def normalize_corrections(value):
    if not isinstance(value, list):
        return []
    corrections = []
    for item in value:
        if not isinstance(item, dict):
            continue
        field = truncate(item.get('field') or '', 32)
        label = truncate(item.get('label') or field, 32)
        if not field and not label:
            continue
        corrections.append(
            {
                'field': field,
                'label': label,
                'before': truncate(item.get('before') or '', 80),
                'after': truncate(item.get('after') or '', 80),
                'reason': truncate(item.get('reason') or '', 140),
            }
        )
    return corrections[:5]


def truncate(value, limit):
    text = str(value or '').strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + '…'


def normalize_approved_at(value):
    now = timezone.localtime().replace(second=0, microsecond=0)
    if not value:
        return now.isoformat()
    if not isinstance(value, str):
        return now.isoformat()

    normalized = value.strip().replace('Z', '+00:00')
    if len(normalized) == 10:
        normalized = f'{normalized}T{now.hour:02d}:{now.minute:02d}:00+09:00'
    elif 'T' not in normalized and ' ' in normalized:
        normalized = normalized.replace(' ', 'T', 1)
    if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$', normalized):
        normalized = f'{normalized}:00+09:00'
    elif re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$', normalized):
        normalized = f'{normalized}+09:00'

    try:
        approved_at = datetime.fromisoformat(normalized)
    except ValueError:
        return now.isoformat()
    if approved_at.tzinfo is None:
        approved_at = timezone.make_aware(approved_at, timezone.get_current_timezone())
    return timezone.localtime(approved_at).replace(second=0, microsecond=0).isoformat()
