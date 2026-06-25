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

      <div class="hero-sticky">
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
      </div>

      <section v-if="hasUsableAnalysis" class="metric-row" aria-label="분석 핵심 지표">
        <article v-for="metric in metricCards" :key="metric.label" class="metric-tile" :class="metric.tone">
          <small>{{ metric.label }}</small>
          <strong>{{ metric.value }}</strong>
          <span>{{ metric.caption }}</span>
        </article>
      </section>

      <article v-if="hasCategoryData" class="analysis-card app-card category-card">
        <p class="rank-card-title"><span class="rank-accent" :style="{ color: topCategory?.color }">{{ categoryRankName }}</span>에 가장 많이 썼어요</p>
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
        <p class="rank-card-title"><span class="rank-accent">{{ cardUsageName }}</span> 카드를 가장 많이 썼어요</p>
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

      <section v-if="aiRecommendations.length" class="ai-reco-section">
        <div class="section-head split">
          <h2>카테고리별 추천 카드</h2>
          <RouterLink class="detail-link" to="/recommendations/usage">
            <Search :size="14" />
            <span>자세히 보기</span>
          </RouterLink>
        </div>

        <div class="ai-reco-card">
          <div class="ai-speech">
            <img class="ai-magpie" src="/card-images/magpie-face2.png" alt="카치AI" />
            <div class="ai-bubble">
              <template v-if="aiBubbleCard">보유 카드 중 <b class="bubble-cat">{{ aiBubbleLead }}</b>엔 <b class="bubble-card">{{ aiBubbleCard }}</b>로 결제하는 게 가장 이득이에요!</template>
              <template v-else>{{ aiBubble }}</template>
            </div>
          </div>

          <ul class="ai-reco-list">
            <li v-for="rec in aiRecommendations" :key="rec.category.id" class="ai-reco-item">
              <span class="ai-reco-thumb">
                <img
                  v-if="rec.card.imageUrl"
                  :src="rec.card.imageUrl"
                  :alt="rec.card.name"
                  :class="thumbOrientation['ai-' + rec.card.id]"
                  @load="onThumbLoad('ai-' + rec.card.id, $event)"
                />
                <CreditCard v-else :size="14" />
              </span>
              <div class="ai-reco-body">
                <div class="ai-reco-line">
                  <span class="ai-reco-cat">{{ rec.category.icon }} {{ rec.category.name }}</span>
                  <em class="ai-reco-status" :class="rec.performanceTone">{{ rec.performanceShort }}</em>
                </div>
                <strong>{{ rec.card.name }}</strong>
                <small>{{ rec.benefitText }}</small>
              </div>
              <b class="ai-reco-benefit" :class="{ muted: rec.benefit <= 0 }">
                {{ rec.benefit > 0 ? `+${krw(rec.benefit)}` : `최대 +${krw(rec.grossBenefit)}` }}
              </b>
            </li>
          </ul>
        </div>
      </section>

      <section class="section-block budget-trend-section">
        <div class="section-head">
          <h2>나의 예산</h2>
        </div>

        <div class="app-card trend-card">
          <div class="bar-legend">
            <span><i class="dot budget"></i>예산</span>
            <span><i class="dot spent"></i>사용</span>
          </div>
          <svg class="bar-svg" :viewBox="`0 0 ${barChart.w} ${barChart.h}`">
            <g
              v-for="b in barChart.bars"
              :key="b.label"
              class="bar-col"
              @click="goMonth(b)"
            >
              <rect class="bar-hit" :x="b.hx" y="0" :width="b.hw" :height="barChart.h" fill="transparent" />
              <rect :x="b.cx - b.barW / 2" :y="b.budgetY" :width="b.barW" :height="b.budgetH" rx="5" fill="#e3e9f1" />
              <rect :x="b.cx - b.barW / 2" :y="b.spentY" :width="b.barW" :height="b.spentH" rx="5" :fill="b.color" />
              <text
                :x="b.cx"
                :y="b.tagY"
                text-anchor="middle"
                class="bar-tag"
                :class="b.remaining < 0 ? 'over' : 'left'"
              >{{ b.remaining < 0 ? `-${shortKrw(-b.remaining)}` : `+${shortKrw(b.remaining)}` }}</text>
              <text :x="b.cx" :y="barChart.h - 9" text-anchor="middle" class="bar-month" :class="{ cur: b.current }">{{ b.label }}</text>
            </g>
          </svg>

          <div class="trend-months">
            <div class="tm-row tm-head">
              <span>월</span>
              <span>사용</span>
              <span>예산</span>
              <span>잔액</span>
            </div>
            <div
              v-for="m in barChart.bars"
              :key="m.label"
              class="tm-row tm-clickable"
              :class="{ cur: m.current }"
              role="button"
              tabindex="0"
              @click="goMonth(m)"
              @keyup.enter="goMonth(m)"
            >
              <span class="tm-month">{{ m.label }}</span>
              <span>{{ shortKrw(m.spent) }}</span>
              <span class="tm-budget">{{ shortKrw(m.budget) }}</span>
              <span :class="m.remaining < 0 ? 'neg' : 'pos'">
                {{ m.remaining < 0 ? '-' : '+' }}{{ shortKrw(Math.abs(m.remaining)) }}
              </span>
            </div>
          </div>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { BarChart3, ChevronDown, CreditCard, RefreshCw, Search, Sparkles } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { cards as mockCards, krw, transactions as mockTransactions } from '@/data/mockData'
