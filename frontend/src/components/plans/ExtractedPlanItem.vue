<template>
  <article class="plan-item">
    <input
      class="pi-name"
      :value="item.name"
      aria-label="품목명"
      placeholder="품목명을 입력하세요"
      @input="patch('name', $event.target.value)"
    />
    <label class="pi-amount">
      <input
        :value="item.amount || ''"
        type="number"
        min="0"
        inputmode="numeric"
        aria-label="예상 금액"
        placeholder="0"
        @input="patch('amount', Number($event.target.value))"
      />
      <span>원</span>
    </label>
    <button class="pi-del" type="button" aria-label="품목 삭제" @click="$emit('remove', item.id)">
      <Trash2 :size="15" />
    </button>
  </article>
</template>

<script setup>
import { Trash2 } from 'lucide-vue-next'

const emit = defineEmits(['update', 'remove'])
const props = defineProps({
  item: { type: Object, required: true },
})

const patch = (field, value) => {
  emit('update', { ...props.item, [field]: value })
}
</script>

<style scoped>
.plan-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 13px 2px;
  border-bottom: 1px solid rgba(36, 54, 79, 0.08);
}

.plan-item:last-child {
  border-bottom: 0;
}

.pi-name {
  flex: 1 1 auto;
  min-width: 0;
  border: 0;
  background: transparent;
  color: #17202b;
  font-size: 14px;
  font-weight: 800;
  outline: none;
}

.pi-name::placeholder {
  color: #b3bdc9;
  font-weight: 700;
}

.pi-amount {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 4px;
}

.pi-amount input {
  width: 100px;
  border: 1px solid #dbe4ee;
  border-radius: 10px;
  padding: 8px 10px;
  background: #fbfdff;
  color: #17202b;
  font-size: 13px;
  font-weight: 700;
  text-align: right;
  outline: none;
  font-variant-numeric: tabular-nums;
}

.pi-amount input:focus {
  border-color: #0f5fae;
}

.pi-amount span {
  color: #6e6e73;
  font-size: 12px;
  font-weight: 800;
}

.pi-del {
  display: inline-flex;
  flex: 0 0 auto;
  width: 30px;
  height: 30px;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 9px;
  background: transparent;
  color: #c0392b !important;
}

.pi-del:active {
  background: #fef3f2;
}
</style>
