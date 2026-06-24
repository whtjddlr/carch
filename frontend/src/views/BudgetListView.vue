<template>
  <section class="screen">
    <header class="budget-list-header blue-gradient">
      <div class="header-row">
        <AppBackButton fallback="/cards" />
        <div>
          <h1>소비계획</h1>
        </div>
      </div>

      <div class="current-summary">
        <RouterLink class="cs-main" to="/budget/current" aria-label="6월 예산 상세 보기">
          <div class="cs-label">
            <span>이번 달 사용</span>
            <em
              class="cs-status"
              :style="{ color: riskColor, background: `${riskColor}1f` }"
            >{{ budgetRiskLabel(currentBudget.percent) }}</em>
          </div>
          <strong class="cs-amount">{{ krw(currentBudget.spent) }}</strong>
          <div class="cs-track">
            <i :style="{ width: `${budgetProgressWidth(currentBudget.percent)}%`, background: riskColor }" />
          </div>
          <div class="cs-meta">
            <em class="cs-pct" :style="{ color: riskColor }">{{ currentBudget.percent }}%</em>
            <em class="cs-remain" :style="{ color: riskColor }">
              {{ currentBudget.remaining < 0 ? `${krw(Math.abs(currentBudget.remaining))} 초과` : `${krw(currentBudget.remaining)} 남음` }}
            </em>
          </div>
        </RouterLink>

        <div class="cs-goal" :class="{ collapsed: headerCollapsed && !isEditingGoal }">
          <span>목표 금액</span>
          <div v-if="isEditingGoal" class="cs-goal-edit">
            <input
              class="cs-goal-input"
              type="number"
              inputmode="numeric"
              v-model.number="editGoal"
              @keyup.enter="saveGoal"
              ref="goalInput"
            />
            <button class="cs-goal-btn" type="button" aria-label="목표 금액 저장" @click="saveGoal">
              <Check :size="15" />
            </button>
          </div>
          <div v-else class="cs-goal-view">
            <strong>{{ krw(currentBudget.budget) }}</strong>
            <button class="cs-goal-btn" type="button" aria-label="목표 금액 수정" @click="startEditGoal">
              <Pencil :size="14" />
            </button>
          </div>
        </div>
      </div>
    </header>

    <div class="screen-scroll scrollbar-hide budget-list-body" @scroll="onScroll">
      <section v-if="cardUsageList.length" class="card-guide-section">
        <div class="section-head split">
          <h2>카드 현황</h2>
        </div>
        <div class="usecard-list">
          <article
            v-for="c in cardUsageList"
            :key="c.id"
            class="usecard"
            :class="{ 'not-eligible': !c.thisMonthOk }"
          >
            <div class="usecard-top">
              <span class="usecard-thumb">
                <img
                  v-if="c.imageUrl"
                  :src="c.imageUrl"
                  :alt="c.name"
                  :class="thumbOrientation[c.id]"
                  @load="onThumbLoad(c.id, $event)"
                />
                <CreditCard v-else :size="16" />
              </span>
              <div class="usecard-name">
                <strong>{{ c.name }}</strong>
                <small>{{ c.benefitTag }}</small>
              </div>
              <div class="usecard-flags">
                <span class="flag" :class="c.thisMonthOk ? 'on' : 'off'">
                  이번달 할인 {{ c.thisMonthOk ? '✓' : '✗' }}
                </span>
                <span class="flag" :class="c.nextMonthOk ? 'on' : 'wait'">
                  {{ c.nextMonthOk ? '실적 충족 ✓' : `실적 ${c.nextPct}%` }}
                </span>
              </div>
            </div>

            <div class="usecard-bars">
              <div class="ubar">
                <div class="ubar-head">
                  <span>사용 한도</span>
                  <b>{{ krw(c.spent) }} <i>/ {{ krw(c.limit) }}</i></b>
                </div>
                <div class="ubar-track"><i :style="{ width: `${c.usagePct}%`, background: budgetRiskColor(c.usagePct) }" /></div>
              </div>
              <div class="ubar">
                <div class="ubar-head">
                  <span>할인 한도</span>
                  <b>{{ krw(c.discountUsed) }} <i>/ {{ krw(c.discountLimit) }}</i></b>
                </div>
                <div class="ubar-track"><i :style="{ width: `${c.discountPct}%`, background: '#008c95' }" /></div>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section v-if="aiRecommendations.length" class="ai-reco-section">
        <div class="section-head split">
          <h2>AI 카드 추천</h2>
          <RouterLink class="detail-link" to="/recommendations/usage">
            <Search :size="14" />
            <span>자세히 보기</span>
          </RouterLink>
        </div>

        <div class="ai-reco-card">
          <div class="ai-speech">
            <img class="ai-magpie" src="/card-images/magpie-face2.png" alt="카치AI" />
            <div class="ai-bubble">{{ aiBubble }}</div>
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

      <section class="plan-section">
        <div class="section-head split">
          <h2>지출 계획</h2>
          <RouterLink to="/plans">계획 보기</RouterLink>
        </div>
        <div class="plan-mode-grid">
          <RouterLink
            v-for="mode in expenseModes"
            :key="mode.id"
            class="plan-mode"
            :to="{ path: '/plans/new', query: { expenseMode: mode.id } }"
          >
            <span class="pm-icon"><component :is="modeIcon(mode.id)" :size="18" /></span>
            <div>
              <strong>{{ mode.label }}</strong>
              <small>{{ mode.title }}</small>
            </div>
          </RouterLink>
        </div>
      </section>

      <section class="section-block">
        <div class="section-head split">
          <h2>나의 예산</h2>
          <RouterLink to="/budget/new">예산 추가</RouterLink>
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
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { CalendarClock, Check, ChevronRight, CreditCard, Pencil, PiggyBank, Search, Zap } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { budgetCategories, cards as mockCards, expenseModes, krw } from '@/data/mockData'
import { demoMonthSummary } from '@/data/monthlyAnalytics'
import { fetchBudget, fetchCardRecommendationBundle, fetchMonthlySpending, fetchOwnedCards, fetchSpendingSummary, fetchTransactions, normalizeCard, saveBudget } from '@/services/api'
import { readBudgetOverride, readCustomBudgetCategories, writeBudgetOverride } from '@/services/budgetStorage'
import { budgetProgressWidth, budgetRiskColor, budgetRiskLabel, budgetUsagePercent } from '@/utils/budgetRisk'
import { compareCardBenefitCandidates, scoreCardBenefit, summarizeWalletPerformance } from '@/utils/cardPerformance'

