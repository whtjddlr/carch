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
        <div class="hero-month">
          <button type="button" class="month-chip" @click="isMonthMenuOpen ? (isMonthMenuOpen = false) : openMonthMenu()">
            {{ periodYear }}년 {{ periodMonthNum }}월
            <ChevronDown :size="13" :stroke-width="2.6" />
          </button>
          <span class="month-suffix">소비</span>
          <template v-if="isMonthMenuOpen">
            <div class="month-backdrop" @click="isMonthMenuOpen = false"></div>
            <div class="month-dial">
              <div class="dial-band"></div>
              <div class="dial-cols">
                <div ref="yearColRef" class="dial-col scrollbar-hide" @scroll="onYearScroll">
                  <button
                    v-for="y in dialYears"
                    :key="y"
                    type="button"
                    class="dial-item"
                    :class="{ sel: y === dialYear }"
                    @click="applyDial(y, dialMonth)"
                  >{{ y }}년</button>
                </div>
                <div ref="monthColRef" class="dial-col scrollbar-hide" @scroll="onMonthScroll">
                  <button
                    v-for="mm in dialMonths"
                    :key="mm"
                    type="button"
                    class="dial-item"
                    :class="{ sel: mm === dialMonth }"
                    @click="applyDial(dialYear, mm)"
                  >{{ mm }}월</button>
                </div>
              </div>
              <button type="button" class="dial-confirm" @click="isMonthMenuOpen = false">확인</button>
            </div>
          </template>
        </div>
        <strong class="hero-amount">{{ heroAmountLabel }}</strong>
        <p v-if="heroInsight" class="hero-insight" :style="{ color: heroInsightColor }">{{ heroInsight }}</p>
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
        <article v-for="metric in metricCards" :key="metric.label" class="metric-tile" :class="metric.tone">
          <small>{{ metric.label }}</small>
          <strong>{{ metric.value }}</strong>
          <span>{{ metric.caption }}</span>
        </article>
      </section>

      <article v-if="hasCategoryData" class="analysis-card app-card category-card">
        <ul class="category-rank-list">
          <li v-for="(category, index) in visibleCategoryRows" :key="category.category" :class="{ 'is-top': index === 0 }">
            <div class="category-row-head">
              <span>
                <em class="rank-emoji">{{ categoryIcon(category.category) }}</em>
                <b>{{ category.category }}</b>
                <i v-if="index === 0" class="rank-crown">👑</i>
              </span>
              <div class="category-amount">
                <strong>{{ krw(category.amount) }}</strong>
                <em class="rank-pct" :style="{ color: category.color }">{{ category.percent }}%</em>
              </div>
            </div>
            <div class="category-track">
              <i :style="{ width: `${category.percent}%`, background: category.color }"></i>
            </div>
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
        <ul class="card-usage-list">
          <li v-for="(card, index) in cardRows" :key="card.id" :class="{ 'is-top': index === 0 }">
            <span class="card-usage-thumb">
              <img
                v-if="card.imageUrl"
                :src="card.imageUrl"
                :alt="card.name"
                :class="thumbOrientation[card.id]"
                @load="onThumbLoad(card.id, $event)"
              />
              <CreditCard v-else :size="16" />
            </span>
            <div class="card-usage-copy">
              <strong>{{ card.name }}</strong>
              <i v-if="index === 0" class="rank-crown">👑</i>
            </div>
            <div class="card-usage-value">
              <b>{{ krw(card.amount) }}</b>
              <span>{{ card.percent }}%</span>
            </div>
          </li>
        </ul>
      </article>

      <article v-if="pendingReviewCandidates.length" class="analysis-card app-card review-card">
        <div class="review-head">
          <strong>이 지출, 매달 반복되나요?</strong>
          <small>반복 여부를 알려주면 추천이 더 정확해져요</small>
        </div>
        <div class="review-list">
          <article v-for="item in pendingReviewCandidates" :key="item.category" class="review-item">
            <span class="review-emoji">{{ categoryIcon(item.category) }}</span>
            <div class="review-info">
              <strong>{{ item.category }}</strong>
              <span>{{ krw(item.currentAmount) }}</span>
            </div>
            <div class="review-toggle" role="group" :aria-label="`${item.category} 지출 반영 방식`">
              <button type="button" :class="{ active: !isRecurring(item.category) }" @click="setRecurringOverride(item.category, false)">이번 달만</button>
              <button type="button" class="is-recurring" :class="{ active: isRecurring(item.category) }" @click="setRecurringOverride(item.category, true)">매달</button>
            </div>
          </article>
        </div>
      </article>

      <section v-if="hasUsableAnalysis && recommendationCards.length" class="rec-section">
        <div class="rec-section-head">
          <strong>새 카드 추천</strong>
          <RouterLink to="/recommendations/new">전체 →</RouterLink>
        </div>
        <article
          v-for="reco in recommendationCards"
          :key="reco.id"
          class="analysis-card app-card recommendation-card"
        >
          <div class="rec-head">
            <span class="rec-rank" :class="`rank-${reco.rank}`">{{ reco.rank }}순위</span>
            <span class="rec-thumb">
              <img
                v-if="reco.imageUrl"
                :src="reco.imageUrl"
                :alt="reco.name"
                :class="thumbOrientation[`rec-${reco.id}`]"
                @load="onThumbLoad(`rec-${reco.id}`, $event)"
              />
              <Sparkles v-else :size="20" :stroke-width="2.2" />
            </span>
            <div class="rec-head-copy">
              <strong>{{ reco.name }}</strong>
              <small v-if="reco.gain">예상 약 {{ reco.gain }}/월 절약</small>
            </div>
          </div>

          <div v-if="reco.benefits.length" class="rec-benefits">
            <div v-for="b in reco.benefits" :key="b.id" class="rec-benefit-row">
              <span class="rec-benefit-emoji">{{ b.icon }}</span>
              <div class="rec-benefit-main">
                <div class="rec-benefit-top">
                  <strong>{{ b.field }}</strong>
                  <b>{{ b.value }}</b>
                </div>
                <span v-if="b.cap">{{ b.cap }}</span>
              </div>
            </div>
          </div>

          <div class="rec-foot">
            <span><i>실적</i> 전월 {{ reco.requiredSpend }}</span>
            <RouterLink to="/recommendations/new">자세히 →</RouterLink>
          </div>
        </article>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { BarChart3, ChevronDown, ChevronRight, CreditCard, FileText, RefreshCw, Sparkles } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { cards as mockCards, krw, transactions as mockTransactions } from '@/data/mockData'
