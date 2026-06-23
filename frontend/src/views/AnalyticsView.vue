<template>
  <section class="screen analytics-screen">
    <header class="simple-header blue-gradient">
      <AppBackButton fallback="/cards" />
      <div>
        <h1>카드 소비 분석</h1>
        <p>소비·혜택 요약</p>
      </div>
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
    </header>

    <div class="screen-scroll scrollbar-hide page-padding">
      <div v-if="error" class="notice-card">{{ error }}</div>
      <div v-if="isLoading" class="notice-card">최신 소비 인사이트를 준비하고 있습니다.</div>
      <div v-if="isRefreshing" class="notice-card">새로운 소비 인사이트를 정리하고 있습니다.</div>

      <div class="metric-grid">
        <article class="app-card metric-card metric-card-total">
          <span>지출</span>
          <strong class="metric-value">{{ krw(totalExpense) }}</strong>
        </article>
        <article class="app-card metric-card metric-card-saving">
          <span>절감</span>
          <strong class="metric-value success">{{ krw(expectedSaving) }}</strong>
        </article>
      </div>

      <article v-if="spendingTrend" class="app-card trend-card">
        <div class="section-title">
          <span>흐름</span>
          <small>{{ trendPeriodLabel }}</small>
        </div>
        <div v-if="primaryTrendChange" class="trend-primary">
          <strong>{{ trendPrimaryTitle }}</strong>
          <p>{{ trendPrimaryCopy }}</p>
        </div>
        <ul class="trend-metrics">
          <li v-for="item in trendHighlights" :key="item.label">
            <small>{{ item.label }}</small>
            <strong :class="{ success: item.tone === 'success', attention: item.tone === 'attention' }">
              {{ item.value }}
            </strong>
            <span>{{ item.caption }}</span>
          </li>
        </ul>
        <div v-if="pendingReviewCandidates.length" class="spend-review-panel">
          <div class="review-copy">
            <span>추천 기준 확인</span>
            <strong>앞으로도 반복될 지출인가요?</strong>
            <p>한 번 선택하면 같은 항목은 다시 묻지 않습니다.</p>
          </div>
          <div class="review-list">
            <article v-for="item in pendingReviewCandidates" :key="item.category" class="review-item">
              <div>
                <strong>{{ item.category }}</strong>
                <small>평소 {{ krw(item.baselineReference) }} · 이번 달 {{ krw(item.currentAmount) }}</small>
              </div>
              <div class="review-toggle" role="group" :aria-label="`${item.category} 지출 반영 방식`">
                <button
                  type="button"
                  @click="setRecurringOverride(item.category, false)"
                >
                  이번 달만
                </button>
                <button
                  type="button"
                  @click="setRecurringOverride(item.category, true)"
                >
                  반복
                </button>
              </div>
            </article>
          </div>
        </div>
      </article>

      <div v-if="aiAnalysis?.summaryCards?.length" class="ai-summary-grid">
        <article
          v-for="card in aiAnalysis.summaryCards"
          :key="`${card.label}-${card.value}`"
          class="app-card ai-summary-card"
          :class="`tone-${card.tone || 'gray'}`"
        >
          <span>{{ compactSummaryLabel(card.label) }}</span>
          <strong class="summary-value">{{ card.value }}</strong>
        </article>
      </div>

      <article v-if="aiAnalysis" class="app-card ai-card">
        <div class="section-title">
          <span>진단</span>
          <small>신뢰도 <b>{{ Math.round(Number(aiAnalysis.confidence || 0) * 100) }}%</b></small>
        </div>
        <div class="primary-insight compact" :class="`severity-${aiAnalysis.primaryInsight?.severity || 'info'}`">
          <div>
            <span>{{ conciseDiagnosis.label }}</span>
            <strong>{{ conciseDiagnosis.title }}</strong>
          </div>
          <em v-if="conciseDiagnosis.amount">
            {{ krw(conciseDiagnosis.amount) }}
          </em>
        </div>
        <ul class="signal-grid">
          <li v-for="item in analysisSignals" :key="`${item.label}-${item.value}`">
            <small>{{ item.label }}</small>
            <strong>{{ item.value }}</strong>
          </li>
        </ul>
      </article>
      <article v-else class="app-card empty-analysis-card">
        <span>대기</span>
        <strong>준비 중</strong>
      </article>

      <article v-if="recommendationAlert?.show && topRecommendation" class="app-card card-switch-card">
        <div class="section-title">
          <span>교체</span>
          <small>매칭 <b>{{ topRecommendation.match }}%</b></small>
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
          </div>
        </div>
        <div class="switch-metrics">
          <span>
            <small>월</small>
            <b>{{ signedKrw(topRecommendationEconomics.monthlyDelta) }}</b>
          </span>
          <span>
            <small>연</small>
            <b>{{ signedKrw(topRecommendationEconomics.annualDelta) }}</b>
          </span>
          <span>
            <small>계산 기준</small>
            <b>연회비 포함</b>
          </span>
        </div>
        <RouterLink class="switch-link" :to="`/recommendations/r1`">
          비교
        </RouterLink>
      </article>

      <article class="app-card chart-card">
        <div class="section-title">
          <span>분포</span>
          <small>{{ categoryCountLabel }}</small>
        </div>
        <div class="donut-panel">
          <div class="category-donut" :style="categoryChartStyle" role="img" :aria-label="categoryChartLabel">
            <div class="donut-hole">
              <span>최다</span>
              <strong>{{ topCategory?.category || '-' }}</strong>
              <small>{{ topCategory ? `${topCategory.percent}%` : '0%' }}</small>
            </div>
          </div>
          <ul class="donut-legend">
            <li v-for="category in categoryRows" :key="category.category">
              <i :style="{ background: category.color }"></i>
              <div>
                <strong>{{ category.category }}</strong>
                <small>{{ category.percent }}%</small>
              </div>
              <b>{{ krw(category.amount) }}</b>
            </li>
          </ul>
        </div>
      </article>

      <article v-if="aiAnalysis?.categoryInsights?.length" class="app-card insight-card">
        <div class="section-title">
          <span>해석</span>
          <small>TOP 3</small>
        </div>
        <ul class="compact-list">
          <li v-for="(item, index) in aiAnalysis.categoryInsights.slice(0, 3)" :key="`${item.category}-${item.amount}`">
            <div>
              <strong>{{ item.category }}</strong>
              <small class="amount-highlight">{{ krw(item.amount) }}</small>
            </div>
            <span>{{ categorySignal(index) }}</span>
          </li>
        </ul>
      </article>

    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RefreshCw } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { krw, transactions as mockTransactions } from '@/data/mockData'
