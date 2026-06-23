<template>
  <section class="screen">
    <header class="simple-header blue-gradient">
      <AppBackButton fallback="/cards" />
      <div>
        <h1>카드 소비 분석</h1>
        <p>최근 결제 내역을 AI가 요약하고 다음 행동을 제안합니다.</p>
      </div>
      <span v-if="aiAnalysis" class="ai-pill">{{ aiAnalysis.aiMode === 'gms' ? 'AI 분석' : '기본 분석' }}</span>
    </header>

    <div class="screen-scroll scrollbar-hide page-padding">
      <div v-if="error" class="notice-card">{{ error }}</div>
      <div v-if="isLoading" class="notice-card">분석 결과를 불러오는 중입니다.</div>

      <div class="metric-grid">
        <article class="app-card">
          <span>총 지출</span>
          <strong>{{ krw(totalExpense) }}</strong>
        </article>
        <article class="app-card">
          <span>예상 절감</span>
          <strong class="success">{{ krw(expectedSaving) }}</strong>
        </article>
      </div>

      <div v-if="aiAnalysis?.summaryCards?.length" class="ai-summary-grid">
        <article
          v-for="card in aiAnalysis.summaryCards"
          :key="`${card.label}-${card.value}`"
          class="app-card ai-summary-card"
          :class="`tone-${card.tone || 'gray'}`"
        >
          <span>{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
          <small v-if="card.caption">{{ card.caption }}</small>
        </article>
      </div>

      <article v-if="aiAnalysis" class="app-card ai-card">
        <div class="section-title">
          <span>{{ aiAnalysis.summaryTitle }}</span>
          <small>신뢰도 {{ Math.round(Number(aiAnalysis.confidence || 0) * 100) }}%</small>
        </div>
        <div v-if="aiAnalysis.primaryInsight" class="primary-insight" :class="`severity-${aiAnalysis.primaryInsight.severity || 'info'}`">
          <div>
            <span>{{ aiAnalysis.primaryInsight.label }}</span>
            <strong>{{ aiAnalysis.primaryInsight.title }}</strong>
            <p>{{ aiAnalysis.primaryInsight.body }}</p>
          </div>
          <em v-if="aiAnalysis.primaryInsight.metricValue">
            {{ krw(aiAnalysis.primaryInsight.metricValue) }}
          </em>
        </div>
        <h2>{{ aiAnalysis.headline }}</h2>
        <p v-if="aiAnalysis.narrative" class="ai-narrative">{{ aiAnalysis.narrative }}</p>
        <ul class="insight-list">
          <li v-for="item in aiAnalysis.savingOpportunities" :key="item.title">
            <strong>{{ item.title }}</strong>
            <span>{{ item.reason }}</span>
            <em>{{ item.action }}</em>
          </li>
        </ul>
      </article>

      <article v-if="recommendationAlert?.show && topRecommendation" class="app-card card-switch-card">
        <div class="section-title">
          <span>카드 교체 인사이트</span>
          <small>{{ topRecommendation.match }}% 매칭</small>
        </div>
        <strong>{{ recommendationAlert.title }}</strong>
        <p>{{ recommendationAlert.body }}</p>
        <div class="switch-metrics">
          <span>
            <small>월 순혜택 차이</small>
            <b>{{ krw(topRecommendation.economics.monthlyDelta) }}</b>
          </span>
          <span>
            <small>연간 예상 차이</small>
            <b>{{ krw(topRecommendation.economics.annualDelta) }}</b>
          </span>
          <span>
            <small>회수 기간</small>
            <b>{{ topRecommendation.economics.paybackMonths ? `${topRecommendation.economics.paybackMonths}개월` : '즉시 비교' }}</b>
          </span>
        </div>
        <RouterLink class="switch-link" :to="`/recommendations/r1`">
          추천 카드 자세히 보기
        </RouterLink>
      </article>

      <article class="app-card chart-card">
        <div class="section-title">
          <span>카테고리별 지출</span>
          <small>{{ categoryRows.length }}개 항목</small>
        </div>
        <div v-for="category in categoryRows" :key="category.category" class="bar-row">
          <span>{{ category.category }}</span>
          <div><i :style="{ width: `${category.percent}%`, background: category.color }" /></div>
          <strong>{{ krw(category.amount) }}</strong>
        </div>
      </article>

      <article v-if="aiAnalysis?.categoryInsights?.length" class="app-card insight-card">
        <div class="section-title">
          <span>AI 카테고리 해석</span>
        </div>
        <ul class="compact-list">
          <li v-for="item in aiAnalysis.categoryInsights" :key="`${item.category}-${item.amount}`">
            <strong>{{ item.category }}</strong>
            <span>{{ item.insight }}</span>
          </li>
        </ul>
      </article>

      <article v-if="aiAnalysis?.nextActions?.length || aiAnalysis?.actionButtons?.length" class="app-card action-card">
        <div class="section-title">
          <span>다음 행동</span>
        </div>
        <div class="action-chips">
          <span v-for="action in aiAnalysis.nextActions" :key="action">{{ action }}</span>
        </div>
        <div v-if="aiAnalysis.actionButtons?.length" class="action-buttons">
          <RouterLink v-for="button in aiAnalysis.actionButtons" :key="`${button.label}-${button.route}`" :to="button.route">
            {{ button.label }}
          </RouterLink>
        </div>
      </article>

      <article v-if="analysisRecords.length" class="app-card record-card">
        <div class="section-title">
          <span>저장된 AI 분석</span>
          <small>DB 저장 {{ analysisRecords.length }}건</small>
        </div>
        <ul class="record-list">
          <li v-for="record in analysisRecords" :key="record.id">
            <div>
              <strong>{{ record.title || '카드 소비 분석' }}</strong>
              <span>{{ record.resultPayload?.headline || '분석 결과가 저장되었습니다.' }}</span>
            </div>
            <em>{{ formatRecordTime(record.createdAt) }}</em>
          </li>
        </ul>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import AppBackButton from '@/components/AppBackButton.vue'
import { krw, transactions as mockTransactions } from '@/data/mockData'
import { fetchAnalysisRecords, fetchCardRecommendationBundle, fetchSpendingSummary } from '@/services/api'

const colors = ['#0f5fae', '#008c95', '#24364f', '#8a9aad', '#c49a49', '#5f6b77']
const summary = ref(null)
const analysisRecords = ref([])
const recommendationBundle = ref(null)
const isLoading = ref(false)
const error = ref('')

const safeSummary = computed(() => summary.value || { totalExpense: 0, totalIncome: 0, byCategory: [], byCard: [] })
const aiAnalysis = computed(() => safeSummary.value.aiAnalysis || null)
const totalExpense = computed(() => Number(safeSummary.value.totalExpense || 0))
const expectedSaving = computed(() =>
  (aiAnalysis.value?.savingOpportunities || []).reduce((sum, item) => sum + Number(item.amount || 0), 0),
)
const topRecommendation = computed(() => recommendationBundle.value?.results?.[0] || null)
const recommendationAlert = computed(() => recommendationBundle.value?.alert || null)
const categoryRows = computed(() => {
  const rows = [...(safeSummary.value.byCategory || [])].sort((a, b) => Number(b.amount || 0) - Number(a.amount || 0))
  const max = Math.max(...rows.map((item) => Number(item.amount || 0)), 1)
  return rows.map((item, index) => ({
    ...item,
    percent: Math.max(6, Math.round((Number(item.amount || 0) / max) * 100)),
    color: colors[index % colors.length],
  }))
})

function buildMockSummary() {
  const expenses = mockTransactions.filter((tx) => Number(tx.amt) < 0)
  const categoryMap = new Map()
  expenses.forEach((tx) => {
    categoryMap.set(tx.cat, (categoryMap.get(tx.cat) || 0) + Math.abs(Number(tx.amt) || 0))
  })
  const byCategory = [...categoryMap.entries()].map(([category, amount]) => ({ category, amount }))
  const totalExpense = expenses.reduce((sum, tx) => sum + Math.abs(Number(tx.amt) || 0), 0)

  return {
    totalExpense,
    totalIncome: mockTransactions
      .filter((tx) => Number(tx.amt) > 0)
      .reduce((sum, tx) => sum + Number(tx.amt || 0), 0),
    byCategory,
    byCard: [],
    aiAnalysis: {
      aiMode: 'mock',
      summaryTitle: '예시 분석',
      confidence: 0.78,
      headline: '쇼핑과 마트 지출 비중이 높아 카드 혜택 점검 여지가 있어요.',
      savingOpportunities: [
        {
          title: '쇼핑 결제 카드 재배치',
          reason: '쿠팡과 온라인 쇼핑 지출이 가장 크게 잡혀 있습니다.',
          action: '카드의정석2 SHOPPER 혜택 한도부터 확인하세요.',
          amount: 12000,
        },
        {
          title: '마트 지출 묶어서 관리',
          reason: '마트 결제는 이마트 신한카드 혜택과 맞물릴 수 있습니다.',
          action: '월 예산의 마트 항목과 카드 실적을 같이 보세요.',
          amount: 8000,
        },
      ],
      categoryInsights: byCategory.slice(0, 3).map((item) => ({
        category: item.category,
        amount: item.amount,
        insight: `${item.category} 지출은 이번 달 카드 혜택 후보로 먼저 확인해볼 만합니다.`,
      })),
      nextActions: ['결제내역 보정하기', '목표 지출 계획 만들기', '추천 카드 다시 보기'],
    },
  }
}

async function loadSummary() {
  isLoading.value = true
  error.value = ''
  try {
    summary.value = await fetchSpendingSummary({ ai: true })
    const [records, recommendations] = await Promise.all([
      fetchAnalysisRecords({ type: 'spending_summary', limit: 3 }),
      fetchCardRecommendationBundle(),
    ])
    analysisRecords.value = records
    recommendationBundle.value = recommendations
  } catch {
    summary.value = buildMockSummary()
    analysisRecords.value = []
    recommendationBundle.value = null
    error.value = '백엔드 연결 전이라 예시 소비 데이터로 분석을 보여드려요.'
  } finally {
    isLoading.value = false
  }
}

function formatRecordTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('ko-KR', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

onMounted(loadSummary)
</script>

<style scoped>
.simple-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
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
  color: rgba(255, 255, 255, 0.72);
  font-size: 12px;
  font-weight: 700;
  line-height: 1.45;
}

.ai-pill {
  flex: 0 0 auto;
  border-radius: 999px;
  padding: 6px 10px;
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
  font-size: 11px;
  font-weight: 900;
}

.page-padding {
  padding: 18px 20px 28px;
}

.notice-card {
  margin-bottom: 12px;
  border-radius: 14px;
  padding: 12px 14px;
  background: #eef4ff;
  color: #0f5fae;
  font-size: 12px;
  font-weight: 800;
}

.metric-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
}