import { demoMonthCategories, demoMonthKeys, demoMonthSummary } from '@/data/monthlyAnalytics'
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

const route = useRoute()
const LATEST_MONTH = '2026-06'
const selectedMonth = ref(null)
const isMonthMenuOpen = ref(false)

// 소비계획에서 ?month=YYYY-MM 으로 넘어오면 그 달 분석을 보여준다
function applyMonthFromRoute() {
  const month = String(route.query.month || '')
  if (!/^\d{4}-\d{2}$/.test(month)) return
  selectedMonth.value = month === LATEST_MONTH ? null : month
  dialYear.value = Number(month.slice(0, 4))
  dialMonth.value = Number(month.slice(5, 7))
}
watch(() => route.query.month, applyMonthFromRoute)

const safeSummary = computed(() => {
  if (selectedMonth.value) {
    return demoMonthSummary(selectedMonth.value) || buildMockSummary(selectedMonth.value)
  }
  return summary.value || (isLoading.value ? buildEmptySummary() : buildMockSummary())
})

const periodMonthKey = computed(() => safeSummary.value.period?.currentMonth || LATEST_MONTH)
const periodYear = computed(() => Number(periodMonthKey.value.split('-')[0]))
const periodMonthNum = computed(() => Number(periodMonthKey.value.split('-')[1]))

const dialYears = [2025, 2026]
const dialMonths = Array.from({ length: 12 }, (_, i) => i + 1)
const dialYear = ref(2026)
const dialMonth = ref(6)

const DIAL_ITEM_H = 36
const yearColRef = ref(null)
const monthColRef = ref(null)

function openMonthMenu() {
  dialYear.value = periodYear.value
  dialMonth.value = periodMonthNum.value
  isMonthMenuOpen.value = true
}

function applyDial(year, monthNum) {
  dialYear.value = year
  dialMonth.value = monthNum
  const key = `${year}-${String(monthNum).padStart(2, '0')}`
  selectedMonth.value = key === LATEST_MONTH ? null : key
}

watch(isMonthMenuOpen, async (open) => {
  if (!open) return
  await nextTick()
  if (yearColRef.value) yearColRef.value.scrollTop = dialYears.indexOf(dialYear.value) * DIAL_ITEM_H
  if (monthColRef.value) monthColRef.value.scrollTop = dialMonths.indexOf(dialMonth.value) * DIAL_ITEM_H
})

