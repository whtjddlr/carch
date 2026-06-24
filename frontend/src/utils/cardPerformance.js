function numberValue(value) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

const PAYMENT_TYPE_INSTALLMENT = 'installment'
const PAYMENT_TYPE_LUMP_SUM = 'lump_sum'

const CATEGORY_KEYWORDS = {
  식비: ['식비', '푸드', '음식', '외식', '배달'],
  카페: ['카페', '커피', '스타벅스'],
  쇼핑: ['쇼핑', '온라인', '오프라인', '무신사', '쿠팡'],
  편의점: ['편의점', 'gs25', 'cu', '세븐일레븐'],
  교통: ['교통', '대중교통', '버스', '지하철', '택시'],
  구독: ['구독', '멤버십', '정기결제'],
  문화: ['문화', '영화', '공연'],
  뷰티: ['뷰티', '올리브영'],
}

const normalizeText = (value = '') => String(value || '').replace(/\s+/g, '').toLowerCase()

const categoryKeywords = (category = '') => {
  const raw = String(category || '').trim()
  return [raw, ...(CATEGORY_KEYWORDS[raw] || [])]
    .map(normalizeText)
    .filter(Boolean)
}

export function normalizePaymentContext(context = {}) {
  const rawType = String(context.paymentType || context.payment_type || '').toLowerCase()
  const rawMode = String(context.paymentMode || context.payment_mode || '').toLowerCase()
  const isInterestFree = Boolean(
    context.isInterestFreeInstallment
      ?? context.is_interest_free_installment
      ?? false,
  ) || rawType === 'interest_free' || rawMode === 'interest_free'
  const isInstallment = rawType === PAYMENT_TYPE_INSTALLMENT
    || rawType === 'installments'
    || rawType === 'interest_free'
    || rawMode === PAYMENT_TYPE_INSTALLMENT
    || rawMode === 'interest_free'
    || numberValue(context.installmentMonths ?? context.installment_months) > 1
    || isInterestFree
  const installmentMonths = isInstallment
    ? Math.max(2, numberValue(context.installmentMonths ?? context.installment_months) || 2)
    : 0

  return {
    paymentType: isInstallment ? PAYMENT_TYPE_INSTALLMENT : PAYMENT_TYPE_LUMP_SUM,
    installmentMonths,
    isInterestFreeInstallment: isInstallment && isInterestFree,
  }
}

export function paymentContextLabel(context = {}) {
  const payment = normalizePaymentContext(context)
  if (payment.paymentType !== PAYMENT_TYPE_INSTALLMENT) return '일시불'
  const prefix = payment.installmentMonths ? `${payment.installmentMonths}개월 ` : ''
  return payment.isInterestFreeInstallment ? `${prefix}무이자` : `${prefix}할부`
}

export function cardPerformance(card = {}, plannedAmount = 0) {
  const required = numberValue(card.previousMonthMinSpend ?? card.previous_month_min_spend)
  const noPerformanceRequired = required <= 0
  const previousSpend = numberValue(card.previousMonthSpend ?? card.previous_month_spend ?? card.spent ?? card.currentSpend ?? card.current_spend)
  const currentSpend = numberValue(card.currentMonthSpend ?? card.current_month_spend ?? card.spent ?? card.currentSpend ?? card.current_spend)
  const projected = currentSpend + Math.max(numberValue(plannedAmount), 0)
  const remainingBefore = Math.max(required - previousSpend, 0)
  const remainingAfter = Math.max(required - projected, 0)
  const currentBenefitEligible = noPerformanceRequired || remainingBefore <= 0
  const nextMonthWillQualify = noPerformanceRequired || remainingAfter <= 0
  const progress = required > 0 ? Math.min(100, Math.round((previousSpend / required) * 100)) : 100
  const projectedProgress = required > 0 ? Math.min(100, Math.round((projected / required) * 100)) : 100

  return {
    required,
    noPerformanceRequired,
    spent: currentSpend,
    previousSpend,
    currentSpend,
    projected,
    remainingBefore,
    remainingAfter,
    achieved: currentBenefitEligible,
    willAchieve: nextMonthWillQualify,
    currentBenefitEligible,
    nextMonthWillQualify,
    progress,
    projectedProgress,
    blocked: !currentBenefitEligible,
    nextMonthBlocked: !nextMonthWillQualify,
  }
}

export function summarizeWalletPerformance(cards = [], plannedAmount = 0) {
  const performances = cards.map((card) => ({
    card,
    performance: cardPerformance(card, plannedAmount),
  }))
  const hasNoPerformanceCard = performances.some((item) => item.performance.noPerformanceRequired)
  const hasCurrentBenefitCard = performances.some((item) => item.performance.currentBenefitEligible)
  const hasQualifiedPerformanceCard = performances.some((item) => (
    item.performance.currentBenefitEligible && !item.performance.noPerformanceRequired
  ))

  return {
    performances,
    hasNoPerformanceCard,
    hasCurrentBenefitCard,
    hasQualifiedPerformanceCard,
    hasOnlyNoPerformanceReady: hasNoPerformanceCard && !hasQualifiedPerformanceCard,
    needsPreparationOnly: performances.length > 0 && !hasNoPerformanceCard && !hasCurrentBenefitCard,
  }
}