import { demoMonthCategories, demoMonthKeys, demoMonthSummary } from '@/data/monthlyAnalytics'
import { fetchBudget, fetchCardRecommendationBundle, fetchMonthlySpending, fetchSpendingSummary } from '@/services/api'
import { budgetRiskColor } from '@/utils/budgetRisk'

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
const router = useRouter()
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

function shiftMonthKey(monthKey, diff) {
  const [year, month] = String(monthKey || LATEST_MONTH).split('-').map(Number)
  const date = new Date(year, month - 1 + diff, 1)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
}

function shortMonthLabel(monthKey) {
  const month = Number(String(monthKey || '').slice(5, 7))
  return month ? `${month}월` : '지난달'
}

const totalMonthComparison = computed(() => {
  const total = spendingTrend.value?.total || {}
  const current = Number(total.current ?? totalExpense.value ?? 0)
  const previousMonth = spendingTrend.value?.previousMonth || shiftMonthKey(periodMonthKey.value, -1)
  const seriesPrevious = Array.isArray(monthlySeries.value)
    ? monthlySeries.value.find((item) => String(item.month) === previousMonth)
    : null
  const previous = Number(seriesPrevious?.spent ?? total.previous ?? 0)
  const delta = current - previous
  return { current, previous, previousMonth, delta }
})

// 상단(hero)은 전체 소비 금액의 전월 대비 증감만 보여준다.
const totalMonthDelta = computed(() => {
  const { previous, delta } = totalMonthComparison.value
  if (!previous || !delta) return null
  const pct = Math.round((Math.abs(delta) / previous) * 100)
  if (!pct) return null
  return { pct, up: delta > 0 }
})

const heroInsight = computed(() => {
  const d = totalMonthDelta.value
  if (!d) return ''
  return `지난달보다 ${d.up ? '+' : '-'}${d.pct}% ${d.up ? '↑' : '↓'}`
})

const heroInsightColor = computed(() => {
  const d = totalMonthDelta.value
  if (!d) return '#0f5fae'
  return d.up ? '#d2624a' : '#0c8f6e'
})