let yearScrollTimer = null
let monthScrollTimer = null

function onYearScroll() {
  clearTimeout(yearScrollTimer)
  yearScrollTimer = setTimeout(() => {
    const idx = Math.round((yearColRef.value?.scrollTop || 0) / DIAL_ITEM_H)
    const year = dialYears[Math.max(0, Math.min(dialYears.length - 1, idx))]
    if (year && year !== dialYear.value) applyDial(year, dialMonth.value)
  }, 110)
}

function onMonthScroll() {
  clearTimeout(monthScrollTimer)
  monthScrollTimer = setTimeout(() => {
    const idx = Math.round((monthColRef.value?.scrollTop || 0) / DIAL_ITEM_H)
    const monthNum = dialMonths[Math.max(0, Math.min(dialMonths.length - 1, idx))]
    if (monthNum && monthNum !== dialMonth.value) applyDial(dialYear.value, monthNum)
  }, 110)
}

function isRecurring(category) {
  return recurringOverrides.value.includes(category)
}
const aiAnalysis = computed(() => safeSummary.value.aiAnalysis || null)
const spendingTrend = computed(() => safeSummary.value.spendingTrend || null)
const totalExpense = computed(() => Number(safeSummary.value.totalExpense || 0))
const expectedSaving = computed(() =>
  (aiAnalysis.value?.savingOpportunities || []).reduce((sum, item) => sum + Number(item.amount || 0), 0),
)
const topRecommendation = computed(() => recommendationBundle.value?.results?.[0] || null)
const topRecommendationEconomics = computed(() => topRecommendation.value?.economics || {})

const RECO_FIELD_RULES = [
  [/배달|요기요|배민|배달의민족|쿠팡이츠/, '배달앱', '🛵'],
  [/카페|커피|베이커리|디저트|스타벅스/, '카페', '☕'],
  [/음식|외식|식당|맛집|푸드|레스토랑|식비/, '음식점', '🍽️'],
  [/편의점/, '편의점', '🏪'],
  [/교육|학원|학습|어학|등록금/, '교육', '✏️'],
  [/해외|국내외|글로벌/, '국내외', '🌐'],
  [/항공|여행|면세|숙박|호텔/, '여행', '✈️'],
  [/통신|휴대폰|모바일|요금제|유플러스|lg\s?u\+|skt|\bkt\b|\bu\+/i, '통신', '📡'],
  [/간편결제|간편|네이버페이|카카오페이|페이코|\bpay\b/i, '간편결제', '💳'],
  [/주유|충전소/, '주유', '⛽'],
  [/교통|대중교통|지하철|버스|택시|주차/, '교통', '🚇'],
  [/병원|의료|약국|건강|치과/, '의료', '🏥'],
  [/마트|마켓|백화점|쿠팡|이마트/, '쇼핑', '🛒'],
  [/쇼핑|아울렛/, '쇼핑', '🛍️'],
  [/뷰티|화장품|미용/, '뷰티', '💄'],
  [/영화|공연|도서|서점|문화|cgv/i, '문화', '🎬'],
  [/구독|스트리밍|넷플릭스|ott/i, '구독', '📺'],
  [/관리비|공과금|아파트|생활/, '생활', '🏠'],
]

function classifyRecoField(raw) {
  const text = String(raw || '')
  for (const [re, label, icon] of RECO_FIELD_RULES) {
    if (re.test(text)) return { label, icon }
  }
  const clean = text.replace(/\s*(업종|가맹점|에서|최대|이용|결제|할인|적립).*$/, '').trim()
  return { label: clean || '기본', icon: '💳' }
}

function categoryIcon(name) {
  return classifyRecoField(name).icon
}

function recoBenefitRows(reco) {
  const items = reco?.benefitItems || []
  const rows = []
  const seen = new Set()
  items.forEach((item, index) => {
    const rate = Number(item.ratePercent ?? item.rate_percent ?? 0)
    const amount = Number(item.amountKrw ?? item.amount_krw ?? 0)
    const raw = String(item.scope || item.label || (item.categories || [])[0] || '')
    const { label, icon } = classifyRecoField(raw)
    if (seen.has(label)) return
    seen.add(label)
    const cap = Number(item.monthlyBenefitLimitKrw ?? item.monthly_benefit_limit_krw ?? 0)
    rows.push({
      id: item.id || item.benefitId || `${label}-${index}`,
      field: label,
      icon,
      value: rate > 0 ? `최대 ${Number(rate.toFixed(1))}% 할인` : (amount > 0 ? `${krw(amount)} 할인` : '혜택 확인'),
      cap: cap > 0 ? `월 최대 ${krw(cap)}` : '',
    })
  })
  return rows.slice(0, 3)
}

