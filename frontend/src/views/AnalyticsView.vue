<template>
  <section class="screen analytics-screen">
    <header class="simple-header analytics-header">
      <AppBackButton fallback="/cards" />
      <div class="analytics-title">
        <h1>카드 소비 분석</h1>
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

    <div class="screen-scroll scrollbar-hide analytics-body">
      <div v-if="statusMessage" class="status-banner" :class="{ error: Boolean(error) }">
        {{ statusMessage }}
      </div>

      <article class="analysis-hero app-card" :class="{ empty: !hasUsableAnalysis }">
        <div class="hero-copy">
          <span>{{ trendPeriodLabel }}</span>
          <strong>{{ heroAmountLabel }}</strong>
          <p>{{ heroMessage }}</p>
        </div>
        <div v-if="topCategory" class="hero-focus">
          <small>최대 지출</small>
          <b>{{ topCategory?.category || '-' }}</b>
          <span>{{ topCategory ? `${topCategory.percent}%` : '0%' }}</span>
        </div>
        <div v-else class="hero-focus muted">
          <small>상태</small>
          <b>{{ isLoading ? '준비 중' : '대기' }}</b>
          <span>내역 필요</span>
        </div>
      </article>

      <div class="insight-actions">
        <RouterLink class="insight-action" to="/reports/monthly">
          <span>
            <FileText :size="18" :stroke-width="2.2" />
          </span>
          <div>
            <strong>월간 보고서</strong>
            <small>요약 리포트 보기</small>
          </div>
          <ChevronRight :size="17" :stroke-width="2.2" />
        </RouterLink>
        <RouterLink class="insight-action teal" to="/recommendations/new">
          <span>
            <Sparkles :size="18" :stroke-width="2.2" />
          </span>
          <div>
            <strong>새 카드 추천</strong>
            <small>발급 후보 비교</small>
          </div>
          <ChevronRight :size="17" :stroke-width="2.2" />
        </RouterLink>
      </div>

      <section v-if="hasUsableAnalysis" class="metric-row" aria-label="분석 핵심 지표">
        <article v-for="metric in metricCards" :key="metric.label" class="metric-tile app-card-sm" :class="metric.tone">
          <small>{{ metric.label }}</small>
          <strong>{{ metric.value }}</strong>
          <span>{{ metric.caption }}</span>
        </article>
      </section>

      <article v-if="hasCategoryData" class="analysis-card app-card category-card">
        <div class="section-title-row">
          <div>
            <span>카테고리 순위</span>
            <strong>어디에 많이 썼는지</strong>
          </div>
          <small>{{ categoryCountLabel }}</small>
        </div>
        <ul class="category-rank-list">
          <li v-for="category in visibleCategoryRows" :key="category.category">
            <div class="category-row-head">
              <span>
                <i :style="{ background: category.color }"></i>
                <b>{{ category.category }}</b>
              </span>
              <strong>{{ krw(category.amount) }}</strong>
            </div>
            <div class="category-track">
              <i :style="{ width: `${category.percent}%`, background: category.color }"></i>
            </div>
            <small>{{ category.percent }}% · {{ category.description }}</small>
          </li>
        </ul>
      </article>

      <article v-else class="analysis-card app-card empty-state-card">
        <div class="empty-icon">
          <BarChart3 :size="22" :stroke-width="2.2" />
        </div>
        <strong>분석할 소비 내역이 아직 부족해요</strong>
        <p>결제 내역을 추가하면 카테고리별 흐름과 카드 개선 포인트가 바로 정리됩니다.</p>
        <RouterLink class="primary-inline-link" to="/transactions/new">결제내역 추가</RouterLink>
      </article>

      <article v-if="hasUsableAnalysis && cardRows.length" class="analysis-card app-card card-usage-card">
        <div class="section-title-row">
          <div>
            <span>카드별 사용</span>
            <strong>어떤 카드에 몰렸는지</strong>
          </div>
          <CreditCard :size="19" :stroke-width="2.2" />
        </div>
        <ul class="card-usage-list">
          <li v-for="card in cardRows" :key="card.id">
            <div class="card-usage-copy">
              <strong>{{ card.name }}</strong>
              <small>{{ card.caption }}</small>
            </div>
            <div class="card-usage-value">
              <b>{{ krw(card.amount) }}</b>
              <span>{{ card.percent }}%</span>
            </div>
          </li>
        </ul>
      </article>

      <article v-if="pendingReviewCandidates.length" class="analysis-card app-card review-card">
        <div class="section-title-row">
          <div>
            <span>반복 지출 확인</span>
            <strong>추천 기준을 더 정확하게</strong>
          </div>
          <small>{{ pendingReviewCandidates.length }}개</small>
        </div>
        <div class="review-list">
          <article v-for="item in pendingReviewCandidates" :key="item.category" class="review-item">
            <div>
              <strong>{{ item.category }}</strong>
              <small>평소 {{ krw(item.baselineReference) }} · 이번 달 {{ krw(item.currentAmount) }}</small>
            </div>
            <div class="review-toggle" role="group" :aria-label="`${item.category} 지출 반영 방식`">
              <button type="button" @click="setRecurringOverride(item.category, false)">이번 달만</button>
              <button type="button" @click="setRecurringOverride(item.category, true)">반복</button>
            </div>
          </article>
        </div>
      </article>

      <article v-if="hasUsableAnalysis && topRecommendation" class="analysis-card app-card recommendation-card">
        <div class="section-title-row">
          <div>
            <span>새 카드 추천</span>
            <strong>{{ recommendationTitle }}</strong>
          </div>
          <small>{{ topRecommendation.match || 0 }}%</small>
        </div>
        <div class="recommendation-body">
          <div class="recommendation-image">
            <img v-if="topRecommendation.imageUrl" :src="topRecommendation.imageUrl" :alt="topRecommendation.name" />
            <Sparkles v-else :size="22" :stroke-width="2.2" />
          </div>
          <div>
            <strong>{{ topRecommendation.name }}</strong>
            <p>{{ topRecommendation.reason || topRecommendation.benefit || '현재 소비 기준으로 비교해볼 만한 카드입니다.' }}</p>
          </div>
        </div>
        <div class="recommendation-metrics">
          <span>
            <small>월 개선</small>
            <b>{{ signedKrw(topRecommendationEconomics.monthlyDelta) }}</b>
          </span>
          <span>
            <small>연 개선</small>
            <b>{{ signedKrw(topRecommendationEconomics.annualDelta) }}</b>
          </span>
        </div>
        <RouterLink class="secondary-inline-link" to="/recommendations/new">새 카드 자세히 보기</RouterLink>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { BarChart3, ChevronRight, CreditCard, FileText, RefreshCw, Sparkles } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { krw, transactions as mockTransactions } from '@/data/mockData'