import { fetchCardRecommendationBundle, fetchSpendingSummary } from '@/services/api'

const colors = ['#0f5fae', '#008c95', '#24364f', '#8a9aad', '#c49a49', '#5f6b77']
const summary = ref(null)
const recommendationBundle = ref(null)
const isLoading = ref(false)
const isRefreshing = ref(false)
const error = ref('')
const REVIEW_HANDLED_STORAGE_KEY = 'carch.analytics.reviewHandled.v1'
const RECURRING_STORAGE_KEY = 'carch.analytics.recurringOverrides.v1'

function readStoredList(key) {
  try {
    const value = window.localStorage.getItem(key)
    const parsed = JSON.parse(value || '[]')
    return Array.isArray(parsed) ? parsed.filter(Boolean) : []
  } catch {
    return []
  }
}

function writeStoredList(key, value) {
  try {
    window.localStorage.setItem(key, JSON.stringify([...new Set(value.filter(Boolean))]))
  } catch {
    // localStorage can be unavailable in privacy modes; the in-memory state still works.
  }
}

const recurringOverrides = ref(readStoredList(RECURRING_STORAGE_KEY))
const handledReviewCategories = ref(readStoredList(REVIEW_HANDLED_STORAGE_KEY))

const safeSummary = computed(() => summary.value || { totalExpense: 0, totalIncome: 0, byCategory: [], byCard: [] })
const aiAnalysis = computed(() => safeSummary.value.aiAnalysis || null)
const spendingTrend = computed(() => safeSummary.value.spendingTrend || null)
const totalExpense = computed(() => Number(safeSummary.value.totalExpense || 0))
const expectedSaving = computed(() =>
  (aiAnalysis.value?.savingOpportunities || []).reduce((sum, item) => sum + Number(item.amount || 0), 0),
)
const topRecommendation = computed(() => recommendationBundle.value?.results?.[0] || null)
const topRecommendationEconomics = computed(() => topRecommendation.value?.economics || {})
const recommendationAlert = computed(() => recommendationBundle.value?.alert || null)
const trendPeriodLabel = computed(() => {
  const currentMonth = spendingTrend.value?.currentMonth
  return currentMonth ? `${currentMonth.replace('-', '.')} 기준` : '최근 6개월'
})
const oneTimeCandidates = computed(() => spendingTrend.value?.oneTimeCandidates || [])
const reviewCandidates = computed(() => spendingTrend.value?.reviewCandidates || oneTimeCandidates.value)
const pendingReviewCandidates = computed(() =>
  reviewCandidates.value.filter((item) => !handledReviewCategories.value.includes(item.category)),
)
const primaryTrendChange = computed(() => {
  const oneTime = oneTimeCandidates.value[0]
  if (oneTime) return oneTime
  return (spendingTrend.value?.categoryChanges || []).find((item) => Number(item.currentAmount || 0) > 0) || null
})
const trendPrimaryTitle = computed(() => {
  const item = primaryTrendChange.value
  if (!item) return '안정'
  if (item.oneTimeCandidate) return `${item.category} 급증`
  if (Number(item.deltaFromBaseline || 0) > 0) return `${item.category} 증가`
  if (Number(item.deltaFromBaseline || 0) < 0) return `${item.category} 감소`
  return `${item.category} 안정`
})
const trendPrimaryCopy = computed(() => {
  const item = primaryTrendChange.value
  if (!item) return '반복 소비 기준선을 쌓고 있습니다.'
  const base = krw(item.baselineReference || item.baselineAverage || 0)
  if (item.userConfirmedRecurring) {
    return `반복 지출로 반영해 카드 추천을 다시 계산했습니다.`
  }
  if (item.oneTimeCandidate) {
    return `평소 ${base} 수준으로 보정해 추천에 반영합니다.`
  }
  return `평소 ${base} 기준으로 변화를 확인했습니다.`
})
const trendHighlights = computed(() => {
  const total = spendingTrend.value?.total || {}
  return [
    {
      label: '전월',
      value: signedKrw(total.deltaFromPrevious),
      caption: '지난달 대비',
      tone: Number(total.deltaFromPrevious || 0) > 0 ? 'attention' : 'success',
    },
    {
      label: '평소',
      value: signedKrw(total.deltaFromBaseline),
      caption: '6개월 평균 대비',
      tone: Number(total.deltaFromBaseline || 0) > 0 ? 'attention' : 'success',
    },
    {
      label: '추천 반영',
      value: krw(total.adjustedForRecommendation),
      caption: '일회성 보정',
      tone: 'success',
    },
  ]
})
const analysisButtonLabel = computed(() => {
  if (isRefreshing.value) return '분석 중'
  return aiAnalysis.value ? '인사이트 갱신' : '인사이트 생성'
})
const rawCategoryRows = computed(() => {
  const rows = [...(safeSummary.value.byCategory || [])].sort((a, b) => Number(b.amount || 0) - Number(a.amount || 0))
  const total = rows.reduce((sum, item) => sum + Number(item.amount || 0), 0)
  return rows.map((item, index) => ({
    ...item,
    percent: total ? Math.max(1, Math.round((Number(item.amount || 0) / total) * 100)) : 0,
    share: total ? (Number(item.amount || 0) / total) * 100 : 0,
    color: colors[index % colors.length],
  }))
})
const categoryRows = computed(() => {
  const rows = rawCategoryRows.value
  if (rows.length <= 6) return rows
  const majorRows = rows.slice(0, 5)
  const restRows = rows.slice(5)
  const restAmount = restRows.reduce((sum, item) => sum + Number(item.amount || 0), 0)
  const restShare = restRows.reduce((sum, item) => sum + Number(item.share || 0), 0)
  const restPercent = restRows.reduce((sum, item) => sum + Number(item.percent || 0), 0)
  return [
    ...majorRows,
    {
      category: '기타',
      amount: restAmount,
      percent: Math.max(1, Math.round(restPercent)),
      share: restShare,
      color: '#8a9aad',
    },
  ]
})
const categoryCountLabel = computed(() => (
  rawCategoryRows.value.length > 6 ? '상위 5개 + 기타' : `${rawCategoryRows.value.length}개`
))
const topCategory = computed(() => categoryRows.value[0] || null)
const categoryChartStyle = computed(() => {
  if (!categoryRows.value.length) {
    return { background: '#e7edf4' }
  }
  let cursor = 0
  const segments = categoryRows.value.map((item, index) => {
    const start = cursor
    const end = index === categoryRows.value.length - 1 ? 360 : cursor + item.share * 3.6
    cursor = end
    return `${item.color} ${start.toFixed(2)}deg ${end.toFixed(2)}deg`
  })
  return { background: `conic-gradient(${segments.join(', ')})` }
})
const categoryChartLabel = computed(() => {
  if (!topCategory.value) return '카테고리별 지출 데이터 없음'
  return `카테고리별 지출. 가장 큰 항목은 ${topCategory.value.category}, ${topCategory.value.percent}%입니다.`
})
const conciseDiagnosis = computed(() => {
  const primary = aiAnalysis.value?.primaryInsight || {}
  const top = categoryRows.value[0]
  return {
    label: '집중',
    title: top ? `${top.category}` : (primary.title || '점검'),
    amount: primary.metricValue || top?.amount || 0,
  }
})
const analysisSignals = computed(() => {
  const items = []
  const top = categoryRows.value[0]
  const second = categoryRows.value[1]
  if (top) items.push({ label: '집중', value: top.category })
  if (second) items.push({ label: '보조', value: second.category })
  if (topRecommendation.value?.economics?.monthlyDelta > 0) {
    items.push({ label: '절감', value: signedKrw(topRecommendation.value.economics.monthlyDelta) })
  }
  return items.slice(0, 3)
})
const cardSwitchTitle = computed(() => topRecommendation.value?.name || '추천 카드')

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

