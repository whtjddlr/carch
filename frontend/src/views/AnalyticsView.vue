<template>
  <section class="screen">
    <header class="simple-header blue-gradient">
      <AppBackButton fallback="/cards" />
      <div>
        <h1>카드 소비 분석</h1>
        <p>최근 소비 흐름을 정리하고 더 나은 카드 선택 기준을 제안합니다.</p>
      </div>
      <div class="insight-control">
        <span v-if="aiAnalysis" class="ai-pill">
          <Sparkles :size="13" :stroke-width="2.2" />
          {{ aiBadgeLabel }}
        </span>
        <button
          class="refresh-analysis-button"
          type="button"
          :disabled="isRefreshing"
          :aria-label="analysisButtonLabel"
          :title="analysisButtonLabel"
          @click="refreshAnalysis"
        >
          <RefreshCw :size="15" :stroke-width="2.2" :class="{ spinning: isRefreshing }" />
        </button>
      </div>
    </header>

    <div class="screen-scroll scrollbar-hide page-padding">
      <div v-if="error" class="notice-card">{{ error }}</div>
      <div v-if="isLoading" class="notice-card">최신 소비 인사이트를 준비하고 있습니다.</div>
      <div v-if="isRefreshing" class="notice-card">새로운 소비 인사이트를 정리하고 있습니다.</div>

      <div class="metric-grid">
        <article class="app-card">
          <span>총 지출</span>
          <strong>{{ krw(totalExpense) }}</strong>
        </article>
        <article class="app-card">
          <span>예상 절감액</span>
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
          <span>이번 달 소비 인사이트</span>
          <small>분석 신뢰도 {{ Math.round(Number(aiAnalysis.confidence || 0) * 100) }}%</small>
        </div>
        <div class="primary-insight compact" :class="`severity-${aiAnalysis.primaryInsight?.severity || 'info'}`">
          <div>
            <span>{{ conciseDiagnosis.label }}</span>
            <strong>{{ conciseDiagnosis.title }}</strong>
            <p>{{ conciseDiagnosis.body }}</p>
          </div>
          <em v-if="conciseDiagnosis.amount">
            {{ krw(conciseDiagnosis.amount) }}
          </em>
        </div>
        <ul class="diagnosis-points">
          <li v-for="point in conciseInsightItems" :key="point">
            <span></span>
            <strong>{{ point }}</strong>
          </li>
        </ul>
      </article>
      <article v-else class="app-card empty-analysis-card">
        <span>분석 준비 중</span>
        <strong>소비 인사이트를 준비하고 있습니다.</strong>
        <p>최초 분석 이후에는 저장된 결과를 바탕으로 안정적으로 제공합니다.</p>
      </article>

      <article v-if="recommendationAlert?.show && topRecommendation" class="app-card card-switch-card">
        <div class="section-title">
          <span>카드 교체 인사이트</span>
          <small>{{ topRecommendation.match }}% 매칭</small>
        </div>
        <div class="switch-hero">
          <div class="switch-card-preview">
            <img v-if="topRecommendation.imageUrl" :src="topRecommendation.imageUrl" :alt="topRecommendation.name" />
            <div v-else class="switch-card-fallback">
              <small>{{ topRecommendation.issuer }}</small>
              <strong>{{ topRecommendation.name }}</strong>
            </div>
          </div>
          <div>
            <strong>{{ cardSwitchTitle }}</strong>
            <p>{{ cardSwitchBody }}</p>
          </div>
        </div>
        <div class="switch-metrics">
          <span>
            <small>월 예상 개선</small>
            <b>{{ signedKrw(topRecommendation.economics.monthlyDelta) }}</b>
          </span>
          <span>
            <small>연간 예상 개선</small>
            <b>{{ signedKrw(topRecommendation.economics.annualDelta) }}</b>
          </span>
          <span>
            <small>비교 기준</small>
            <b>연회비 포함</b>
          </span>
        </div>
        <RouterLink class="switch-link" :to="`/recommendations/r1`">
          추천 카드 살펴보기
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
          <span>카테고리별 해석</span>
          <small>주요 지출 기준</small>
        </div>
        <ul class="compact-list">
          <li v-for="item in aiAnalysis.categoryInsights" :key="`${item.category}-${item.amount}`">
            <div>
              <strong>{{ item.category }}</strong>
              <small>{{ krw(item.amount) }}</small>
            </div>
            <span>{{ item.insight }}</span>
          </li>
        </ul>
      </article>

      <article v-if="nextActionItems.length" class="app-card next-summary-card">
        <div class="section-title">
          <span>우선 검토 항목</span>
          <small>권장 순서</small>
        </div>
        <ul class="next-summary-list">
          <li v-for="(action, index) in nextActionItems" :key="`${action}-${index}`">
            <span>{{ index + 1 }}</span>
            <strong>{{ action }}</strong>
          </li>
        </ul>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RefreshCw, Sparkles } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { krw, transactions as mockTransactions } from '@/data/mockData'