import { fetchCardRecommendationBundle, fetchSpendingSummary } from '@/services/api'

const colors = ['#0f5fae', '#008c95', '#24364f', '#c49a49', '#8a9aad', '#5f6b77']
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
    // localStorage can be unavailable; keep the in-memory choice for this session.
  }
}

const recurringOverrides = ref(readStoredList(RECURRING_STORAGE_KEY))
const handledReviewCategories = ref(readStoredList(REVIEW_HANDLED_STORAGE_KEY))

const safeSummary = computed(() => summary.value || (isLoading.value ? buildEmptySummary() : buildMockSummary()))
const aiAnalysis = computed(() => safeSummary.value.aiAnalysis || null)
const spendingTrend = computed(() => safeSummary.value.spendingTrend || null)
const totalExpense = computed(() => Number(safeSummary.value.totalExpense || 0))
const expectedSaving = computed(() =>
  (aiAnalysis.value?.savingOpportunities || []).reduce((sum, item) => sum + Number(item.amount || 0), 0),
)
const topRecommendation = computed(() => recommendationBundle.value?.results?.[0] || null)
const topRecommendationEconomics = computed(() => topRecommendation.value?.economics || {})

const trendPeriodLabel = computed(() => {
  const currentMonth = spendingTrend.value?.currentMonth || safeSummary.value.period?.currentMonth
  return currentMonth ? `${currentMonth.replace('-', '.')} 기준` : '이번 달 기준'
})