function trendRequestOptions(extra = {}) {
  return {
    ...extra,
    recurringCategories: recurringOverrides.value,
  }
}

async function loadSummary() {
  isLoading.value = true
  error.value = ''
  try {
    summary.value = await fetchSpendingSummary(trendRequestOptions({ ai: true }))
    if (!summary.value?.aiAnalysis && summary.value?.aiAnalysisStatus === 'empty') {
      summary.value = await fetchSpendingSummary(trendRequestOptions({ ai: true, refresh: true }))
    }
    const recommendations = await fetchCardRecommendationBundle(trendRequestOptions())
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
    summary.value = await fetchSpendingSummary(trendRequestOptions({ ai: true, refresh: true }))
    recommendationBundle.value = await fetchCardRecommendationBundle(trendRequestOptions())
  } catch {
    error.value = '새 인사이트를 저장하지 못했습니다. 잠시 후 다시 시도해 주세요.'
  } finally {
    isRefreshing.value = false
  }
}

async function setRecurringOverride(category, enabled) {
  const next = new Set(recurringOverrides.value)
  if (enabled) next.add(category)
  else next.delete(category)
  recurringOverrides.value = [...next]
  if (!handledReviewCategories.value.includes(category)) {
    handledReviewCategories.value = [...handledReviewCategories.value, category]
  }
  writeStoredList(RECURRING_STORAGE_KEY, recurringOverrides.value)
  writeStoredList(REVIEW_HANDLED_STORAGE_KEY, handledReviewCategories.value)
  error.value = ''
  try {
    summary.value = await fetchSpendingSummary(trendRequestOptions({ ai: true }))
    recommendationBundle.value = await fetchCardRecommendationBundle(trendRequestOptions())
  } catch {
    error.value = '추천 기준을 다시 계산하지 못했습니다.'
  }
}

