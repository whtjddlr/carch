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
        <div class="summary-top">
          <span>이번 달 사용</span>
          <strong>{{ krw(currentBudget.spent) }}</strong>
        </div>
        <div class="summary-meta">
          <span>{{ currentBudget.percent }}%</span>
          <b :class="{ danger: currentBudget.remaining < 0 }">
            {{ currentBudget.remaining < 0 ? `${krw(Math.abs(currentBudget.remaining))} 초과` : `${krw(currentBudget.remaining)} 남음` }}
          </b>
        </div>
        <div class="summary-track">
          <i :style="{ width: `${budgetProgressWidth(currentBudget.percent)}%`, background: budgetRiskColor(currentBudget.percent) }" />
        </div>
      </RouterLink>
    </header>

    <div class="screen-scroll scrollbar-hide budget-list-body">
      <section v-if="cardGuideItems.length" class="card-guide-section">
        <div class="section-head split">
          <h2>카드 사용 가이드</h2>
          <RouterLink to="/recommendations/new">상세 추천</RouterLink>
        </div>
        <article class="card-guide-card">
          <div class="guide-focus">
            <div>
              <span>다음 달 혜택 준비</span>
              <strong>{{ primaryCardGuide.card.name }}</strong>
              <p>{{ primaryCardGuide.reason }}</p>
            </div>
            <span class="guide-card-image">
              <img
                v-if="primaryCardGuide.card.imageUrl"
                :src="primaryCardGuide.card.imageUrl"
                :alt="primaryCardGuide.card.name"
                :class="primaryCardGuide.card.imageOrientation === 'landscape' ? 'is-landscape' : 'is-portrait'"
              />
            </span>
          </div>

          <div class="guide-list">
            <RouterLink
              v-for="item in cardGuideItems"
              :key="item.category.id"
              class="guide-row"
              :to="{ path: '/plans/new', query: { category: item.category.name, cardId: item.card.id, budget: item.remaining } }"
            >
              <div>
                <span>{{ item.category.name }} · {{ item.rateLabel }}</span>
                <strong>{{ item.card.name }}</strong>
              </div>
              <p>
                <span class="guide-budget">{{ item.remainingLabel }}</span>
                <b class="guide-status" :class="item.performanceTone">{{ item.performanceLabel }}</b>
              </p>
            </RouterLink>
          </div>
        </article>
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
import { computed } from 'vue'
import { CalendarClock, ChevronRight, PiggyBank, Zap } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { budgetCategories, cards as mockCards, expenseModes, krw } from '@/data/mockData'
import { readBudgetOverride, readCustomBudgetCategories } from '@/services/budgetStorage'
import { budgetProgressWidth, budgetRiskColor, budgetUsagePercent } from '@/utils/budgetRisk'
import { compareCardBenefitCandidates, scoreCardBenefit, summarizeWalletPerformance } from '@/utils/cardPerformance'

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

function performanceStatusTone(performance) {
  if (!performance) return 'is-waiting'
  return performance.currentBenefitEligible || performance.nextMonthWillQualify ? 'is-ready' : 'is-waiting'
}

function cardGuideReason(item) {
  if (item.performance?.noPerformanceRequired) {
    return `${item.category.name} 예산은 전월 조건 없이 바로 혜택을 받을 수 있어요.`
  }
  if (item.performance?.currentBenefitEligible) {
    return `${item.category.name} 예산은 전월 실적이 충족된 카드라 이번 달 혜택을 받을 수 있어요.`
  }
  if (item.fillsPerformanceOverNoPerformance) {
    return `무실적 카드는 당장 혜택을 받을 수 있지만, ${item.category.name} 예산은 ${item.card.name} 실적을 완성해 다음 달 혜택을 여는 쪽이 더 좋아요.`
  }
  if (item.needsPreparationOnly && item.performance?.nextMonthWillQualify) {
    return `전월 실적 충족 카드가 없어 이번 달 혜택은 어렵지만, ${item.category.name} 예산을 ${item.card.name}에 쓰면 다음 달 조건을 열 수 있어요.`
  }
  if (item.needsPreparationOnly) {
    return `전월 실적 충족 카드가 없어 이번 달은 혜택보다 다음 달 조건 준비가 우선이에요. ${item.card.name}은 ${item.category.name} 기대혜택이 가장 큽니다.`
  }
  if (item.performance?.nextMonthWillQualify) {
    return `${item.category.name} 지출을 ${item.card.name}에 모으면 다음 달 혜택 조건을 채워요.`
  }
  return `이번 달 사용 기준 ${item.card.name} 다음 달 조건까지 ${krw(item.performance.remainingAfter)} 부족해요.`
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
  padding: 24px 20px 22px;
  border: 1px solid rgba(138, 154, 173, 0.12);
  border-top: 0;
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
  gap: 14px;
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
  font-size: 24px;
  font-weight: 900;
  line-height: 1.1;
}