const rawCategoryRows = computed(() => {
  const rows = [...(safeSummary.value.byCategory || [])]
    .filter((item) => Number(item.amount || 0) > 0)
    .sort((a, b) => Number(b.amount || 0) - Number(a.amount || 0))
  const total = rows.reduce((sum, item) => sum + Number(item.amount || 0), 0)
  return rows.map((item, index) => {
    const percent = total ? Math.round((Number(item.amount || 0) / total) * 100) : 0
    return {
      ...item,
      percent: Math.max(percent, total ? 1 : 0),
      share: total ? (Number(item.amount || 0) / total) * 100 : 0,
      color: colors[index % colors.length],
      description: categoryDescription(item.category, index),
    }
  })
})

const visibleCategoryRows = computed(() => rawCategoryRows.value.slice(0, 5))
const hasCategoryData = computed(() => rawCategoryRows.value.length > 0)
const categoryCountLabel = computed(() => `${rawCategoryRows.value.length}개 항목`)
const topCategory = computed(() => rawCategoryRows.value[0] || null)
const heroMessage = computed(() => {
  if (!totalExpense.value) return '결제 내역을 쌓으면 소비 성향이 선명하게 보여요.'
  if (!topCategory.value) return '이번 달 소비 데이터를 정리했습니다.'
  return `${topCategory.value.category} 비중이 가장 높아서 이 항목의 카드 혜택을 먼저 보면 좋아요.`
})

const oneTimeCandidates = computed(() => spendingTrend.value?.oneTimeCandidates || [])
const reviewCandidates = computed(() => spendingTrend.value?.reviewCandidates || oneTimeCandidates.value)
const pendingReviewCandidates = computed(() =>
  reviewCandidates.value.filter((item) => !handledReviewCategories.value.includes(item.category)),
)

const metricCards = computed(() => {
  const total = spendingTrend.value?.total || {}
  return [
    {
      label: '전월 대비',
      value: signedKrw(total.deltaFromPrevious),
      caption: '지난달과 비교',
      tone: Number(total.deltaFromPrevious || 0) > 0 ? 'warning' : 'good',
    },
    {
      label: '평소 대비',
      value: signedKrw(total.deltaFromBaseline),
      caption: '최근 6개월 기준',
      tone: Number(total.deltaFromBaseline || 0) > 0 ? 'warning' : 'good',
    },
    {
      label: '예상 개선',
      value: signedKrw(topRecommendationEconomics.value.monthlyDelta || expectedSaving.value),
      caption: '월 기준 혜택',
      tone: 'good',
    },
  ]
})

const cardRows = computed(() => {
  const insightRows = aiAnalysis.value?.cardInsights || []
  const sourceRows = insightRows.length
    ? insightRows.map((item) => ({
      id: item.cardId || item.cardName,
      name: item.cardName || `카드 ${item.cardId}`,
      amount: Number(item.amount || 0),
      caption: item.fit ? `적합도 ${item.fit}` : (item.insight || '사용 흐름 확인'),
    }))
    : (safeSummary.value.byCard || []).map((item) => ({
      id: item.cardId,
      name: `카드 ${item.cardId}`,
      amount: Number(item.amount || 0),
      caption: '사용 흐름 확인',
    }))
  const total = sourceRows.reduce((sum, item) => sum + Number(item.amount || 0), 0)
  return sourceRows
    .filter((item) => Number(item.amount || 0) > 0)
    .sort((a, b) => Number(b.amount || 0) - Number(a.amount || 0))
    .slice(0, 3)
    .map((item) => ({
      ...item,
      percent: total ? Math.round((Number(item.amount || 0) / total) * 100) : 0,
    }))
})

