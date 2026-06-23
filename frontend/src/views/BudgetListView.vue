<template>
  <section class="screen">
    <header class="budget-list-header blue-gradient">
      <div class="header-row">
        <AppBackButton fallback="/cards" />
        <div>
          <h1>소비계획</h1>
        </div>
      </div>

      <RouterLink class="current-summary" to="/budget/current" aria-label="6월 예산 상세 보기">
        <div class="summary-top">
          <span>이번 달 사용</span>
          <strong>{{ krw(currentBudget.spent) }}</strong>
        </div>
        <div class="summary-meta">
          <span>{{ currentBudget.percent }}%</span>
          <b>{{ krw(currentBudget.remaining) }} 남음</b>
        </div>
        <div class="summary-track">
          <i :style="{ width: `${currentBudget.percent}%` }" />
        </div>
      </RouterLink>
    </header>

    <div class="screen-scroll scrollbar-hide budget-list-body">
      <section class="plan-section">
        <div class="section-head split">
          <h2>지출 계획</h2>
          <RouterLink to="/plans">계획 보기</RouterLink>
        </div>
        <div class="plan-mode-grid">
          <RouterLink
            v-for="mode in expenseModes"
            :key="mode.id"
            class="plan-mode"
            :to="{ path: '/plans/new', query: { expenseMode: mode.id } }"
          >
            <span class="pm-icon"><component :is="modeIcon(mode.id)" :size="18" /></span>
            <div>
              <strong>{{ mode.label }}</strong>
              <small>{{ mode.title }}</small>
            </div>
          </RouterLink>
        </div>
      </section>

      <section class="section-block">
        <div class="section-head">
          <h2>나의 예산</h2>
        </div>

        <RouterLink
          v-for="item in budgetHistory"
          :key="item.id"
          class="app-card budget-history-card"
          :to="item.to"
        >
          <div class="history-content">
            <div class="history-title-row">
              <div>
                <strong :class="['history-headline', item.tone]">{{ item.relativeLabel }}</strong>
                <span>{{ item.month }}월 · {{ item.period }}</span>
              </div>
              <ChevronRight :size="17" />
            </div>

            <div class="history-metrics">
              <div>
                <span>사용</span>
                <b>{{ krw(item.spent) }}</b>
              </div>
              <div>
                <span>예산</span>
                <b>{{ krw(item.budget) }}</b>
              </div>
              <div class="remaining-cell">
                <b :class="item.remaining < 0 ? 'neg' : 'pos'">{{ item.remaining < 0 ? '-' : '+' }}{{ krw(item.remaining) }}</b>
              </div>
            </div>

            <div class="history-track">
              <i :class="{ danger: item.remaining < 0 }" :style="{ width: `${Math.min(item.percent, 100)}%` }" />
            </div>
          </div>
        </RouterLink>
      </section>

    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { CalendarClock, ChevronRight, PiggyBank, Zap } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { budgetCategories, expenseModes, krw } from '@/data/mockData'

function modeIcon(id) {
  if (id === 'within-budget') return PiggyBank
  if (id === 'planned-extra') return CalendarClock
  return Zap
}

const totalBudget = computed(() => budgetCategories.reduce((sum, category) => sum + category.budget, 0))
const totalSpent = computed(() => budgetCategories.reduce((sum, category) => sum + category.spent, 0))

const currentBudget = computed(() => {
  const spent = totalSpent.value
  const budget = totalBudget.value
  const remaining = budget - spent

  return {
    spent,
    budget,
    remaining,
    percent: Math.min(Math.round((spent / budget) * 100), 100),
  }
})

const budgetHistory = computed(() => {
  const current = currentBudget.value
  const nextBudget = 950000

  return [
    {
      id: '2026-06',
      relativeLabel: '이번 달',
      month: 6,
      title: '6월 예산',
      period: '2026.06.01 - 06.30',
      spent: current.spent,
      budget: current.budget,
      remaining: current.remaining,
      percent: current.percent,
      to: '/budget/current',
      tone: 'active',
    },
    {
      id: '2026-05',
      relativeLabel: '지난 달',
      month: 5,
      title: '5월 예산',
      period: '2026.05.01 - 05.31',
      spent: 620000,
      budget: 910000,
      remaining: 290000,
      percent: 68,
      to: '/budget/current',
      tone: 'done',
    },
    {
      id: '2026-07',
      relativeLabel: '다음 달',
      month: 7,
      title: '7월 예산',
      period: '2026.07.01 - 07.31',
      spent: 0,
      budget: nextBudget,
      remaining: nextBudget,
      percent: 0,
      to: '/budget/current',
      tone: 'upcoming',
      upcoming: true,
    },
  ]
})
</script>

