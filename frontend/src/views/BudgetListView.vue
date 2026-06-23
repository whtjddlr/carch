<template>
  <section class="screen">
    <header class="budget-list-header blue-gradient">
      <div class="header-row">
        <AppBackButton fallback="/cards" />
        <div>
          <p>월별 예산 관리</p>
          <h1>예산</h1>
        </div>
        <span class="header-spacer" aria-hidden="true" />
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
      <div class="mode-guide">
        <article class="mode-card primary">
          <span>월 예산</span>
          <strong>매달 쓰는 돈</strong>
          <p>식비, 카페, 교통비를 관리해요.</p>
        </article>
        <RouterLink class="mode-card" to="/plans">
          <span>목표 지출</span>
          <strong>큰 지출 준비</strong>
          <p>여행, 가전, 이사 비용을 따로 모아요.</p>
        </RouterLink>
      </div>

      <section class="expense-mode-section">
        <div class="section-head split">
          <div>
            <h2>큰 지출은 어떻게 관리할까요?</h2>
            <p>예산에 포함할지, 따로 볼지 먼저 고르면 계획이 깔끔해져요.</p>
          </div>
          <RouterLink to="/plans">계획 보기</RouterLink>
        </div>

        <div class="expense-mode-grid">
          <RouterLink
            v-for="mode in expenseModes"
            :key="mode.id"
            class="expense-mode-card app-card"
            :to="{ path: '/plans/new', query: { expenseMode: mode.id } }"
          >
            <span>{{ mode.label }}</span>
            <strong>{{ mode.title }}</strong>
            <p>{{ mode.description }}</p>
          </RouterLink>
        </div>
      </section>

      <section class="section-block">
        <div class="section-head">
          <h2>예산 내역</h2>
        </div>

        <RouterLink
          v-for="item in budgetHistory"
          :key="item.id"
          class="app-card budget-history-card"
          :to="item.to"
        >
          <div class="history-icon" :class="item.tone">
            <component :is="item.icon" :size="18" />
          </div>
          <div class="history-content">
            <div class="history-title-row">
              <div>
                <strong>{{ item.title }}</strong>
                <span>{{ item.period }}</span>
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
              <div>
                <span>{{ item.remaining >= 0 ? '잔액' : '초과' }}</span>
                <b :class="{ danger: item.remaining < 0 }">{{ krw(item.remaining) }}</b>
              </div>
            </div>

            <div class="history-track">
              <i :class="{ danger: item.remaining < 0 }" :style="{ width: `${Math.min(item.percent, 100)}%` }" />
            </div>
          </div>
        </RouterLink>
      </section>

    </div>

    <RouterLink class="floating-action-button" to="/budget/new" aria-label="예산 추가">
      <Plus :size="20" />
    </RouterLink>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { ChevronRight, Plus, WalletCards } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { budgetCategories, expenseModes, krw } from '@/data/mockData'

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

  return [
    {
      id: '2026-06',
      title: '6월 예산',
      period: '2026.06.01 - 06.30',
      spent: current.spent,
      budget: current.budget,
      remaining: current.remaining,
      percent: current.percent,
      to: '/budget/current',
      icon: WalletCards,
      tone: 'active',
    },
    {
      id: '2026-05',
      title: '5월 예산',
      period: '2026.05.01 - 05.31',
      spent: 620000,
      budget: 910000,
      remaining: 290000,
      percent: 68,
      to: '/budget/current',
      icon: WalletCards,
      tone: 'done',
    },
    {
      id: '2026-04',
      title: '4월 예산',
      period: '2026.04.01 - 04.30',
      spent: 875000,
      budget: 880000,
      remaining: 5000,
      percent: 99,
      to: '/budget/current',
      icon: WalletCards,
      tone: 'done',
    },
  ]
})
</script>

<style scoped>
.budget-list-header {
  padding: 32px 20px 22px;
  color: #fff;
  text-align: center;
}

.header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
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
  font-size: 32px;
  font-weight: 900;
  line-height: 1.08;
}

.current-summary {
  display: block;
  border-block: 1px solid rgba(32, 36, 42, 0.1);
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
  background: rgba(36, 54, 79, 0.11);
}

.summary-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #0f5fae;
}

.budget-list-body {
  padding: 16px 20px 112px;
}

.mode-guide {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 9px;
  margin-bottom: 22px;
}

.mode-card {
  border: 1px solid rgba(32, 36, 42, 0.06);
  min-height: 106px;
  padding: 15px 14px;
  color: inherit;
  text-decoration: none;
}

.mode-card.primary {
  border-color: rgba(32, 36, 42, 0.06) !important;
  background: transparent !important;
}

.mode-card span {
  display: block;
  color: #0f5fae;
  font-size: 10px;
  font-weight: 900;
}

.mode-card strong {
  display: block;
  margin-top: 5px;
  color: #20242a;
  font-size: 15px;
  font-weight: 900;
}

.mode-card p {
  margin: 6px 0 0;
  color: #6e6e73;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.42;
}

.section-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.expense-mode-section {
  margin-bottom: 22px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.section-head.split {
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.section-head h2 {
  margin: 0;
  color: #20242a;
  font-size: 19px;
  font-weight: 900;
}

.section-head p {
  margin: 5px 0 0;
  color: #6e6e73;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.45;
}

.section-head a {
  flex-shrink: 0;
  color: #0f5fae;
  font-size: 12px;
  font-weight: 900;
  text-decoration: none;
}

.expense-mode-grid {
  display: grid;
  gap: 8px;
}

.expense-mode-card {
  display: grid;
  gap: 4px;
  padding: 14px 15px;
  color: inherit;
  text-decoration: none;
}

.expense-mode-card span {
  color: #0f5fae;
  font-size: 11px;
  font-weight: 900;
}

.expense-mode-card strong {
  color: #20242a;
  font-size: 14px;
  font-weight: 900;
}

.expense-mode-card p {
  margin: 0;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.45;
}

.budget-history-card {
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr);
  gap: 12px;
  padding: 15px;
  color: inherit;
  text-decoration: none;
}

.history-icon {
  display: inline-flex;
  width: 40px;
  height: 40px;
  align-items: center;
  justify-content: center;
  border-radius: 13px;
  background: rgba(15, 95, 174, 0.08);
  color: #0f5fae;
}

.history-icon.done {
  background: rgba(36, 54, 79, 0.055);
  color: #6e6e73;
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
  font-size: 16px;
  font-weight: 900;
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
  gap: 8px;
  margin-top: 12px;
  border-top: 1px solid rgba(32, 36, 42, 0.075);
  padding-top: 11px;
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

.history-metrics b.danger {
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
  background: #0f5fae;
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
