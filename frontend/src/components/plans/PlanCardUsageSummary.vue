<template>
  <section class="usage-summary">
    <h3>카드별 사용 요약</h3>
    <div class="summary-list">
      <article v-for="card in cards" :key="card.cardName" class="app-card usage-card">
        <div class="usage-head">
          <strong>{{ card.cardName }}</strong>
          <span class="badge-soft" :class="card.achieved ? 'success' : 'warning'">
            {{ card.achieved ? '다음 달 조건 충족' : '다음 달 조건 부족' }}
          </span>
        </div>
        <div class="usage-grid">
          <div class="metric-tile">
            <p class="metric-label">배정 사용액</p>
            <p class="metric-value">{{ krw(card.totalAmount) }}</p>
          </div>
          <div class="metric-tile">
            <p class="metric-label">예상 혜택</p>
            <p class="metric-value success-text">+{{ krw(card.benefit) }}</p>
          </div>
          <div class="metric-tile">
            <p class="metric-label">남은 혜택 한도</p>
            <p class="metric-value">{{ krw(card.remainingLimit) }}</p>
          </div>
          <div class="metric-tile">
            <p class="metric-label">배정 품목 수</p>
            <p class="metric-value">{{ card.itemCount }}개</p>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { krw } from '@/data/mockData'

defineProps({
  cards: { type: Array, default: () => [] },
})
</script>

<style scoped>
.usage-summary h3 {
  margin: 0 0 14px;
  color: #17202b;
  font-size: 15px;
  font-weight: 900;
}

.summary-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.usage-card {
  padding: 14px;
}

.usage-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.usage-head strong {
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
}

.usage-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.success {
  background: #f0fdf4;
  color: #16a34a;
}

.warning {
  background: #fffaeb;
  color: #b54708;
}

.success-text {
  color: #008c95;
}
</style>
