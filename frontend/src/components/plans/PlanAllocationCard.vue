<template>
  <article class="allocation-card app-card">
    <div class="allocation-head">
      <h4>{{ item.name }}</h4>
      <span class="badge-soft" :class="statusClass">{{ item.status }}</span>
    </div>
    <p class="amount">{{ krw(item.amount) }}</p>
    <div class="card-line">
      <CreditCard :size="15" />
      <span>{{ item.card }}</span>
      <strong>예상 혜택 {{ krw(item.benefit) }}</strong>
    </div>
    <p class="note">{{ item.note }}</p>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { CreditCard } from 'lucide-vue-next'
import { krw } from '@/data/mockData'

const props = defineProps({
  item: { type: Object, required: true },
})

const statusClass = computed(() => ({
  '구매 예정': 'primary',
  '구매 완료': 'success',
  '일정 변경': 'warning',
  '예산 초과': 'danger',
}[props.item.status] || 'primary'))
</script>

<style scoped>
.allocation-card {
  padding: 14px;
}

.allocation-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

h4 {
  margin: 0;
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
}

.amount {
  margin: 7px 0;
  color: #17202b;
  font-size: 18px;
  font-weight: 900;
}

.card-line {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 800;
}

.card-line strong {
  margin-left: auto;
  color: #008c95;
}

.note {
  margin: 10px 0 0;
  border-radius: 10px;
  padding: 10px;
  background: #e7edf4;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.45;
}

.primary {
  background: #e8f1ff;
  color: #0f5fae;
}

.success {
  background: #f0fdf4;
  color: #16a34a;
}

.warning {
  background: #fffaeb;
  color: #b54708;
}

.danger {
  background: #fef3f2;
  color: #d92d20;
}
</style>
