<template>
  <article
    class="scenario-card"
    :class="{ selected }"
    role="radio"
    :aria-checked="selected"
    tabindex="0"
    @click="$emit('select', scenario.id)"
    @keydown.enter="$emit('select', scenario.id)"
  >
    <div v-if="selected" class="selected-mark">
      <Check :size="13" />
    </div>
    <div class="scenario-title">
      <div class="scenario-icon" :style="{ background: color + '18', color }">
        <component :is="icon" :size="17" />
      </div>
      <strong :style="{ color }">{{ scenario.type }}</strong>
      <span v-if="scenario.recommended" class="badge-soft" :style="{ color, background: color + '18' }">추천</span>
    </div>

    <div class="scenario-grid">
      <div class="metric-tile">
        <p class="metric-label">총 구매 예정액</p>
        <p class="metric-value">{{ krw(scenario.totalAmount) }}</p>
      </div>
      <div class="metric-tile">
        <p class="metric-label">전체 예상 혜택</p>
        <p class="metric-value success">+{{ krw(scenario.totalBenefit) }}</p>
      </div>
      <div class="metric-tile">
        <p class="metric-label">예산 차이</p>
        <p class="metric-value" :class="{ danger: scenario.budgetDiff < 0 }">{{ scenario.budgetDiff < 0 ? '-' : '+' }}{{ krw(scenario.budgetDiff) }}</p>
      </div>
      <div class="metric-tile">
        <p class="metric-label">월 최대 지출액</p>
        <p class="metric-value">{{ krw(scenario.maxMonthlySpend) }}</p>
      </div>
      <div class="metric-tile wide">
        <p class="metric-label">실적 달성 예상 카드 수</p>
        <p class="metric-value">{{ scenario.achievedCards }}장</p>
      </div>
    </div>

    <ul>
      <li v-for="reason in scenario.reasons" :key="reason">
        <Check :size="12" />
        <span>{{ reason }}</span>
      </li>
    </ul>

    <PlanWarningAlert v-if="scenario.warning" :message="scenario.warning" tone="warning" />

    <div class="scenario-actions">
      <button class="outline-button" type="button" @click.stop="$emit('view-detail', scenario.id)">상세 계획 보기</button>
      <button class="primary-button" type="button" :style="{ background: color }" @click.stop="$emit('select', scenario.id)">이 계획 선택</button>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { Check, ShieldAlert, SlidersHorizontal, Zap } from 'lucide-vue-next'
import { krw } from '@/data/mockData'
import PlanWarningAlert from './PlanWarningAlert.vue'

defineEmits(['select', 'view-detail'])
const props = defineProps({
  scenario: { type: Object, required: true },
  selected: { type: Boolean, default: false },
})

const color = computed(() => ({
  '혜택 최대화': '#7C3AED',
  '예산 안정': '#059669',
  '실적 균형': '#0B63CE',
  '카드 실적 균형': '#0B63CE',
}[props.scenario.type] || '#0B63CE'))

const icon = computed(() => ({
  '혜택 최대화': Zap,
  '예산 안정': ShieldAlert,
  '실적 균형': SlidersHorizontal,
  '카드 실적 균형': SlidersHorizontal,
}[props.scenario.type] || SlidersHorizontal))
</script>

<style scoped>
.scenario-card {
  position: relative;
  border: 2px solid #dbe4ee;
  border-radius: 18px;
  padding: 16px;
  background: #fff;
  cursor: pointer;
}

.scenario-card.selected {
  border-color: #0f5fae;
  box-shadow: 0 0 0 1px #0f5fae;
}

.selected-mark {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  width: 26px;
  height: 26px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #0f5fae;
  color: #fff;
}

.scenario-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}

.scenario-title strong {
  font-size: 15px;
  font-weight: 900;
}

.scenario-icon {
  display: flex;
  width: 32px;
  height: 32px;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
}

.scenario-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.wide {
  grid-column: span 2;
}

.success {
  color: #008c95;
}

.danger {
  color: #d92d20;
}

ul {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 0;
  margin: 12px 0;
  list-style: none;
}

li {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  color: #17202b;
  font-size: 12px;
  font-weight: 700;
}

.scenario-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 12px;
}

.scenario-actions button {
  padding: 9px 8px;
  font-size: 12px;
}
</style>