const hasUsableAnalysis = computed(() =>
  totalExpense.value > 0 || rawCategoryRows.value.length > 0 || cardRows.value.length > 0,
)

const heroAmountLabel = computed(() => {
  if (hasUsableAnalysis.value) return krw(totalExpense.value)
  return isLoading.value ? '준비 중' : '데이터 없음'
})

const recommendationTitle = computed(() => {
  const delta = Number(topRecommendationEconomics.value.monthlyDelta || 0)
  if (delta > 0) return `월 ${krw(delta)} 개선 가능`
  return '현재 소비와 비교해볼 카드'
})

const analysisButtonLabel = computed(() => {
  if (isRefreshing.value) return '분석 중'
  return aiAnalysis.value ? '인사이트 갱신' : '인사이트 생성'
})

const statusMessage = computed(() => {
  if (error.value) return error.value
  if (isRefreshing.value) return '새로운 소비 인사이트를 정리하고 있습니다.'
  if (isLoading.value) return '최신 소비 인사이트를 준비하고 있습니다.'
  return ''
})

function buildMockSummary() {
  const expenses = mockTransactions.filter((tx) => Number(tx.amt) < 0)
  const categoryMap = new Map()
  const cardMap = new Map()
  expenses.forEach((tx) => {
    categoryMap.set(tx.cat, (categoryMap.get(tx.cat) || 0) + Math.abs(Number(tx.amt) || 0))
    cardMap.set(String(tx.cardId), (cardMap.get(String(tx.cardId)) || 0) + Math.abs(Number(tx.amt) || 0))
  })
  const byCategory = [...categoryMap.entries()].map(([category, amount]) => ({ category, amount }))
  const byCard = [...cardMap.entries()].map(([cardId, amount]) => ({ cardId, amount }))
  const totalExpense = expenses.reduce((sum, tx) => sum + Math.abs(Number(tx.amt) || 0), 0)
  return {
    totalExpense,
    totalIncome: mockTransactions
      .filter((tx) => Number(tx.amt) > 0)
      .reduce((sum, tx) => sum + Number(tx.amt || 0), 0),
    byCategory,
    byCard,
    period: { currentMonth: '2026-06' },
    spendingTrend: {
      currentMonth: '2026-06',
      total: {
        deltaFromPrevious: totalExpense - 483500,
        deltaFromBaseline: totalExpense - 463183,
      },
      reviewCandidates: [],
      oneTimeCandidates: [],
    },
    aiAnalysis: {
      savingOpportunities: [{ amount: 12000 }],
      cardInsights: byCard.map((item) => ({
        cardId: item.cardId,
        cardName: `카드 ${item.cardId}`,
        amount: item.amount,
        fit: '보통',
      })),
    },
  }
}

