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

      <section class="plan-section">
        <RouterLink class="plan-cta" to="/plans/new">
          <span class="pc-icon"><PencilLine :size="20" /></span>
          <div class="pc-text">
            <strong>지출 계획 입력하기</strong>
            <small>큰 지출을 어떤 카드로 결제할지 계획해요</small>
          </div>
          <ChevronRight :size="18" class="pc-go" />
        </RouterLink>
      </section>

      <section v-if="pendingReviewCandidates.length" class="review-section">
        <div class="section-head split">
          <h2>이 지출, 매달 반복되나요?</h2>
        </div>
        <p class="review-sub">매달 나가는 지출인지 알려주면 추천이 정확해져요</p>

        <div class="analysis-card app-card review-card">
          <div class="review-list">
          <div
            v-for="item in pendingReviewCandidates"
            :key="item.category"
            class="review-group"
            :class="{ open: expandedCategory === item.category }"
          >
            <article
              class="review-item"
              role="button"
              :aria-expanded="expandedCategory === item.category"
              @click="toggleExpand(item.category)"
            >
              <span class="review-emoji">{{ categoryIcon(item.category) }}</span>
              <div class="review-info">
                <strong>{{ item.category }}</strong>
                <span class="review-amount">{{ krw(item.currentAmount) }}</span>
                <em v-if="spikeLabel(item)" class="review-spike">{{ spikeLabel(item) }}</em>
              </div>
              <div class="review-toggle" role="group" :aria-label="`${item.category} 지출 반영 방식`" @click.stop>
                <button type="button" :class="{ active: !isCategoryRecurring(item.category) }" @click="setCategoryRecurring(item.category, false)">이번 달만</button>
                <button type="button" class="is-recurring" :class="{ active: isCategoryRecurring(item.category) }" @click="setCategoryRecurring(item.category, true)">매달</button>
              </div>
              <ChevronDown class="review-caret" :class="{ open: expandedCategory === item.category }" :size="16" />
            </article>

            <div v-if="expandedCategory === item.category" class="review-detail">
              <div v-for="tx in categoryItems(item.category)" :key="tx.id" class="rd-item">
                <div class="rd-info">
                  <strong>{{ tx.merchant }}</strong>
                  <span>{{ tx.date }}</span>
                </div>
                <b class="rd-amount">{{ krw(tx.amount) }}</b>
                <div class="rd-toggle" role="group" :aria-label="`${tx.merchant} 반영 방식`">
                  <button type="button" :class="{ active: !isItemRecurring(tx.id) }" @click="setItemRecurring(tx.id, false)">이번 달만</button>
                  <button type="button" class="is-recurring" :class="{ active: isItemRecurring(tx.id) }" @click="setItemRecurring(tx.id, true)">매달</button>
                </div>
              </div>
              <p v-if="!categoryItems(item.category).length" class="rd-empty">이 카테고리의 이번 달 상세 내역을 불러오지 못했어요.</p>
            </div>
          </div>
          </div>
        </div>
      </section>

      <section v-if="recommendationCards.length" class="rec-section">
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

      <section v-if="planSummaries.length" class="plan-reco-section">
        <div class="section-head split">
          <h2>내 지출 계획</h2>
        </div>
        <RouterLink
          v-for="p in visiblePlans"
          :key="p.id"
          :to="`/plans/${p.id}`"
          class="plan-reco"
        >
          <div class="pr-top">
            <strong>{{ p.title }}</strong>
            <div class="pr-meta">
              <span class="pr-date"><CalendarClock :size="12" /> {{ p.dateLabel }}</span>
              <span class="pr-total">{{ krw(p.total) }}</span>
            </div>
          </div>
          <ul v-if="p.items.length" class="pr-items">
            <li v-for="(it, idx) in p.items" :key="idx" class="pr-item">
              <span class="pr-thumb">
                <img
                  v-if="it.cardImage"
                  :src="it.cardImage"
                  :alt="it.card"
                  :class="thumbOri[`${p.id}-${idx}`]"
                  @load="onThumb($event, `${p.id}-${idx}`)"
                />
                <CreditCard v-else :size="14" />
              </span>
              <div class="pr-item-body">
                <strong>{{ it.name }}</strong>
                <small><b>{{ it.card }}</b>로 {{ krw(it.amount) }} 결제</small>
              </div>
              <em v-if="it.benefit" class="pr-benefit">+{{ krw(it.benefit) }}</em>
            </li>
          </ul>
          <p v-else class="pr-line"><b>{{ p.card }}</b>{{ p.tail }}</p>
          <div v-if="p.totalBenefit" class="pr-foot">
            <span>예상 혜택</span>
            <b>+{{ krw(p.totalBenefit) }}</b>
          </div>
        </RouterLink>
        <button
          v-if="planSummaries.length > 2"
          type="button"
          class="pr-more"
          @click="showAllPlans = !showAllPlans"
        >
          {{ showAllPlans ? '접기' : `더보기 (${planSummaries.length - 2})` }}
          <ChevronDown :size="15" :class="{ flip: showAllPlans }" />
        </button>
      </section>

    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { CalendarClock, Check, ChevronDown, ChevronRight, CreditCard, Pencil, PencilLine, PiggyBank, Search, Sparkles, Zap } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { budgetCategories, cards as mockCards, expenseModes, krw, monthLabel } from '@/data/mockData'
