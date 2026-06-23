<template>
  <div class="budget-summary">
    <div class="summary-row">
      <span>전체 예산</span>
      <strong>{{ krw(budget) }}</strong>
    </div>
    <div class="summary-row">
      <span>품목 합계</span>
      <strong :class="tone">{{ krw(total) }}</strong>
    </div>
    <div class="progress-track">
      <i :class="tone" :style="{ width: `${Math.min(ratio * 100, 100)}%` }" />
    </div>
    <p v-if="ratio > 1" class="danger">입력한 품목 금액이 전체 예산을 초과했어요.</p>
    <p v-else-if="ratio >= 0.9" class="warning">예산의 90% 이상 사용 예정입니다.</p>
    <p v-else class="normal">정상 범위 안에서 계획하고 있어요.</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { krw } from '@/data/mockData'

const props = defineProps({
  budget: { type: Number, required: true },
  total: { type: Number, required: true },
})

const ratio = computed(() => (props.budget > 0 ? props.total / props.budget : 0))
const tone = computed(() => (ratio.value > 1 ? 'danger' : ratio.value >= 0.9 ? 'warning' : 'normal'))
</script>

<style scoped>
.budget-summary {
  border: 1px solid rgba(37, 99, 235, 0.16);
  border-radius: 16px;
  padding: 14px;
  background: #e8f1ff;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 7px;
  color: #0f5fae;
  font-size: 12px;
  font-weight: 800;
}

.summary-row strong {
  font-weight: 900;
}

.progress-track {
  height: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.15);
}

.progress-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  transition: width 0.2s ease;
}

.normal {
  color: #0f5fae;
}

.warning {
  color: #b54708;
}

.danger {
  color: #d92d20;
}

i.normal {
  background: #0f5fae;
}

i.warning {
  background: #f79009;
}

i.danger {
  background: #d92d20;
}

p {
  margin: 8px 0 0;
  font-size: 12px;
  font-weight: 800;
}
</style>