.metric-grid article,
.chart-card,
.ai-card,
.insight-card,
.action-card {
  padding: 16px;
}

.metric-grid span {
  color: #6e6e73;
  font-size: 12px;
  font-weight: 800;
}

.metric-grid strong {
  display: block;
  color: #17202b;
  font-size: 19px;
  font-weight: 900;
}

.success {
  color: #008c95 !important;
}

.ai-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.ai-summary-card {
  padding: 14px;
  border-color: rgba(36, 54, 79, 0.09);
  background: rgba(255, 255, 255, 0.72);
}

.ai-summary-card span {
  display: block;
  color: #6e6e73;
  font-size: 11px;
  font-weight: 900;
}

.ai-summary-card strong {
  display: block;
  margin-top: 4px;
  color: #17202b;
  font-size: 17px;
  font-weight: 900;
}

.ai-summary-card small {
  display: block;
  margin-top: 3px;
  color: #8a9aad;
  font-size: 10px;
  font-weight: 800;
}

.ai-summary-card.tone-teal strong {
  color: #008c95;
}

.ai-summary-card.tone-gold strong {
  color: #a66f00;
}

.primary-insight {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: start;
  margin-bottom: 12px;
  border: 1px solid rgba(15, 95, 174, 0.12);
  border-radius: 14px;
  padding: 12px;
  background: rgba(232, 241, 255, 0.62);
}

