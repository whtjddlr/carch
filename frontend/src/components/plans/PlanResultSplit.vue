<template>
  <div class="result-split">
    <div class="result-summary">
      <div>
        <span>예산</span>
        <strong>{{ krw(budget) }}</strong>
      </div>
      <div>
        <span>품목 합계</span>
        <strong>{{ krw(totalAmount) }}</strong>
      </div>
      <div class="benefit">
        <span>예상 혜택</span>
        <strong>+{{ krw(ownedBenefitTotal) }}</strong>
      </div>
    </div>

    <section class="rs-section">
      <div class="rs-head">
        <span class="rs-badge owned"><CreditCard :size="13" /> 보유 카드</span>
        <strong>품목별로 어떤 카드가 유리한지 비교했어요</strong>
      </div>
      <div class="rs-item-list">
        <div v-for="(item, i) in ownedItems" :key="i" class="rs-item">
          <div class="rs-item-head">
            <strong>{{ item.name }}</strong>
            <b>{{ krw(item.amount) }}</b>
          </div>
          <div class="rs-options">
            <button
              v-for="(opt, oi) in item.options"
              :key="oi"
              type="button"
              class="rs-option"
              :class="{ active: selected(i) === oi }"
              @click="select(i, oi)"
            >
              <span class="rs-rank" :class="`r${opt.rank}`">{{ opt.rank }}순위</span>
              <span class="rs-opt-thumb">
                <img v-if="opt.image" :src="opt.image" :alt="opt.card" :class="oriKey(i, oi)" @load="onThumb($event, i, oi)" />
                <CreditCard v-else :size="13" />
              </span>
              <span class="rs-opt-name">{{ opt.card }}</span>
              <em class="rs-opt-benefit">+{{ krw(opt.benefit) }}</em>
            </button>
          </div>
        </div>
        <p v-if="!ownedItems.length" class="rs-empty">배정할 품목이 없어요.</p>
      </div>
    </section>

    <section v-if="newCards.length" class="rs-section">
      <div class="rs-head">
        <span class="rs-badge issue"><Sparkles :size="13" /> 새 카드</span>
        <strong>발급하면 이만큼 더 받아요</strong>
      </div>
      <div class="rs-card-list">
        <button
          v-for="card in newCards"
          :key="card.id"
          type="button"
          class="rs-card"
          @click="$emit('open-card', card.id)"
        >
          <span class="rs-card-thumb">
            <img v-if="card.imageUrl" :src="card.imageUrl" :alt="card.name" :class="card.orientation" @load="onCardThumb($event, card)" />
            <Sparkles v-else :size="18" />
          </span>
          <div class="rs-card-body">
            <strong>{{ card.name }}</strong>
            <small>{{ card.benefitText }}</small>
            <span v-if="card.event" class="rs-event">🎁 발급 시 현금 {{ krw(card.event) }}</span>
          </div>
          <div class="rs-card-gain">
            <b v-if="card.planBenefit">+{{ krw(card.planBenefit) }}</b>
            <span>이 지출 혜택</span>
            <ChevronRight class="rs-card-go" :size="15" />
          </div>
        </button>
      </div>
      <p class="rs-note">카드를 누르면 발급 안내로 이동해요. 이벤트 혜택은 카드사 조건에 따라 달라질 수 있어요.</p>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive } from 'vue'
import { ChevronRight, CreditCard, Sparkles } from 'lucide-vue-next'
import { krw } from '@/data/mockData'

defineEmits(['open-card'])
const props = defineProps({
  budget: { type: Number, default: 0 },
  totalAmount: { type: Number, default: 0 },
  ownedItems: { type: Array, default: () => [] },
  newCards: { type: Array, default: () => [] },
})

// 항목별 선택(기본 1순위 = index 0)
const picked = reactive({})
function selected(index) {
  return picked[index] ?? 0
}
function select(index, optionIndex) {
  picked[index] = optionIndex
}

const ownedBenefitTotal = computed(() => props.ownedItems.reduce((sum, item, i) => {
  const opt = item.options?.[selected(i)] || item.options?.[0]
  return sum + Number(opt?.benefit || 0)
}, 0))

// 세로 카드 이미지는 가로 썸네일에 맞춰 회전
const ori = reactive({})
function oriKey(i, oi) {
  return ori[`${i}-${oi}`] || ''
}
function onThumb(event, i, oi) {
  const img = event.target
  ori[`${i}-${oi}`] = img.naturalWidth > img.naturalHeight ? 'is-landscape' : 'is-portrait'
}
function onCardThumb(event, card) {
  const img = event.target
  card.orientation = img.naturalWidth > img.naturalHeight ? 'is-landscape' : 'is-portrait'
}
</script>

<style scoped>
.result-split {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.result-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  border: 1px solid rgba(36, 54, 79, 0.08);
  border-radius: 16px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 12px 26px rgba(36, 54, 79, 0.05);
}

.result-summary span {
  display: block;
  color: #6e7885;
  font-size: 11px;
  font-weight: 800;
}