const router = useRouter()

// 카드 썸네일: 세로 이미지면 가로 썸네일에 맞춰 회전 (로드 시 자동 감지)
const thumbOrientation = ref({})
function onThumbLoad(key, event) {
  const img = event.target
  thumbOrientation.value = {
    ...thumbOrientation.value,
    [key]: img.naturalWidth > img.naturalHeight ? 'is-landscape' : 'is-portrait',
  }
}

function modeIcon(id) {
  if (id === 'within-budget') return PiggyBank
  if (id === 'planned-extra') return CalendarClock
  return Zap
}

const CURRENT_MONTH = '2026-06'
const customBudgetCategories = readCustomBudgetCategories()
const displayBudgetCategories = [...budgetCategories, ...customBudgetCategories]
const budgetOverride = ref(readBudgetOverride())
const totalBudget = computed(() => budgetOverride.value ?? displayBudgetCategories.reduce((sum, category) => sum + category.budget, 0))

// 목표 금액: 백엔드(사용자별·월별 Budget) 우선, 실패 시 localStorage 캐시 유지
async function loadBudgetGoal() {
  try {
    const data = await fetchBudget(CURRENT_MONTH)
    if (data && data.totalGoal != null) {
      budgetOverride.value = Number(data.totalGoal)
      writeBudgetOverride(budgetOverride.value)
    }
  } catch {
    // 실패 시 localStorage 캐시 그대로 사용
  }
}
onMounted(loadBudgetGoal)

// 이번 달 사용액: 사용자 실제 거래 합(spending summary) 우선, 실패 시 데모 카테고리 합
const realSpent = ref(null)
async function loadCurrentSpending() {
  try {
    const summary = await fetchSpendingSummary()
    if (summary && Number.isFinite(Number(summary.totalExpense))) {
      realSpent.value = Number(summary.totalExpense)
    }
  } catch {
    // 실패 시 데모 카테고리 합 사용
  }
}
onMounted(loadCurrentSpending)

// 스크롤 내리면 헤더의 '목표 금액' 줄만 접고 '이번 달 사용'은 상단 고정 유지
const headerCollapsed = ref(false)
function onScroll(event) {
  headerCollapsed.value = event.target.scrollTop > 16
}