// 카드가 "매달"로 표시된 분야 혜택을 얼마나 커버하는지 점수화
function recoRecurringScore(reco, recurringSet) {
  if (!recurringSet.size) return 0
  const fields = new Set()
  ;(reco?.benefitItems || []).forEach((item) => {
    const raw = String(item.scope || item.label || (item.categories || [])[0] || '')
    fields.add(classifyRecoField(raw).label)
    ;(item.categories || []).forEach((c) => fields.add(String(c)))
  })
  let score = 0
  recurringSet.forEach((cat) => {
    fields.forEach((field) => {
      if (field === cat || field.includes(cat) || cat.includes(field)) score += 1
    })
  })
  return score
}

// 1·2순위 추천 카드. 반복지출(매달) 선택에 맞춰 해당 분야를 커버하는 카드를 우선 정렬한다.
const recommendationCards = computed(() => {
  const recurring = new Set(recurringOverrides.value)
  return [...(recommendationBundle.value?.results || [])]
    .map((reco, index) => ({ reco, index, score: recoRecurringScore(reco, recurring) }))
    .sort((a, b) => (b.score - a.score) || (a.index - b.index))
    .slice(0, 2)
    .map(({ reco }, rank) => {
      const gain = Number(reco?.economics?.monthlyDelta || 0)
      const required = Number(reco?.previousMonthMinSpend ?? reco?.previous_month_min_spend ?? 0)
      return {
        id: reco.id || reco.cardAdId || `reco-${rank}`,
        rank: rank + 1,
        name: reco.name,
        imageUrl: reco.imageUrl,
        gain: gain > 0 ? `+${krw(gain)}` : '',
        requiredSpend: required > 0 ? krw(required) : '실적 없음',
        benefits: recoBenefitRows(reco),
      }
    })
})

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

// 직전 달 카테고리(증감 비교) — 데모 데이터에서 가져온다
const previousMonthCategories = computed(() => {
  const key = periodMonthKey.value
  const keys = demoMonthKeys()
  let prevKey = null
  if (key === LATEST_MONTH) prevKey = '2026-05'
  else {
    const idx = keys.indexOf(key)
    if (idx > 0) prevKey = keys[idx - 1]
  }
  return prevKey ? demoMonthCategories(prevKey) : null
})

const mostIncreasedCategory = computed(() => {
  const prev = previousMonthCategories.value
  if (!prev) return null
  let best = null
  rawCategoryRows.value.forEach((row) => {
    const before = Number(prev[row.category] || 0)
    const diff = Number(row.amount || 0) - before
    if (before > 0 && diff > 0 && (!best || diff > best.diff)) {
      best = { category: row.category, diff, pct: Math.round((diff / before) * 100) }
    }
  })
  return best
})

const heroInsight = computed(() => {
  const top = topCategory.value
  if (!top) return ''
  const inc = mostIncreasedCategory.value
  if (inc && inc.category !== top.category) {
    return `${top.category} 최다 지출 · 지난달보다 ${inc.category} +${inc.pct}% ↑`
  }
  if (inc) {
    return `${top.category}에 가장 많이 썼어요 · 지난달보다 +${inc.pct}% ↑`
  }
  return `${top.category}에 가장 많이 썼어요`
})

const heroInsightColor = computed(() => topCategory.value?.color || '#0f5fae')

const heroMessage = computed(() => {
  if (!totalExpense.value) return '결제 내역을 쌓으면 소비 성향이 선명하게 보여요.'
  if (!topCategory.value) return '이번 달 소비 데이터를 정리했습니다.'
  return `${topCategory.value.category} 비중이 가장 높아서 이 항목의 카드 혜택을 먼저 보면 좋아요.`
})

const oneTimeCandidates = computed(() => spendingTrend.value?.oneTimeCandidates || [])
const reviewCandidates = computed(() => spendingTrend.value?.reviewCandidates || oneTimeCandidates.value)
const pendingReviewCandidates = computed(() => reviewCandidates.value)

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
      tone: 'improve',
    },
  ]
})