import { fetchCardRecommendationBundle, fetchSpendingSummary } from '@/services/api'

const colors = ['#0f5fae', '#008c95', '#24364f', '#8a9aad', '#c49a49', '#5f6b77']
const summary = ref(null)
const recommendationBundle = ref(null)
const isLoading = ref(false)
const isRefreshing = ref(false)
const error = ref('')

const safeSummary = computed(() => summary.value || { totalExpense: 0, totalIncome: 0, byCategory: [], byCard: [] })
const aiAnalysis = computed(() => safeSummary.value.aiAnalysis || null)
const totalExpense = computed(() => Number(safeSummary.value.totalExpense || 0))
const expectedSaving = computed(() =>
  (aiAnalysis.value?.savingOpportunities || []).reduce((sum, item) => sum + Number(item.amount || 0), 0),
)
const topRecommendation = computed(() => recommendationBundle.value?.results?.[0] || null)
const recommendationAlert = computed(() => recommendationBundle.value?.alert || null)
const analysisButtonLabel = computed(() => {
  if (isRefreshing.value) return '분석 중'
  return aiAnalysis.value ? '인사이트 갱신' : '인사이트 생성'
})
const aiBadgeLabel = computed(() => {
  if (!aiAnalysis.value) return ''
  return aiAnalysis.value.aiMode === 'gms' ? 'AI 인사이트' : '기본 인사이트'
})
const nextActionItems = computed(() => (aiAnalysis.value?.nextActions || []).slice(0, 3))
const categoryRows = computed(() => {
  const rows = [...(safeSummary.value.byCategory || [])].sort((a, b) => Number(b.amount || 0) - Number(a.amount || 0))
  const max = Math.max(...rows.map((item) => Number(item.amount || 0)), 1)
  return rows.map((item, index) => ({
    ...item,
    percent: Math.max(6, Math.round((Number(item.amount || 0) / max) * 100)),
    color: colors[index % colors.length],
  }))
})
const conciseDiagnosis = computed(() => {
  const primary = aiAnalysis.value?.primaryInsight || {}
  const top = categoryRows.value[0]
  const second = categoryRows.value[1]
  const categoryText = [top?.category, second?.category].filter(Boolean).join('·')
  return {
    label: primary.label || '핵심 포인트',
    title: primary.title || (top ? `${top.category} 지출 비중 확대` : '소비 패턴 점검'),
    body: categoryText
      ? `${categoryText} 지출 비중이 높습니다. 해당 영역의 혜택 조건을 우선 검토하는 편이 유리합니다.`
      : '최근 소비를 기준으로 카드 혜택 조건을 재점검해 보시기 바랍니다.',
    amount: primary.metricValue || top?.amount || 0,
  }
})
const conciseInsightItems = computed(() => {
  const items = []
  const top = categoryRows.value[0]
  const second = categoryRows.value[1]
  if (top) items.push(`${top.category} 혜택 조건이 우수한 카드부터 비교해 보세요.`)
  if (second) items.push(`${second.category} 지출까지 함께 반영해 비교하는 것을 권장합니다.`)
  if (topRecommendation.value?.economics?.monthlyDelta > 0) {
    items.push(`${topRecommendation.value.name} 기준 월 ${signedKrw(topRecommendation.value.economics.monthlyDelta)} 개선 여지가 있습니다.`)
  }
  return items.slice(0, 3)
})
const cardSwitchTitle = computed(() => `${topRecommendation.value?.name || '추천 카드'}의 혜택 조건이 더 적합합니다`)
const cardSwitchBody = computed(() => {
  const delta = topRecommendation.value?.economics?.monthlyDelta || 0
  return `연회비를 반영해도 월 ${signedKrw(delta)} 수준의 개선 효과가 예상됩니다.`
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
      headline: '쇼핑과 마트 지출 비중이 높아 카드 혜택 조건 점검이 필요합니다.',
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
    if (!summary.value?.aiAnalysis && summary.value?.aiAnalysisStatus === 'empty') {
      summary.value = await fetchSpendingSummary({ ai: true, refresh: true })
    }
    const recommendations = await fetchCardRecommendationBundle()
    recommendationBundle.value = recommendations
  } catch {
    summary.value = buildMockSummary()
    recommendationBundle.value = null
    error.value = '백엔드 연결 전이므로 예시 소비 데이터 기반 인사이트를 제공합니다.'
  } finally {
    isLoading.value = false
  }
}

async function refreshAnalysis() {
  if (isRefreshing.value) return
  isRefreshing.value = true
  error.value = ''
  try {
    summary.value = await fetchSpendingSummary({ ai: true, refresh: true })
  } catch {
    error.value = '새 인사이트를 저장하지 못했습니다. 잠시 후 다시 시도해 주세요.'
  } finally {
    isRefreshing.value = false
  }
}