// 목표(이번 달 예산) 금액: 연필로 수정 가능
const isEditingGoal = ref(false)
const editGoal = ref(0)
const goalInput = ref(null)
function startEditGoal() {
  editGoal.value = totalBudget.value
  isEditingGoal.value = true
  nextTick(() => goalInput.value?.focus())
}
function saveGoal() {
  const next = Number(editGoal.value)
  budgetOverride.value = next > 0 ? next : null
  writeBudgetOverride(budgetOverride.value)
  // 백엔드(사용자별)에도 저장 — 실패해도 로컬 캐시는 유지되므로 UI는 정상
  saveBudget(CURRENT_MONTH, { totalGoal: budgetOverride.value || 0 }).catch(() => {})
  isEditingGoal.value = false
}
const totalSpent = computed(() => realSpent.value ?? displayBudgetCategories.reduce((sum, category) => sum + category.spent, 0))
const cards = mockCards
const walletPerformance = computed(() => summarizeWalletPerformance(cards))
const cardGuideItems = computed(() => (
  prioritizeCardGuideItems(displayBudgetCategories
    .map((category) => {
      const remaining = Math.max(Number(category.budget || 0) - Number(category.spent || 0), 0)
      const recommendation = recommendCardForCategory(category.name, remaining)
      const card = recommendation?.card
      if (!card) return null
      const needsPreparationOnly = walletPerformance.value.needsPreparationOnly && !recommendation.performance.currentBenefitEligible
      const fillsPerformanceOverNoPerformance = walletPerformance.value.hasOnlyNoPerformanceReady
        && !recommendation.performance.currentBenefitEligible
        && recommendation.performance.nextMonthWillQualify
      return {
        category,
        card,
        remaining,
        rateLabel: benefitRateLabel(category.name, card),
        benefitText: categoryBenefitText(category.name, card, recommendation.rate),
        benefit: recommendation.benefit,
        potentialBenefit: recommendation.grossBenefit,
        grossBenefit: recommendation.grossBenefit,
        performance: recommendation.performance,
        needsPreparationOnly,
        fillsPerformanceOverNoPerformance,
        performanceLabel: performanceStatusLabel(recommendation.performance, needsPreparationOnly, fillsPerformanceOverNoPerformance),
        performanceShort: performanceShortLabel(recommendation.performance, needsPreparationOnly, fillsPerformanceOverNoPerformance),
        performanceTone: performanceStatusTone(recommendation.performance),
        remainingLabel: remaining > 0 ? `${krw(remaining)} 남음` : '예산 초과',
      }
    })
    .filter(Boolean)
    .sort(sortCardGuideItems))
))
const primaryCardGuide = computed(() => {
  const item = cardGuideItems.value[0]
  if (!item) return { card: cards[0], reason: '남은 예산을 카드 혜택에 맞춰 나눠 쓰세요.' }
  return {
    ...item,
    reason: cardGuideReason(item),
  }
})

const currentBudget = computed(() => {
  const spent = totalSpent.value
  const budget = totalBudget.value
  const remaining = budget - spent

  return {
    spent,
    budget,
    remaining,
    percent: budgetUsagePercent(spent, budget),
  }
})

const riskColor = computed(() => budgetRiskColor(currentBudget.value.percent))

// 카드 이름 아래에 표시할 짧은 혜택 태그 (예: 쇼핑 10%)
function shortBenefit(card) {
  const item = card.benefitItems?.[0]
  if (item?.scope && item?.ratePercent) return `${item.scope} ${item.ratePercent}%`
  return card.benefitSummary || ''
}

// 카드 현황 데이터: 백엔드(보유 카드 + 거래 집계 사용액) 우선, 실패하면 목 데이터 그대로 유지.
// 할인 한도/실적 등 데모 전용 필드는 백엔드에 없으므로 목 값으로 보강 → 화면은 기존과 동일.
const mockCardById = new Map(mockCards.map((card) => [String(card.id), card]))
const walletCards = ref(mockCards.map((card) => ({ ...card })))

function mergeWalletCard(apiCard, index, transactions) {
  const normalized = normalizeCard(apiCard, index, transactions || [])
  const demo = mockCardById.get(String(normalized.id)) || {}
  const hasTx = Array.isArray(transactions) && transactions.length > 0
  return {
    ...demo,
    ...normalized,
    // 백엔드에 없는 데모 전용 필드는 목 값 유지(현 화면 보존)
    limit: Number(demo.limit) || Number(normalized.limit) || 0,
    discountLimit: demo.discountLimit ?? 0,
    discountUsed: demo.discountUsed ?? 0,
    previousMonthMinSpend: demo.previousMonthMinSpend ?? normalized.previousMonthMinSpend ?? 0,
    previousMonthSpend: demo.previousMonthSpend ?? 0,
    // 이번 달 사용액·당월 실적은 실제 거래가 있으면 거래 집계, 없으면 목 값
    spent: hasTx ? normalized.spent : (demo.spent ?? normalized.spent ?? 0),
    currentMonthSpend: hasTx ? normalized.spent : (demo.currentMonthSpend ?? demo.spent),
    // 혜택 표기는 큐레이션된 데모 값을 유지(카드 현황 표기 보존)
    benefitItems: demo.benefitItems?.length ? demo.benefitItems : normalized.benefitItems,
    benefitSummary: demo.benefitSummary || normalized.benefitSummary,
  }
}

