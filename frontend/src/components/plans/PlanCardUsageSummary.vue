<template>
  <section class="usage-summary">
    <h3>카드별 사용 요약</h3>
    <div class="summary-list">
      <article v-for="card in cards" :key="card.cardName" class="app-card usage-card">
        <div class="usage-head">
          <span class="uh-thumb">
            <img
              v-if="imageFor(card.cardName)"
              :src="imageFor(card.cardName)"
              :alt="card.cardName"
              :class="ori[card.cardName]"
              @load="onThumb($event, card.cardName)"
            />
            <CreditCard v-else :size="16" />
          </span>
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
import { reactive } from 'vue'
import { CreditCard } from 'lucide-vue-next'
import { cards as mockCards, krw } from '@/data/mockData'

defineProps({
  cards: { type: Array, default: () => [] },
})

const imageFor = (name) => mockCards.find((c) => c?.name === name)?.imageUrl || ''

// 세로 카드 이미지는 가로 썸네일에 맞춰 회전
const ori = reactive({})
function onThumb(event, name) {
  const img = event.target
  ori[name] = img.naturalWidth > img.naturalHeight ? 'is-landscape' : 'is-portrait'
}
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
  gap: 9px;
  margin-bottom: 12px;
}

.uh-thumb {
  position: relative;
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 44px;
  height: 28px;
  overflow: hidden;
  border-radius: 6px;
  background: #e8edf2;
  color: #8a9aad;
  box-shadow: 0 2px 8px rgba(36, 54, 79, 0.18);
}

.uh-thumb img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.uh-thumb img.is-portrait {
  inset: auto;
  top: 50%;
  left: 50%;
  width: 28px;
  height: 44px;
  max-width: none;
  transform: translate(-50%, -50%) rotate(-90deg);
}

.usage-head strong {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.usage-head .badge-soft {
  flex: 0 0 auto;
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