// 목록 위 제목에서 색을 다르게 줄 동적 부분(바뀌는 값)
const categoryRankName = computed(() => topCategory.value?.category || '카테고리')
const cardUsageName = computed(() => cardRows.value[0]?.name || '카드')

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
  const monthComparison = totalMonthComparison.value
  return [
    {
      label: '전체 전월 대비',
      value: signedKrw(monthComparison.delta),
      caption: `${shortMonthLabel(monthComparison.previousMonth)} 사용액 기준`,
      tone: Number(monthComparison.delta || 0) > 0 ? 'warning' : 'good',
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

// ── AI 카드 추천 (소비계획 탭에서 이동) — 분석이 이미 가진 추천 번들 재사용 ──
const CATEGORY_EMOJI = {
  식비: '🥗', 외식: '🥗', 카페: '☕', 쇼핑: '🛍️', 뷰티: '💄', 교통: '🚇', 교육: '📚',
  편의점: '🏪', 문화: '🎬', 헬스: '🏋️', 생활: '🏠', 통신: '📡', 구독: '📺',
}
function categoryEmoji(name) {
  return CATEGORY_EMOJI[String(name || '').trim()] || '💳'
}
function mapGuideToReco(item, index) {
  const label = String(item.category || '추천 분야').replace(/\s+/g, ' ').trim()
  const card = {
    id: item.cardId,
    name: item.cardName,
    imageUrl: item.imageUrl,
    benefitSummary: item.benefitLabel,
  }
  const eligible = Boolean(item.eligibleForBenefit)
  const nextMonth = Boolean(item.nextMonthEligible)
  return {
    category: { id: `guide-${label}-${index}`, name: label, icon: categoryEmoji(label) },
    card,
    benefitText: item.benefitLabel || card.benefitSummary || '혜택 확인',
    benefit: eligible ? Number(item.estimatedBenefit || 0) : 0,
    grossBenefit: Number(item.potentialBenefit || item.estimatedBenefit || 0),
    performanceShort: eligible ? '이번 달 가능' : nextMonth ? '다음 달 충족' : '준비 필요',
    performanceTone: eligible || nextMonth ? 'is-ready' : 'is-waiting',
  }
}
const aiRecommendations = computed(() => {
  const guides = recommendationBundle.value?.ownedCategoryGuides
  return Array.isArray(guides) && guides.length ? guides.map(mapGuideToReco).slice(0, 3) : []
})
const aiBubbleLead = computed(() => aiRecommendations.value[0]?.category.name || '')
const aiBubbleCard = computed(() => aiRecommendations.value[0]?.card.name || '')
const aiBubble = computed(() => '카드별 혜택을 비교해서 알뜰하게 써봐요!')

// ── 나의 예산 추이 (소비계획 탭에서 이동) ──
const CURRENT_MONTH = '2026-06'
const DEFAULT_BUDGET_GOAL = 1400000
const budgetGoal = ref(null)
const monthlySeries = ref(null)
async function loadBudgetGoal() {
  try {
    const data = await fetchBudget(CURRENT_MONTH)
    if (data && data.totalGoal != null) budgetGoal.value = Number(data.totalGoal)
  } catch {
    // 백엔드 예산 없으면 기본값 사용
  }
}
async function loadMonthly() {
  try {
    const data = await fetchMonthlySpending(5)
    if (data && Array.isArray(data.months) && data.months.length) monthlySeries.value = data.months
  } catch {
    // 실패 시 데모 데이터로 폴백
  }
}
// 이번 달 사용액은 항상 현재 달 summary 기준(월 선택과 무관하게 막대 6월 고정)
const currentMonthExpense = computed(() => Number(summary.value?.totalExpense ?? 0) || (demoMonthSummary(CURRENT_MONTH)?.totalExpense ?? 0))
const liveBudget = computed(() => {
  const series = monthlySeries.value
  let goal = budgetGoal.value
  if (goal == null && series && series.length) {
    const june = series.find((m) => String(m.month) === CURRENT_MONTH)
    if (june && june.budget != null) goal = Number(june.budget)
  }
  const budget = goal != null ? goal : DEFAULT_BUDGET_GOAL
  const spent = currentMonthExpense.value
  return { budget, spent, remaining: budget - spent }
})
function shortKrw(value) {
  if (value >= 10000) return `${Math.round(value / 10000).toLocaleString()}만`
  return krw(value)
}
const barChart = computed(() => {
  const monthBudget = { '2026-02': 600000, '2026-03': 700000, '2026-04': 700000, '2026-05': 750000 }
  const series = monthlySeries.value
  const months = (series && series.length)
    ? series.map((m) => {
      const ym = String(m.month)
      const isCurrent = ym === CURRENT_MONTH
      return {
        label: `${Number(ym.slice(5, 7))}월`,
        ym,
        current: isCurrent,
        budget: isCurrent ? liveBudget.value.budget : Number(m.budget || 0),
        spent: isCurrent ? liveBudget.value.spent : Number(m.spent || 0),
      }
    })
    : [
      { label: '2월', ym: '2026-02' },
      { label: '3월', ym: '2026-03' },
      { label: '4월', ym: '2026-04' },
      { label: '5월', ym: '2026-05' },
      { label: '6월', ym: '2026-06', current: true },
    ].map((m) => (m.current
      ? { ...m, budget: liveBudget.value.budget, spent: liveBudget.value.spent }
      : { ...m, budget: monthBudget[m.ym] || 0, spent: demoMonthSummary(m.ym)?.totalExpense || 0 }))
  const w = 320
  const h = 168
  const padTop = 28
  const padBottom = 28
  const padX = 10
  const baseY = h - padBottom
  const usableH = baseY - padTop
  const max = Math.max(...months.flatMap((m) => [m.budget, m.spent])) * 1.16 || 1
  const slot = (w - padX * 2) / months.length
  const barW = Math.min(30, slot * 0.5)
  const bars = months.map((m, i) => {
    const cx = padX + slot * i + slot / 2
    const hx = padX + slot * i
    const budgetH = (m.budget / max) * usableH
    const spentH = (m.spent / max) * usableH
    const budgetY = baseY - budgetH
    const spentY = baseY - spentH
    const pct = m.budget ? Math.round((m.spent / m.budget) * 100) : 0
    const remaining = m.budget - m.spent
    return {
      ...m, cx, hx, hw: slot, barW, budgetY, budgetH, spentY, spentH,
      color: budgetRiskColor(pct), remaining, tagY: Math.min(budgetY, spentY) - 6,
    }
  })
  return { w, h, baseY, bars }
})
function goMonth(month) {
  router.push({ path: '/analytics', query: { month: month.ym } })
}

onMounted(() => {
  applyMonthFromRoute()
  loadSummary()
  loadBudgetGoal()
  loadMonthly()
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
  padding: 0 clamp(14px, 4.6vw, 20px) 120px;
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

/* 소비계획 헤더처럼: 전체 너비 불투명 띠가 고정되어 뒤 콘텐츠가 비치지 않게 */
.hero-sticky {
  position: sticky;
  top: 0;
  z-index: 20;
  margin: 0 calc(-1 * clamp(14px, 4.6vw, 20px));
  padding: 12px clamp(14px, 4.6vw, 20px);
  background: var(--carch-page);
}

.analysis-hero {
  display: block;
  overflow: visible;
}

.app-backdrop .phone-shell .analytics-body .analysis-hero {
  border: 0 !important;
  border-radius: 22px !important;
  padding: 14px 18px 16px !important;
  background: linear-gradient(135deg, #ffffff 0%, #e9f2f6 100%) !important;
  box-shadow: none !important;
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

.rank-card-title {
  margin: 0 0 11px;
  color: #8a95a3;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.4;
  word-break: keep-all;
}

.rank-card-title .rank-accent {
  color: #0f5fae;
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

/* ── 소비계획 탭에서 이동: AI 카드 추천 + 나의 예산 추이 ── */
.ai-reco-section {
  margin-top: 14px;
}

.section-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 14px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.section-head.split {
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 11px;
}

.section-head h2 {
  margin: 0;
  color: #20242a;
  font-size: 19px;
  font-weight: 900;
}

.section-head a {
  flex-shrink: 0;
  color: #0f5fae;
  font-size: 12px;
  font-weight: 900;
  text-decoration: none;
}

.detail-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.detail-link svg {
  margin-top: -1px;
}

.ai-reco-card {
  border-radius: 18px;
  padding: 14px;
  background:
    radial-gradient(circle at 10% -4%, rgba(99, 102, 241, 0.12), transparent 42%),
    radial-gradient(circle at 102% 6%, rgba(56, 189, 248, 0.14), transparent 46%),
    linear-gradient(158deg, #f2f8ff 0%, #eef3ff 52%, #f4f0ff 100%);
  box-shadow: 0 12px 26px rgba(60, 80, 160, 0.09);
}

.ai-speech {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  margin-bottom: 12px;
}

.ai-magpie {
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  object-fit: cover;
  background: #fff;
  box-shadow: 0 3px 9px rgba(36, 54, 79, 0.16);
}

.ai-bubble {
  position: relative;
  align-self: center;
  border-radius: 14px;
  padding: 9px 13px;
  background: #ffffff;
  color: #2a3441;
  font-size: 12.5px;
  font-weight: 650;
  line-height: 1.4;
  letter-spacing: -0.3px;
  box-shadow: 0 5px 14px rgba(60, 80, 160, 0.1);
}

.ai-bubble::before {
  content: '';
  position: absolute;
  top: 50%;
  left: -5px;
  width: 11px;
  height: 11px;
  background: #ffffff;
  border-radius: 2px;
  transform: translateY(-50%) rotate(45deg);
}

.ai-bubble .bubble-cat {
  color: #2a3441;
  font-weight: 800;
}

.ai-bubble .bubble-card {
  color: #0f5fae;
  font-weight: 800;
}

.ai-reco-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.ai-reco-item {
  display: flex;
  align-items: center;
  gap: 11px;
  border-radius: 13px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 6px 16px rgba(36, 54, 79, 0.045);
}

.ai-reco-thumb {
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

.ai-reco-thumb img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.ai-reco-thumb img.is-portrait {
  inset: auto;
  top: 50%;
  left: 50%;
  width: 26px;
  height: 40px;
  max-width: none;
  transform: translate(-50%, -50%) rotate(-90deg);
}

.ai-reco-body {
  flex: 1 1 auto;
  min-width: 0;
}

.ai-reco-line {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 2px;
}

.ai-reco-cat {
  color: #0f5fae;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: -0.2px;
}

.ai-reco-status {
  border-radius: 999px;
  padding: 2px 7px;
  font-size: 9.5px;
  font-weight: 700;
  font-style: normal;
}

.ai-reco-status.is-ready {
  background: rgba(22, 163, 74, 0.12);
  color: #15803d;
}

.ai-reco-status.is-waiting {
  background: rgba(245, 158, 11, 0.15);
  color: #b45309;
}

.ai-reco-body strong {
  display: block;
  overflow: hidden;
  color: #1c2530;
  font-size: 13.5px;
  font-weight: 750;
  letter-spacing: -0.3px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ai-reco-body small {
  display: block;
  margin-top: 2px;
  color: #6e7885;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: -0.2px;
}

.ai-reco-benefit {
  flex-shrink: 0;
  color: #16a34a;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: -0.3px;
  font-variant-numeric: tabular-nums;
}

.ai-reco-benefit.muted {
  color: #9aa6b3;
  font-size: 11px;
  font-weight: 500;
}

.trend-card {
  display: block;
  padding: 14px 14px 13px;
  color: inherit;
  text-decoration: none;
}

.bar-legend {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-bottom: 2px;
}

.bar-legend span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: #6e7885;
  font-size: 10.5px;
  font-weight: 800;
}

.bar-legend .dot {
  width: 9px;
  height: 9px;
  border-radius: 3px;
}

.bar-legend .dot.budget {
  background: #e3e9f1;
}

.bar-legend .dot.spent {
  background: #f59e0b;
}

.bar-svg {
  display: block;
  width: 100%;
  height: auto;
  overflow: visible;
}

.bar-col {
  cursor: pointer;
}

.bar-hit {
  pointer-events: all;
}

.bar-col rect:not(.bar-hit) {
  transition: opacity 0.15s ease;
}

.bar-col:hover rect:not(.bar-hit) {
  opacity: 0.82;
}

.bar-tag {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: -0.2px;
}

.bar-tag.left {
  fill: #16a34a;
}

.bar-tag.over {
  fill: #e5484d;
}

.bar-month {
  fill: #9aa6b3;
  font-size: 9.5px;
  font-weight: 600;
  letter-spacing: -0.2px;
}

.bar-month.cur {
  fill: #20242a;
  font-weight: 800;
}

.trend-months {
  margin-top: 8px;
  border-top: 1px solid rgba(32, 36, 42, 0.075);
  padding-top: 8px;
}

.tm-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  align-items: center;
  padding: 5px 2px;
  font-size: 12px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.2px;
}

.tm-row span:not(:first-child) {
  text-align: right;
  color: #3a4452;
}

.tm-row .tm-budget {
  color: #9aa6b3;
}

.tm-clickable {
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.15s ease;
}

.tm-clickable:hover {
  background: rgba(15, 95, 174, 0.06);
}

.tm-head {
  padding-bottom: 4px;
  border-bottom: 1px solid rgba(32, 36, 42, 0.06);
}

.tm-head span {
  color: #9aa6b3 !important;
  font-size: 10.5px;
  font-weight: 700;
}

.tm-row .tm-month {
  color: #6e7885;
  font-weight: 700;
}

.tm-row.cur {
  border-radius: 8px;
  background: rgba(245, 158, 11, 0.08);
}

.tm-row.cur span,
.tm-row.cur .tm-month {
  color: #20242a;
  font-weight: 600;
}

.tm-row.cur .tm-budget {
  color: #6e7885;
}

.trend-months .tm-row .pos {
  color: #16a34a;
  font-weight: 500;
}

.trend-months .tm-row .neg {
  color: #e5484d;
  font-weight: 500;
}
</style>