function buildEmptySummary() {
  return {
    totalExpense: 0,
    totalIncome: 0,
    byCategory: [],
    byCard: [],
    period: { currentMonth: '2026-06' },
    spendingTrend: { currentMonth: '2026-06', total: {} },
    aiAnalysis: null,
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
    recommendationBundle.value = await fetchCardRecommendationBundle(trendRequestOptions())
  } catch {
    summary.value = buildMockSummary()
    recommendationBundle.value = null
    error.value = '저장된 소비 데이터를 기준으로 분석을 제공합니다.'
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
    error.value = '새 분석을 저장하지 못했습니다. 잠시 후 다시 시도해 주세요.'
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

function categoryDescription(category, index) {
  if (index === 0) return '가장 먼저 볼 항목'
  if (category === '쇼핑') return '혜택 카드 비교 추천'
  if (category === '식비') return '반복 지출 관리'
  if (category === '교통') return '고정 소비 확인'
  return '이번 달 주요 지출'
}

onMounted(loadSummary)
</script>

<style scoped>
.analytics-screen {
  background: #f3f6f8;
}

.simple-header {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 22px 20px 20px;
  color: #17202b;
}

.analytics-header {
  border: 0;
  border-radius: 0 0 28px 28px;
  background:
    radial-gradient(circle at 12% -10%, rgba(15, 95, 174, 0.13), transparent 42%),
    linear-gradient(180deg, #ffffff 0%, #fbfdff 57%, #eef5fa 100%);
  box-shadow: 0 12px 30px rgba(36, 54, 79, 0.08);
}

.analytics-title {
  min-width: 0;
}

.simple-header h1 {
  margin: 0;
  color: #17202b;
  font-size: 22px;
  font-weight: 900;
  line-height: 1.2;
}

.simple-header p {
  margin: 0;
  color: #6f7d8c;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.45;
}

.refresh-analysis-button {
  display: inline-flex;
  width: 40px;
  height: 40px;
  flex: 0 0 40px;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(36, 54, 79, 0.08);
  border-radius: 50%;
  padding: 0;
  background: rgba(255, 255, 255, 0.72);
  color: #24364f;
  box-shadow: 0 10px 22px rgba(36, 54, 79, 0.08);
  touch-action: manipulation;
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

.analytics-body {
  padding: 16px clamp(14px, 4.6vw, 20px) 120px;
  background: #f3f6f8;
}

.status-banner {
  margin-bottom: 12px;
  border: 1px solid rgba(15, 95, 174, 0.1);
  border-radius: 14px;
  padding: 11px 13px;
  background: rgba(232, 241, 251, 0.72);
  color: #0f5fae;
  font-size: 12px;
  font-weight: 850;
}

.status-banner.error {
  border-color: rgba(196, 154, 73, 0.2);
  background: rgba(255, 249, 235, 0.76);
  color: #8a640e;
}

.analysis-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 14px;
  align-items: end;
  overflow: hidden;
  border: 1px solid rgba(36, 54, 79, 0.08) !important;
  border-radius: 22px !important;
  padding: 20px 18px !important;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(238, 247, 250, 0.9)),
    radial-gradient(circle at 100% 0%, rgba(0, 140, 149, 0.16), transparent 40%) !important;
  box-shadow: 0 16px 34px rgba(36, 54, 79, 0.08) !important;
}

.analysis-hero.empty {
  align-items: center;
}

.hero-copy span,
.section-title-row span {
  color: #0f5fae;
  font-size: 11px;
  font-weight: 950;
}

.hero-copy strong {
  display: block;
  margin-top: 7px;
  color: #17202b;
  font-size: clamp(30px, 8vw, 38px);
  font-weight: 950;
  letter-spacing: 0;
  line-height: 1.03;
}

.hero-copy p {
  margin: 10px 0 0;
  color: #5f6b77;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.5;
  word-break: keep-all;
}

.hero-focus {
  display: grid;
  min-width: 82px;
  justify-items: center;
  border-radius: 18px;
  padding: 12px 10px;
  background: #24364f;
  color: #fff;
  box-shadow: 0 14px 24px rgba(36, 54, 79, 0.18);
}

.hero-focus small {
  color: rgba(255, 255, 255, 0.66);
  font-size: 10px;
  font-weight: 900;
}

.hero-focus b {
  margin-top: 5px;
  font-size: 16px;
  font-weight: 950;
}

.hero-focus span {
  margin-top: 3px;
  color: #9be6df;
  font-size: 12px;
  font-weight: 950;
}

.hero-focus.muted {
  background: rgba(36, 54, 79, 0.08);
  color: #24364f;
  box-shadow: none;
}

.hero-focus.muted small,
.hero-focus.muted span {
  color: #7a8592;
}

.insight-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 12px;
}

.insight-action {
  display: grid;
  grid-template-columns: 34px minmax(0, 1fr) 14px;
  gap: 9px;
  align-items: center;
  border: 1px solid rgba(36, 54, 79, 0.08);
  border-radius: 16px;
  padding: 11px 10px;
  background: rgba(255, 255, 255, 0.8);
  color: inherit;
  text-decoration: none;
  box-shadow: 0 10px 22px rgba(36, 54, 79, 0.05);
}

.insight-action > span {
  display: inline-flex;
  width: 34px;
  height: 34px;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: rgba(15, 95, 174, 0.09);
  color: #0f5fae;
}

.insight-action.teal > span {
  background: rgba(0, 140, 149, 0.1);
  color: #008c95;
}

.insight-action strong,
.insight-action small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.insight-action strong {
  color: #17202b;
  font-size: 13px;
  font-weight: 950;
}

.insight-action small {
  margin-top: 3px;
  color: #7a8592;
  font-size: 10px;
  font-weight: 850;
}

.insight-action > svg {
  color: #8a9aad;
}

.metric-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 9px;
  margin-top: 12px;
}