function signedKrw(value) {
  const amount = Number(value || 0)
  return `${amount > 0 ? '+' : amount < 0 ? '-' : ''}${krw(Math.abs(amount))}`
}

function compactSummaryLabel(label) {
  const text = String(label || '')
  if (text.includes('지출')) return '지출'
  if (text.includes('절감')) return '절감'
  if (text.includes('점검')) return '점검'
  if (text.includes('카드')) return '카드'
  return text.replace(/이번 달|예상|기준|분석/g, '').trim() || '요약'
}

function categorySignal(index) {
  return ['집중', '비교', '관리'][index] || '점검'
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

.refresh-analysis-button {
  display: inline-flex;
  width: 38px;
  height: 38px;
  flex: 0 0 38px;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 50%;
  padding: 0;
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  box-shadow: 0 8px 18px rgba(7, 15, 28, 0.14);
  backdrop-filter: blur(12px);
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
  padding: 18px 18px 28px;
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
  margin-bottom: 14px;
}

.metric-grid article,
.chart-card,
.ai-card,
.insight-card,
.trend-card {
  padding: 17px 16px;
}

.metric-card,
.trend-card,
.ai-summary-card,
.ai-card,
.card-switch-card,
.chart-card,
.insight-card {
  border: 1px solid rgba(36, 54, 79, 0.1) !important;
  border-radius: 18px !important;
  background: rgba(251, 253, 255, 0.76) !important;
  box-shadow: 0 14px 30px rgba(36, 54, 79, 0.055) !important;
  backdrop-filter: blur(14px) saturate(1.06) !important;
}

.trend-card,
.ai-card,
.card-switch-card,
.chart-card,
.insight-card {
  position: relative;
  overflow: hidden;
}

.trend-card::before,
.ai-card::before,
.card-switch-card::before,
.chart-card::before,
.insight-card::before {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 3px;
  background: #24364f;
  content: '';
}

.ai-card::before,
.card-switch-card::before {
  background: #008c95;
}

.metric-card {
  position: relative;
  overflow: hidden;
  border-color: rgba(36, 54, 79, 0.08);
  background: rgba(255, 255, 255, 0.78);
}

.metric-card::before {
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  height: 3px;
  background: #24364f;
  content: '';
}

.metric-card-saving::before {
  background: #008c95;
}

.metric-grid span {
  color: #6e6e73;
  font-size: 12px;
  font-weight: 800;
}

.metric-grid strong {
  display: block;
  color: #17202b;
  font-size: 23px;
  font-weight: 900;
  line-height: 1.12;
}

.metric-value {
  margin-top: 7px;
  letter-spacing: 0;
  text-shadow: 0 8px 22px rgba(15, 95, 174, 0.08);
}

.success {
  color: #008c95 !important;
}

.attention {
  color: #b45309 !important;
}

.trend-card {
  margin-bottom: 14px;
  border-color: rgba(36, 54, 79, 0.1);
  background: rgba(255, 255, 255, 0.78);
}

.trend-primary {
  border-radius: 15px;
  margin-bottom: 10px;
  padding: 13px;
  background: rgba(244, 248, 251, 0.88);
}

.trend-primary strong {
  display: block;
  color: #17202b;
  font-size: 20px;
  font-weight: 950;
  line-height: 1.18;
}

.trend-primary p {
  margin: 6px 0 0;
  color: #5f6b77;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.5;
  word-break: keep-all;
}

.trend-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  padding: 0;
  margin: 0;
  list-style: none;
}