import { demoMonthSummary } from '@/data/monthlyAnalytics'
import { fetchBudget, fetchCardRecommendationBundle, fetchMonthlySpending, fetchOwnedCards, fetchSpendingSummary, fetchTransactions, normalizeCard, saveBudget } from '@/services/api'
import { getPurchasePlans } from '@/services/purchasePlans'
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
// 신규 유저(백엔드에 월 예산 없음) 기본 제안값
const DEFAULT_NEW_USER_GOAL = 300000
const totalBudget = computed(() => {
  if (budgetOverride.value != null) return budgetOverride.value
  const series = monthlySeries.value
  if (series && series.length) {
    const june = series.find((m) => String(m.month) === CURRENT_MONTH)
    // 백엔드에 이번 달 예산이 있으면(데모 등) 그 값, 없으면(신규 유저) 30만 기본 제안값
    return june && june.budget != null ? Number(june.budget) : DEFAULT_NEW_USER_GOAL
  }
  // 월별 데이터 로딩 전: 데모 깜빡임 방지용 기존 기본값
  return displayBudgetCategories.reduce((sum, category) => sum + category.budget, 0)
})

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
const spendingSummary = ref(null)
async function loadCurrentSpending() {
  try {
    const summary = await fetchSpendingSummary({ recurringCategories: recurringCategories.value })
    spendingSummary.value = summary
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

const allTransactions = ref([])
async function loadWallet() {
  try {
    const [txResult, cardResult] = await Promise.allSettled([fetchTransactions(), fetchOwnedCards()])
    const transactions = txResult.status === 'fulfilled' && Array.isArray(txResult.value) ? txResult.value : null
    // 반복지출 드릴다운(가맹점별 내역)에서 사용할 거래 원본 보관
    if (transactions) allTransactions.value = transactions
    // 호출 실패 시에만 초기 목 데이터 유지(오프라인 폴백). 성공하면 빈 배열도 그대로 반영 → 빈 지갑.
    if (cardResult.status !== 'fulfilled' || !Array.isArray(cardResult.value)) return
    walletCards.value = cardResult.value.map((card, index) => mergeWalletCard(card, index, transactions))
  } catch {
    // 어떤 단계든 실패하면 초기 목 데이터 유지
  }
}
onMounted(loadWallet)

// AI 추천(ownedCategoryGuides)과 동일한 실제 거래 기준 자격 맵 — 카드 현황과 추천 화면의 '이번달 할인' 표시를 통일
const ownedEligibilityMap = computed(() => {
  const map = {}
  for (const g of (aiBundle.value?.ownedCategoryGuides || [])) {
    const id = String(g.cardId)
    if (!(id in map)) {
      map[id] = {
        thisMonthOk: Boolean(g.eligibleForBenefit),
        nextMonthOk: Boolean(g.eligibleForBenefit || g.nextMonthEligible),
      }
    }
  }
  return map
})

// 보유 카드별: 사용 한도 / 할인 한도 / 실적 기반 이번달·다음달 할인 가능 여부
const cardUsageList = computed(() => walletCards.value.map((card) => {
  const limit = Number(card.limit || 0)
  const spent = Number(card.spent || 0)
  const minSpend = Number(card.previousMonthMinSpend || 0)
  const prevSpend = Number(card.previousMonthSpend || 0)
  const curSpend = Number(card.currentMonthSpend ?? spent)
  const noPerf = minSpend <= 0
  // 이번달/다음달 할인 — AI 추천과 동일한 실제 거래 기준(백엔드 ownedCategoryGuides)으로 통일.
  // 추천 번들에 잡힌 카드는 백엔드 산출 자격을 그대로 쓰고, 없으면 기존 실적 계산으로 폴백.
  const elig = ownedEligibilityMap.value[String(card.id)]
  const thisMonthOk = elig ? elig.thisMonthOk : (noPerf || prevSpend >= minSpend)
  const nextMonthOk = elig ? elig.nextMonthOk : (noPerf || curSpend >= minSpend)
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
const aiBundleLoaded = ref(false)
async function loadAiRecommendations() {
  try {
    aiBundle.value = await fetchCardRecommendationBundle()
    aiBundleLoaded.value = true // 응답 성공(빈 결과 포함) → 백엔드 결과를 신뢰
  } catch {
    aiBundleLoaded.value = false // 호출 실패 시에만 로컬 추천으로 폴백
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
  if (aiBundleLoaded.value) {
    // 백엔드가 응답했으면 그 결과만 사용 — 보유 카드 없는 신규 유저는 빈 추천(섹션 자동 숨김)
    const guides = aiBundle.value?.ownedCategoryGuides
    return Array.isArray(guides) && guides.length ? guides.map(mapGuideToReco).slice(0, 3) : []
  }
  // 호출 실패(오프라인) 시에만 로컬 추천으로 폴백
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

// 소비계획 하단 요약 — 저장된 목표 지출 계획의 카드 추천을 간략히
const purchasePlanList = ref([])
async function loadPurchasePlanSummaries() {
  try {
    purchasePlanList.value = await getPurchasePlans()
  } catch {
    // 실패 시 빈 목록(섹션 자동 숨김)
  }
}
onMounted(loadPurchasePlanSummaries)

// 카드 이름 → 카드 이미지 매핑
const cardImageByName = computed(() => {
  const map = {}
  for (const c of mockCards) {
    if (c?.name) map[c.name] = c.imageUrl
  }
  return map
})

// 카드 썸네일 방향(세로 이미지는 가로 썸네일에 맞춰 회전)
const thumbOri = reactive({})
function onThumb(event, key) {
  const img = event.target
  thumbOri[key] = img.naturalWidth > img.naturalHeight ? 'is-landscape' : 'is-portrait'
}

// 결제 예상 시기 라벨(시작·종료 월이 같으면 한 달만)
function planDateLabel(plan) {
  const start = plan.startMonth || ''
  const end = plan.endMonth || start
  if (!start) return '시기 미정'
  if (!end || start === end) return monthLabel(start)
  return `${monthLabel(start)} ~ ${monthLabel(end)}`
}

// 소비계획 하단 — 저장된 지출 계획을 항목별 카드 배정까지 상세히 표시
const planSummaries = computed(() => (purchasePlanList.value || []).map((plan) => {
  const scs = plan.scenarios || []
  const sc = scs.find((s) => s.id === plan.selectedScenarioId) || scs[0]
  const rawItems = (sc?.monthlyPlan || []).flatMap((m) => m.items || [])
  const items = rawItems.map((it) => ({
    name: it.name,
    amount: Number(it.amount || 0),
    card: it.card || '',
    cardImage: cardImageByName.value[it.card] || '',
    benefit: Number(it.benefit || 0),
  }))
  const card = sc?.cardSummary?.[0]?.cardName || rawItems[0]?.card || ''
  const total = Number(plan.totalBudget || 0) || (plan.items || []).reduce((sum, i) => sum + Number(i.amount || 0), 0)
  return {
    id: plan.id,
    title: plan.title,
    dateLabel: planDateLabel(plan),
    total,
    items,
    totalBenefit: items.reduce((sum, i) => sum + i.benefit, 0),
    card: card || '카드 추천',
    tail: card ? '로 결제하면 혜택을 챙길 수 있어요' : ' 확인이 필요해요',
  }
}))

// 기본 2개만 노출, 더보기로 나머지 인라인 펼침
const showAllPlans = ref(false)
const visiblePlans = computed(() => (showAllPlans.value ? planSummaries.value : planSummaries.value.slice(0, 2)))

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

// ── 분석 탭에서 이동: 새 카드 추천 + "이 지출, 매달 반복되나요?" ──
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
  const rows = []
  const seen = new Set()
  const formatRate = (value) => {
    const rate = Number(value || 0)
    return rate > 0 ? `최대 ${Number(rate.toFixed(1))}% 할인` : ''
  }
  const formatLimit = (value) => {
    const limit = Number(value || 0)
    return limit > 0 ? `월 최대 ${krw(limit)}` : ''
  }

  const breakdown = reco?.economics?.categoryBreakdown || reco?.spendingFit?.categoryBreakdown || []
  breakdown.forEach((item, index) => {
    const category = String(item.category || '').trim()
    if (!category) return
    const benefit = Number(item.estimatedBenefit || item.potentialBenefit || 0)
    if (benefit <= 0) return
    const { label, icon } = classifyRecoField(category)
    if (seen.has(label)) return
    seen.add(label)
    const rateLabel = formatRate(item.rate ?? item.ratePercent ?? item.rate_percent)
    const cap = item.monthlyBenefitLimitKrw ?? item.monthly_benefit_limit_krw ?? item.monthlyLimitKrw ?? item.monthly_limit_krw ?? 0
    rows.push({
      id: `breakdown-${category}-${index}`,
      field: label,
      icon,
      value: rateLabel || item.benefitLabel || '혜택 확인',
      cap: formatLimit(cap),
    })
  })

  const items = reco?.benefitItems || reco?.benefit_items || reco?.benefits || reco?.highlights || []
  items.forEach((item, index) => {
    const textItem = typeof item === 'string' ? item : ''
    const percentMatch = textItem.match(/(\d+(?:\.\d+)?)\s*%/)
    if (textItem && !percentMatch) return
    const rate = Number(item.ratePercent ?? item.rate_percent ?? 0)
    const amount = Number(item.amountKrw ?? item.amount_krw ?? 0)
    const raw = String(textItem || item.scope || item.label || item.title || item.field || (item.categories || [])[0] || '')
    const { label, icon } = classifyRecoField(raw)
    if (seen.has(label)) return
    seen.add(label)
    const cap = item.monthlyBenefitLimitKrw ?? item.monthly_benefit_limit_krw ?? item.monthlyLimitKrw ?? item.monthly_limit_krw ?? 0
    const rateLabel = formatRate(rate) || (percentMatch ? formatRate(percentMatch[1]) : '')
    rows.push({
      id: item.id || item.benefitId || `${label}-${index}`,
      field: label,
      icon,
      value: rateLabel || (amount > 0 ? `${krw(amount)} 할인` : (textItem || '혜택 확인')),
      cap: formatLimit(cap),
    })
  })
  return rows.slice(0, 3)
}

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

// "이 지출, 매달 반복되나요?" — 급증 카테고리 → 클릭 시 가맹점별 내역 → 항목별 이번달만/매달
const RECURRING_ITEMS_KEY = 'carch.review.recurringItems.v1'
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
    // localStorage 사용 불가 시 이번 세션 메모리 값만 유지
  }
}
const recurringItemIds = ref(readStoredList(RECURRING_ITEMS_KEY).map(String))
const expandedCategory = ref('')

function toggleExpand(category) {
  expandedCategory.value = expandedCategory.value === category ? '' : category
}

const pendingReviewCandidates = computed(() => {
  const trend = spendingSummary.value?.spendingTrend
  const picked = []
  const seen = new Set()
  const addCandidate = (item, fallback = {}) => {
    const category = String(item?.category || fallback.category || '').trim()
    if (!category || seen.has(category)) return
    seen.add(category)
    picked.push({
      ...fallback,
      ...item,
      category,
      currentAmount: Number(item?.currentAmount ?? fallback.currentAmount ?? 0),
      previousAmount: Number(item?.previousAmount ?? fallback.previousAmount ?? 0),
      changeRateFromBaseline: Number(item?.changeRateFromBaseline ?? fallback.changeRateFromBaseline ?? 0),
    })
  }

  ;(trend?.reviewCandidates || []).forEach(addCandidate)
  ;(trend?.oneTimeCandidates || []).forEach(addCandidate)

  const trendByCategory = new Map((trend?.categoryChanges || []).map((item) => [item.category, item]))
  const currentCategoryRows = Object.entries(txByCategory.value)
    .map(([category, items]) => {
      const trendRow = trendByCategory.get(category) || {}
      const currentAmount = items.reduce((sum, item) => sum + Number(item.amount || 0), 0)
      return {
        category,
        currentAmount,
        previousAmount: Number(trendRow.previousAmount || 0),
        changeRateFromBaseline: Number(trendRow.changeRateFromBaseline || 0),
      }
    })
    .filter((item) => item.currentAmount > 0)
    .sort((a, b) => b.currentAmount - a.currentAmount)

  currentCategoryRows.forEach((item) => addCandidate(item))
  return picked.slice(0, 5)
})

// 지난달보다 얼마나 늘었는지 짧은 라벨
function spikeLabel(item) {
  const prev = Number(item.previousAmount || 0)
  const cur = Number(item.currentAmount || 0)
  if (prev > 0 && cur > prev) return `지난달보다 +${Math.round(((cur - prev) / prev) * 100)}%`
  const rate = Number(item.changeRateFromBaseline || 0)
  return rate > 0 ? `평소보다 +${Math.round(rate)}%` : ''
}

// 이번 달 카테고리별 거래 내역(지출만, 큰 금액순)
const txByCategory = computed(() => {
  const map = {}
  for (const tx of allTransactions.value) {
    const date = String(tx.date || tx.approvedAt || tx.approved_at || '')
    if (!date.startsWith(CURRENT_MONTH)) continue
    const signed = Number(tx.amount ?? tx.amt ?? 0)
    if (signed >= 0) continue
    const cat = tx.category || tx.cat || '기타'
    if (!map[cat]) map[cat] = []
    map[cat].push({
      id: String(tx.id),
      merchant: tx.merchant || tx.merchantName || tx.merchant_name || '가맹점',
      date: date.slice(0, 10),
      amount: Math.abs(signed),
    })
  }
  Object.values(map).forEach((list) => list.sort((a, b) => b.amount - a.amount))
  return map
})

function categoryItems(category) {
  return txByCategory.value[category] || []
}
function isItemRecurring(id) {
  return recurringItemIds.value.includes(String(id))
}
// 카테고리(어미)는 하위 항목이 '모두 매달'일 때만 반복 지출로 본다 — 자손 하나가 어미를 뒤집지 않게.
// 카테고리 토글을 누르면 setCategoryRecurring이 하위 항목 전체를 같은 상태로 내려보낸다(어미 우선).
function isCategoryRecurring(category) {
  const items = categoryItems(category)
  return items.length > 0 && items.every((i) => recurringItemIds.value.includes(i.id))
}

// 추천 엔진(recurringCategories)에는 '하위 항목 전부 매달'인 카테고리만 전달
const recurringCategories = computed(() =>
  Object.keys(txByCategory.value).filter((cat) => {
    const items = txByCategory.value[cat]
    return items.length > 0 && items.every((i) => recurringItemIds.value.includes(i.id))
  }),
)

// 1·2순위 추천 카드 — 분석이 쓰던 같은 추천 번들(aiBundle)을 재사용
const recommendationCards = computed(() => {
  const recurring = new Set(recurringCategories.value)
  return [...(aiBundle.value?.results || [])]
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

function persistRecurringItems() {
  writeStoredList(RECURRING_ITEMS_KEY, recurringItemIds.value)
}
async function setItemRecurring(id, enabled) {
  const key = String(id)
  const next = new Set(recurringItemIds.value)
  if (enabled) next.add(key)
  else next.delete(key)
  recurringItemIds.value = [...next]
  persistRecurringItems()
  await loadCurrentSpending()
}
async function setCategoryRecurring(category, enabled) {
  const next = new Set(recurringItemIds.value)
  categoryItems(category).forEach((item) => {
    if (enabled) next.add(item.id)
    else next.delete(item.id)
  })
  recurringItemIds.value = [...next]
  persistRecurringItems()
  await loadCurrentSpending()
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
  box-shadow: none;
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
  background: #ffffff;
  color: #17202b;
  box-shadow: none;
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
  font-weight: 500;
}

.cs-meta .cs-remain {
  font-size: 13px;
  font-weight: 500;
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
  font-weight: 500;
}

.ubar-head b i {
  color: #9aa6b3;
  font-size: 11px;
  font-weight: 500;
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
  font-weight: 500;
  letter-spacing: -0.3px;
  font-variant-numeric: tabular-nums;
}

.ai-reco-benefit.muted {
  color: #9aa6b3;
  font-size: 11px;
  font-weight: 500;
}

.plan-section {
  margin-bottom: 24px;
}

.plan-cta {
  display: flex;
  align-items: center;
  gap: 12px;
  border-radius: 16px;
  padding: 15px 16px;
  background: linear-gradient(135deg, #24364f 0%, #33507a 100%);
  color: #fff;
  text-decoration: none;
  box-shadow: 0 14px 26px rgba(36, 54, 79, 0.22);
}

.pc-icon {
  display: inline-flex;
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
}

.pc-text {
  flex: 1 1 auto;
  min-width: 0;
}

.pc-text strong {
  display: block;
  color: #fff;
  font-size: 14.5px;
  font-weight: 800;
}

.pc-text small {
  display: block;
  margin-top: 2px;
  color: rgba(255, 255, 255, 0.74);
  font-size: 11.5px;
  font-weight: 600;
}

.pc-go {
  flex: 0 0 auto;
  color: rgba(255, 255, 255, 0.7);
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

/* 잔액: + 초록 / − 빨강 (현재월 강조 행에서도 색 유지) */
.trend-months .tm-row .pos {
  color: #16a34a;
  font-weight: 500;
}

.trend-months .tm-row .neg {
  color: #e5484d;
  font-weight: 500;
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

/* ── 분석 탭에서 이동: "이 지출 반복?" + 새 카드 추천 ── */
.analysis-card {
  margin-top: 12px;
  border: 1px solid rgba(36, 54, 79, 0.08) !important;
  border-radius: 18px !important;
  padding: 16px !important;
  background: rgba(255, 255, 255, 0.82) !important;
  box-shadow: 0 13px 28px rgba(36, 54, 79, 0.055) !important;
}

.review-section {
  margin-top: 24px;
}

.review-sub {
  margin: -3px 0 11px;
  color: #7a8592;
  font-size: 11.5px;
  font-weight: 700;
  line-height: 1.4;
}

.review-card {
  margin-top: 0;
}

.review-head {
  margin-bottom: 12px;
}

.review-head strong {
  display: block;
  color: #20242a;
  font-size: 19px;
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

.review-group {
  border-radius: 14px;
  background: #f5f8fb;
  overflow: hidden;
}

.review-group + .review-group {
  margin-top: 8px;
}

.review-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto;
  gap: 10px;
  align-items: center;
  border-radius: 14px;
  padding: 11px 12px;
  background: #f5f8fb;
  cursor: pointer;
}

.review-spike {
  display: block;
  margin-top: 2px;
  color: #d2624a;
  font-size: 11px;
  font-weight: 800;
  font-style: normal;
}

.review-caret {
  flex-shrink: 0;
  color: #9aa6b3;
  transition: transform 160ms ease;
}

.review-caret.open {
  transform: rotate(180deg);
}

.review-detail {
  padding: 2px 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rd-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  grid-template-areas: 'info amount' 'toggle toggle';
  gap: 6px 10px;
  align-items: center;
  border-radius: 11px;
  padding: 9px 11px;
  background: #fff;
  border: 1px solid rgba(36, 54, 79, 0.06);
}

.rd-info {
  grid-area: info;
  min-width: 0;
}

.rd-info strong {
  display: block;
  overflow: hidden;
  color: #17202b;
  font-size: 12.5px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rd-info span {
  display: block;
  margin-top: 1px;
  color: #8a95a3;
  font-size: 10.5px;
  font-weight: 700;
}

.rd-amount {
  grid-area: amount;
  color: #17202b;
  font-size: 12.5px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.rd-toggle {
  grid-area: toggle;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  margin-top: 2px;
}

.rd-toggle button {
  min-height: 30px;
  border: 1px solid rgba(36, 54, 79, 0.16);
  border-radius: 9px;
  padding: 0 8px;
  background: #f7f9fc;
  color: #8a95a3;
  font-size: 11.5px;
  font-weight: 900;
  white-space: nowrap;
  touch-action: manipulation;
  transition: transform 120ms ease, background 140ms ease, color 140ms ease;
}

.rd-toggle button.active {
  border-color: transparent;
  background: #24364f;
  color: #fff;
}

.rd-toggle button.is-recurring.active {
  background: #0f5fae;
}

.rd-toggle button:active {
  transform: scale(0.96);
}

.rd-empty {
  margin: 4px 2px;
  color: #8a95a3;
  font-size: 11.5px;
  font-weight: 700;
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

.rec-section {
  margin-top: 24px;
}

.rec-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 11px;
  padding: 0;
}

.rec-section-head strong {
  color: #17202b;
  font-size: 19px;
  font-weight: 900;
}

.rec-section-head a {
  color: #0f5fae;
  font-size: 12px;
  font-weight: 800;
  text-decoration: none;
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

/* 소비계획 하단 — 목표 지출 계획 추천 요약 */
.plan-reco-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 24px;
}

.plan-reco {
  display: block;
  border: 1px solid rgba(36, 54, 79, 0.08);
  border-radius: 18px;
  padding: 16px 16px 14px;
  background: #fff;
  color: inherit;
  text-decoration: none;
  box-shadow: 0 12px 26px rgba(36, 54, 79, 0.06);
}

.pr-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.pr-top strong {
  overflow: hidden;
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pr-meta {
  display: flex;
  flex: 0 0 auto;
  flex-direction: column;
  align-items: flex-end;
  gap: 3px;
}

.pr-date {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  border-radius: 999px;
  padding: 2px 8px;
  background: rgba(15, 95, 174, 0.1);
  color: #0f5fae;
  font-size: 10.5px;
  font-weight: 800;
  white-space: nowrap;
}

.pr-total {
  color: #5f6b77;
  font-size: 13px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.pr-more {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  width: 100%;
  border: 1px solid rgba(36, 54, 79, 0.12);
  border-radius: 12px;
  padding: 11px;
  background: #fff;
  color: #4a5663;
  font-size: 12.5px;
  font-weight: 800;
}

.pr-more svg {
  transition: transform 180ms ease;
}

.pr-more svg.flip {
  transform: rotate(180deg);
}

.pr-line {
  margin: 6px 0 0;
  color: #5f6b77;
  font-size: 12px;
  font-weight: 700;
}

.pr-line b {
  color: #0f5fae;
  font-weight: 900;
}

.pr-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 12px 0 0;
  padding: 12px 0 0;
  border-top: 1px solid rgba(36, 54, 79, 0.08);
  list-style: none;
}

.pr-item {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 4px 0;
}

.pr-thumb {
  position: relative;
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 42px;
  height: 27px;
  overflow: hidden;
  border-radius: 6px;
  background: #e8edf2;
  color: #8a9aad;
  box-shadow: 0 2px 7px rgba(36, 54, 79, 0.18);
}

.pr-thumb img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.pr-thumb img.is-portrait {
  inset: auto;
  top: 50%;
  left: 50%;
  width: 27px;
  height: 42px;
  max-width: none;
  transform: translate(-50%, -50%) rotate(-90deg);
}

.pr-item-body {
  flex: 1 1 auto;
  min-width: 0;
}

.pr-item-body strong {
  display: block;
  overflow: hidden;
  color: #17202b;
  font-size: 13px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pr-item-body small {
  display: block;
  margin-top: 2px;
  overflow: hidden;
  color: #6e7885;
  font-size: 11.5px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pr-item-body small b {
  color: #0f5fae;
  font-weight: 900;
}

.pr-benefit {
  flex: 0 0 auto;
  color: #15a34a;
  font-size: 12.5px;
  font-weight: 900;
  font-style: normal;
  font-variant-numeric: tabular-nums;
}

.pr-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
  padding-top: 11px;
  border-top: 1px solid rgba(36, 54, 79, 0.08);
}

.pr-foot span {
  color: #6e7885;
  font-size: 12px;
  font-weight: 800;
}

.pr-foot b {
  color: #15a34a;
  font-size: 14px;
  font-weight: 900;
  font-variant-numeric: tabular-nums;
}
</style>
