<template>
  <form class="prompt-form" @submit.prevent="$emit('submit')">
    <div>
      <label class="field-label" for="plan-prompt">자연어 입력</label>
      <textarea
        id="plan-prompt"
        :value="rawPrompt"
        class="form-field prompt-textarea"
        rows="4"
        placeholder="예: 다음 달 큰 지출 예산 80만 원을 관리하고 싶어요.
정장 셔츠, 구두, 증명사진, 토익스피킹 응시료를 순서대로 결제할 예정입니다."
        @input="$emit('update:rawPrompt', $event.target.value)"
      />
      <p v-if="errors.prompt" class="error-text">{{ errors.prompt }}</p>
    </div>

    <PlanExampleChips :examples="examples" @select="$emit('update:rawPrompt', $event)" />

    <div>
      <span class="field-label">큰 지출 처리 방식</span>
      <div class="expense-mode-grid">
        <button
          v-for="mode in expenseModes"
          :key="mode.id"
          class="expense-mode-button"
          :class="{ active: planForm.expenseMode === mode.id }"
          type="button"
          @click="patch('expenseMode', mode.id)"
        >
          <strong>{{ mode.label }}</strong>
          <small>{{ mode.description }}</small>
        </button>
      </div>
    </div>

    <div>
      <label class="field-label" for="plan-budget">전체 예산</label>
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

    <div class="month-grid">
      <div>
        <AppCalendarPicker
          :model-value="planForm.startMonth"
          label="시작 월"
          mode="month"
          @update:model-value="patch('startMonth', $event)"
        />
      </div>
      <div>
        <AppCalendarPicker
          :model-value="planForm.endMonth"
          label="종료 월"
          mode="month"
          @update:model-value="patch('endMonth', $event)"
        />
      </div>
    </div>
    <p v-if="errors.endMonth" class="error-text">{{ errors.endMonth }}</p>

    <div>
      <span class="field-label">우선 전략</span>
      <div class="strategy-grid">
        <button
          v-for="strategy in strategies"
          :key="strategy"
          class="strategy-button"
          :class="{ active: planForm.strategy === strategy }"
          type="button"
          @click="patch('strategy', strategy)"
        >
          {{ strategy }}
        </button>
      </div>
    </div>

    <AiRoleNotice />

    <button class="primary-button w-100" type="submit">AI로 품목 정리하기</button>
  </form>
</template>

<script setup>
import AiRoleNotice from './AiRoleNotice.vue'
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

const patch = (key, value) => {
  emit('update:planForm', { ...props.planForm, [key]: value })
}
</script>

<style scoped>
.prompt-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.prompt-textarea {
  min-height: 102px;
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

.strategy-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
}

.expense-mode-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
}

.expense-mode-button {
  display: flex;
  min-height: 64px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  border: 1px solid #dbe4ee;
  border-radius: 13px;
  padding: 10px 8px;
  background: rgba(255, 255, 255, 0.82);
  text-align: center;
}

.expense-mode-button strong {
  color: #20242a;
  font-size: 12px;
  font-weight: 900;
  line-height: 1.25;
}

.expense-mode-button small {
  display: -webkit-box;
  overflow: hidden;
  color: #6e6e73;
  font-size: 9px;
  font-weight: 700;
  line-height: 1.25;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.expense-mode-button.active {
  border-color: rgba(15, 95, 174, 0.34);
  background: #e8f1fb;
  box-shadow: inset 0 0 0 1px rgba(15, 95, 174, 0.16);
}

.expense-mode-button.active strong,
.expense-mode-button.active small {
  color: #0f5fae;
}

.strategy-button {
  min-height: 40px;
  border: 1px solid #dbe4ee;
  border-radius: 12px;
  background: #fff;
  color: #6e6e73;
  font-size: 11px;
  font-weight: 900;
  line-height: 1.25;
}

.strategy-button.active {
  border-color: #0f5fae;
  background: #e8f1ff;
  color: #0f5fae;
}

.error-text {
  margin: 6px 0 0;
  color: #d92d20;
  font-size: 12px;
  font-weight: 700;
}
</style>