.trend-metrics li {
  min-width: 0;
  border-radius: 13px;
  padding: 11px 10px;
  background: rgba(251, 253, 255, 0.82);
}

.trend-metrics small,
.trend-metrics span {
  display: block;
  color: #8a9aad;
  font-size: 10px;
  font-weight: 900;
}

.trend-metrics strong {
  display: block;
  margin: 5px 0 3px;
  color: #17202b;
  font-size: 14px;
  font-weight: 950;
  line-height: 1.1;
  white-space: nowrap;
}

.one-time-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  align-items: center;
  margin-top: 10px;
}

.one-time-strip span,
.one-time-strip b {
  display: inline-flex;
  min-height: 30px;
  align-items: center;
  border-radius: 999px;
  padding: 0 10px;
  font-size: 11px;
  font-weight: 900;
}

.one-time-strip span {
  background: rgba(36, 54, 79, 0.08);
  color: #5f6b77;
}

.one-time-strip b {
  background: rgba(180, 83, 9, 0.09);
  color: #b45309;
}

.spend-review-panel {
  margin-top: 12px;
  border-top: 1px solid rgba(36, 54, 79, 0.08);
  padding-top: 12px;
}

.review-copy span {
  color: #008c95;
  font-size: 10px;
  font-weight: 950;
}

