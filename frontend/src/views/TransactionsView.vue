<template>
  <section class="screen">
    <header class="simple-header blue-gradient">
      <AppBackButton fallback="/cards" />
      <div>
        <h1>거래내역</h1>
      </div>
    </header>
    <div class="screen-scroll scrollbar-hide page-padding">
      <template v-if="transactions.length">
        <section v-for="group in groupedByDate" :key="group.date" class="tx-group">
          <p class="tx-date">{{ dateLabel(group.date) }}</p>
          <article class="app-card tx-list">
            <button v-for="tx in group.items" :key="tx.id" type="button" @click="router.push(`/transactions/${tx.id}`)">
              <span class="tx-emoji">{{ tx.icon }}</span>
              <div class="tx-info">
                <strong>{{ tx.merchant }}</strong>
                <small>{{ tx.time }} · {{ tx.cat }}</small>
              </div>
              <span class="tx-mini-card">
                <img
                  v-if="txCard(tx)"
                  :src="txCard(tx).imageUrl"
                  :alt="txCard(tx).name"
                  :class="cardImageClass(txCard(tx))"
                  @load="setImageOrientation(txCard(tx)?.id, $event)"
                />
              </span>
              <b :class="{ plus: tx.amt > 0 }">{{ Math.abs(tx.amt).toLocaleString() }}원</b>
            </button>
          </article>
        </section>
      </template>

      <article v-else class="app-card tx-empty">
        <span class="tx-empty-icon">🧾</span>
        <strong>아직 거래내역이 없어요</strong>
        <p>결제 내역을 추가하면 날짜별로 모아서 보여드려요.</p>
        <RouterLink class="tx-empty-add" to="/transactions/new">결제 추가하기</RouterLink>
      </article>
    </div>

    <RouterLink class="floating-action-button" to="/transactions/new" aria-label="결제 추가">
      <Plus :size="20" />
    </RouterLink>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { cards as mockCards, krw, transactions as mockTransactions } from '@/data/mockData'
import { fetchOwnedCards, fetchTransactions, normalizeCard } from '@/services/api'

const router = useRouter()
const transactions = ref(mockTransactions)
const cards = ref(mockCards)
const imageOrientations = ref({})

// 날짜별로 묶어서 보여준다(원래 순서 유지)
const groupedByDate = computed(() => {
  const groups = []
  const byDate = new Map()
  for (const tx of transactions.value) {
    const key = tx.date || ''
    if (!byDate.has(key)) {
      byDate.set(key, { date: key, items: [] })
      groups.push(byDate.get(key))
    }
    byDate.get(key).items.push(tx)
  }
  return groups
})

function dateLabel(value) {
  const m = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2})$/)
  return m ? `${Number(m[2])}월 ${Number(m[3])}일` : (value || '날짜 미상')
}

function txCard(tx) {
  return cards.value.find((card) => String(card.id) === String(tx.cardId)) || null
}

function setImageOrientation(cardId, event) {
  if (cardId == null) return
  const image = event.target
  const orientation = image.naturalWidth > image.naturalHeight ? 'landscape' : 'portrait'
  imageOrientations.value = { ...imageOrientations.value, [cardId]: orientation }
}

function cardImageClass(card) {
  if (!card) return {}
  const orientation = imageOrientations.value[card.id] || card.imageOrientation
  return {
    'is-ready': Boolean(orientation),
    'is-landscape': orientation === 'landscape',
    'is-portrait': orientation === 'portrait',
  }
}

onMounted(async () => {
  try {
    const [apiTransactions, apiCards] = await Promise.all([fetchTransactions(), fetchOwnedCards()])
    transactions.value = apiTransactions
    cards.value = apiCards.map((card, index) => normalizeCard(card, index, apiTransactions))
  } catch (error) {
    console.warn('거래내역 API를 불러오지 못해 mock 데이터를 사용합니다.', error)
  }
})
</script>

<style scoped>
.simple-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 24px 20px;
  color: #fff;
}

.simple-header h1 {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 900;
}

.simple-header p {
  margin: 0;
  color: rgba(255, 255, 255, 0.68);
  font-size: 12px;
  font-weight: 700;
}

.page-padding {
  padding: 14px 20px 116px;
}

.tx-group {
  margin-bottom: 16px;
}

.tx-date {
  margin: 0 4px 8px;
  color: #8a96a5;
  font-size: 12px;
  font-weight: 800;
}

.tx-info {
  min-width: 0;
}

.tx-list {
  overflow: hidden;
}

.tx-list button {
  display: grid;
  width: 100%;
  grid-template-columns: 42px minmax(0, 1fr) 24px 92px;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(23, 32, 43, 0.075);
  padding: 14px 6px;
  background: transparent;
  color: #17202b;
  text-align: left;
}

.tx-list button > .tx-emoji {
  display: inline-flex;
  width: 42px;
  height: 42px;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  line-height: 1;
}

.tx-list button:last-child {
  border-bottom: 0;
}

.tx-mini-card {
  position: relative;
  display: block;
  justify-self: center;
  width: 15px;
  height: 24px;
  overflow: hidden;
  border-radius: 3px;
  background: #e8edf2;
  box-shadow: 0 1px 3px rgba(36, 54, 79, 0.2);
}

.tx-mini-card img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.tx-mini-card img.is-landscape {
  inset: auto;
  top: 50%;
  left: 50%;
  width: 24px;
  height: 15px;
  transform: translate(-50%, -50%) rotate(90deg);
}

.tx-list strong {
  display: block;
  color: #17202b;
  font-size: 13px;
  font-weight: 900;
}

.tx-list small {
  color: #6e6e73;
  font-size: 11px;
  font-weight: 700;
}

.tx-list b {
  color: #17202b;
  font-size: 13px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.tx-list b.plus {
  color: #008c95;
}

.tx-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  padding: 40px 24px;
  text-align: center;
}

.tx-empty-icon {
  font-size: 38px;
  line-height: 1;
  margin-bottom: 6px;
}

.tx-empty strong {
  color: #17202b;
  font-size: 16px;
  font-weight: 900;
}

.tx-empty p {
  margin: 0;
  color: #6e7885;
  font-size: 12.5px;
  font-weight: 600;
  line-height: 1.5;
}

.tx-empty-add {
  display: inline-flex;
  align-items: center;
  min-height: 40px;
  margin-top: 12px;
  padding: 0 20px;
  border-radius: 999px;
  background: #0f5fae;
  color: #fff;
  font-size: 13px;
  font-weight: 800;
  text-decoration: none;
}
</style>
