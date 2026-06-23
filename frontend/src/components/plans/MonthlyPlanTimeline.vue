<template>
  <section class="timeline">
    <h3>월별 구매 타임라인</h3>
    <div v-if="months.length" class="month-list">
      <div v-for="month in months" :key="month.month" class="month-section">
        <div class="month-title">
          <CalendarDays :size="16" />
          <strong>{{ monthLabel(month.month) }}</strong>
        </div>
        <div class="allocation-list">
          <PlanAllocationCard v-for="item in month.items" :key="`${month.month}-${item.name}`" :item="item" />
        </div>
      </div>
    </div>
    <p v-else class="empty-text">월별 계획이 없습니다.</p>
  </section>
</template>

<script setup>
import { CalendarDays } from 'lucide-vue-next'
import { monthLabel } from '@/data/mockData'
import PlanAllocationCard from './PlanAllocationCard.vue'

defineProps({
  months: { type: Array, default: () => [] },
})
</script>

<style scoped>
.timeline h3 {
  margin: 0 0 14px;
  color: #17202b;
  font-size: 15px;
  font-weight: 900;
}

.month-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.month-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  color: #0f5fae;
}

.month-title strong {
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
}

.allocation-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-left: 26px;
}

.empty-text {
  margin: 0;
  color: #6e6e73;
  font-size: 13px;
  font-weight: 700;
}
</style>