async function loadWallet() {
  try {
    const [txResult, cardResult] = await Promise.allSettled([fetchTransactions(), fetchOwnedCards()])
    // 호출 실패 시에만 초기 목 데이터 유지(오프라인 폴백). 성공하면 빈 배열도 그대로 반영 → 빈 지갑.
    if (cardResult.status !== 'fulfilled' || !Array.isArray(cardResult.value)) return
    const transactions = txResult.status === 'fulfilled' && Array.isArray(txResult.value) ? txResult.value : null
    walletCards.value = cardResult.value.map((card, index) => mergeWalletCard(card, index, transactions))
  } catch {
    // 어떤 단계든 실패하면 초기 목 데이터 유지
  }
}
onMounted(loadWallet)

// 보유 카드별: 사용 한도 / 할인 한도 / 실적 기반 이번달·다음달 할인 가능 여부
const cardUsageList = computed(() => walletCards.value.map((card) => {
  const limit = Number(card.limit || 0)
  const spent = Number(card.spent || 0)
  const minSpend = Number(card.previousMonthMinSpend || 0)
  const prevSpend = Number(card.previousMonthSpend || 0)
  const curSpend = Number(card.currentMonthSpend ?? spent)
  const noPerf = minSpend <= 0
  // 이번달 할인 = 지난달(전월) 실적을 채웠는가 / 다음달 할인 = 이번달 실적을 채웠는가
  const thisMonthOk = noPerf || prevSpend >= minSpend
  const nextMonthOk = noPerf || curSpend >= minSpend
  // 할인 한도(월 최대)는 카드 metadata, 받은 할인은 이번 달 사용액 × 혜택률을 한도 내에서 계산.
  // 혜택률/한도 정보가 없으면(예: 신규 사용자 카드) metadata 값으로 폴백(보통 0).
  const rawDiscountLimit = Number(card.discountLimit || 0)
  const benefitRate = Number(card.benefitItems?.[0]?.ratePercent || 0) / 100
  const computedUsed = benefitRate > 0 && rawDiscountLimit > 0
    ? Math.min(Math.round(spent * benefitRate), rawDiscountLimit)
    : Number(card.discountUsed || 0)
  // 이번달 할인이 안 되는 카드는 할인 한도 자체가 0원 (0원 / 0원)
  const discountLimit = thisMonthOk ? rawDiscountLimit : 0
  const discountUsed = thisMonthOk ? computedUsed : 0
  return {
    id: card.id,
    name: card.name,
    imageUrl: card.imageUrl,
    brand: card.brand,
    benefitTag: shortBenefit(card),
    spent,
    limit,
    usagePct: limit ? Math.min(Math.round((spent / limit) * 100), 100) : 0,
    discountUsed,
    discountLimit,
    discountPct: discountLimit ? Math.min(Math.round((discountUsed / discountLimit) * 100), 100) : 0,
    noPerf,
    thisMonthOk,
    nextMonthOk,
    nextPct: minSpend ? Math.min(Math.round((curSpend / minSpend) * 100), 100) : 100,
  }
}))

// AI 카드 추천: 실제 추천 엔진(/api/recommendations/cards/)의 ownedCategoryGuides 우선,
// 실패하거나 비어 있으면 기존 로컬 추천(cardGuideItems)으로 폴백 → 섹션은 항상 동일하게 채워짐.
const CATEGORY_EMOJI = {
  식비: '🥗', 외식: '🥗', 카페: '☕', 쇼핑: '🛍️', 뷰티: '💄', 교통: '🚇', 교육: '📚',
  편의점: '🏪', 문화: '🎬', 헬스: '🏋️', 생활: '🏠', 통신: '📡', 구독: '📺',
}
function categoryEmoji(name) {
  return CATEGORY_EMOJI[String(name || '').trim()] || '💳'
}

const aiBundle = ref(null)
async function loadAiRecommendations() {
  try {
    const bundle = await fetchCardRecommendationBundle()
    const guides = bundle?.ownedCategoryGuides
    if (Array.isArray(guides) && guides.length) aiBundle.value = bundle
  } catch {
    // 실패 시 aiBundle은 null 유지 → 로컬 추천으로 폴백
  }
}
onMounted(loadAiRecommendations)

function mapGuideToReco(item, index) {
  const label = String(item.category || '추천 분야').replace(/\s+/g, ' ').trim()
  const card = walletCards.value.find((c) => String(c.id) === String(item.cardId))
    || { id: item.cardId, name: item.cardName, imageUrl: item.imageUrl, benefitSummary: item.benefitLabel }
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
  const guides = aiBundle.value?.ownedCategoryGuides
  if (Array.isArray(guides) && guides.length) {
    return guides.map(mapGuideToReco).slice(0, 3)
  }
  return cardGuideItems.value.slice(0, 3)
})
// 까치(카치AI)가 말풍선에서 건네는 짧은 추천 한마디
const aiBubble = computed(() => {
  const top = aiRecommendations.value[0]
  if (!top) return '카드별 혜택을 비교해서 알뜰하게 써봐요!'
  return `${top.category.name}엔 ${top.card.name}가 딱이에요!`
})

