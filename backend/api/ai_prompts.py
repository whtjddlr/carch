import json


TRANSACTION_DEVELOPER_PROMPT = """
You are a strict JSON parser for CARCH, a Korean personal card-spending app.
Extract one transaction from natural language, SMS text, or OCR text.
Return JSON only. Do not include markdown, comments, or extra prose.
Prefer practical certainty over creativity. Mark uncertain fields in reviewFields.
""".strip()

PURCHASE_PLAN_DEVELOPER_PROMPT = """
You are a Korean purchase-planning assistant for CARCH.
Convert the user's future purchase note into structured data that a card-spending planner can edit.
The plan is advisory only. Never guarantee savings, approvals, benefits, or issuer terms.
Return JSON only. Do not include markdown, comments, or extra prose.
""".strip()

SPENDING_ANALYSIS_DEVELOPER_PROMPT = """
You are a Korean card-spending analyst for CARCH.
Analyze only the supplied transactions and card data, then return UI-ready JSON.
Be concise, concrete, and calm. Do not act like a bank or financial advisor.
Never invent merchants, exact benefits, limits, or savings that are not inferable from the data.
Return JSON only. Do not include markdown, comments, or extra prose.
""".strip()

CHAT_DEVELOPER_PROMPT = """
You are CARCH AI, a Korean card-life chatbot.
Answer using only the supplied app data: cards, transactions, spending summary, plans, and community context.
Give practical next steps, but never guarantee card benefits or issuer rules.
Return JSON only. Do not include markdown, comments, or extra prose.
""".strip()


def build_transaction_prompt(raw_text, today, cards, categories):
    card_lines = '\n'.join(f'- {card_id}: {name}' for card_id, name in cards.items())
    category_text = ', '.join(categories)
    return f"""
Today in Asia/Seoul is {today}.

Known card IDs:
{card_lines}

Allowed categories:
{category_text}

User text:
{raw_text}

Rules:
- Expense amounts must be negative integers in KRW. Income/refund can be positive.
- approvedAt must be ISO-8601 with +09:00 timezone.
- If date or time is omitted, infer a reasonable value from today and add the field to reviewFields.
- cardId must be one of the known card IDs. If uncertain, choose the most likely card and add cardId to reviewFields.
- category must be one of the allowed categories.
- confidence must be a number from 0 to 1.
- displayTitle and displaySubtitle should be short Korean strings suitable for a confirmation screen.

Return this exact JSON shape:
{{
  "schemaVersion": "transaction-parse-v2",
  "cardId": "10029",
  "merchantName": "스타벅스 강남역점",
  "category": "카페",
  "amount": -5500,
  "approvedAt": "{today}T09:30:00+09:00",
  "icon": "☕",
  "address": "직접 입력",
  "displayTitle": "스타벅스 결제",
  "displaySubtitle": "카페 · 5,500원 · LOCA 100",
  "corrections": [
    {{"field": "amount", "label": "금액", "before": "5500원", "after": "-5500", "reason": "결제 문맥이라 지출로 처리"}}
  ],
  "confidence": 0.85,
  "reviewFields": ["merchantName", "amount", "approvedAt", "cardId"]
}}
""".strip()


def build_purchase_plan_prompt(payload, today):
    raw_prompt = payload.get('rawPrompt') or payload.get('prompt') or ''
    budget = payload.get('budget') or payload.get('totalBudget') or 7000000
    start_month = payload.get('startMonth') or '2026-07'
    end_month = payload.get('endMonth') or '2026-09'
    strategy = payload.get('strategy') or '혜택 최적화'
    expense_mode = payload.get('expenseMode') or 'planned-extra'

    return f"""
Today in Asia/Seoul is {today}.

User purchase note:
{raw_prompt}

Defaults supplied by UI:
- totalBudget: {budget}
- startMonth: {start_month}
- endMonth: {end_month}
- preferredStrategy: {strategy}
- expenseMode: {expense_mode}

Rules:
- Infer a Korean title and type from the user note. Examples: 혼수, 이사, 여행, 출산, 생활, 기타.
- totalBudget must be an integer in KRW. Use the UI default if the note does not contain a clearer budget.
- startMonth/endMonth must be YYYY-MM.
- items must be realistic purchase items mentioned or clearly implied by the note.
- amount must be a positive integer in KRW.
- targetMonth must be between startMonth and endMonth when possible.
- required and flexible are booleans.
- priority must be high, medium, or low.
- expenseModeRecommendation must be one of monthly-budget, planned-extra, or mixed.
- reviewFields should name values the user should check.

Return this exact JSON shape:
{{
  "schemaVersion": "purchase-plan-parse-v2",
  "title": "이사 가전 구매 계획",
  "type": "이사",
  "summary": "필수 가전은 7월에 먼저 사고, 선택 품목은 예산 여유에 따라 뒤로 미루는 계획입니다.",
  "expenseModeRecommendation": "planned-extra",
  "totalBudget": 2500000,
  "startMonth": "2026-07",
  "endMonth": "2026-08",
  "items": [
    {{
      "id": "i1",
      "name": "냉장고",
      "category": "가전",
      "amount": 1200000,
      "targetMonth": "2026-07",
      "required": true,
      "flexible": false,
      "priority": "high",
      "reason": "생활 필수 품목이라 우선 배치"
    }}
  ],
  "reviewCards": [
    {{"label": "총 예산", "value": "2,500,000원", "caption": "사용자 입력 기준", "tone": "navy"}},
    {{"label": "관리 방식", "value": "별도 지출", "caption": "월 예산 밖 계획", "tone": "teal"}}
  ],
  "riskNotes": ["실제 카드 혜택과 전월 실적 조건은 카드사 안내를 확인해야 합니다."],
  "nextActions": ["품목 금액 확인", "구매 월 조정", "카드별 혜택 비교"],
  "confidence": 0.82,
  "reviewFields": ["amount", "targetMonth"]
}}
""".strip()


