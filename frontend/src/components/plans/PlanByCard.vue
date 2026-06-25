<template>
  <section class="by-card">
    <div class="bc-head">
      <h3>카드별 구매 계획</h3>
      <span class="bc-total">예상 혜택 <b>+{{ krw(totalBenefit) }}</b></span>
    </div>

    <!-- 카드별 금액 배분 그래프 -->
    <div v-if="total > 0" class="bc-bar">
      <i
        v-for="g in groups"
        :key="g.card"
        class="bc-seg"
        :style="{ width: pct(g.amount), background: g.color }"
      />
    </div>

    <div class="bc-list">
      <article v-for="g in groups" :key="g.card" class="cardgroup app-card" :style="{ '--c': g.color }">
        <header class="cg-head">
          <span class="cg-thumb">
            <img
              v-if="g.image"
              :src="g.image"
              :alt="g.card"
              :class="ori[g.card]"
              @load="onThumb($event, g.card)"
            />
            <CreditCard v-else :size="16" />
          </span>
          <div class="cg-name">
            <strong>{{ g.card }}</strong>
            <span class="cg-sub">{{ g.items.length }}개 · {{ krw(g.amount) }}</span>
          </div>
          <span class="cg-badge" :class="g.achieved ? 'ok' : 'low'">
            <component :is="g.achieved ? CheckCircle2 : AlertCircle" :size="12" />
            {{ g.achieved ? '조건 충족' : '조건 부족' }}
          </span>
        </header>

        <div class="cg-benefit">
          <Sparkles :size="13" />
          <span>이 카드 예상 혜택</span>
          <b>+{{ krw(g.benefit) }}</b>
        </div>

        <ul class="cg-items">
          <li v-for="(it, i) in g.items" :key="i" class="cg-item">
            <span class="cg-dot" />
            <span class="cg-item-name">{{ it.name }}</span>
            <span class="cg-item-amt">{{ krw(it.amount) }}</span>
            <em class="cg-item-ben">+{{ krw(it.benefit) }}</em>
          </li>
        </ul>
      </article>
    </div>
    <p v-if="!groups.length" class="bc-empty">카드 배정 내역이 없습니다.</p>
  </section>
</template>

<script setup>
import { computed, reactive } from 'vue'
import { AlertCircle, CheckCircle2, CreditCard, Sparkles } from 'lucide-vue-next'
import { cards as mockCards, krw } from '@/data/mockData'

const props = defineProps({
  scenario: { type: Object, default: null },
})

const PALETTE = ['#0f5fae', '#008c95', '#d97706', '#7c3aed', '#dc2626', '#0891b2']

// 월별 배정을 같은 카드끼리 묶어 금액 큰 순으로 정렬
const groups = computed(() => {
  const sc = props.scenario
  if (!sc) return []
  const summaryByName = {}
  for (const c of (sc.cardSummary || [])) summaryByName[c.cardName] = c
  const map = {}
  const order = []
  for (const month of (sc.monthlyPlan || [])) {
    for (const it of (month.items || [])) {
      if (!map[it.card]) {
        map[it.card] = { card: it.card, items: [], amount: 0, benefit: 0 }
        order.push(it.card)
      }
      const g = map[it.card]
      g.items.push(it)
      g.amount += Number(it.amount || 0)
      g.benefit += Number(it.benefit || 0)
    }
  }
  return order
    .map((name) => map[name])
    .sort((a, b) => b.amount - a.amount)
    .map((g, i) => ({
      ...g,
      color: PALETTE[i % PALETTE.length],
      image: mockCards.find((c) => c?.name === g.card)?.imageUrl || '',
      achieved: Boolean(summaryByName[g.card]?.achieved),
    }))
})

const total = computed(() => groups.value.reduce((sum, g) => sum + g.amount, 0))
const totalBenefit = computed(() => groups.value.reduce((sum, g) => sum + g.benefit, 0))
const pct = (value) => (total.value > 0 ? `${((value / total.value) * 100).toFixed(1)}%` : '0%')

const ori = reactive({})
function onThumb(event, name) {
  const img = event.target
  ori[name] = img.naturalWidth > img.naturalHeight ? 'is-landscape' : 'is-portrait'
}
</script>

<style scoped>
.by-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bc-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}

.bc-head h3 {
  margin: 0;
  color: #17202b;
  font-size: 15px;
  font-weight: 900;
}

.bc-total {
  color: #6e7885;
  font-size: 12px;
  font-weight: 800;
}

.bc-total b {
  color: #15a34a;
  font-weight: 900;
}

.bc-bar {
  display: flex;
  height: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: #eef2f7;
  box-shadow: inset 0 1px 2px rgba(36, 54, 79, 0.08);
}

.bc-seg + .bc-seg {
  box-shadow: inset 1px 0 0 rgba(255, 255, 255, 0.7);
}

.bc-list {
  display: flex;
  flex-direction: column;
  gap: 11px;
}

.cardgroup {
  padding: 14px;
  border-left: 3px solid var(--c);
}

.cg-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.cg-thumb {
  position: relative;
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 46px;
  height: 29px;
  overflow: hidden;
  border-radius: 6px;
  background: #e8edf2;
  color: #8a9aad;
  box-shadow: 0 2px 8px rgba(36, 54, 79, 0.18);
}

.cg-thumb img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cg-thumb img.is-portrait {
  inset: auto;
  top: 50%;
  left: 50%;
  width: 29px;
  height: 46px;
  max-width: none;
  transform: translate(-50%, -50%) rotate(-90deg);
}

.cg-name {
  flex: 1 1 auto;
  min-width: 0;
}

.cg-name strong {
  display: block;
  overflow: hidden;
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cg-sub {
  display: block;
  margin-top: 2px;
  color: #6e7885;
  font-size: 11.5px;
  font-weight: 700;
}

.cg-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  flex: 0 0 auto;
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 10.5px;
  font-weight: 900;
}

.cg-badge.ok {
  background: #f0fdf4;
  color: #16a34a;
}

.cg-badge.low {
  background: #fffaeb;
  color: #b54708;
}

.cg-benefit {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  border-radius: 11px;
  padding: 9px 11px;
  background: color-mix(in srgb, var(--c) 9%, #fff);
  color: var(--c);
}

.cg-benefit span {
  flex: 1 1 auto;
  font-size: 12px;
  font-weight: 800;
}

.cg-benefit b {
  color: #15a34a;
  font-size: 14px;
  font-weight: 900;
  font-variant-numeric: tabular-nums;
}

.cg-items {
  margin: 12px 0 0;
  padding: 0;
  list-style: none;
}

.cg-item {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 8px 0;
  border-top: 1px solid rgba(36, 54, 79, 0.07);
}

.cg-dot {
  flex: 0 0 auto;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--c);
}

.cg-item-name {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  color: #2b3a4d;
  font-size: 13px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cg-item-amt {
  flex: 0 0 auto;
  color: #5f6b77;
  font-size: 12.5px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.cg-item-ben {
  flex: 0 0 auto;
  min-width: 56px;
  color: #15a34a;
  font-size: 12.5px;
  font-weight: 900;
  font-style: normal;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.bc-empty {
  margin: 0;
  color: #8a95a3;
  font-size: 13px;
  font-weight: 700;
}
</style>
