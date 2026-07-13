import assert from 'node:assert/strict'
import test from 'node:test'

import {
  demoMonthlySeries,
  demoMonthSummary,
  emptyDemoMonthSummary,
} from '../src/data/monthlyAnalytics.js'

test('historical demo summary keeps the requested month and has spending data', () => {
  const summary = demoMonthSummary('2026-05')

  assert.equal(summary.period.currentMonth, '2026-05')
  assert.equal(summary.spendingTrend.currentMonth, '2026-05')
  assert.equal(summary.totalExpense, 702900)
  assert.ok(summary.byCategory.length > 0)
})

test('unsupported demo month returns an empty summary for that same month', () => {
  const summary = emptyDemoMonthSummary('2025-09')

  assert.equal(summary.period.currentMonth, '2025-09')
  assert.equal(summary.totalExpense, 0)
  assert.deepEqual(summary.byCategory, [])
})

test('monthly series is anchored to the requested month', () => {
  const currentSeries = demoMonthlySeries(5, '2026-06', 1051950)
  assert.deepEqual(currentSeries.map((item) => item.month), [
    '2026-02',
    '2026-03',
    '2026-04',
    '2026-05',
    '2026-06',
  ])
  assert.equal(currentSeries[3].spent, 702900)
  assert.equal(currentSeries[4].spent, 1051950)
  assert.equal(currentSeries[4].budget, 1400000)

  const maySeries = demoMonthlySeries(5, '2026-05')
  assert.deepEqual(maySeries.map((item) => item.month), [
    '2026-01',
    '2026-02',
    '2026-03',
    '2026-04',
    '2026-05',
  ])
  assert.equal(maySeries[4].spent, 702900)
})