.review-copy strong {
  display: block;
  margin-top: 3px;
  color: #17202b;
  font-size: 15px;
  font-weight: 950;
}

.review-copy p {
  margin: 4px 0 0;
  color: #6e6e73;
  font-size: 11px;
  font-weight: 800;
  line-height: 1.45;
}

.review-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
}

.review-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  border-radius: 14px;
  padding: 10px;
  background: rgba(251, 253, 255, 0.82);
}

.review-item strong {
  display: block;
  color: #17202b;
  font-size: 13px;
  font-weight: 950;
}

.review-item small {
  display: block;
  margin-top: 3px;
  color: #7a8592;
  font-size: 10px;
  font-weight: 850;
  line-height: 1.35;
}

.review-toggle {
  display: inline-grid;
  grid-template-columns: 1fr 1fr;
  overflow: hidden;
  border: 1px solid rgba(36, 54, 79, 0.1);
  border-radius: 999px;
  background: rgba(237, 242, 247, 0.86);
}

.review-toggle button {
  min-height: 34px;
  border: 0;
  padding: 0 10px;
  background: transparent;
  color: #6e6e73;
  font-size: 11px;
  font-weight: 950;
  white-space: nowrap;
  cursor: pointer;
  touch-action: manipulation;
}

.review-toggle button.active {
  background: #24364f;
  color: #fff;
  box-shadow: 0 8px 18px rgba(36, 54, 79, 0.16);
}

.ai-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
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