// 월별 사용액 추이 선그래프 (지난달·이번달·다음달 계획)
function shortKrw(value) {
  if (value >= 10000) return `${Math.round(value / 10000).toLocaleString()}만`
  return krw(value)
}
// 최근 5개월 사용액·예산: 백엔드(사용자별 거래 집계 + 월 예산) 우선, 실패 시 데모 데이터
const monthlySeries = ref(null)
async function loadMonthly() {
  try {
    const data = await fetchMonthlySpending(5)
    if (data && Array.isArray(data.months) && data.months.length) monthlySeries.value = data.months
  } catch {
    // 실패 시 데모 데이터(monthlyAnalytics)로 폴백
  }
}
onMounted(loadMonthly)

// 최근 5개월 예산(연한 트랙) + 사용(색상) 겹침 막대그래프
const barChart = computed(() => {
  // 과거 달 사용액은 분석 화면과 동일한 데모 데이터(monthlyAnalytics)에서 가져와 숫자를 일치시킨다
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
        // 현재 달은 헤더(목표/사용)와 동기화되도록 라이브 값 사용
        budget: isCurrent ? currentBudget.value.budget : Number(m.budget || 0),
        spent: isCurrent ? currentBudget.value.spent : Number(m.spent || 0),
      }
    })
    : [
      { label: '2월', ym: '2026-02' },
      { label: '3월', ym: '2026-03' },
      { label: '4월', ym: '2026-04' },
      { label: '5월', ym: '2026-05' },
      { label: '6월', ym: '2026-06', current: true },
    ].map((m) => (m.current
      ? { ...m, budget: currentBudget.value.budget, spent: currentBudget.value.spent }
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
      ...m,
      cx,
      hx,
      hw: slot,
      barW,
      budgetY,
      budgetH,
      spentY,
      spentH,
      color: budgetRiskColor(pct),
      remaining,
      tagY: Math.min(budgetY, spentY) - 6,
    }
  })
  return { w, h, baseY, bars }
})

// 차트/표에서 달을 누르면 그 달 소비 분석으로 이동
function goMonth(month) {
  router.push({ path: '/analytics', query: { month: month.ym } })
}

const budgetHistory = computed(() => {
  const current = currentBudget.value
  const nextBudget = 950000

  return [
    {
      id: '2026-06',
      relativeLabel: '이번 달',
      month: 6,
      title: '6월 예산',
      period: '2026.06.01 - 06.30',
      spent: current.spent,
      budget: current.budget,
      remaining: current.remaining,
      percent: current.percent,
      to: '/budget/current',
      tone: 'active',
    },
    {
      id: '2026-05',
      relativeLabel: '지난 달',
      month: 5,
      title: '5월 예산',
      period: '2026.05.01 - 05.31',
      spent: 620000,
      budget: 910000,
      remaining: 290000,
      percent: 68,
      to: '/budget/current',
      tone: 'done',
    },
    {
      id: '2026-07',
      relativeLabel: '다음 달',
      month: 7,
      title: '7월 예산',
      period: '2026.07.01 - 07.31',
      spent: 0,
      budget: nextBudget,
      remaining: nextBudget,
      percent: 0,
      to: '/budget/current',
      tone: 'upcoming',
      upcoming: true,
    },
  ]
})

function normalizedText(value) {
  return String(value || '').toLowerCase().replace(/\s+/g, '')
}

function findCardById(id) {
  return cards.find((card) => String(card.id) === String(id) || String(card.cardAdId) === String(id)) || cards[0]
}

function recommendCardForCategory(name, amount = 0) {
  const scored = cards
    .map((card) => {
      const rate = categoryBenefitRate(name, card)
      const score = scoreCardBenefit({ card, amount, rate })
      return {
        card,
        rate,
        benefit: score.activeBenefit,
        grossBenefit: score.grossBenefit,
        performance: score,
      }
    })
    .filter((item) => item.rate > 0)
    .sort(sortCardRecommendations)

  if (scored.length) return scored[0]

  const text = normalizedText(name)
  const card = /(쇼핑|뷰티|온라인|패션|무신사|쿠팡)/.test(text)
    ? findCardById('10612')
    : /(식비|외식|배달|카페|커피|편의점|gs25|cu)/.test(text)
      ? findCardById('10106')
      : findCardById('10029')
  const score = scoreCardBenefit({ card, amount, rate: categoryBenefitRate(name, card) })
  return {
    card,
    rate: categoryBenefitRate(name, card),
    benefit: score.activeBenefit,
    grossBenefit: score.grossBenefit,
    performance: score,
  }
}

