const BUDGET_RISK_COLORS = {
  safe: '#2563eb',
  caution: '#eab308',
  warning: '#f97316',
  danger: '#dc2626',
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
