<template>
  <div class="budget-summary">
    <div class="bs-grid">
      <div class="bs-tile">
        <span class="bs-ico budget"><Wallet :size="15" /></span>
        <div class="bs-text">
          <small>전체 예산</small>
          <strong>{{ krw(budget) }}</strong>
        </div>
      </div>
      <div class="bs-tile">
        <span class="bs-ico total"><ShoppingBag :size="15" /></span>
        <div class="bs-text">
          <small>품목 합계</small>
          <strong :class="tone">{{ krw(total) }}</strong>
        </div>
      </div>
    </div>
    <div class="progress-track">
      <i :class="tone" :style="{ width: `${Math.min(ratio * 100, 100)}%` }" />
    </div>
    <p class="bs-note" :class="tone">
      <component :is="noteIcon" :size="13" />
      <span>{{ noteText }}</span>
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { AlertTriangle, CheckCircle2, ShoppingBag, TriangleAlert, Wallet } from 'lucide-vue-next'
import { krw } from '@/data/mockData'

const props = defineProps({
  budget: { type: Number, required: true },
  total: { type: Number, required: true },
})

const ratio = computed(() => (props.budget > 0 ? props.total / props.budget : 0))
const tone = computed(() => (ratio.value > 1 ? 'danger' : ratio.value >= 0.9 ? 'warning' : 'normal'))
const noteText = computed(() => (
  ratio.value > 1
    ? '입력한 품목 금액이 전체 예산을 초과했어요.'
    : ratio.value >= 0.9
      ? '예산의 90% 이상 사용 예정입니다.'
      : '정상 범위 안에서 계획하고 있어요.'
))
const noteIcon = computed(() => (ratio.value > 1 ? TriangleAlert : ratio.value >= 0.9 ? AlertTriangle : CheckCircle2))
</script>

<style scoped>
.budget-summary {
  border: 1px solid rgba(15, 95, 174, 0.14);
  border-radius: 16px;
  padding: 14px;
  background: linear-gradient(180deg, #f3f8ff 0%, #ffffff 100%);
  box-shadow: 0 10px 22px rgba(36, 54, 79, 0.05);
}

.bs-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 12px;
}

.bs-tile {
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: 0;
}

.bs-ico {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
}

.bs-ico.budget {
  background: rgba(15, 95, 174, 0.12);
  color: #0f5fae;
}

.bs-ico.total {
  background: rgba(0, 140, 149, 0.13);
  color: #008c95;
}

.bs-text {
  min-width: 0;
}

.bs-text small {
  display: block;
  color: #6e7885;
  font-size: 11px;
  font-weight: 800;
}

.bs-text strong {
  display: block;
  margin-top: 2px;
  color: #17202b;
  font-size: 15px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.bs-text strong.danger {
  color: #d92d20;
}

.bs-text strong.warning {
  color: #b54708;
}

.progress-track {
  height: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(15, 95, 174, 0.12);
}

.progress-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  transition: width 0.2s ease;
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

.bs-note {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 10px 0 0;
  font-size: 12px;
  font-weight: 800;
}

.bs-note.normal {
  color: #0f5fae;
}

.bs-note.warning {
  color: #b54708;
}

.bs-note.danger {
  color: #d92d20;
}
</style>