.ai-summary-card strong,
.summary-value {
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

.primary-insight > div > span {
  color: #0f5fae;
  font-size: 10px;
  font-weight: 900;
}

.primary-insight strong {
  display: block;
  margin-top: 3px;
  color: #17202b;
  font-size: 20px;
  font-weight: 900;
  line-height: 1.12;
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
  align-self: start;
  border-radius: 12px;
  padding: 8px 10px;
  background: rgba(15, 95, 174, 0.1);
  color: #0f5fae;
  font-size: 16px;
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

.signal-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  padding: 0;
  margin: 0;
  list-style: none;
}

.signal-grid li {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
  border-radius: 12px;
  padding: 10px;
  background: rgba(246, 248, 251, 0.82);
}

.signal-grid small {
  color: #8a9aad;
  font-size: 10px;
  font-weight: 900;
}

.signal-grid strong {
  overflow: hidden;
  color: #17202b;
  font-size: 13px;
  font-weight: 900;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-analysis-card {
  padding: 16px;
  margin-bottom: 14px;
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
  margin-bottom: 14px;
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
  font-size: 18px;
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
  border: 1px solid rgba(0, 140, 149, 0.08);
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
  font-size: 15px;
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

.section-title small b {
  color: #008c95;
  font-size: 12px;
  font-weight: 900;
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
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  border-radius: 12px;
  padding: 11px 12px;
  background: #fbfdff;
}

.compact-list strong {
  color: #17202b;
  font-size: 12px;
  font-weight: 900;
}

.compact-list .amount-highlight {
  color: #008c95;
  font-size: 12px;
  font-weight: 900;
}

.compact-list span {
  border-radius: 999px;
  padding: 5px 8px;
  background: rgba(15, 95, 174, 0.08);
  color: #0f5fae;
  font-size: 11px;
  font-weight: 900;
  white-space: nowrap;
}

.chart-card,
.insight-card {
  margin-top: 14px;
}

.donut-panel {
  display: grid;
  grid-template-columns: minmax(138px, 158px) minmax(0, 1fr);
  align-items: center;
  gap: 16px;
}

.category-donut {
  position: relative;
  width: min(158px, 100%);
  aspect-ratio: 1;
  border-radius: 50%;
  box-shadow: inset 0 0 0 1px rgba(23, 32, 43, 0.04), 0 18px 38px rgba(15, 95, 174, 0.1);
}

.category-donut::after {
  position: absolute;
  inset: 15px;
  border: 1px solid rgba(219, 228, 238, 0.74);
  border-radius: inherit;
  background: rgba(251, 253, 255, 0.96);
  content: '';
}

.donut-hole {
  position: absolute;
  inset: 32px;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  text-align: center;
}

.donut-hole span {
  color: #7a8593;
  font-size: 10px;
  font-weight: 900;
}

.donut-hole strong {
  max-width: 72px;
  overflow: hidden;
  color: #17202b;
  font-size: 15px;
  font-weight: 900;
  line-height: 1.15;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.donut-hole small {
  color: #008c95;
  font-size: 18px;
  font-weight: 900;
  line-height: 1;
}

.donut-legend {
  display: flex;
  flex-direction: column;
  gap: 9px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.donut-legend li {
  display: grid;
  grid-template-columns: 9px minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
}

.donut-legend i {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  box-shadow: 0 0 0 3px rgba(23, 32, 43, 0.04);
}

.donut-legend div {
  display: flex;
  min-width: 0;
  align-items: baseline;
  gap: 5px;
}

.donut-legend strong {
  overflow: hidden;
  color: #17202b;
  font-size: 12px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.donut-legend small {
  flex: 0 0 auto;
  color: #008c95;
  font-size: 11px;
  font-weight: 900;
}

.donut-legend b {
  color: #17202b;
  font-size: 13px;
  font-weight: 900;
  text-align: right;
  white-space: nowrap;
}

@media (max-width: 380px) {
  .simple-header {
    align-items: stretch;
  }

  .donut-panel {
    grid-template-columns: 1fr;
    justify-items: center;
  }

  .donut-legend {
    width: 100%;
  }

  .refresh-analysis-button {
    width: 36px;
    height: 36px;
    flex-basis: 36px;
  }
}

/* ── 카드 메인 페이지 톤 통일 (플랫/헤어라인) ── */
.metric-card,
.trend-card,
.ai-card,
.empty-analysis-card,
.card-switch-card,
.chart-card,
.insight-card,
.trend-primary,
.primary-insight,
.ai-summary-card,
.switch-card-fallback {
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  backdrop-filter: none !important;
}

.trend-metrics li,
.signal-grid li,
.compact-list li,
.switch-metrics span {
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}

.trend-card,
.ai-card,
.empty-analysis-card,
.card-switch-card,
.chart-card,
.insight-card {
  margin-top: 14px !important;
  border-top: 1px solid rgba(32, 36, 42, 0.085) !important;
  padding: 16px 0 2px !important;
}

.metric-card {
  padding: 4px 0 !important;
}

.switch-link {
  background: linear-gradient(150deg, #2c4e72, #1c3149) !important;
}
</style>