function categoryBenefitRate(categoryName, card) {
  const text = normalizedText(categoryName)
  const cardId = String(card.id)
  if (cardId === '10612' && /(쇼핑|뷰티|온라인|패션|무신사|쿠팡)/.test(text)) return 0.1
  if (cardId === '10106' && /(카페|커피|식비|외식|배달|편의점|gs25|cu)/.test(text)) return 0.06
  if (cardId === '10029' && /(교통|택시|전철|대중교통|버스|지하철|공항철도)/.test(text)) return 0.01
  if (cardId === '10029' && /(헬스|교육|구독|데이트|문화|마트|장보기)/.test(text)) return 0.015
  return 0
}

function benefitRateLabel(categoryName, card) {
  const text = normalizedText(categoryName)
  if (String(card.id) === '10612' && /(쇼핑|뷰티|온라인|패션)/.test(text)) return '최대 10%'
  if (String(card.id) === '10106' && /(카페|식비|외식|편의점)/.test(text)) return '생활 집중'
  if (String(card.id) === '10029' && /(교통|택시|전철|대중교통|버스|지하철)/.test(text)) return '기본 할인'
  if (String(card.id) === '10029') return '기본 1.5%'
  return '혜택 확인'
}

// 추천 카드의 해당 카테고리 혜택을 정확하고 짧게 (예: 쇼핑 10% 할인)
function categoryBenefitText(categoryName, card, rate) {
  if (rate > 0) {
    const pct = Number((rate * 100).toFixed(rate * 100 % 1 ? 1 : 0))
    return `${categoryName} ${pct}% 할인`
  }
  return card.benefitSummary || shortBenefit(card)
}

function sortCardRecommendations(a, b) {
  return compareCardBenefitCandidates(a, b)
}

function sortCardGuideItems(a, b) {
  return compareCardBenefitCandidates(a, b)
    || b.remaining - a.remaining
}

function performanceStatusLabel(performance, needsPreparationOnly = false, fillsPerformanceOverNoPerformance = false) {
  if (!performance) return '실적 정보 없음'
  if (performance.noPerformanceRequired) return '무실적 혜택'
  if (performance.currentBenefitEligible) return '이번 달 혜택 가능'
  if (fillsPerformanceOverNoPerformance) return '무실적보다 실적 완성'
  if (performance.nextMonthWillQualify) return '다음 달 조건 충족'
  if (needsPreparationOnly) return '실적 준비 우선'
  return `다음 달 조건 ${krw(performance.remainingAfter)} 부족`
}

function performanceShortLabel(performance, needsPreparationOnly = false, fillsPerformanceOverNoPerformance = false) {
  if (!performance) return '확인 필요'
  if (performance.noPerformanceRequired) return '무실적 혜택'
  if (performance.currentBenefitEligible) return '이번 달 가능'
  if (fillsPerformanceOverNoPerformance) return '실적 완성'
  if (performance.nextMonthWillQualify) return '다음 달 충족'
  if (needsPreparationOnly) return '준비 우선'
  return '준비 필요'
}

function performanceStatusTone(performance) {
  if (!performance) return 'is-waiting'
  return performance.currentBenefitEligible || performance.nextMonthWillQualify ? 'is-ready' : 'is-waiting'
}

function cardGuideReason(item) {
  if (item.performance?.noPerformanceRequired) {
    return `${item.category.name} · 무실적으로 바로 혜택`
  }
  if (item.performance?.currentBenefitEligible) {
    return `${item.category.name} · 이번 달 혜택 바로 가능`
  }
  if (item.fillsPerformanceOverNoPerformance) {
    return `${item.category.name}을 모아 다음 달 혜택 준비`
  }
  if (item.performance?.nextMonthWillQualify) {
    return `${item.category.name}을 모으면 다음 달 조건 충족`
  }
  return `다음 달 조건까지 ${krw(item.performance.remainingAfter)} 남음`
}

function prioritizeCardGuideItems(items) {
  const picked = []
  const pickedKeys = new Set()
  const cardIds = new Set()

  for (const item of items) {
    if (cardIds.has(String(item.card.id))) continue
    picked.push(item)
    pickedKeys.add(item.category.id)
    cardIds.add(String(item.card.id))
    if (picked.length >= 3) return picked
  }

  for (const item of items) {
    if (pickedKeys.has(item.category.id)) continue
    picked.push(item)
    if (picked.length >= 3) return picked
  }

  return picked
}
</script>

