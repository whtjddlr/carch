function numberValue(value) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
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

export function scoreCardBenefit({ card = {}, amount = 0, rate = 0 } = {}) {
  const performance = cardPerformance(card, amount)
  const grossBenefit = Math.round(Math.abs(numberValue(amount)) * Math.max(numberValue(rate), 0))
  const activeBenefit = performance.currentBenefitEligible ? grossBenefit : 0

  return {
    ...performance,
    grossBenefit,
    activeBenefit,
  }
}
