<template>
  <section class="screen">
    <header class="budget-header blue-gradient">
      <div class="header-row">
        <AppBackButton fallback="/budget" />
        <div>
          <h1>6월 예산</h1>
          <p>카테고리별 지출 현황</p>
        </div>
        <button
          class="icon-button budget-edit-button"
          type="button"
          :aria-label="isEditingBudget ? '예산 저장' : '예산 수정'"
          @click="isEditingBudget ? saveBudget() : startEditBudget()"
        >
          <Check v-if="isEditingBudget" :size="18" />
          <Pencil v-else :size="18" />
        </button>
      </div>
      <div class="budget-summary-box">
        <div>
          <span>사용</span>
          <strong>{{ krw(totalSpent) }}</strong>
        </div>
        <div>
          <span>{{ isEditingBudget ? '예산 수정' : '예산' }}</span>
          <strong v-if="!isEditingBudget">{{ krw(displayBudget) }}</strong>
          <input
            v-else
            class="budget-edit-input"
            type="number"
            inputmode="numeric"
            v-model.number="editBudget"
            @keyup.enter="saveBudget"
          />
        </div>
        <div class="summary-progress">
          <i :style="{ width: `${percent}%` }" />
        </div>
        <p>{{ isEditingBudget ? '이번 달 전체 예산을 입력하고 ✓ 를 누르세요' : `전체 예산의 ${percent}% 사용 중` }}</p>
      </div>
    </header>

    <div class="screen-scroll scrollbar-hide budget-body">
      <article v-for="category in budgetCategories" :key="category.id" class="app-card budget-row">
        <div class="budget-row-head">
          <div>
            <span class="category-icon">{{ category.icon }}</span>
            <strong>{{ category.name }}</strong>
          </div>
          <p>
            <b>{{ krw(category.spent) }}</b>
            / {{ krw(category.budget) }}
          </p>
        </div>
        <div class="category-track">
          <i :style="{ width: `${Math.min((category.spent / category.budget) * 100, 100)}%`, background: category.spent > category.budget ? '#D92D20' : category.color }" />
        </div>
        <small>{{ category.spent > category.budget ? `${krw(category.spent - category.budget)} 초과` : `${krw(category.budget - category.spent)} 남음` }}</small>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Check, Pencil } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { budgetCategories, krw } from '@/data/mockData'

const totalBudget = computed(() => budgetCategories.reduce((sum, category) => sum + category.budget, 0))
const totalSpent = computed(() => budgetCategories.reduce((sum, category) => sum + category.spent, 0))

const budgetOverride = ref(null)
const displayBudget = computed(() => budgetOverride.value ?? totalBudget.value)
const percent = computed(() => Math.min(Math.round((totalSpent.value / displayBudget.value) * 100), 100))

const isEditingBudget = ref(false)
const editBudget = ref(0)

function startEditBudget() {
  editBudget.value = displayBudget.value
  isEditingBudget.value = true
}

function saveBudget() {
  const next = Number(editBudget.value)
  budgetOverride.value = next > 0 ? next : displayBudget.value
  isEditingBudget.value = false
}
</script>

<style scoped>
.budget-header {
  padding: 24px 20px;
  color: #fff;
}

.header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

h1 {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 900;
}

.header-row p {
  margin: 0;
  color: rgba(255, 255, 255, 0.68);
  font-size: 12px;
  font-weight: 700;
}

.budget-summary-box {
  border-radius: 18px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.16);
}

.budget-summary-box {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.budget-summary-box span {
  color: rgba(255, 255, 255, 0.68);
  font-size: 12px;
  font-weight: 700;
}

.budget-summary-box strong {
  display: block;
  font-size: 22px;
  font-weight: 900;
}

.budget-edit-input {
  width: 100%;
  margin-top: 2px;
  border: 0;
  border-bottom: 2px solid rgba(255, 255, 255, 0.6);
  border-radius: 0;
  padding: 0 0 3px;
  background: transparent;
  color: #fff;
  font-size: 22px;
  font-weight: 900;
  font-variant-numeric: tabular-nums;
  outline: none;
}

.summary-progress {
  grid-column: 1 / -1;
  height: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.22);
}

.summary-progress i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #fff;
}

.budget-summary-box p {
  grid-column: 1 / -1;
  margin: 0;
  color: rgba(255, 255, 255, 0.68);
  font-size: 12px;
  font-weight: 700;
}

.budget-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 20px 116px;
}

.big-expense-selector {
  display: grid;
  gap: 10px;
}

.selector-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.selector-head strong {
  color: #20242a;
  font-size: 15px;
  font-weight: 900;
}

.selector-head a {
  flex-shrink: 0;
  color: #0f5fae;
  font-size: 12px;
  font-weight: 900;
  text-decoration: none;
}

.selector-grid {
  display: grid;
  gap: 8px;
}

.selector-card {
  display: grid;
  gap: 3px;
  border: 1px solid rgba(32, 36, 42, 0.06);
  border-radius: 14px;
  padding: 12px 13px;
  background: rgba(255, 255, 255, 0.82);
  color: inherit;
  text-decoration: none;
  box-shadow: 0 10px 30px rgba(36, 54, 79, 0.055);
}

.selector-card span {
  color: #0f5fae;
  font-size: 11px;
  font-weight: 900;
}

.selector-card p {
  margin: 0;
  color: #20242a;
  font-size: 13px;
  font-weight: 900;
}

.budget-row {
  padding: 15px;
}

.budget-row-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.budget-row-head div {
  display: flex;
  align-items: center;
  gap: 9px;
}

.category-icon {
  font-size: 21px;
}

.budget-row-head strong,
.budget-row-head b {
  color: #17202b;
  font-size: 13px;
  font-weight: 900;
}

.budget-row-head p,
.budget-row small {
  margin: 0;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 700;
}

.category-track {
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: #e7edf4;
}

.category-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
}
</style>
