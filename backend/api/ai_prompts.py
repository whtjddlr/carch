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

CARD_RECOMMENDATION_DEVELOPER_PROMPT = """
You are CARCH's card recommendation strategist.
You decide the user's card strategy from verified calculation context.
Use the supplied JSON only. Never invent card benefits, card names, issuer terms, rates, caps, or savings.
The rule engine already calculated benefit amounts, performance gaps, eligibility, and payment exclusions.
Your job is to resolve trade-offs and explain the best strategy in polished Korean.
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
- paymentType must be "lump_sum" or "installment". Use installment only when the text clearly says 할부, 무이자, or a month count.
- installmentMonths must be 0 for lump_sum, otherwise the installment month count if known.
- isInterestFreeInstallment must be true only when 무이자/interest-free installment is stated.
- confidence must be a number from 0 to 1.
- displayTitle and displaySubtitle should be short Korean strings suitable for a confirmation screen.

Return this exact JSON shape:
{{
  "schemaVersion": "transaction-parse-v2",
  "cardId": "10106",
  "merchantName": "컴포즈커피 역삼센터필드점",
  "category": "카페",
  "amount": -3800,
  "approvedAt": "{today}T09:30:00+09:00",
  "paymentType": "lump_sum",
  "installmentMonths": 0,
  "isInterestFreeInstallment": false,
  "icon": "☕",
  "address": "직접 입력",
  "displayTitle": "컴포즈커피 결제",
  "displaySubtitle": "카페 · 3,800원 · LOCA LIKIT Eat",
  "corrections": [
    {{"field": "amount", "label": "금액", "before": "3800원", "after": "-3800", "reason": "결제 문맥이라 지출로 처리"}}
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
    strategy = payload.get('strategy') or '혜택 개선'
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
- Infer a Korean title and type from the user note. Examples: 큰 지출, 취업 준비, 여행, 기념일, 운동, 전자기기, 이사, 결혼 준비, 생활, 기타.
- totalBudget must be an integer in KRW. Use the UI default if the note does not contain a clearer budget.
- startMonth/endMonth must be YYYY-MM.
- items must be realistic purchase items mentioned or clearly implied by the note.
- amount must be a positive integer in KRW.
- targetMonth must be between startMonth and endMonth when possible.
- paymentType must be "lump_sum" or "installment" for each item.
- installmentMonths must be 0 for lump_sum, otherwise the installment month count if the user says 할부/무이자/month count.
- isInterestFreeInstallment must be true only when 무이자/interest-free installment is stated for that item.
- required and flexible are booleans.
- priority must be high, medium, or low.
- expenseModeRecommendation must be one of monthly-budget, planned-extra, or mixed.
- reviewFields should name values the user should check.

Return this exact JSON shape:
{{
  "schemaVersion": "purchase-plan-parse-v2",
  "title": "취업 준비 지출 계획",
  "type": "취업 준비",
  "summary": "필수 면접 준비물은 7월에 먼저 결제하고, 응시료와 교통비는 8월 일정에 맞춰 분리하는 계획입니다.",
  "expenseModeRecommendation": "planned-extra",
  "totalBudget": 800000,
  "startMonth": "2026-07",
  "endMonth": "2026-08",
  "items": [
    {{
      "id": "i1",
      "name": "정장 셔츠·슬랙스",
      "category": "쇼핑",
      "amount": 210000,
      "targetMonth": "2026-07",
      "paymentType": "lump_sum",
      "installmentMonths": 0,
      "isInterestFreeInstallment": false,
      "required": true,
      "flexible": false,
      "priority": "high",
      "reason": "면접 일정 전 준비가 필요한 필수 품목"
    }}
  ],
  "reviewCards": [
    {{"label": "총 예산", "value": "800,000원", "caption": "사용자 입력 기준", "tone": "navy"}},
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
            'paymentType': item.get('paymentType') or item.get('payment_type'),
            'installmentMonths': item.get('installmentMonths') or item.get('installment_months'),
            'isInterestFreeInstallment': item.get('isInterestFreeInstallment') or item.get('is_interest_free_installment'),
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
- actionButtons[].route must be one of /cards, /transactions, /transactions/new, /budget, /recommendations/new, /analytics, /plans, /plans/new.
- nextActions should be short Korean action labels, no more than 16 Korean characters each when possible.
- Keep Korean copy polished, direct, and suitable for a formal finance app.
- Use a refined financial-service tone. Avoid casual endings and prefer precise formal phrasing such as "권장합니다", "필요합니다", "예상됩니다", "유리합니다".
- Do not mention categories, cards, merchants, or benefits that are not present in the supplied JSON.
- Do not expose implementation words such as mock, fallback, DB, cache, candidate, or confidence in reader-facing Korean copy.
- Treat one-time spending separately: say it is reflected lightly in recommendations; do not describe it as recurring spending.
- Keep UI copy concise: one sentence per field when possible.

Return this exact JSON shape:
{{
  "schemaVersion": "spending-analysis-v2",
  "summaryTitle": "이번 달 소비 인사이트",
  "headline": "상위 지출 변화에 맞춰 카드 혜택 조건 확인이 필요합니다.",
  "narrative": "최근 6개월 흐름과 이번 달 소비를 함께 반영했습니다. 반복 지출 중심으로 보유 카드의 전월 실적 충족 여부를 확인하는 것이 유리합니다.",
  "primaryInsight": {{
    "label": "핵심 포인트",
    "title": "상위 지출 변화",
    "body": "반복 지출 기준으로 카드 사용 조정이 필요합니다.",
    "severity": "attention",
    "metricLabel": "대상 금액",
    "metricValue": 89000
  }},
  "summaryCards": [
    {{"label": "총 지출", "value": "280,000원", "caption": "최근 거래 기준", "tone": "navy"}},
    {{"label": "우선 확인", "value": "쇼핑", "caption": "가장 큰 카테고리", "tone": "teal"}}
  ],
  "savingOpportunities": [
    {{
      "title": "상위 지출 카드 조정",
      "amount": 20000,
      "reason": "상위 지출과 카드 혜택 조건이 맞물리는 구간입니다.",
      "action": "현재 카드 실적과 비교 카드 혜택 조건을 함께 확인하시기 바랍니다.",
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
      "cardId": "10106",
      "cardName": "LOCA LIKIT Eat",
      "amount": 150000,
      "fit": "보통",
      "insight": "카페와 식비 지출에 넓게 쓰이고 있어 다음 달 혜택 조건 확인이 필요합니다.",
      "action": "조건 확인"
    }}
  ],
  "warnings": ["카드 혜택과 전월 실적 조건은 카드사 안내를 최종 확인해야 합니다."],
  "nextActions": ["상위 지출 확인", "혜택 조건 확인", "카드 혜택 비교"],
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
- Use concise, refined Korean. Avoid casual endings such as "해줘", "좋아요", "예상돼요" in assistant copy.
- Do not expose implementation words such as mock, fallback, DB, cache, candidate, or confidence.
- messageType must be one of general, spending-analysis, card-recommendation, transaction-help, purchase-plan, navigation.
- tone must be one of navy, teal, blue, gray, gold, danger.
- actionButtons[].route must be one of /cards, /transactions, /transactions/new, /budget, /recommendations/new, /recommendations/usage, /analytics, /community, /plans, /plans/new.
- Use /recommendations/usage when the user asks which owned card to use, how to split payments, performance preparation, or current spending strategy.
- Use /recommendations/new only when the user asks for a new card to issue or compare with cards they do not own.
- quickReplies should be 2 to 4 short Korean follow-up buttons.

Return this exact JSON shape:
{{
  "schemaVersion": "chat-response-v2",
  "messageType": "spending-analysis",
  "reply": "최근 지출은 상위 카테고리 중심으로 확인이 필요합니다. 보유 카드의 전월 실적과 혜택 조건을 함께 비교하면 누락되는 혜택을 줄일 수 있습니다.",
  "summaryChips": [
    {{"label": "우선 확인", "value": "상위 지출", "tone": "teal"}},
    {{"label": "다음으로", "value": "카드 비교", "tone": "navy"}}
  ],
  "quickReplies": ["소비 분석 보기", "카드 추천 보기", "결제내역 추가"],
  "actionButtons": [
    {{"label": "소비 분석 보기", "route": "/analytics", "intent": "open-analysis"}}
  ],
  "relatedRoute": "/analytics",
  "confidence": 0.78
}}
""".strip()