.metric-tile {
  min-width: 0;
  border: 1px solid rgba(36, 54, 79, 0.08) !important;
  border-radius: 16px !important;
  padding: 12px 10px !important;
  background: rgba(255, 255, 255, 0.78) !important;
  box-shadow: 0 10px 22px rgba(36, 54, 79, 0.05) !important;
}

.metric-tile small,
.metric-tile span {
  display: block;
  color: #8a9aad;
  font-size: 10px;
  font-weight: 900;
}

.metric-tile strong {
  display: block;
  overflow: hidden;
  margin: 5px 0 3px;
  color: #17202b;
  font-size: clamp(13px, 3.7vw, 16px);
  font-weight: 950;
  letter-spacing: 0;
  line-height: 1.14;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.metric-tile.good strong {
  color: #008c95;
}

.metric-tile.warning strong {
  color: #b45309;
}

.analysis-card {
  margin-top: 12px;
  border: 1px solid rgba(36, 54, 79, 0.08) !important;
  border-radius: 18px !important;
  padding: 16px !important;
  background: rgba(255, 255, 255, 0.82) !important;
  box-shadow: 0 13px 28px rgba(36, 54, 79, 0.055) !important;
}

.section-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 13px;
}

.section-title-row strong {
  display: block;
  margin-top: 3px;
  color: #17202b;
  font-size: 16px;
  font-weight: 950;
  line-height: 1.25;
}

.section-title-row > small,
.section-title-row > svg {
  flex: 0 0 auto;
  color: #8a9aad;
  font-size: 11px;
  font-weight: 900;
}

.category-rank-list,
.card-usage-list {
  display: flex;
  flex-direction: column;
  gap: 13px;
  padding: 0;
  margin: 0;
  list-style: none;
}

.category-row-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.category-row-head span {
  display: inline-flex;
  min-width: 0;
  align-items: center;
  gap: 7px;
}

.category-row-head i {
  width: 9px;
  height: 9px;
  flex: 0 0 9px;
  border-radius: 50%;
}

.category-row-head b {
  overflow: hidden;
  color: #17202b;
  font-size: 14px;
  font-weight: 950;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.category-row-head strong {
  color: #17202b;
  font-size: 14px;
  font-weight: 950;
  white-space: nowrap;
}

.category-track {
  height: 7px;
  overflow: hidden;
  border-radius: 999px;
  margin-top: 8px;
  background: #e7edf4;
}

.category-track i {
  display: block;
  height: 100%;
  min-width: 7px;
  border-radius: inherit;
}

.category-rank-list li > small {
  display: block;
  margin-top: 6px;
  color: #7a8592;
  font-size: 11px;
  font-weight: 800;
}

.empty-state-card {
  text-align: left;
}

.empty-icon {
  display: inline-flex;
  width: 42px;
  height: 42px;
  align-items: center;
  justify-content: center;
  border-radius: 15px;
  background: rgba(15, 95, 174, 0.09);
  color: #0f5fae;
}

.empty-state-card strong {
  display: block;
  margin-top: 12px;
  color: #17202b;
  font-size: 17px;
  font-weight: 950;
}

.empty-state-card p {
  margin: 7px 0 0;
  color: #5f6b77;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.5;
}

.primary-inline-link,
.secondary-inline-link {
  display: inline-flex;
  min-height: 38px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  margin-top: 13px;
  padding: 0 15px;
  background: #24364f;
  color: #fff;
  font-size: 12px;
  font-weight: 950;
  text-decoration: none;
}

.secondary-inline-link {
  width: 100%;
  background: rgba(15, 95, 174, 0.09);
  color: #0f5fae;
}

.card-usage-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border-radius: 14px;
  padding: 12px;
  background: #f5f8fb;
}