export function cardStrategyPriority(performance = {}, grossBenefit = 0) {
  if (performance.currentBenefitEligible && !performance.noPerformanceRequired && grossBenefit > 0) return 5
  if (!performance.currentBenefitEligible && performance.nextMonthWillQualify && grossBenefit > 0) return 4
  if (performance.currentBenefitEligible && performance.noPerformanceRequired && grossBenefit > 0) return 3
  if (!performance.currentBenefitEligible && grossBenefit > 0) return 2
  return 1
}

export function compareCardBenefitCandidates(a = {}, b = {}) {
  const aPerformance = a.performance || a || {}
  const bPerformance = b.performance || b || {}
  const aGrossBenefit = a.grossBenefit ?? aPerformance.grossBenefit ?? 0
  const bGrossBenefit = b.grossBenefit ?? bPerformance.grossBenefit ?? 0
  const aBenefit = a.benefit ?? a.activeBenefit ?? aPerformance.activeBenefit ?? 0
  const bBenefit = b.benefit ?? b.activeBenefit ?? bPerformance.activeBenefit ?? 0
  const aPriority = cardStrategyPriority(aPerformance, aGrossBenefit)
  const bPriority = cardStrategyPriority(bPerformance, bGrossBenefit)

  return bPriority - aPriority
    || bBenefit - aBenefit
    || bGrossBenefit - aGrossBenefit
    || ((bPerformance.paymentStatus?.confidence ?? 1) - (aPerformance.paymentStatus?.confidence ?? 1))
    || (bPerformance.projectedProgress || 0) - (aPerformance.projectedProgress || 0)
    || (aPerformance.remainingAfter || 0) - (bPerformance.remainingAfter || 0)
}

function benefitItemMatchesCategory(item = {}, category = '') {
  const keywords = categoryKeywords(category)
  if (!keywords.length) return true
  const haystack = normalizeText([
    item.label,
    item.scope,
    item.type,
    ...(item.categories || []),
    ...(item.normalizedCategories || []),
    ...(item.targetMerchants || []),
  ].join(' '))
  return keywords.some((keyword) => haystack.includes(keyword))
}

function benefitItemExcludesPayment(item = {}, paymentContext = {}) {
  const payment = normalizePaymentContext(paymentContext)
  if (payment.paymentType !== PAYMENT_TYPE_INSTALLMENT) return false

  const excluded = new Set(item.excludedPaymentMethods || item.excluded_payment_methods || [])
  const rules = item.paymentMethodRules || item.payment_method_rules || {}
  if (excluded.has('installment') || rules.installmentBenefitEligible === false) return true
  return payment.isInterestFreeInstallment
    && (excluded.has('interest_free_installment') || rules.interestFreeInstallmentEligible === false)
}

export function paymentBenefitStatus(card = {}, category = '', paymentContext = {}) {
  const payment = normalizePaymentContext(paymentContext)
  if (payment.paymentType !== PAYMENT_TYPE_INSTALLMENT) {
    return {
      key: 'confirmed',
      label: '일시불 기준 혜택',
      tone: 'is-ready',
      confidence: 1,
      blocksBenefit: false,
    }
  }

  const benefitItems = Array.isArray(card.benefitItems) ? card.benefitItems : []
  const relevantItems = benefitItems.filter((item) => benefitItemMatchesCategory(item, category))
  const inspectedItems = relevantItems.length ? relevantItems : benefitItems
  const hasRuleData = inspectedItems.some((item) => (
    (item.excludedPaymentMethods || item.excluded_payment_methods || []).length
    || item.paymentMethodRules
    || item.payment_method_rules
  ))

  if (inspectedItems.length && inspectedItems.every((item) => benefitItemExcludesPayment(item, payment))) {
    return {
      key: 'excluded',
      label: `${paymentContextLabel(payment)} 혜택 제외`,
      tone: 'is-danger',
      confidence: 0,
      blocksBenefit: true,
    }
  }

  if (!hasRuleData) {
    return {
      key: 'needs_confirmation',
      label: `${paymentContextLabel(payment)} 확인 필요`,
      tone: 'is-warning',
      confidence: payment.isInterestFreeInstallment ? 0.55 : 0.7,
      blocksBenefit: false,
    }
  }

  if (inspectedItems.some((item) => benefitItemExcludesPayment(item, payment))) {
    return {
      key: 'partial',
      label: `${paymentContextLabel(payment)} 일부 확인`,
      tone: 'is-warning',
      confidence: 0.75,
      blocksBenefit: false,
    }
  }

  return {
    key: 'confirmed',
    label: `${paymentContextLabel(payment)} 혜택 반영`,
    tone: 'is-ready',
    confidence: 1,
    blocksBenefit: false,
  }
}

export function scoreCardBenefit({ card = {}, amount = 0, rate = 0, category = '', paymentContext = {} } = {}) {
  const performance = cardPerformance(card, amount)
  const paymentStatus = paymentBenefitStatus(card, category, paymentContext)
  const rawGrossBenefit = Math.round(Math.abs(numberValue(amount)) * Math.max(numberValue(rate), 0))
  const rawActiveBenefit = performance.currentBenefitEligible ? rawGrossBenefit : 0
  const grossBenefit = paymentStatus.blocksBenefit ? 0 : Math.round(rawGrossBenefit * paymentStatus.confidence)
  const activeBenefit = paymentStatus.blocksBenefit ? 0 : Math.round(rawActiveBenefit * paymentStatus.confidence)

  return {
    ...performance,
    paymentStatus,
    paymentContext: normalizePaymentContext(paymentContext),
    paymentLabel: paymentContextLabel(paymentContext),
    rawGrossBenefit,
    rawActiveBenefit,
    grossBenefit,
    activeBenefit,
  }
}
