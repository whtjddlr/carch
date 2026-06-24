const BUDGET_OVERRIDE_KEY = 'carch.budget.currentOverride.v1'
const BUDGET_CATEGORIES_KEY = 'carch.budget.categories.v1'

function getStorage() {
  if (typeof window === 'undefined') return null
  return window.localStorage
}

function readJson(key, fallback) {
  const storage = getStorage()
  if (!storage) return fallback
  try {
    return JSON.parse(storage.getItem(key) || 'null') ?? fallback
  } catch (error) {
    console.warn('Failed to read budget storage.', error)
    return fallback
  }
}

function writeJson(key, value) {
  const storage = getStorage()
  if (!storage) return
  storage.setItem(key, JSON.stringify(value))
}

export function readBudgetOverride() {
  const value = Number(readJson(BUDGET_OVERRIDE_KEY, null))
  return value > 0 ? value : null
}

export function writeBudgetOverride(value) {
  const storage = getStorage()
  if (!storage) return
  const amount = Number(value)
  if (amount > 0) {
    writeJson(BUDGET_OVERRIDE_KEY, amount)
  } else {
    storage.removeItem(BUDGET_OVERRIDE_KEY)
  }
}

export function readCustomBudgetCategories() {
  const rows = readJson(BUDGET_CATEGORIES_KEY, [])
  if (!Array.isArray(rows)) return []
  return rows
    .map((item) => ({
      id: String(item.id || ''),
      name: String(item.name || '').trim(),
      icon: item.icon || '🎯',
      budget: Number(item.budget || 0),
      spent: Number(item.spent || 0),
      color: item.color || '#0f5fae',
    }))
    .filter((item) => item.id && item.name && item.budget > 0)
}

export function appendCustomBudgetCategory(input) {
  const name = String(input.name || '').trim()
  const budget = Number(input.budget || input.amount || 0)
  if (!name || budget <= 0) return null

  const category = {
    id: `local-budget-${Date.now()}`,
    name,
    icon: input.icon || '🎯',
    budget,
    spent: 0,
    color: input.color || '#0f5fae',
  }
  writeJson(BUDGET_CATEGORIES_KEY, [...readCustomBudgetCategories(), category])
  return category
}
