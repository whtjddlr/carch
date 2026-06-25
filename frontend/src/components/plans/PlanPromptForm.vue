<template>
  <form class="prompt-form" @submit.prevent="$emit('submit')">
    <div class="field-block">
      <label class="field-label" for="plan-prompt">어떤 지출인가요?</label>
      <textarea
        id="plan-prompt"
        :value="rawPrompt"
        class="form-field prompt-textarea"
        rows="3"
        placeholder="예: 이사하면서 가전·가구를 200만 원 정도 장만하려고 해요."
        @input="$emit('update:rawPrompt', $event.target.value)"
      />
      <PlanExampleChips :examples="examples" @select="$emit('update:rawPrompt', $event)" />
      <p v-if="errors.prompt" class="error-text">{{ errors.prompt }}</p>
    </div>

    <div class="field-pair">
      <div class="field-block">
        <span class="field-label"><Wallet :size="14" /> 예산</span>
        <div class="field-with-unit">
          <input
            id="plan-budget"
            :value="planForm.budget"
            class="form-field"
            min="1"
            type="number"
            @input="patch('budget', Number($event.target.value))"
          />
          <span>원</span>
        </div>
        <p v-if="errors.budget" class="error-text">{{ errors.budget }}</p>
      </div>

      <div class="field-block">
        <span class="field-label"><CalendarDays :size="14" /> 결제 시기</span>
        <AppCalendarPicker
          :model-value="planForm.startMonth"
          label="결제 예정 월"
          mode="month"
          @update:model-value="patchDate"
        />
        <p v-if="errors.endMonth" class="error-text">{{ errors.endMonth }}</p>
      </div>
    </div>

    <div class="field-block">
      <span class="field-label"><Layers :size="14" /> 처리 방식</span>
      <div class="chip-grid">
        <button
          v-for="mode in expenseModes"
          :key="mode.id"
          class="select-chip"
          :class="{ active: planForm.expenseMode === mode.id }"
          type="button"
          @click="patch('expenseMode', mode.id)"
        >
          <component :is="modeIcon(mode.id)" :size="17" />
          {{ mode.label }}
        </button>
      </div>
    </div>

    <div class="field-block">
      <span class="field-label"><Target :size="14" /> 우선 전략</span>
      <div class="chip-grid">
        <button
          v-for="strategy in strategies"
          :key="strategy"
          class="select-chip"
          :class="{ active: planForm.strategy === strategy }"
          type="button"
          @click="patch('strategy', strategy)"
        >
          <component :is="strategyIcon(strategy)" :size="17" />
          {{ strategy }}
        </button>
      </div>
    </div>

    <button class="primary-button w-100" type="submit">다음</button>
  </form>
</template>

<script setup>
import { CalendarDays, Coins, Gift, Layers, PiggyBank, Target, Wallet } from 'lucide-vue-next'
import PlanExampleChips from './PlanExampleChips.vue'
import AppCalendarPicker from '@/components/AppCalendarPicker.vue'

const emit = defineEmits(['submit', 'update:rawPrompt', 'update:planForm'])
const props = defineProps({
  rawPrompt: { type: String, required: true },
  planForm: { type: Object, required: true },
  examples: { type: Array, required: true },
  expenseModes: { type: Array, required: true },
  strategies: { type: Array, required: true },
  errors: { type: Object, default: () => ({}) },
})

const MODE_ICONS = { 'within-budget': PiggyBank, 'planned-extra': Coins }
const STRATEGY_ICONS = { '혜택 최대화': Gift, '실적 채우기': Target }
const modeIcon = (id) => MODE_ICONS[id] || PiggyBank
const strategyIcon = (name) => STRATEGY_ICONS[name] || Gift

const patch = (key, value) => {
  emit('update:planForm', { ...props.planForm, [key]: value })
}

// 단일 예상 결제 시기 → 시작/종료 월을 동일하게 설정(결제일 하나)
const patchDate = (value) => {
  emit('update:planForm', { ...props.planForm, startMonth: value, endMonth: value })
}
</script>

<style scoped>
.prompt-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.field-label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.field-label :deep(svg) {
  color: #0f5fae;
}

.field-pair {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  align-items: start;
}

.field-pair .field-block {
  min-width: 0;
}

.prompt-textarea {
  min-height: 78px;
  resize: vertical;
  line-height: 1.5;
}

.field-with-unit {
  position: relative;
}

.field-with-unit input {
  padding-right: 42px;
}

.field-with-unit span {
  position: absolute;
  top: 50%;
  right: 14px;
  color: #6e6e73;
  font-size: 13px;
  font-weight: 800;
  transform: translateY(-50%);
}

.month-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

/* 처리 방식 · 우선 전략 — 한 줄에 두 개씩 꽉 차는 칩 */
.chip-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 9px;
}

.select-chip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-height: 50px;
  width: 100%;
  border: 1px solid #dbe4ee;
  border-radius: 14px;
  padding: 0 12px;
  background: #fff;
  color: #6e7885;
  font-size: 13px;
  font-weight: 800;
}

.select-chip :deep(svg) {
  flex: 0 0 auto;
  color: #98a3b1;
}

.select-chip.active {
  border-color: transparent;
  background: #24364f;
  color: #fff;
}

.select-chip.active :deep(svg) {
  color: #fff;
}

.error-text {
  margin: 2px 0 0;
  color: #d92d20;
  font-size: 12px;
  font-weight: 700;
}

/* 예산 입력 ↔ 결제 시기 — 두 박스 높이·모양 통일 */
.field-pair .form-field {
  height: 54px;
  border-radius: 14px;
}

.field-pair :deep(.calendar-trigger) {
  min-height: 54px;
  height: 54px;
  border-radius: 14px;
  /* 라벨·값·달력 아이콘을 박스 안에서 살짝 위로 */
  padding: 6px 12px 13px;
}
</style>
