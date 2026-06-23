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
          <span>{{ tx.icon }}</span>
          <div>
            <strong>{{ tx.merchant }}</strong>
            <small>{{ tx.date }} {{ tx.time }} · {{ tx.cat }}</small>
          </div>
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
import { krw, transactions as mockTransactions } from '@/data/mockData'
import { fetchTransactions } from '@/services/api'

const router = useRouter()
const transactions = ref(mockTransactions)

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
  grid-template-columns: 32px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(23, 32, 43, 0.075);
  padding: 13px 14px;
  background: transparent;
  color: #17202b;
  text-align: left;
}

.tx-list button > span:first-child {
  display: inline-flex;
  width: 32px;
  height: 32px;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  line-height: 1;
}

.tx-list button:last-child {
  border-bottom: 0;
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
}

.tx-list b.plus {
  color: #008c95;
}
</style>