.current-summary {
  display: block;
  border: 1px solid rgba(36, 54, 79, 0.08);
  border-radius: 20px;
  padding: 16px 16px 15px;
  background: rgba(255, 255, 255, 0.82);
  color: #17202b;
  text-decoration: none;
  box-shadow: 0 14px 28px rgba(36, 54, 79, 0.07);
  backdrop-filter: blur(12px) saturate(1.04);
}

.summary-top,
.summary-meta {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.summary-top {
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.summary-top span,
.summary-meta b {
  color: #6f7d8c;
  font-size: 12px;
  font-weight: 800;
}

.summary-meta b.danger {
  color: var(--carch-danger);
}

.summary-top strong {
  display: block;
  font-size: 38px;
  font-weight: 900;
  line-height: 1;
}

.summary-meta {
  justify-content: center;
  margin-top: 10px;
}

.summary-meta span {
  font-size: 13px;
  font-weight: 900;
}

.summary-track {
  height: 7px;
  overflow: hidden;
  width: min(100%, 300px);
  margin: 12px auto 0;
  border-radius: 999px;
  background: #e7edf4;
}

.summary-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  box-shadow: 0 5px 12px rgba(36, 54, 79, 0.12);
  transition: width 0.2s ease, background-color 0.2s ease;
}

.budget-list-body {
  padding: 16px 20px 112px;
}

.card-guide-section {
  margin-bottom: 24px;
}

.card-guide-card {
  overflow: hidden;
  border: 1px solid rgba(15, 95, 174, 0.1);
  border-radius: 18px;
  padding: 15px;
  background:
    radial-gradient(circle at 95% 0%, rgba(0, 140, 149, 0.1), transparent 35%),
    linear-gradient(145deg, #ffffff 0%, #f8fbfe 100%);
  box-shadow: 0 10px 24px rgba(36, 54, 79, 0.07);
}

.guide-focus {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 48px;
  align-items: center;
  gap: 14px;
}

.guide-focus span:first-child {
  display: block;
  color: #0f5fae;
  font-size: 11px;
  font-weight: 900;
}

.guide-focus strong {
  display: block;
  margin-top: 5px;
  color: #17202b;
  font-size: 17px;
  font-weight: 950;
  line-height: 1.22;
  word-break: keep-all;
}

.guide-focus p {
  margin: 6px 0 0;
  color: #536170;
  font-size: 12px;
  font-weight: 750;
  line-height: 1.45;
  word-break: keep-all;
}

.guide-card-image {
  position: relative;
  display: block;
  width: 42px;
  height: 58px;
  justify-self: end;
  overflow: hidden;
  border-radius: 7px;
  background: #e8edf2;
  box-shadow: 0 8px 18px rgba(36, 54, 79, 0.16);
}

.guide-card-image img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.guide-card-image img.is-landscape {
  inset: auto;
  top: 50%;
  left: 50%;
  width: 58px;
  height: 42px;
  transform: translate(-50%, -50%) rotate(90deg);
}

.guide-list {
  display: grid;
  gap: 0;
  margin-top: 13px;
  border-top: 1px solid rgba(32, 36, 42, 0.08);
}

.guide-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid rgba(32, 36, 42, 0.075);
  padding: 11px 0;
  color: inherit;
  text-decoration: none;
}

.guide-row:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.guide-row span {
  display: block;
  color: #7a8795;
  font-size: 10.5px;
  font-weight: 800;
}

.guide-row strong {
  display: block;
  margin-top: 3px;
  color: #20242a;
  font-size: 13px;
  font-weight: 900;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.guide-row p {
  display: flex;
  min-width: 96px;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  margin: 0;
  color: #0f5fae;
  white-space: nowrap;
}

.guide-row .guide-budget {
  color: #8a96a5;
  font-size: 10.5px;
  font-weight: 800;
}

.guide-status {
  border-radius: 999px;
  padding: 4px 7px;
  background: rgba(15, 95, 174, 0.08);
  color: #0f5fae;
  font-size: 10.5px;
  font-weight: 900;
  line-height: 1;
}

.guide-status.is-waiting {
  background: rgba(249, 115, 22, 0.1);
  color: #c2410c;
}

.guide-status.is-ready {
  background: rgba(0, 140, 149, 0.1);
  color: #007780;
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
