<template>
  <section class="screen">
    <header class="simple-header blue-gradient">
      <AppBackButton fallback="/cards" />
      <div>
        <h1>거래내역</h1>
        <p>최근 카드 사용 내역을 확인하세요.</p>
      </div>
    </header>
    <div class="screen-scroll scrollbar-hide page-padding">
      <article class="app-card tx-list">
        <button v-for="tx in transactions" :key="tx.id" type="button" @click="router.push(`/transactions/${tx.id}`)">
          <span class="tx-emoji">{{ tx.icon }}</span>
          <div>
            <strong>{{ tx.merchant }}</strong>
            <small>{{ tx.date }} {{ tx.time }} · {{ tx.cat }}</small>
          </div>
          <span class="tx-mini-card">
            <img
              v-if="txCard(tx)"
              :src="txCard(tx).imageUrl"
              :alt="txCard(tx).name"
              :class="cardImageClass(txCard(tx))"
              @load="setImageOrientation(txCard(tx).id, $event)"
            />
          </span>
          <b :class="{ plus: tx.amt > 0 }">{{ tx.amt > 0 ? '+' : '-' }}{{ krw(tx.amt) }}</b>
        </button>
      </article>
    </div>

    <RouterLink class="floating-action-button" to="/transactions/new" aria-label="결제 추가">
      <Plus :size="20" />
    </RouterLink>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { cards as mockCards, krw, transactions as mockTransactions } from '@/data/mockData'
import { fetchTransactions } from '@/services/api'

const router = useRouter()
const transactions = ref(mockTransactions)
const cards = ref(mockCards)
const imageOrientations = ref({})

function txCard(tx) {
  return cards.value.find((card) => String(card.id) === String(tx.cardId)) || null
}

function setImageOrientation(cardId, event) {
  const image = event.target
  const orientation = image.naturalWidth > image.naturalHeight ? 'landscape' : 'portrait'
  imageOrientations.value = { ...imageOrientations.value, [cardId]: orientation }
}

function cardImageClass(card) {
  const orientation = imageOrientations.value[card.id]
  return {
    'is-ready': Boolean(orientation),
    'is-landscape': orientation === 'landscape',
    'is-portrait': orientation === 'portrait',
  }
}

onMounted(async () => {
  try {
    transactions.value = await fetchTransactions()
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
  padding: 18px 20px 116px;
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
  font-weight: 900;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.tx-list b.plus {
  color: #008c95;
}
</style>
