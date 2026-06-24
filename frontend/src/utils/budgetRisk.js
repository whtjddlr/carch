const BUDGET_RISK_COLORS = {
  safe: '#16a34a',
  caution: '#f59e0b',
  warning: '#f97316',
  danger: '#e5484d',
}

// 진행률에 따른 상태 라벨 (안정 → 임박)
export function budgetRiskLabel(percent) {
  const value = Number(percent || 0)
  if (value >= 95) return '예산 임박'
  if (value >= 80) return '주의'
  if (value >= 60) return '적정'
  return '안정'
}

export function budgetUsagePercent(spent, budget) {
  const normalizedBudget = Number(budget || 0)
  if (normalizedBudget <= 0) return 0
  return Math.max(0, Math.round((Number(spent || 0) / normalizedBudget) * 100))
}

export function budgetProgressWidth(percent) {
  return Math.min(Math.max(Number(percent || 0), 0), 100)
}

export function budgetRiskColor(percent) {
  const value = Number(percent || 0)
  if (value >= 95) return BUDGET_RISK_COLORS.danger
  if (value >= 80) return BUDGET_RISK_COLORS.warning
  if (value >= 60) return BUDGET_RISK_COLORS.caution
  return BUDGET_RISK_COLORS.safe
}
