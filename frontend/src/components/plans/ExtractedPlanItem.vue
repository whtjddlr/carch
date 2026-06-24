<template>
  <article class="app-card extracted-item">
    <div class="item-top">
      <input
        :value="item.name"
        aria-label="품목명"
        placeholder="품목명"
        @input="patch('name', $event.target.value)"
      />
      <button type="button" aria-label="품목 삭제" @click="$emit('remove', item.id)">
        <Trash2 :size="15" />
      </button>
    </div>
    <div class="item-grid">
      <label>
        <span>내부 카테고리</span>
        <input :value="item.category" @input="patch('category', $event.target.value)" />
      </label>
      <label>
        <span>예상 금액</span>
        <input :value="item.amount" type="number" @input="patch('amount', Number($event.target.value))" />
      </label>
      <div class="picker-field">
        <AppCalendarPicker
          :model-value="item.targetMonth"
          label="목표 구매 월"
          mode="month"
          @update:model-value="patch('targetMonth', $event)"
        />
      </div>
      <label>
        <span>결제 방식</span>
        <select :value="item.paymentType || 'lump_sum'" @change="patchPaymentType($event.target.value)">
          <option value="lump_sum">일시불</option>
          <option value="installment">할부</option>
        </select>
      </label>
      <label v-if="(item.paymentType || 'lump_sum') === 'installment'">
        <span>개월 수</span>
        <select :value="item.installmentMonths || 2" @change="patch('installmentMonths', Number($event.target.value))">
          <option v-for="month in installmentMonthOptions" :key="month" :value="month">{{ month }}개월</option>
        </select>
      </label>
      <div class="check-grid">
        <label><input :checked="item.required" type="checkbox" @change="patch('required', $event.target.checked)" /> 필수</label>
        <label><input :checked="item.flexible" type="checkbox" @change="patch('flexible', $event.target.checked)" /> 일정 변경 가능</label>
        <label v-if="(item.paymentType || 'lump_sum') === 'installment'">
          <input
            :checked="Boolean(item.isInterestFreeInstallment)"
            type="checkbox"
            @change="patch('isInterestFreeInstallment', $event.target.checked)"
          />
          무이자
        </label>
      </div>
    </div>
  </article>
</template>

<script setup>
import { Trash2 } from 'lucide-vue-next'
import AppCalendarPicker from '@/components/AppCalendarPicker.vue'

const emit = defineEmits(['update', 'remove'])
const props = defineProps({
  item: { type: Object, required: true },
})

const installmentMonthOptions = [2, 3, 4, 5, 6, 9, 10, 12]

const patch = (field, value) => {
  emit('update', { ...props.item, [field]: value })
}

const patchPaymentType = (paymentType) => {
  emit('update', {
    ...props.item,
    paymentType,
    installmentMonths: paymentType === 'installment' ? Number(props.item.installmentMonths || 2) : 0,
    isInterestFreeInstallment: paymentType === 'installment' ? Boolean(props.item.isInterestFreeInstallment) : false,
  })
}
</script>

<style scoped>
.extracted-item {
  padding: 14px;
}

.item-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.item-top input {
  min-width: 0;
  flex: 1;
  border: 0;
  background: transparent;
  color: #17202b;
  font-size: 15px;
  font-weight: 900;
  outline: none;
}

.item-top button {
  display: inline-flex;
  width: 32px;
  height: 32px;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: #fef3f2;
  color: #d92d20;
}

.item-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

label {
  min-width: 0;
}

.picker-field {
  min-width: 0;
}

label span {
  display: block;
  margin-bottom: 4px;
  color: #6e6e73;
  font-size: 10px;
  font-weight: 800;
}

label input:not([type='checkbox']),
label select {
  width: 100%;
  border: 1px solid #dbe4ee;
  border-radius: 10px;
  padding: 9px 10px;
  background: #fbfdff;
  color: #17202b;
  font-size: 12px;
  font-weight: 700;
}

.check-grid {
  display: flex;
  grid-column: 1 / -1;
  gap: 14px;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 800;
}
</style>