<style scoped>
.budget-list-header {
  padding: 24px 20px 22px;
  color: #fff;
  text-align: left;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 14px;
  margin-bottom: 20px;
}

.header-row p {
  margin: 0 0 4px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  font-weight: 800;
}

h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 900;
  line-height: 1.1;
}

.current-summary {
  display: block;
  border-top: 1px solid rgba(255, 255, 255, 0.16);
  padding: 18px 0 16px;
  background: transparent;
  color: #20242a;
  text-decoration: none;
}

.summary-top,
.summary-meta {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.summary-top {
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.summary-top span,
.summary-meta b {
  color: #6e6e73;
  font-size: 12px;
  font-weight: 800;
}

.summary-top strong {
  display: block;
  font-size: 38px;
  font-weight: 900;
  line-height: 1;
}

.summary-meta {
  justify-content: center;
  margin-top: 10px;
}

.summary-meta span {
  font-size: 13px;
  font-weight: 900;
}

.summary-track {
  height: 6px;
  overflow: hidden;
  width: min(100%, 300px);
  margin: 12px auto 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.22);
}

.summary-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #ffffff, #d4e0ee);
}

.budget-list-body {
  padding: 16px 20px 112px;
}

.plan-section {
  margin-bottom: 24px;
}

.plan-mode-grid {
  display: grid;
  gap: 8px;
}

.plan-mode {
  display: flex;
  align-items: center;
  gap: 12px;
  border-radius: 14px;
  padding: 13px 14px;
  background: rgba(44, 78, 114, 0.05);
  color: inherit;
  text-decoration: none;
}

.pm-icon {
  display: inline-flex;
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: #fff;
  color: #2c4e72;
  box-shadow: 0 2px 8px rgba(36, 54, 79, 0.1);
}

.plan-mode strong {
  display: block;
  color: #20242a;
  font-size: 13px;
  font-weight: 900;
}

.plan-mode small {
  display: block;
  margin-top: 2px;
  color: #6e6e73;
  font-size: 11px;
  font-weight: 700;
}

.section-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.section-head.split {
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 11px;
}

.section-head h2 {
  margin: 0;
  color: #20242a;
  font-size: 19px;
  font-weight: 900;
}

.section-head a {
  flex-shrink: 0;
  color: #2c4e72;
  font-size: 12px;
  font-weight: 900;
  text-decoration: none;
}

.budget-history-card {
  display: block;
  padding: 15px;
  color: inherit;
  text-decoration: none;
}

.history-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.history-title-row strong {
  display: block;
  color: #20242a;
  font-size: 18px;
  font-weight: 900;
}

.history-headline.active {
  color: #2c4e72 !important;
}

.history-title-row span {
  display: block;
  margin-top: 3px;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 700;
}

.history-title-row svg {
  flex-shrink: 0;
  margin-top: 2px;
  color: #8a9aad;
}

.history-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  align-items: end;
  gap: 8px;
  margin-top: 12px;
  border-top: 1px solid rgba(32, 36, 42, 0.075);
  padding-top: 11px;
}

.remaining-cell {
  text-align: right;
}

.history-metrics span {
  display: block;
  color: #6e6e73;
  font-size: 10px;
  font-weight: 800;
}

.history-metrics b {
  display: block;
  margin-top: 3px;
  color: #20242a;
  font-size: 12px;
  font-weight: 900;
}

.history-metrics b.pos {
  color: #16a34a;
}

.history-metrics b.neg {
  color: #d92d20;
}

.history-track {
  height: 7px;
  overflow: hidden;
  margin-top: 12px;
  border-radius: 999px;
  background: rgba(36, 54, 79, 0.11);
}

.history-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #2c4e72, #1c3149);
}

.history-track i.danger {
  background: #d92d20;
}

.plan-entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-top: 16px;
  padding: 14px 15px;
  color: inherit;
  text-decoration: none;
}

.plan-entry span {
  display: block;
  color: #008c95;
  font-size: 11px;
  font-weight: 900;
}

.plan-entry strong {
  display: block;
  margin-top: 4px;
  color: #20242a;
  font-size: 13px;
  font-weight: 900;
  line-height: 1.45;
}

.plan-entry svg {
  flex-shrink: 0;
  color: #008c95;
}
</style>