def build_card_recommendation_prompt(context):
    return f"""
Recommend a card strategy for this Korean CARCH user.

Recommendation context JSON:
{json.dumps(context, ensure_ascii=False)}

Decision rules:
- Use only card IDs in allowedCardIds.
- Do not create new cards, rates, limits, merchants, or benefit amounts.
- Keep benefit amounts at or below the supplied maxExpectedBenefit or monthlyGain for that card.
- Separate owned-card usage strategy from new-card issuance strategy.
- Prefer owned-card usage when it solves the user's situation without a meaningful new-card gain.
- If a card is not currently eligible but can unlock meaningful next-month benefits, explain it as performance preparation, not current benefit.
- If a benefit is excluded because of installment, interest-free installment, or simple payment conditions, include a warning.
- If dataReadiness is conditional or low-confidence, use conservative wording.
- Do not encourage extra spending. Only distribute spending the user already made or planned.
- Make the decision visibly different from a static score list by naming the trade-off: current benefit, next-month preparation, no-performance fallback, cap/exclusion risk, or new-card issuance.

Return this exact JSON shape:
{{
  "schemaVersion": "card-recommendation-decision-v1",
  "strategyType": "owned_usage",
  "title": "이번 달은 보유 카드 안에서 먼저 조정하세요",
  "summary": "현재 받을 수 있는 혜택과 다음 달 실적 준비를 함께 보면, 새 카드 발급보다 보유 카드 배분을 먼저 조정하는 편이 유리합니다.",
  "primaryAction": "식비는 혜택 가능 카드로 유지하고, 남은 일반 결제는 다음 달 조건을 열 카드에 배정하세요.",
  "decisionCards": [
    {{
      "cardId": "10106",
      "role": "use_now",
      "title": "식비 결제 우선",
      "reason": "전월 실적이 충족되어 이번 달 혜택이 바로 적용될 수 있습니다.",
      "category": "식비",
      "expectedBenefit": 2250,
      "remainingCondition": 0
    }}
  ],
  "tradeoffs": [
    {{
      "title": "당장 혜택과 다음 달 준비",
      "body": "지금 혜택이 가능한 카드와 다음 달 조건을 열 카드가 달라서 결제 목적별로 나누는 전략이 적합합니다."
    }}
  ],
  "reasonCodes": ["CURRENT_BENEFIT_AVAILABLE", "NEXT_MONTH_PERFORMANCE"],
  "warnings": ["무이자 할부는 일부 카드 혜택에서 제외될 수 있어 결제 전 조건 확인이 필요합니다."],
  "confidence": 0.82
}}
""".strip()