function signedKrw(value) {
  const amount = Number(value || 0)
  return `${amount > 0 ? '+' : amount < 0 ? '-' : ''}${krw(Math.abs(amount))}`
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

.insight-control {
  display: inline-flex;
  min-height: 40px;
  flex: 0 0 auto;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 999px;
  padding: 4px;
  background: rgba(255, 255, 255, 0.12);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(12px);
}

.ai-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 0 8px 0 10px;
  color: #fff;
  font-size: 11px;
  font-weight: 900;
  white-space: nowrap;
}

.refresh-analysis-button {
  display: inline-flex;
  width: 32px;
  height: 32px;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 50%;
  padding: 0;
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
  box-shadow: 0 8px 18px rgba(7, 15, 28, 0.14);
  touch-action: manipulation;
}

.refresh-analysis-button:hover {
  background: rgba(255, 255, 255, 0.24);
}

.refresh-analysis-button:disabled {
  cursor: progress;
  opacity: 0.58;
}

.refresh-analysis-button .spinning {
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
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
.next-summary-card {
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

.primary-insight.compact {
  margin-bottom: 10px;
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

.primary-insight p {
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

.diagnosis-points {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0;
  margin: 0;
  list-style: none;
}

.diagnosis-points li {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  color: #3c4654;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.45;
}

.diagnosis-points li span {
  width: 6px;
  height: 6px;
  flex: 0 0 6px;
  border-radius: 50%;
  margin-top: 6px;
  background: #008c95;
}

.empty-analysis-card {
  padding: 16px;
  margin-bottom: 12px;
}

.empty-analysis-card span {
  color: #0f5fae;
  font-size: 11px;
  font-weight: 900;
}

.empty-analysis-card strong {
  display: block;
  margin-top: 5px;
  color: #17202b;
  font-size: 16px;
  font-weight: 900;
  line-height: 1.4;
}

.empty-analysis-card p {
  margin: 6px 0 0;
  color: #5f6b77;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.5;
}

.card-switch-card {
  margin-bottom: 12px;
  padding: 16px;
  border-color: rgba(0, 140, 149, 0.18);
  background: linear-gradient(180deg, rgba(240, 253, 250, 0.82), rgba(255, 255, 255, 0.78));
}

.switch-hero {
  display: grid;
  grid-template-columns: 74px minmax(0, 1fr);
  gap: 13px;
  align-items: center;
}

.switch-card-preview {
  display: flex;
  min-height: 96px;
  align-items: center;
  justify-content: center;
  border-radius: 15px;
  background: rgba(255, 255, 255, 0.58);
}

.switch-card-preview img {
  width: 56px;
  height: 88px;
  object-fit: contain;
  filter: drop-shadow(0 10px 14px rgba(16, 24, 40, 0.18));
}

.switch-card-fallback {
  display: flex;
  width: 56px;
  height: 88px;
  flex-direction: column;
  justify-content: space-between;
  border-radius: 9px;
  padding: 9px 7px;
  background: #24364f;
  color: #fff;
  box-shadow: 0 10px 14px rgba(16, 24, 40, 0.18);
}

.switch-card-fallback small,
.switch-card-fallback strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.switch-card-fallback small {
  font-size: 8px;
  font-weight: 800;
  opacity: 0.76;
}

.switch-card-fallback strong {
  font-size: 10px;
  font-weight: 900;
}

.switch-hero strong {
  display: block;
  color: #17202b;
  font-size: 16px;
  font-weight: 900;
  line-height: 1.35;
}

.switch-hero p {
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

.compact-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0;
  margin: 0;
  list-style: none;
}

.compact-list li {
  display: flex;
  flex-direction: column;
  gap: 3px;
  border-radius: 12px;
  padding: 11px 12px;
  background: #fbfdff;
}

.compact-list strong {
  color: #17202b;
  font-size: 12px;
  font-weight: 900;
}

.compact-list span {
  color: #5f6b77;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.45;
}

.chart-card,
.insight-card,
.next-summary-card {
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

.next-summary-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.next-summary-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  border-radius: 14px;
  padding: 12px;
  background: rgba(246, 248, 251, 0.78);
}

.next-summary-list span {
  display: inline-flex;
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(15, 95, 174, 0.12);
  color: #0f5fae;
  font-size: 11px;
  font-weight: 900;
}

.next-summary-list strong {
  color: #17202b;
  font-size: 13px;
  font-weight: 800;
  line-height: 1.4;
}

@media (max-width: 380px) {
  .simple-header {
    align-items: stretch;
  }

  .insight-control {
    min-height: 38px;
  }

  .refresh-analysis-button {
    width: 30px;
    height: 30px;
  }
}
</style>