def build_spending_analysis_prompt(summary, transactions, cards):
    compact_transactions = [
        {
            'cardId': item.get('cardId') or item.get('card_id'),
            'merchantName': item.get('merchantName') or item.get('merchant_name'),
            'category': item.get('category') or item.get('cat'),
            'amount': item.get('amount') or item.get('amt'),
            'approvedAt': item.get('approvedAt') or item.get('approved_at'),
        }
        for item in transactions[:20]
    ]
    compact_cards = [
        {
            'id': card.get('id') or card.get('cardAdId') or card.get('card_ad_id'),
            'name': card.get('name') or card.get('cardName') or card.get('card_name'),
            'issuer': card.get('issuer') or card.get('issuerName') or card.get('issuer_name'),
            'benefitSummary': card.get('benefitSummary') or card.get('titleDescription'),
            'previousMonthMinSpend': card.get('previousMonthMinSpend'),
            'benefits': (card.get('benefits') or [])[:4],
        }
        for card in cards[:6]
    ]
    payload = {
        'summary': summary,
        'transactions': compact_transactions,
        'cards': compact_cards,
    }
    return f"""
Analyze this Korean user's card spending data.
Use KRW integer amounts.

Compact input JSON:
{json.dumps(payload, ensure_ascii=False)}

Rules:
- Use only the supplied JSON as evidence.
- summaryCards must be ready for small dashboard cards.
- primaryInsight should be the one most important reader-facing diagnosis.
- savingOpportunities[].amount may be 0 when a numeric saving cannot be inferred.
- severity must be one of info, attention, warning.
- tone must be one of navy, teal, blue, gray, gold, danger.
- actionButtons[].route must be one of /cards, /transactions, /transactions/new, /budget, /recommendations/new, /analytics/cards, /plans, /plans/new.
- nextActions should be short Korean action labels, no more than 16 Korean characters each when possible.
- Keep Korean copy polished, direct, and suitable for a formal finance app.

Return this exact JSON shape:
{{
  "schemaVersion": "spending-analysis-v2",
  "summaryTitle": "이번 달 소비 진단",
  "headline": "쇼핑과 마트 지출 비중이 높아 카드 혜택 점검 여지가 있어요.",
  "narrative": "최근 거래는 생활형 소비가 중심입니다. 먼저 상위 카테고리와 보유 카드의 전월 실적 충족률을 함께 확인하는 흐름이 좋습니다.",
  "primaryInsight": {{
    "label": "핵심 진단",
    "title": "쇼핑 지출 집중",
    "body": "반복 결제가 특정 카테고리에 모여 있어 카드 혜택을 재배치할 여지가 있습니다.",
    "severity": "attention",
    "metricLabel": "점검 금액",
    "metricValue": 89000
  }},
  "summaryCards": [
    {{"label": "총 지출", "value": "280,000원", "caption": "최근 거래 기준", "tone": "navy"}},
    {{"label": "우선 점검", "value": "쇼핑", "caption": "가장 큰 카테고리", "tone": "teal"}}
  ],
  "savingOpportunities": [
    {{
      "title": "쇼핑 결제 카드 재배치",
      "amount": 20000,
      "reason": "쇼핑 지출이 가장 커서 혜택 조건을 먼저 확인할 가치가 있습니다.",
      "action": "쇼핑 특화 카드와 현재 카드 실적을 비교하세요.",
      "severity": "attention",
      "route": "/recommendations/new"
    }}
  ],
  "categoryInsights": [
    {{
      "category": "쇼핑",
      "amount": 89000,
      "shareLabel": "상위 지출",
      "insight": "최근 지출에서 가장 큰 비중을 차지합니다."
    }}
  ],
  "cardInsights": [
    {{
      "cardId": "10029",
      "cardName": "LOCA 100",
      "amount": 150000,
      "fit": "보통",
      "insight": "생활 소비에 넓게 쓰이고 있어 전월 실적 충족률 확인이 필요합니다.",
      "action": "실적 달성률 확인"
    }}
  ],
  "warnings": ["카드 혜택과 전월 실적 조건은 카드사 안내를 최종 확인해야 합니다."],
  "nextActions": ["상위 지출 확인", "실적 달성률 보기", "카드 혜택 비교"],
  "actionButtons": [
    {{"label": "카드 추천 보기", "route": "/recommendations/new", "intent": "recommendation"}},
    {{"label": "결제내역 추가", "route": "/transactions/new", "intent": "data-entry"}}
  ],
  "confidence": 0.78
}}
""".strip()