.primary-insight span {
  color: #0f5fae;
  font-size: 10px;
  font-weight: 900;
}

.primary-insight strong {
  display: block;
  margin-top: 3px;
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
}

.primary-insight p,
.ai-narrative {
  margin: 4px 0 0;
  color: #5f6b77;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.5;
  word-break: keep-all;
}

.primary-insight em {
  color: #0f5fae;
  font-size: 13px;
  font-style: normal;
  font-weight: 900;
  white-space: nowrap;
}

.primary-insight.severity-warning {
  border-color: rgba(220, 38, 38, 0.15);
  background: rgba(254, 242, 242, 0.72);
}

.primary-insight.severity-warning span,
.primary-insight.severity-warning em {
  color: #dc2626;
}

.card-switch-card {
  margin-bottom: 12px;
  padding: 16px;
  border-color: rgba(0, 140, 149, 0.18);
  background: linear-gradient(180deg, rgba(240, 253, 250, 0.82), rgba(255, 255, 255, 0.78));
}

.card-switch-card > strong {
  display: block;
  color: #17202b;
  font-size: 16px;
  font-weight: 900;
}

.card-switch-card > p {
  margin: 6px 0 0;
  color: #5f6b77;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.5;
}

.switch-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-top: 13px;
}

.switch-metrics span {
  min-width: 0;
  border-radius: 12px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.72);
}