<style scoped>
.budget-list-header {
  padding: 22px 20px 22px;
  border: 0;
  border-radius: 0 0 28px 28px;
  color: #17202b;
  text-align: left;
  background:
    radial-gradient(circle at 18% 0%, rgba(15, 95, 174, 0.1), transparent 38%),
    linear-gradient(180deg, #ffffff 0%, #fbfdff 62%, #edf4fb 100%) !important;
  box-shadow: 0 14px 36px rgba(36, 54, 79, 0.1);
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  margin-bottom: 20px;
}

.header-row p {
  margin: 0 0 4px;
  color: #6f7d8c;
  font-size: 12px;
  font-weight: 800;
}

h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 900;
  line-height: 1.2;
}

.current-summary {
  border: 0;
  border-radius: 20px;
  padding: 15px 18px 14px;
  background: rgba(255, 255, 255, 0.92);
  color: #17202b;
  box-shadow: 0 14px 28px rgba(36, 54, 79, 0.07);
  backdrop-filter: blur(12px) saturate(1.04);
}

.cs-main {
  display: block;
  color: inherit;
  text-decoration: none;
}

.cs-goal {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  max-height: 44px;
  margin-top: 13px;
  padding-top: 12px;
  border-top: 1px solid rgba(36, 54, 79, 0.09);
  overflow: hidden;
  opacity: 1;
  transition: max-height 0.28s ease, opacity 0.22s ease, margin-top 0.28s ease, padding-top 0.28s ease, border-top-color 0.28s ease;
}

.cs-goal.collapsed {
  max-height: 0;
  margin-top: 0;
  padding-top: 0;
  border-top-color: transparent;
  opacity: 0;
  pointer-events: none;
}

.cs-goal > span {
  color: #6f7d8c;
  font-size: 12px;
  font-weight: 850;
}

.cs-goal-view,
.cs-goal-edit {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cs-goal-view strong {
  color: #17202b;
  font-size: 15px;
  font-weight: 950;
  font-variant-numeric: tabular-nums;
}

.cs-goal-input {
  width: 120px;
  border: 0;
  border-bottom: 2px solid rgba(15, 95, 174, 0.32);
  border-radius: 0;
  padding: 0 0 2px;
  background: transparent;
  color: #17202b;
  font-size: 15px;
  font-weight: 950;
  font-variant-numeric: tabular-nums;
  text-align: right;
  outline: none;
}

.cs-goal-btn {
  display: inline-flex;
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 8px;
  background: rgba(15, 95, 174, 0.1);
  color: #0f5fae;
  cursor: pointer;
}

.cs-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.cs-label span {
  color: #6f7d8c;
  font-size: 12px;
  font-weight: 850;
}

.cs-status {
  flex-shrink: 0;
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 950;
  font-style: normal;
}

.cs-amount {
  display: block;
  margin-top: 5px;
  color: #17202b;
  font-size: 34px;
  font-weight: 950;
  line-height: 1.05;
  letter-spacing: 0;
}

.cs-track {
  height: 9px;
  overflow: hidden;
  margin-top: 13px;
  border-radius: 999px;
  background: #e7edf4;
}

.cs-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  transition: width 0.3s ease, background-color 0.3s ease;
}

.cs-meta {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-top: 9px;
}

.cs-meta em {
  font-style: normal;
}

.cs-meta .cs-pct {
  font-size: 14px;
  font-weight: 950;
}

.cs-meta .cs-remain {
  font-size: 13px;
  font-weight: 900;
}

.budget-list-body {
  padding: 16px 20px 112px;
}

.card-guide-section {
  margin-bottom: 24px;
}

.usecard-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.usecard {
  border: 0;
  border-radius: 16px;
  padding: 13px 14px;
  /* 이번달 할인 되는 카드: 연한 파란색 */
  background: rgba(37, 99, 235, 0.09);
}

.usecard.not-eligible {
  /* 이번달 할인 안 되는 카드: 연한 빨강 */
  background: rgba(229, 72, 77, 0.09);
  box-shadow: none;
}

.usecard-top {
  display: flex;
  align-items: center;
  gap: 11px;
}

.usecard-thumb {
  position: relative;
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 42px;
  height: 27px;
  overflow: hidden;
  border-radius: 5px;
  background: #e8edf2;
  color: #8a9aad;
  box-shadow: 0 1px 4px rgba(36, 54, 79, 0.2);
}

.usecard-thumb img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.usecard-thumb img.is-portrait {
  inset: auto;
  top: 50%;
  left: 50%;
  width: 27px;
  height: 42px;
  max-width: none;
  transform: translate(-50%, -50%) rotate(-90deg);
}

.usecard-name {
  flex: 1 1 auto;
  min-width: 0;
}