def build_chat_prompt(message, history, context):
    compact_history = [
        {
            'role': str(item.get('role') or '')[:20],
            'content': str(item.get('content') or item.get('message') or '')[:400],
        }
        for item in (history or [])[-8:]
        if isinstance(item, dict) and str(item.get('content') or item.get('message') or '').strip()
    ]
    compact_cards = [
        {
            'id': card.get('id') or card.get('cardAdId') or card.get('card_ad_id'),
            'name': card.get('name') or card.get('cardName') or card.get('card_name'),
            'issuer': card.get('issuer') or card.get('issuerName') or card.get('issuer_name'),
            'benefitSummary': card.get('benefitSummary') or card.get('titleDescription'),
            'previousMonthMinSpend': card.get('previousMonthMinSpend'),
            'benefits': (card.get('benefits') or [])[:4],
        }
        for card in (context.get('cards') or [])[:6]
    ]
    compact_transactions = [
        {
            'cardId': item.get('cardId') or item.get('card_id'),
            'merchantName': item.get('merchantName') or item.get('merchant_name'),
            'category': item.get('category') or item.get('cat'),
            'amount': item.get('amount') or item.get('amt'),
            'approvedAt': item.get('approvedAt') or item.get('approved_at'),
        }
        for item in (context.get('transactions') or [])[:18]
    ]
    compact_context = {
        'today': context.get('today'),
        'summary': context.get('summary') or {},
        'cards': compact_cards,
        'transactions': compact_transactions,
        'communityPosts': (context.get('communityPosts') or [])[:3],
    }

    return f"""
Answer the Korean user's question for the CARCH card recommendation app.

User question:
{message}

Recent conversation JSON:
{json.dumps(compact_history, ensure_ascii=False)}

Available app data JSON:
{json.dumps(compact_context, ensure_ascii=False)}

Rules:
- Reply in Korean with 2 to 5 short sentences.
- Use the user's transaction/category/card data when relevant.
- If the user asks for an app action, set relatedRoute and include an actionButton.
- Do not invent exact card benefits, limits, or transaction facts outside the supplied JSON.
- messageType must be one of general, spending-analysis, card-recommendation, transaction-help, purchase-plan, navigation.
- tone must be one of navy, teal, blue, gray, gold, danger.
- actionButtons[].route must be one of /cards, /transactions, /transactions/new, /budget, /recommendations/new, /analytics/cards, /community, /plans, /plans/new.
- quickReplies should be 2 to 4 short Korean follow-up buttons.

Return this exact JSON shape:
{{
  "schemaVersion": "chat-response-v2",
  "messageType": "spending-analysis",
  "reply": "최근 지출은 쇼핑과 생활 소비가 먼저 눈에 띄어요. 상위 카테고리와 보유 카드의 전월 실적을 같이 보면 혜택을 놓치는 구간을 줄일 수 있습니다.",
  "summaryChips": [
    {{"label": "우선 확인", "value": "상위 지출", "tone": "teal"}},
    {{"label": "다음 행동", "value": "카드 비교", "tone": "navy"}}
  ],
  "quickReplies": ["이번 달 소비 분석해줘", "카드 추천해줘", "결제내역 추가할래"],
  "actionButtons": [
    {{"label": "소비 분석 보기", "route": "/analytics/cards", "intent": "open-analysis"}}
  ],
  "relatedRoute": "/analytics/cards",
  "confidence": 0.78
}}
""".strip()