.switch-metrics small {
  display: block;
  color: #6e6e73;
  font-size: 10px;
  font-weight: 900;
}

.switch-metrics b {
  display: block;
  margin-top: 3px;
  color: #008c95;
  font-size: 12px;
  font-weight: 900;
  word-break: keep-all;
}

.switch-link {
  display: inline-flex;
  min-height: 40px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  margin-top: 13px;
  padding: 10px 13px;
  background: #17202b;
  color: #fff;
  font-size: 12px;
  font-weight: 900;
  text-decoration: none;
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
}

.section-title span {
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
}

.section-title small {
  color: #6e6e73;
  font-size: 11px;
  font-weight: 800;
}

h2 {
  margin: 0 0 12px;
  color: #17202b;
  font-size: 16px;
  font-weight: 900;
  line-height: 1.4;
}

.insight-list,
.compact-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0;
  margin: 0;
  list-style: none;
}

.insight-list li,
.compact-list li {
  display: flex;
  flex-direction: column;
  gap: 3px;
  border-radius: 12px;
  padding: 11px 12px;
  background: #fbfdff;
}

.insight-list strong,
.compact-list strong {
  color: #17202b;
  font-size: 12px;
  font-weight: 900;
}

.insight-list span,
.compact-list span {
  color: #5f6b77;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.45;
}

.insight-list em {
  color: #0f5fae;
  font-size: 11px;
  font-style: normal;
  font-weight: 900;
}

.chart-card,
.insight-card,
.action-card,
.record-card {
  margin-top: 12px;
}

.bar-row {
  display: grid;
  grid-template-columns: 54px 1fr 84px;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 800;
}

.bar-row:last-child {
  margin-bottom: 0;
}

.bar-row div {
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: #e7edf4;
}

.bar-row i {
  display: block;
  height: 100%;
  border-radius: inherit;
}

.bar-row strong {
  color: #17202b;
  text-align: right;
}

.action-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.action-chips span {
  border-radius: 999px;
  padding: 8px 10px;
  background: #f4f7ff;
  color: #0f5fae;
  font-size: 12px;
  font-weight: 900;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.action-buttons a {
  min-height: 38px;
  border-radius: 999px;
  padding: 10px 12px;
  background: #17202b;
  color: #fff;
  font-size: 12px;
  font-weight: 900;
  text-decoration: none;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 9px;
  padding: 0;
  margin: 0;
  list-style: none;
}

.record-list li {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: start;
  border-radius: 10px;
  padding: 11px 12px;
  background: #f6f8fb;
}

.record-list strong {
  display: block;
  overflow: hidden;
  color: #17202b;
  font-size: 12px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-list span {
  display: -webkit-box;
  margin-top: 3px;
  overflow: hidden;
  color: #5f6b77;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.45;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.record-list em {
  color: #6e6e73;
  font-size: 10px;
  font-style: normal;
  font-weight: 800;
  white-space: nowrap;
}
</style>