.usecard-name strong {
  display: block;
  overflow: hidden;
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.usecard-name small {
  display: block;
  margin-top: 1px;
  color: #8a96a5;
  font-size: 10.5px;
  font-weight: 800;
}

.usecard-flags {
  display: flex;
  flex-shrink: 0;
  gap: 5px;
}

.flag {
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 10px;
  font-weight: 900;
  white-space: nowrap;
}

.flag.on {
  background: rgba(22, 163, 74, 0.13);
  color: #15803d;
}

.flag.off {
  background: rgba(229, 72, 77, 0.14);
  color: #c2333a;
}

.flag.wait {
  background: rgba(245, 158, 11, 0.16);
  color: #b45309;
}

.usecard-bars {
  display: flex;
  flex-direction: column;
  gap: 9px;
  margin-top: 12px;
}

.ubar-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 5px;
}

.ubar-head span {
  color: #6e7885;
  font-size: 11px;
  font-weight: 850;
}

.ubar-head b {
  color: #17202b;
  font-size: 12px;
  font-weight: 900;
}

.ubar-head b i {
  color: #9aa6b3;
  font-size: 11px;
  font-weight: 800;
  font-style: normal;
}

.ubar-track {
  height: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: #e7edf4;
}

.ubar-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  transition: width 0.3s ease, background-color 0.3s ease;
}

.ai-reco-section {
  margin-bottom: 24px;
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
  /* AI 느낌: 은은한 하늘색 → 연보라 그라데이션 */
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
  font-weight: 750;
  letter-spacing: -0.3px;
  font-variant-numeric: tabular-nums;
}

.ai-reco-benefit.muted {
  color: #9aa6b3;
  font-size: 11px;
  font-weight: 600;
}

.plan-section {
  margin-bottom: 24px;
}

.plan-mode-grid {
  display: grid;
  gap: 8px;
}

.plan-mode {
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid rgba(36, 54, 79, 0.07);
  border-radius: 14px;
  padding: 13px 14px;
  background: rgba(255, 255, 255, 0.72);
  color: inherit;
  text-decoration: none;
  box-shadow: 0 10px 22px rgba(36, 54, 79, 0.045);
}

.pm-icon {
  display: inline-flex;
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: #fff;
  color: #0f5fae;
  box-shadow: 0 2px 8px rgba(36, 54, 79, 0.1);
}

.plan-mode strong {
  display: block;
  color: #20242a;
  font-size: 13px;
  font-weight: 900;
}

.plan-mode small {
  display: block;
  margin-top: 2px;
  color: #6e6e73;
  font-size: 11px;
  font-weight: 700;
}

.section-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
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

.budget-history-card {
  display: block;
  padding: 15px;
  color: inherit;
  text-decoration: none;
}

.history-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.history-title-row strong {
  display: block;
  color: #20242a;
  font-size: 18px;
  font-weight: 900;
}

.history-headline.active {
  color: #0f5fae !important;
}

.history-title-row span {
  display: block;
  margin-top: 3px;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 700;
}

.history-title-row svg {
  flex-shrink: 0;
  margin-top: 2px;
  color: #8a9aad;
}

.history-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  align-items: end;
  gap: 8px;
  margin-top: 12px;
  border-top: 1px solid rgba(32, 36, 42, 0.075);
  padding-top: 11px;
}

.remaining-cell {
  text-align: right;
}

.history-metrics span {
  display: block;
  color: #6e6e73;
  font-size: 10px;
  font-weight: 800;
}

.history-metrics b {
  display: block;
  margin-top: 3px;
  color: #20242a;
  font-size: 12px;
  font-weight: 900;
}

.history-metrics b.pos {
  color: var(--carch-success);
}

.history-metrics b.neg {
  color: var(--carch-danger);
}

.history-track {
  height: 7px;
  overflow: hidden;
  margin-top: 12px;
  border-radius: 999px;
  background: #e7edf4;
}

.history-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  transition: width 0.2s ease, background-color 0.2s ease;
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
  font-weight: 600;
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
  font-weight: 800;
}

.tm-row.cur .tm-budget {
  color: #6e7885;
}

/* 잔액: + 초록 / − 빨강 (현재월 강조 행에서도 색 유지) */
.trend-months .tm-row .pos {
  color: #16a34a;
  font-weight: 800;
}

.trend-months .tm-row .neg {
  color: #e5484d;
  font-weight: 800;
}

.plan-entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-top: 16px;
  padding: 14px 15px;
  color: inherit;
  text-decoration: none;
}

.plan-entry span {
  display: block;
  color: #008c95;
  font-size: 11px;
  font-weight: 900;
}

.plan-entry strong {
  display: block;
  margin-top: 4px;
  color: #20242a;
  font-size: 13px;
  font-weight: 900;
  line-height: 1.45;
}

.plan-entry svg {
  flex-shrink: 0;
  color: #008c95;
}
</style>
