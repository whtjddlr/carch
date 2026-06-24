<template>
  <section class="screen">
    <header class="budget-list-header blue-gradient">
      <div class="header-row">
        <AppBackButton fallback="/cards" />
        <div>
          <h1>소비계획</h1>
        </div>
      </div>

      <RouterLink class="current-summary" to="/budget/current" aria-label="6월 예산 상세 보기">
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
    </header>

    <div class="screen-scroll scrollbar-hide budget-list-body">
      <section v-if="cardGuideItems.length" class="card-guide-section">
        <div class="section-head split">
          <h2>카드 사용 가이드</h2>
          <RouterLink to="/recommendations/usage">상세 추천</RouterLink>
        </div>
        <div class="guide-list">
          <RouterLink
            v-for="item in cardGuideItems"
            :key="item.category.id"
            class="guide-row"
            :to="{ path: '/plans/new', query: { category: item.category.name, cardId: item.card.id, budget: item.remaining } }"
          >
            <span class="guide-thumb">
              <img
                v-if="item.card.imageUrl"
                :src="item.card.imageUrl"
                :alt="item.card.name"
                :class="thumbOrientation[item.card.id]"
                @load="onThumbLoad(item.card.id, $event)"
              />
              <CreditCard v-else :size="16" />
            </span>
            <div class="guide-info">
              <span class="guide-cat">{{ item.category.name }} · {{ item.rateLabel }}</span>
              <strong>{{ item.card.name }}</strong>
              <small>남은 {{ krw(item.remaining) }} · 한도 {{ krw(item.category.budget) }}</small>
            </div>
            <b class="guide-status" :class="item.performanceTone">{{ item.performanceShort }}</b>
          </RouterLink>
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

        <RouterLink
          v-for="item in budgetHistory"
          :key="item.id"
          class="app-card budget-history-card"
          :to="item.to"
        >
          <div class="history-content">
            <div class="history-title-row">
              <div>
                <strong :class="['history-headline', item.tone]">{{ item.relativeLabel }}</strong>
                <span>{{ item.month }}월 · {{ item.period }}</span>
              </div>
              <ChevronRight :size="17" />
            </div>

            <div class="history-metrics">
              <div>
                <span>사용</span>
                <b>{{ krw(item.spent) }}</b>
              </div>
              <div>
                <span>예산</span>
                <b>{{ krw(item.budget) }}</b>
              </div>
              <div class="remaining-cell">
                <b :class="item.remaining < 0 ? 'neg' : 'pos'">{{ item.remaining < 0 ? '-' : '+' }}{{ krw(item.remaining) }}</b>
              </div>
            </div>

            <div class="history-track">
              <i :style="{ width: `${budgetProgressWidth(item.percent)}%`, background: budgetRiskColor(item.percent) }" />
            </div>
          </div>
        </RouterLink>
      </section>

    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { CalendarClock, ChevronRight, CreditCard, PiggyBank, Zap } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { budgetCategories, cards as mockCards, expenseModes, krw } from '@/data/mockData'
import { readBudgetOverride, readCustomBudgetCategories } from '@/services/budgetStorage'
import { budgetProgressWidth, budgetRiskColor, budgetRiskLabel, budgetUsagePercent } from '@/utils/budgetRisk'
import { compareCardBenefitCandidates, scoreCardBenefit, summarizeWalletPerformance } from '@/utils/cardPerformance'

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

const customBudgetCategories = readCustomBudgetCategories()
const displayBudgetCategories = [...budgetCategories, ...customBudgetCategories]
const budgetOverride = readBudgetOverride()
const totalBudget = computed(() => budgetOverride ?? displayBudgetCategories.reduce((sum, category) => sum + category.budget, 0))
const totalSpent = computed(() => displayBudgetCategories.reduce((sum, category) => sum + category.spent, 0))
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
  display: block;
  border: 1px solid rgba(36, 54, 79, 0.08);
  border-radius: 20px;
  padding: 15px 18px 16px;
  background: rgba(255, 255, 255, 0.88);
  color: #17202b;
  text-decoration: none;
  box-shadow: 0 14px 28px rgba(36, 54, 79, 0.07);
  backdrop-filter: blur(12px) saturate(1.04);
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

.guide-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.guide-row {
  display: flex;
  align-items: center;
  gap: 11px;
  border-radius: 15px;
  padding: 11px 13px;
  background: rgba(44, 78, 114, 0.05);
  color: inherit;
  text-decoration: none;
}

.guide-thumb {
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

.guide-thumb img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.guide-thumb img.is-portrait {
  inset: auto;
  top: 50%;
  left: 50%;
  width: 27px;
  height: 42px;
  max-width: none;
  transform: translate(-50%, -50%) rotate(-90deg);
}

.guide-info {
  flex: 1 1 auto;
  min-width: 0;
}

.guide-info .guide-cat {
  display: block;
  color: #2c4e72;
  font-size: 11px;
  font-weight: 900;
}

.guide-info strong {
  display: block;
  overflow: hidden;
  margin-top: 1px;
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.guide-info small {
  display: block;
  margin-top: 2px;
  color: #6e7885;
  font-size: 11px;
  font-weight: 800;
}

.guide-status {
  flex-shrink: 0;
  align-self: center;
  border-radius: 999px;
  padding: 5px 9px;
  background: rgba(15, 95, 174, 0.08);
  color: #0f5fae;
  font-size: 10.5px;
  font-weight: 900;
  line-height: 1;
  white-space: nowrap;
}

.guide-status.is-waiting {
  background: rgba(245, 158, 11, 0.14);
  color: #b45309;
}

.guide-status.is-ready {
  background: rgba(22, 163, 74, 0.12);
  color: #15803d;
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
