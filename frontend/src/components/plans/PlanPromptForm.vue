<template>
  <form class="prompt-form" @submit.prevent="$emit('submit')">
    <div>
      <label class="field-label" for="plan-prompt">자연어 입력</label>
      <textarea
        id="plan-prompt"
        :value="rawPrompt"
        class="form-field prompt-textarea"
        rows="5"
        placeholder="예: 10월 결혼 예정이고 혼수가전 예산은 700만 원이에요.
7월부터 9월까지 냉장고, TV, 세탁기와 건조기를 구매하고 싶어요."
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
        <label class="field-label" for="start-month">시작 월</label>
        <input
          id="start-month"
          :value="planForm.startMonth"
          class="form-field"
          type="month"
          @input="patch('startMonth', $event.target.value)"
        />
      </div>
      <div>
        <label class="field-label" for="end-month">종료 월</label>
        <input
          id="end-month"
          :value="planForm.endMonth"
          class="form-field"
          type="month"
          @input="patch('endMonth', $event.target.value)"
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
  gap: 18px;
}

.prompt-textarea {
  resize: vertical;
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
  gap: 12px;
}

.strategy-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.expense-mode-grid {
  display: grid;
  gap: 8px;
}

.expense-mode-button {
  display: flex;
  min-height: 66px;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 4px;
  border: 1px solid #dbe4ee;
  border-radius: 14px;
  padding: 12px 13px;
  background: rgba(255, 255, 255, 0.82);
  text-align: left;
}

.expense-mode-button strong {
  color: #20242a;
  font-size: 13px;
  font-weight: 900;
}

.expense-mode-button small {
  color: #6e6e73;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.35;
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
  min-height: 44px;
  border: 1px solid #dbe4ee;
  border-radius: 12px;
  background: #fff;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 900;
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