const cardLookup = computed(() => {
  const map = new Map()
  mockCards.forEach((card) => {
    map.set(String(card.id), card)
    if (card.cardAdId != null) map.set(String(card.cardAdId), card)
  })
  return map
})

function resolveCardMeta(cardId, fallbackName) {
  const card = cardLookup.value.get(String(cardId))
  return {
    name: card?.name || fallbackName || `카드 ${cardId}`,
    imageUrl: card?.imageUrl || '',
  }
}

// 세로 카드 이미지를 가로 썸네일에 맞춰 회전(메인 분야별추천 썸네일과 동일 방식)
const thumbOrientation = ref({})
function onThumbLoad(key, event) {
  const img = event.target
  const orientation = img.naturalWidth > img.naturalHeight ? 'is-landscape' : 'is-portrait'
  thumbOrientation.value = { ...thumbOrientation.value, [key]: orientation }
}

const cardRows = computed(() => {
  const insightRows = aiAnalysis.value?.cardInsights || []
  const sourceRows = insightRows.length
    ? insightRows.map((item) => ({
      id: item.cardId || item.cardName,
      ...resolveCardMeta(item.cardId, item.cardName),
      amount: Number(item.amount || 0),
    }))
    : (safeSummary.value.byCard || []).map((item) => ({
      id: item.cardId,
      ...resolveCardMeta(item.cardId),
      amount: Number(item.amount || 0),
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

function buildMockSummary(monthKey = null) {
  const inMonth = (tx) => !monthKey || String(tx.date || '').slice(0, 7) === monthKey
  const expenses = mockTransactions.filter((tx) => Number(tx.amt) < 0 && inMonth(tx))
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
      .filter((tx) => Number(tx.amt) > 0 && inMonth(tx))
      .reduce((sum, tx) => sum + Number(tx.amt || 0), 0),
    byCategory,
    byCard,
    period: { currentMonth: monthKey || '2026-06' },
    spendingTrend: {
      currentMonth: monthKey || '2026-06',
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
  writeStoredList(RECURRING_STORAGE_KEY, recurringOverrides.value)
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

onMounted(() => {
  applyMonthFromRoute()
  loadSummary()
})
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
  padding: 10px clamp(14px, 4.6vw, 20px) 120px;
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
  display: block;
  overflow: visible;
  border: 1px solid rgba(36, 54, 79, 0.08) !important;
  border-radius: 22px !important;
  padding: 14px 18px 16px !important;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(238, 247, 250, 0.9)),
    radial-gradient(circle at 100% 0%, rgba(0, 140, 149, 0.16), transparent 40%) !important;
  box-shadow: 0 16px 34px rgba(36, 54, 79, 0.08) !important;
}

.hero-amount {
  display: block;
  margin-top: 7px;
  color: #17202b;
  font-size: 34px;
  /* 소비계획 '이번 달 사용' 금액(.cs-amount)과 동일한 렌더 굵기로 통일 */
  font-weight: 500;
  letter-spacing: 0;
  line-height: 1.05;
}

.hero-insight {
  display: inline-flex;
  align-items: center;
  margin: 9px 0 0;
  font-size: 12px;
  font-weight: 850;
  line-height: 1.4;
  word-break: keep-all;
}

.hero-month {
  position: relative;
  display: inline-flex;
  align-items: baseline;
  gap: 5px;
  margin-bottom: 2px;
}

.month-suffix {
  color: #5f6b77;
  font-size: 13px;
  font-weight: 850;
}

.month-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  border: 0;
  border-radius: 999px;
  padding: 4px 9px 4px 11px;
  background: rgba(15, 95, 174, 0.1);
  color: #0f5fae;
  font-size: 12px;
  font-weight: 950;
  cursor: pointer;
}

.month-backdrop {
  position: fixed;
  inset: 0;
  z-index: 20;
}

.month-dial {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  z-index: 21;
  width: 196px;
  border-radius: 16px;
  padding: 10px 12px 12px;
  background: #fff;
  box-shadow: 0 18px 40px rgba(36, 54, 79, 0.2);
}

.dial-cols {
  position: relative;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  height: 132px;
}

.dial-band {
  position: absolute;
  top: 48px;
  right: 12px;
  left: 12px;
  height: 36px;
  z-index: 0;
  border-radius: 10px;
  background: rgba(15, 95, 174, 0.09);
  pointer-events: none;
}

.dial-col {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  scroll-snap-type: y mandatory;
  padding: 48px 0;
}

.dial-item {
  flex: 0 0 36px;
  height: 36px;
  border: 0;
  background: transparent;
  color: #9aa6b3;
  font-size: 15px;
  font-weight: 800;
  scroll-snap-align: center;
  cursor: pointer;
  transition: color 140ms ease, transform 140ms ease;
}

.dial-item.sel {
  color: #0f5fae;
  font-weight: 950;
  transform: scale(1.08);
}

.dial-confirm {
  width: 100%;
  min-height: 36px;
  margin-top: 8px;
  border: 0;
  border-radius: 10px;
  background: #0f5fae;
  color: #fff;
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
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
  border: 0 !important;
  border-radius: 0 !important;
  padding: 2px 2px !important;
  background: transparent !important;
  box-shadow: none !important;
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
  font-weight: 500;
  letter-spacing: 0;
  line-height: 1.14;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.metric-tile.good strong {
  color: #15a34a;
}

.metric-tile.warning strong {
  color: #e5484d;
}

.metric-tile.improve strong {
  color: #0f5fae;
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

.rank-emoji {
  flex: 0 0 auto;
  font-size: 16px;
  font-style: normal;
  line-height: 1;
}

.rank-crown {
  flex: 0 0 auto;
  margin-left: 2px;
  font-size: 12px;
  font-style: normal;
  line-height: 1;
}

.category-rank-list {
  gap: 6px;
}

.category-rank-list li {
  padding: 7px 10px;
  border-radius: 12px;
}

.category-rank-list li.is-top {
  background: linear-gradient(90deg, rgba(196, 154, 73, 0.16), rgba(196, 154, 73, 0.03));
  box-shadow: inset 0 0 0 1px rgba(196, 154, 73, 0.22);
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
  font-weight: 500;
  white-space: nowrap;
}

.category-amount {
  display: flex;
  flex-shrink: 0;
  align-items: baseline;
  gap: 7px;
}

.category-amount em {
  color: #8a9aad;
  font-size: 11px;
  font-weight: 500;
  font-style: normal;
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
  gap: 11px;
  border-radius: 14px;
  padding: 10px 12px;
  background: #f5f8fb;
}

.card-usage-list li.is-top {
  background: linear-gradient(90deg, rgba(196, 154, 73, 0.18), rgba(196, 154, 73, 0.05));
  box-shadow: inset 0 0 0 1px rgba(196, 154, 73, 0.22);
}

.card-usage-thumb {
  position: relative;
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 40px;
  height: 26px;
  overflow: hidden;
  border-radius: 5px;
  background: #e8edf2;
  color: #8a9aad;
  box-shadow: 0 1px 4px rgba(36, 54, 79, 0.2);
}

.card-usage-thumb img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-usage-thumb img.is-portrait {
  inset: auto;
  top: 50%;
  left: 50%;
  width: 26px;
  height: 40px;
  max-width: none;
  transform: translate(-50%, -50%) rotate(-90deg);
}

.card-usage-copy {
  display: flex;
  align-items: center;
  gap: 5px;
  flex: 1 1 auto;
  min-width: 0;
}

.card-usage-copy strong {
  overflow: hidden;
  min-width: 0;
  color: #17202b;
  font-size: 14px;
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
  font-weight: 500;
}

.card-usage-value span {
  display: block;
  margin-top: 3px;
  color: #008c95;
  font-size: 11px;
  font-weight: 950;
}

.review-head {
  margin-bottom: 12px;
}

.review-head strong {
  display: block;
  color: #17202b;
  font-size: 15px;
  font-weight: 900;
}

.review-head small {
  display: block;
  margin-top: 3px;
  color: #7a8592;
  font-size: 11px;
  font-weight: 800;
}

.review-info {
  min-width: 0;
}

.review-info strong {
  display: block;
  color: #17202b;
  font-size: 13px;
  font-weight: 900;
}

.review-info span {
  display: block;
  margin-top: 2px;
  color: #5f6b77;
  font-size: 12px;
  font-weight: 500;
}

.review-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.review-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 11px;
  align-items: center;
  border-radius: 14px;
  padding: 11px 12px;
  background: #f5f8fb;
}

.review-emoji {
  flex: 0 0 auto;
  font-size: 18px;
  line-height: 1;
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
  grid-template-columns: auto auto;
  gap: 6px;
}

.review-toggle button {
  min-height: 33px;
  border: 1px solid rgba(36, 54, 79, 0.16);
  border-radius: 9px;
  padding: 0 12px;
  background: #fff;
  color: #8a95a3;
  font-size: 12px;
  font-weight: 900;
  white-space: nowrap;
  touch-action: manipulation;
  transition: transform 120ms ease, background 140ms ease, color 140ms ease;
}

.review-toggle button.active {
  border-color: transparent;
  background: #24364f;
  color: #fff;
}

.review-toggle button.is-recurring.active {
  background: #0f5fae;
}

.review-toggle button:active {
  transform: scale(0.95);
}

.recommendation-card {
  background:
    linear-gradient(180deg, rgba(240, 253, 250, 0.88), rgba(255, 255, 255, 0.86)) !important;
}

.rec-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.rec-thumb {
  position: relative;
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 46px;
  height: 30px;
  overflow: hidden;
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.85);
  color: #008c95;
  box-shadow: 0 2px 8px rgba(36, 54, 79, 0.16);
}

.rec-thumb img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.rec-thumb img.is-portrait {
  inset: auto;
  top: 50%;
  left: 50%;
  width: 30px;
  height: 46px;
  max-width: none;
  transform: translate(-50%, -50%) rotate(-90deg);
}

.rec-head-copy {
  flex: 1 1 auto;
  min-width: 0;
}

.rec-head-copy strong {
  display: block;
  overflow: hidden;
  color: #17202b;
  font-size: 15px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rec-head-copy small {
  display: block;
  margin-top: 2px;
  color: #15a34a;
  font-size: 11.5px;
  font-weight: 900;
}

.rec-section {
  margin-top: 12px;
}

.rec-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2px;
  padding: 0 2px;
}

.rec-section-head strong {
  color: #17202b;
  font-size: 15px;
  font-weight: 900;
}

.rec-section-head a {
  color: #0f5fae;
  font-size: 12px;
  font-weight: 800;
  text-decoration: none;
}

.rec-rank {
  flex: 0 0 auto;
  align-self: flex-start;
  border-radius: 999px;
  padding: 3px 9px;
  font-size: 11px;
  font-weight: 950;
}

.rec-rank.rank-1 {
  background: rgba(196, 154, 73, 0.16);
  color: #b5852b;
}

.rec-rank.rank-2 {
  background: rgba(36, 54, 79, 0.1);
  color: #44546b;
}

.rec-gain {
  flex: 0 0 auto;
  color: #15a34a;
  font-size: 15px;
  font-weight: 900;
}

.rec-gain i {
  margin-left: 1px;
  color: #7a8592;
  font-size: 11px;
  font-weight: 800;
  font-style: normal;
}

.rec-benefits {
  display: flex;
  flex-direction: column;
}

.rec-benefit-row {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 9px 2px;
  border-bottom: 1px solid rgba(36, 54, 79, 0.07);
}

.rec-benefit-row:last-child {
  border-bottom: 0;
}

.rec-benefit-emoji {
  flex: 0 0 auto;
  font-size: 19px;
  line-height: 1;
}

.rec-benefit-main {
  flex: 1 1 auto;
  min-width: 0;
}

.rec-benefit-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}

.rec-benefit-top strong {
  color: #17202b;
  font-size: 13px;
  font-weight: 800;
}

.rec-benefit-top b {
  flex: 0 0 auto;
  color: #008c95;
  font-size: 13px;
  font-weight: 800;
}

.rec-benefit-main span {
  display: block;
  margin-top: 2px;
  color: #8a95a3;
  font-size: 11px;
  font-weight: 800;
}

.rec-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 12px;
  padding-top: 11px;
  border-top: 1px solid rgba(36, 54, 79, 0.08);
}

.rec-foot > span {
  color: #5f6b77;
  font-size: 12px;
  font-weight: 800;
}

.rec-foot > span i {
  margin-right: 6px;
  padding: 2px 6px;
  border-radius: 6px;
  background: rgba(15, 95, 174, 0.1);
  color: #0f5fae;
  font-size: 10px;
  font-weight: 900;
  font-style: normal;
}

.rec-foot a {
  flex: 0 0 auto;
  color: #0f5fae;
  font-size: 12px;
  font-weight: 900;
  text-decoration: none;
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
