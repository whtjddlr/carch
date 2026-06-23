<template>
  <article class="app-card plan-card" @click="$emit('open', plan.id)">
    <div class="plan-head">
      <div class="plan-title">
        <div>
          <h3>{{ plan.title }}</h3>
          <p>{{ monthLabel(plan.startMonth) }} ~ {{ monthLabel(plan.endMonth) }} · 품목 {{ plan.items.length }}개</p>
        </div>
        <span class="badge-soft type-badge">{{ plan.type }}</span>
      </div>
      <button class="menu-button" type="button" aria-label="더보기 메뉴" @click.stop="$emit('menu', plan.id)">
        <MoreVertical :size="15" />
      </button>
    </div>

    <div class="plan-metrics">
      <div class="metric-tile">
        <p class="metric-label">총예산</p>
        <p class="metric-value">{{ krw(plan.totalBudget) }}</p>
      </div>
      <div class="metric-tile">
        <p class="metric-label">예상 총혜택</p>
        <p class="metric-value success">+{{ krw(selectedScenario?.totalBenefit || 0) }}</p>
      </div>
      <div class="metric-tile">
        <p class="metric-label">상태</p>
        <p class="metric-value">{{ plan.status }}</p>
      </div>
    </div>

    <div class="budget-row">
      <span :class="{ danger: isOverBudget }">{{ isOverBudget ? '예산 초과' : '예산 범위 내' }}</span>
      <strong>{{ progress }}%</strong>
    </div>
    <div class="progress-track">
      <i :style="{ width: `${progress}%` }" />
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { MoreVertical } from 'lucide-vue-next'
import { krw, monthLabel } from '@/data/mockData'

defineEmits(['open', 'menu'])
const props = defineProps({
  plan: { type: Object, required: true },
})

const selectedScenario = computed(() => props.plan.scenarios.find((scenario) => scenario.id === props.plan.selectedScenarioId) || props.plan.scenarios[0])
const isOverBudget = computed(() => Number(selectedScenario.value?.totalAmount || 0) > Number(props.plan.totalBudget || 0))
const progress = computed(() => Math.min(Math.round((Number(selectedScenario.value?.totalAmount || 0) / Number(props.plan.totalBudget || 1)) * 100), 100))
</script>

<style scoped>
.plan-card {
  padding: 16px;
  cursor: pointer;
}

.plan-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 14px;
}

.plan-title {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-wrap: wrap;
  gap: 7px;
}

h3 {
  margin: 0 0 4px;
  color: #17202b;
  font-size: 15px;
  font-weight: 900;
}

.plan-title p {
  margin: 0;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 700;
}

.type-badge {
  align-self: flex-start;
  background: #f5f3ff;
  color: #24364f;
}

.menu-button {
  display: inline-flex;
  width: 32px;
  height: 32px;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: #fef3f2;
  color: #d92d20;
}

.plan-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}

.success {
  color: #008c95;
}

.budget-row {
  display: flex;
  justify-content: space-between;
  color: #6e6e73;
  font-size: 11px;
  font-weight: 800;
}

.budget-row .danger {
  color: #d92d20;
}

.progress-track {
  height: 7px;
  overflow: hidden;
  border-radius: 999px;
  margin-top: 6px;
  background: #e7edf4;
}

.progress-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #0f5fae;
}
</style>