.result-summary strong {
  display: block;
  margin-top: 4px;
  color: #20242a;
  font-size: 15px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.result-summary .benefit strong {
  color: #15a34a;
}

.rs-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  border: 1px solid rgba(36, 54, 79, 0.08);
  border-radius: 18px;
  padding: 15px;
  background: #fff;
  box-shadow: 0 12px 24px rgba(36, 54, 79, 0.05);
}

.rs-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rs-head strong {
  color: #17202b;
  font-size: 13.5px;
  font-weight: 900;
  line-height: 1.3;
}

.rs-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex: 0 0 auto;
  border-radius: 999px;
  padding: 3px 9px;
  font-size: 11px;
  font-weight: 900;
}

.rs-badge.owned {
  background: rgba(15, 95, 174, 0.12);
  color: #0f5fae;
}

.rs-badge.issue {
  background: rgba(0, 140, 149, 0.13);
  color: #008c95;
}

.rs-item-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.rs-item-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 7px;
}

.rs-item-head strong {
  overflow: hidden;
  color: #17202b;
  font-size: 13.5px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rs-item-head b {
  flex: 0 0 auto;
  color: #20242a;
  font-size: 13px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.rs-options {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rs-option {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  border: 1px solid #e3e9f1;
  border-radius: 12px;
  padding: 9px 11px;
  background: #fff;
  text-align: left;
}

.rs-option.active {
  border-color: rgba(15, 95, 174, 0.5);
  background: #f1f7fd;
  box-shadow: inset 0 0 0 1px rgba(15, 95, 174, 0.35);
}

.rs-rank {
  flex: 0 0 auto;
  border-radius: 999px;
  padding: 2px 7px;
  font-size: 10px;
  font-weight: 900;
}

.rs-rank.r1 {
  background: rgba(15, 95, 174, 0.14);
  color: #0f5fae;
}

.rs-rank.r2 {
  background: rgba(36, 54, 79, 0.1);
  color: #6e7885;
}

.rs-opt-thumb {
  position: relative;
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 38px;
  height: 24px;
  overflow: hidden;
  border-radius: 5px;
  background: #e8edf2;
  color: #8a9aad;
  box-shadow: 0 1px 4px rgba(36, 54, 79, 0.2);
}

.rs-opt-thumb img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.rs-opt-thumb img.is-portrait {
  inset: auto;
  top: 50%;
  left: 50%;
  width: 24px;
  height: 38px;
  max-width: none;
  transform: translate(-50%, -50%) rotate(-90deg);
}

.rs-opt-name {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  color: #17202b;
  font-size: 12.5px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rs-opt-benefit {
  flex: 0 0 auto;
  color: #15a34a;
  font-size: 12.5px;
  font-weight: 900;
  font-style: normal;
}

.rs-card-list {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.rs-card {
  display: flex;
  align-items: center;
  gap: 11px;
  width: 100%;
  border-radius: 13px;
  padding: 11px 12px;
  text-align: left;
  background:
    linear-gradient(180deg, rgba(240, 253, 250, 0.7), rgba(255, 255, 255, 0.82));
  border: 1px solid rgba(0, 140, 149, 0.12);
}

.rs-card-thumb {
  position: relative;
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 44px;
  height: 28px;
  overflow: hidden;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.85);
  color: #008c95;
  box-shadow: 0 2px 8px rgba(36, 54, 79, 0.16);
}

.rs-card-thumb img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.rs-card-thumb img.is-portrait {
  inset: auto;
  top: 50%;
  left: 50%;
  width: 28px;
  height: 44px;
  max-width: none;
  transform: translate(-50%, -50%) rotate(-90deg);
}

.rs-card-body {
  flex: 1 1 auto;
  min-width: 0;
}

.rs-card-body strong {
  display: block;
  overflow: hidden;
  color: #17202b;
  font-size: 13.5px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rs-card-body small {
  display: block;
  margin-top: 2px;
  color: #6e7885;
  font-size: 11px;
  font-weight: 700;
}

.rs-event {
  display: inline-flex;
  align-items: center;
  margin-top: 5px;
  border-radius: 999px;
  padding: 2px 8px;
  background: rgba(217, 119, 6, 0.12);
  color: #b45309;
  font-size: 10.5px;
  font-weight: 900;
}

.rs-card-gain {
  flex: 0 0 auto;
  position: relative;
  padding-right: 16px;
  text-align: right;
}

.rs-card-gain b {
  display: block;
  color: #008c95;
  font-size: 14px;
  font-weight: 900;
}

.rs-card-gain span {
  display: block;
  color: #8a95a3;
  font-size: 10px;
  font-weight: 800;
}

.rs-card-go {
  position: absolute;
  top: 50%;
  right: -2px;
  color: #b6c2cf;
  transform: translateY(-50%);
}

.rs-note,
.rs-empty {
  margin: 0;
  color: #8a95a3;
  font-size: 11px;
  font-weight: 700;
}
</style>