.card-usage-copy {
  min-width: 0;
}

.card-usage-copy strong,
.recommendation-body strong {
  display: block;
  overflow: hidden;
  color: #17202b;
  font-size: 14px;
  font-weight: 950;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-usage-copy small {
  display: block;
  overflow: hidden;
  margin-top: 4px;
  color: #7a8592;
  font-size: 11px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-usage-value {
  flex: 0 0 auto;
  text-align: right;
}

.card-usage-value b {
  display: block;
  color: #17202b;
  font-size: 14px;
  font-weight: 950;
}

.card-usage-value span {
  display: block;
  margin-top: 3px;
  color: #008c95;
  font-size: 11px;
  font-weight: 950;
}

.review-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.review-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  border-radius: 14px;
  padding: 11px;
  background: #f5f8fb;
}

.review-item strong {
  display: block;
  color: #17202b;
  font-size: 13px;
  font-weight: 950;
}

.review-item small {
  display: block;
  margin-top: 4px;
  color: #7a8592;
  font-size: 10px;
  font-weight: 850;
  line-height: 1.35;
}

.review-toggle {
  display: inline-grid;
  grid-template-columns: 1fr 1fr;
  overflow: hidden;
  border: 1px solid rgba(36, 54, 79, 0.08);
  border-radius: 999px;
  background: #edf2f7;
}

.review-toggle button {
  min-height: 34px;
  border: 0;
  padding: 0 10px;
  background: transparent;
  color: #5f6b77;
  font-size: 11px;
  font-weight: 950;
  white-space: nowrap;
  touch-action: manipulation;
}

.review-toggle button:active {
  background: #24364f;
  color: #fff;
}

.recommendation-card {
  background:
    linear-gradient(180deg, rgba(240, 253, 250, 0.88), rgba(255, 255, 255, 0.86)) !important;
}

.recommendation-body {
  display: grid;
  grid-template-columns: 66px minmax(0, 1fr);
  gap: 13px;
  align-items: center;
}

.recommendation-image {
  display: flex;
  min-height: 88px;
  align-items: center;
  justify-content: center;
  border-radius: 15px;
  background: rgba(255, 255, 255, 0.7);
  color: #008c95;
}

.recommendation-image img {
  display: block;
  width: 52px;
  max-height: 82px;
  object-fit: contain;
  filter: drop-shadow(0 10px 14px rgba(36, 54, 79, 0.16));
}

.recommendation-body p {
  display: -webkit-box;
  overflow: hidden;
  margin: 6px 0 0;
  color: #5f6b77;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.48;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.recommendation-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 12px;
}

.recommendation-metrics span {
  border-radius: 13px;
  padding: 10px 11px;
  background: rgba(255, 255, 255, 0.74);
}

.recommendation-metrics small {
  display: block;
  color: #7a8592;
  font-size: 10px;
  font-weight: 900;
}

.recommendation-metrics b {
  display: block;
  margin-top: 3px;
  color: #008c95;
  font-size: 15px;
  font-weight: 950;
}

@media (max-width: 380px) {
  .metric-row {
    grid-template-columns: 1fr;
  }

  .analysis-hero {
    grid-template-columns: 1fr;
  }

  .hero-focus {
    justify-items: start;
  }

  .insight-actions {
    grid-template-columns: 1fr;
  }
}
</style>
