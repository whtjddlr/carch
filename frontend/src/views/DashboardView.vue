<template>
  <section class="screen">
    <header class="dashboard-header">
      <div class="header-top">
        <RouterLink class="brand-lockup" to="/cards" aria-label="Carch 홈">
          <div class="brand-copy">
            <span class="brand-logo-shell">
              <img class="brand-wordmark" src="/brand/carch-wordmark-transparent.png" alt="Carch" />
            </span>
          </div>
        </RouterLink>
        <div class="header-actions">
          <RouterLink class="icon-button" to="/search" aria-label="검색">
            <Search :size="18" />
          </RouterLink>
          <RouterLink class="icon-button" to="/notifications" aria-label="알림">
            <Bell :size="18" />
          </RouterLink>
          <RouterLink class="icon-button" to="/settings" aria-label="프로필 및 설정">
            <User :size="18" />
          </RouterLink>
        </div>
      </div>

      <div class="month-summary">
        <div class="greet">
          <div class="greet-copy">
            <span>안녕하세요, {{ user.name }}님</span>
            <strong>오늘도 선명한 하루 보내세요.</strong>
          </div>
        </div>
        <div class="spend-figure">
          <span>이번 달 사용 금액</span>
          <strong>{{ totalSpendLabel }}</strong>
        </div>
      </div>
    </header>

    <div class="screen-scroll scrollbar-hide dashboard-body">

      <div class="card-carousel" :class="[{ 'is-gliding': isCarouselGliding }, `glide-${carouselDirection}`]">
        <div
          class="card-stage"
          @pointerdown="onDragStart"
          @pointermove="onDragMove"
          @pointerup="onDragEnd"
          @pointercancel="onDragEnd"
        >
          <button
            v-for="(card, index) in cards"
            :key="card.id"
            type="button"
            class="slide-card"
            :class="[`card-tone-${card.grad}`, { 'is-active': activeCardIndex === index }]"
            :style="slideCardStyle(index)"
            :aria-label="activeCardIndex === index ? `${card.name} 상세 보기` : `${card.name} 선택`"
            @click="onSlideClick(index)"
          >
            <span class="fan-card-media">
              <span v-if="card.imageUrl" class="fan-card-image" :class="cardImageClass(card)">
                <img
                  :src="card.imageUrl"
                  :alt="card.name"
                  @load="setImageOrientation(card.id, $event)"
                />
              </span>
            </span>
          </button>

          <button
            type="button"
            class="slide-card slide-add"
            :class="{ 'is-active': activeCardIndex === cards.length }"
            :style="slideCardStyle(cards.length)"
            :aria-label="activeCardIndex === cards.length ? '카드 추가 열기' : '카드 추가 선택'"
            @click="onSlideClick(cards.length)"
          >
            <span class="fan-card-media slide-add-media">
              <PlusCircle :size="48" :stroke-width="1.8" />
            </span>
          </button>
        </div>

        <div class="card-detail-stage">
          <Transition name="card-detail-spin">
            <div
              v-if="detailCard"
              :key="detailCard.id"
              class="card-detail-panel"
              :class="`card-tone-${detailCard.grad}`"
            >
            <div class="card-info">
              <div class="issuer-row">
                <span>{{ detailCard.issuer || detailCard.brand }}</span>
                <em>{{ detailCard.brand }}</em>
              </div>
              <strong>{{ detailCard.name }}</strong>
              <p class="benefit-summary">{{ detailCard.benefitSummary || detailCard.titleDescription }}</p>
            </div>
            <div class="card-bottom">
              <div class="spend-progress" :class="{ 'is-no-performance': hasNoPerformanceRequirement(detailCard) }">
                <div class="progress-head">
                  <span>{{ hasNoPerformanceRequirement(detailCard) ? '혜택 조건' : '혜택 조건 충족률' }}</span>
                  <b>{{ hasNoPerformanceRequirement(detailCard) ? '전월실적 없음' : `${spendProgress(detailCard)}%` }}</b>
                </div>
                <template v-if="hasNoPerformanceRequirement(detailCard)">
                  <div class="progress-meta no-requirement">
                    <span>
                      <small>이번 달 사용액</small>
                      <b>{{ krw(detailCard.spent) }}</b>
                    </span>
                    <span>
                      <small>혜택 적용</small>
                      <b>바로 가능</b>
                    </span>
                  </div>
                </template>
                <template v-else>
                  <div class="progress-track">
                    <i :style="{ width: `${spendProgress(detailCard)}%` }" />
                  </div>
                  <div class="progress-meta">
                    <span>
                      <small>기준 사용액</small>
                      <b>{{ krw(detailCard.spent) }}</b>
                    </span>
                    <span>
                      <small>남은 조건</small>
                      <b>{{ remainingSpend(detailCard) > 0 ? krw(remainingSpend(detailCard)) : '충족' }}</b>
                    </span>
                  </div>
                </template>
              </div>
              <div class="benefit-chips">
                <span v-for="benefit in benefitTags(detailCard)" :key="benefit">{{ benefit }}</span>
              </div>
            </div>
          </div>
          </Transition>

          <div v-if="activeCardIndex >= cards.length" class="add-card-prompt">
            <strong>새 카드 추가</strong>
            <p>보유 카드를 등록해 한눈에 관리하세요</p>
          </div>
        </div>

        <p v-if="cardManageMessage" class="card-manage-note">{{ cardManageMessage }}</p>
        <p v-if="cardManageError" class="card-manage-note error">{{ cardManageError }}</p>
      </div>

      <div class="quick-grid">
        <RouterLink
          v-for="action in quickActions"
          :key="action.label"
          :to="action.path"
          class="quick-action app-card-sm"
          :class="{ 'is-primary': action.primary }"
        >
          <component :is="action.icon" :size="20" :style="{ color: action.color }" />
          <span>{{ action.label }}</span>
        </RouterLink>
      </div>

      <section v-if="merchantRecommendation" class="section-block payment-advice-section">
        <div class="section-head">
          <h2>보유 카드 사용 가이드</h2>
          <RouterLink :to="merchantRecommendationLink">소비계획</RouterLink>
        </div>
        <RouterLink class="payment-advice-card" :to="merchantRecommendationLink">
          <div class="advice-topline">
            <span><Sparkles :size="14" /> 예정 지출 가이드</span>
            <b v-if="merchantRecommendation.extraBenefit > 0">+{{ krw(merchantRecommendation.extraBenefit) }}</b>
            <b v-else-if="merchantRecommendation.isBlocked">다음달 준비</b>
            <b v-else>적합</b>
          </div>
          <div class="advice-main">
            <div class="advice-copy">
              <span>{{ merchantRecommendation.category }} · {{ merchantRecommendation.merchant }}</span>
              <strong>{{ merchantRecommendation.headline }}</strong>
              <p>{{ merchantRecommendation.message }}</p>
              <small class="advice-performance" :class="merchantRecommendation.performanceTone">
                {{ merchantRecommendation.performanceNote }}
              </small>
            </div>
            <span class="advice-card-image">
              <img
                v-if="merchantRecommendation.recommendedCard.imageUrl"
                :src="merchantRecommendation.recommendedCard.imageUrl"
                :alt="merchantRecommendation.recommendedCard.name"
                :class="cardImageClass(merchantRecommendation.recommendedCard)"
                @load="setImageOrientation(merchantRecommendation.recommendedCard.id, $event)"
              />
            </span>
          </div>
          <div class="advice-route">
            <span>{{ merchantRecommendation.currentCard.name }}</span>
            <i aria-hidden="true" />
            <strong>{{ merchantRecommendation.routeTargetLabel }}</strong>
          </div>
        </RouterLink>
      </section>

      <section class="section-block">
        <div class="section-head">
          <h2>최근 거래</h2>
          <RouterLink to="/transactions">전체보기</RouterLink>
        </div>
        <article class="tx-card">
          <button v-for="tx in transactions.slice(0, 5)" :key="tx.id" type="button" @click="router.push(`/transactions/${tx.id}`)">
            <span>{{ tx.icon }}</span>
            <div>
              <strong>{{ tx.merchant }}</strong>
              <small>{{ tx.cat }} · {{ tx.time }}</small>
            </div>
            <span class="tx-mini-card">
              <img
                v-if="txCard(tx)"
                :src="txCard(tx).imageUrl"
                :alt="txCard(tx).name"
                :class="cardImageClass(txCard(tx))"
                @load="setImageOrientation(txCard(tx).id, $event)"
              />
            </span>
            <b :class="{ plus: tx.amt > 0 }">{{ tx.amt > 0 ? '+' : '-' }}{{ krw(tx.amt) }}</b>
          </button>
        </article>
      </section>

    </div>

    <div v-if="isCardPickerOpen" class="card-picker-backdrop" @click.self="closeCardPicker">
      <section class="card-picker-sheet" aria-label="카드 추가">
        <header>
          <div>
            <span>카드 추가</span>
            <h2>목록에서 내 카드를 선택하세요</h2>
          </div>
          <button type="button" class="picker-close-button" aria-label="닫기" @click="closeCardPicker">
            <X :size="18" />
          </button>
        </header>

        <form class="card-search-form" @submit.prevent="loadCandidateCards">
          <Search :size="17" />
          <input
            v-model.trim="cardSearch"
            type="search"
            placeholder="카드명, 카드사, 혜택 검색"
            @input="scheduleCandidateSearch"
          />
        </form>

        <div class="candidate-card-list scrollbar-hide">
          <p v-if="isLoadingCandidateCards" class="candidate-empty">카드를 찾는 중입니다.</p>
          <p v-else-if="candidateCards.length === 0" class="candidate-empty">검색 결과가 없습니다.</p>
          <template v-else>
            <article v-for="candidate in candidateCards" :key="candidateCardId(candidate)" class="candidate-card-row">
              <div class="candidate-card-image">
                <img
                  v-if="candidate.imageUrl || candidate.image_url"
                  :src="candidate.imageUrl || candidate.image_url"
                  :alt="candidate.name || candidate.cardName || candidate.card_name"
                />
              </div>
              <div class="candidate-card-copy">
                <span>{{ candidate.issuer || candidate.issuerName || candidate.issuer_name }}</span>
                <strong>{{ candidate.name || candidate.cardName || candidate.card_name }}</strong>
                <p>{{ candidate.benefitSummary || candidate.titleDescription || candidate.title_description }}</p>
              </div>
              <button
                type="button"
                :aria-label="isOwnedCandidate(candidate) ? '이미 보유한 카드' : `${candidate.name || candidate.cardName || candidate.card_name} 추가`"
                :disabled="isOwnedCandidate(candidate) || isAddingCardId === candidateCardId(candidate)"
                @click="handleAddCandidate(candidate)"
              >
                <Check v-if="isOwnedCandidate(candidate)" :size="16" />
                <PlusCircle v-else :size="16" />
              </button>
            </article>
          </template>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, CalendarDays, Check, PlusCircle, Search, Sparkles, User, X } from 'lucide-vue-next'
import { budgetCategories, cards as mockCards, krw, transactions as mockTransactions, user } from '@/data/mockData'
import { addOwnedCard, deleteOwnedCard, fetchCards, fetchOwnedCards, fetchTransactions, normalizeCard } from '@/services/api'
import { readCustomBudgetCategories } from '@/services/budgetStorage'
import { cardPerformance, scoreCardBenefit } from '@/utils/cardPerformance'

const router = useRouter()
const cards = ref(mockCards)
const transactions = ref(mockTransactions)
const activeCardIndex = ref(0)
const isCarouselGliding = ref(false)
const carouselDirection = ref('next')
const imageOrientations = ref({})
const isCardPickerOpen = ref(false)
const isCardManageMenuOpen = ref(false)
const cardSearch = ref('')
const candidateCards = ref([])
const isLoadingCandidateCards = ref(false)
const cardManageMessage = ref('')
const cardManageError = ref('')
const isDeletingCard = ref(false)
const isAddingCardId = ref('')
const totalSpent = computed(() => cards.value.reduce((sum, card) => sum + card.spent, 0))
const totalSpendLabel = computed(() => krw(totalSpent.value))
const activeCard = computed(() => cards.value[activeCardIndex.value] || null)
const detailCard = computed(() => activeCard.value)
const quickActions = [
  { label: '결제 추가', path: '/transactions/new', icon: PlusCircle, color: '#0f5fae' },
  { label: '카드 추천', path: '/recommendations/new', icon: Sparkles, color: '#008c95' },
  { label: '지출계획하기', path: '/plans/new', icon: CalendarDays, color: '#24364f' },
]
const futurePaymentCandidates = computed(() => (
  [...budgetCategories, ...readCustomBudgetCategories()]
    .map((category) => {
      const budget = Number(category.budget || 0)
      const spent = Number(category.spent || 0)
      const amount = Math.max(budget - spent, 0)
      return {
        id: `budget-${category.id}`,
        source: 'budget',
        category: category.name,
        merchant: '이번 달 남은 예산',
        amount,
        budget,
        spent,
      }
    })
    .filter((item) => item.amount > 0)
    .sort((a, b) => b.amount - a.amount)
))
const merchantRecommendation = computed(() => {
  const futureRows = futurePaymentCandidates.value
    .map(buildMerchantRecommendation)
    .filter(Boolean)
  return futureRows.find((item) => !item.isBlocked && item.extraBenefit > 0)
    || futureRows.find((item) => !item.isBlocked)
    || futureRows[0]
    || null
})
const merchantRecommendationLink = computed(() => {
  const item = merchantRecommendation.value
  if (!item) return '/budget'
  return {
    path: '/budget',
    query: {
      category: item.category,
      cardId: item.recommendedCard.id,
    },
  }
})
let cardGlideTimer = null
let cardSearchTimer = null

function focusCard(index) {
  if (index < 0 || index === activeCardIndex.value) return
  // 항상 오른쪽 → 왼쪽으로 전환 (그래프/상세 방향 통일)
  carouselDirection.value = 'next'
  activeCardIndex.value = index
}

const dragStartX = ref(null)
const wasDragged = ref(false)

function slideCardStyle(index) {
  const offset = index - activeCardIndex.value
  const abs = Math.abs(offset)
  const x = offset * 112
  const scale = Math.max(0.72, 1 - abs * 0.14)
  const opacity = offset === 0 ? 1 : Math.max(0.1, 0.32 - (abs - 1) * 0.22)
  return {
    transform: `translate(calc(-50% + ${x}%), 0) scale(${scale})`,
    opacity,
    zIndex: 20 - abs,
    pointerEvents: abs > 2 ? 'none' : 'auto',
  }
}

function onSlideClick(index) {
  if (wasDragged.value) return
  if (index >= cards.value.length) {
    if (activeCardIndex.value === cards.value.length) {
      openCardPicker()
      return
    }
    focusCard(cards.value.length)
    return
  }
  if (index === activeCardIndex.value) {
    router.push(`/cards/${cards.value[index].id}`)
    return
  }
  focusCard(index)
}

function onDragStart(event) {
  dragStartX.value = event.clientX
  wasDragged.value = false
}

function onDragMove(event) {
  if (dragStartX.value === null) return
  if (Math.abs(event.clientX - dragStartX.value) > 8) wasDragged.value = true
}

function onDragEnd(event) {
  if (dragStartX.value === null) return
  const dx = event.clientX - dragStartX.value
  dragStartX.value = null
  if (dx <= -36 && activeCardIndex.value < cards.value.length) focusCard(activeCardIndex.value + 1)
  else if (dx >= 36 && activeCardIndex.value > 0) focusCard(activeCardIndex.value - 1)
}

function spendProgress(card) {
  return cardPerformance(card).progress
}

function remainingSpend(card) {
  return cardPerformance(card).remainingBefore
}

function hasNoPerformanceRequirement(card) {
  return cardPerformance(card).noPerformanceRequired
}

function setImageOrientation(cardId, event) {
  const image = event.target
  const orientation = image.naturalWidth > image.naturalHeight ? 'landscape' : 'portrait'
  imageOrientations.value = { ...imageOrientations.value, [cardId]: orientation }
}

function cardImageClass(card) {
  const orientation = imageOrientations.value[card.id] || card.imageOrientation
  return {
    'is-ready': Boolean(orientation),
    'is-landscape': orientation === 'landscape',
    'is-portrait': orientation === 'portrait',
  }
}

function txCard(tx) {
  return cards.value.find((card) => String(card.id) === String(tx.cardId)) || null
}

function transactionAmount(tx) {
  return Number(tx.amount ?? tx.amt) || 0
}

function transactionCategory(tx) {
  return String(tx.category || tx.cat || '기타').trim()
}

function transactionMerchant(tx) {
  return String(tx.merchant || tx.merchantName || tx.merchant_name || '최근 결제').replace(/\s+/g, ' ').trim()
}

function normalizeSearchText(value) {
  return String(value || '').toLowerCase().replace(/\s+/g, ' ')
}

function includesAny(text, keywords) {
  return keywords.some((keyword) => text.includes(normalizeSearchText(keyword)))
}

function cardBenefitText(card) {
  return normalizeSearchText([
    card.name,
    card.issuer,
    card.benefitSummary,
    card.titleDescription,
    ...(card.benefits || []),
  ].filter(Boolean).join(' '))
}

function inferPaymentBenefitRate(card, tx) {
  const cardId = String(card.id || card.cardAdId || card.card_ad_id)
  const usageText = normalizeSearchText(`${transactionCategory(tx)} ${transactionMerchant(tx)}`)
  const benefitText = cardBenefitText(card)
  let rate = 0

  if (cardId === '10106') {
    if (includesAny(usageText, ['카페', '커피', '컴포즈', '스타벅스', '편의점', 'gs25', 'cu'])) {
      rate = Math.max(rate, 0.06)
    } else if (includesAny(usageText, ['식비', '외식', '배달'])) {
      rate = Math.max(rate, 0.06)
    }
  }
  if (cardId === '10612' && includesAny(usageText, ['쇼핑', '뷰티', '온라인', '무신사', '쿠팡', '올리브영'])) {
    rate = Math.max(rate, 0.1)
  }
  if (cardId === '10029') {
    rate = Math.max(rate, includesAny(usageText, ['교통', '택시', '전철', '철도', '지하철', '버스', '카카오t']) ? 0.01 : 0.015)
  }

  if (includesAny(usageText, ['쇼핑', '뷰티', '온라인']) && includesAny(benefitText, ['쇼핑', '온라인', '오프라인'])) {
    rate = Math.max(rate, 0.01)
  }
  if (includesAny(usageText, ['마트', '이마트']) && includesAny(benefitText, ['마트', '이마트'])) {
    rate = Math.max(rate, 0.15)
  }
  if (includesAny(usageText, ['교통', '택시', '전철', '철도', '지하철', '버스']) && includesAny(benefitText, ['교통', '대중교통'])) {
    rate = Math.max(rate, 0.1)
  }
  if (includesAny(usageText, ['편의점', 'gs25']) && includesAny(benefitText, ['편의점', '생활'])) {
    rate = Math.max(rate, 0.05)
  }
  if (!rate && includesAny(benefitText, ['언제나', '일상', '가맹점'])) {
    rate = 0.015
  }
  if (!rate && includesAny(benefitText, ['국내외 가맹점', '적립'])) {
    rate = 0.005
  }

  return rate
}

function formatBenefitRate(rate) {
  if (!rate) return '혜택'
  return `${Number((rate * 100).toFixed(1))}%`
}

function buildMerchantRecommendation(tx) {
  const amount = Math.abs(transactionAmount(tx))
  if (!amount || !cards.value.length) return null

  const currentCard = txCard(tx) || activeCard.value || cards.value[0]
  const scoredCards = cards.value.map((card) => {
    const rate = inferPaymentBenefitRate(card, tx)
    const score = scoreCardBenefit({ card, amount, rate })
    return {
      card,
      rate,
      benefit: score.activeBenefit,
      grossBenefit: score.grossBenefit,
      performance: score,
    }
  })
  const currentScore = scoredCards.find((item) => String(item.card.id) === String(currentCard.id)) || scoredCards[0]
  const activeScores = scoredCards.filter((item) => item.grossBenefit > 0 && item.performance.currentBenefitEligible)
  const blockedScores = scoredCards.filter((item) => item.grossBenefit > 0)
  const bestScore = (activeScores.length ? activeScores : blockedScores).sort((a, b) => (
    b.benefit - a.benefit
    || Number(!b.performance.blocked) - Number(!a.performance.blocked)
    || b.grossBenefit - a.grossBenefit
    || a.performance.remainingAfter - b.performance.remainingAfter
  ))[0]
  if (!bestScore || bestScore.grossBenefit <= 0) return null

  const extraBenefit = Math.max(bestScore.benefit - (currentScore?.benefit || 0), 0)
  const merchant = transactionMerchant(tx)
  const category = transactionCategory(tx)
  const performance = bestScore.performance
  const isBlocked = !performance.currentBenefitEligible
  const performanceNote = performance.noPerformanceRequired
    ? '무실적 혜택 카드'
    : performance.currentBenefitEligible
    ? '이번 달 혜택 가능 카드'
    : performance.nextMonthWillQualify
      ? '이번 지출로 다음 달 조건 충족'
      : `다음 달 조건까지 ${krw(performance.remainingAfter)} 부족`
  const performanceTone = isBlocked ? 'is-waiting' : 'is-ready'
  const isSameCard = String(bestScore.card.id) === String(currentCard.id)
  const headline = isBlocked
    ? `${bestScore.card.name}은 다음 달 혜택 준비가 필요해요`
    : performance.noPerformanceRequired
      ? `${bestScore.card.name}는 조건 없이 혜택 가능해요`
    : performance.nextMonthWillQualify && !performance.currentBenefitEligible
      ? `${bestScore.card.name}은 다음 달 혜택 조건을 채워요`
      : `${bestScore.card.name}로 결제하면 좋아요`
  const routeTargetLabel = isSameCard
    ? isBlocked ? '다음달 준비' : performance.noPerformanceRequired ? '무실적 유지' : '현재 카드 유지'
    : bestScore.card.name
  const message = isBlocked
    ? `이번 결제는 다음 달 실적에 반영돼요. 현재 ${krw(performance.spent)} 사용 중이고, ${category} 예정을 더해도 ${krw(performance.remainingAfter)} 부족합니다.`
    : performance.noPerformanceRequired
      ? `${category} 예정 지출은 전월 조건 없이 바로 혜택 계산이 가능해요.`
      : extraBenefit > 0
      ? `${category} 예정 지출은 ${currentCard.name}보다 약 ${krw(extraBenefit)} 더 유리해요.`
      : `${category} 예정 지출은 실적 조건과 혜택을 함께 보면 지금 카드가 잘 맞아요.`

  return {
    transaction: tx,
    merchant,
    category,
    amount,
    currentCard,
    recommendedCard: bestScore.card,
    expectedBenefit: bestScore.benefit,
    potentialBenefit: bestScore.grossBenefit,
    extraBenefit,
    rateLabel: formatBenefitRate(bestScore.rate),
    isBlocked,
    performanceNote,
    performanceTone,
    headline,
    routeTargetLabel,
    message,
  }
}

function benefitTags(card) {
  const candidates = card.benefits?.length ? card.benefits : [card.benefitSummary || card.titleDescription]
  return candidates
    .map((benefit) => String(benefit || '').replace(/\s+/g, ' ').trim())
    .filter(Boolean)
    .slice(0, 2)
}

function candidateCardId(card) {
  return String(card.id || card.cardAdId || card.card_ad_id)
}

function isOwnedCandidate(card) {
  const id = candidateCardId(card)
  return cards.value.some((ownedCard) => String(ownedCard.id) === id)
}

async function loadWalletData() {
  const [transactionResult, cardResult] = await Promise.allSettled([fetchTransactions(), fetchOwnedCards()])
  const apiTransactions = transactionResult.status === 'fulfilled' ? transactionResult.value : transactions.value
  const apiCards = cardResult.status === 'fulfilled' ? cardResult.value : cards.value

  if (transactionResult.status === 'rejected') {
    console.warn('거래내역 API를 불러오지 못해 기존 거래 목록을 유지합니다.', transactionResult.reason)
  }
  if (cardResult.status === 'rejected') {
    console.warn('보유 카드 API를 불러오지 못해 기존 카드 목록을 유지합니다.', cardResult.reason)
  }

  transactions.value = apiTransactions
  cards.value = apiCards.map((card, index) => normalizeCard(card, index, apiTransactions))
  activeCardIndex.value = Math.min(activeCardIndex.value, Math.max(cards.value.length - 1, 0))
  await nextTick()
}

async function loadCandidateCards() {
  isLoadingCandidateCards.value = true
  cardManageError.value = ''
  try {
    candidateCards.value = await fetchCards({
      search: cardSearch.value,
      active: 1,
      limit: 24,
    })
  } catch (error) {
    candidateCards.value = []
    cardManageError.value = '카드 목록을 불러오지 못했습니다.'
  } finally {
    isLoadingCandidateCards.value = false
  }
}

function scheduleCandidateSearch() {
  window.clearTimeout(cardSearchTimer)
  cardSearchTimer = window.setTimeout(loadCandidateCards, 260)
}

function toggleCardManageMenu() {
  isCardManageMenuOpen.value = !isCardManageMenuOpen.value
}

async function openCardPicker() {
  isCardManageMenuOpen.value = false
  isCardPickerOpen.value = true
  cardManageMessage.value = ''
  cardManageError.value = ''
  await loadCandidateCards()
}

async function openCardPickerFromMenu() {
  await openCardPicker()
}

function closeCardPicker() {
  isCardPickerOpen.value = false
  window.clearTimeout(cardSearchTimer)
}

async function handleAddCandidate(candidate) {
  const id = candidateCardId(candidate)
  if (!id || isOwnedCandidate(candidate) || isAddingCardId.value) return

  isAddingCardId.value = id
  cardManageError.value = ''
  try {
    await addOwnedCard(id)
    cardManageMessage.value = '보유 카드에 추가했습니다.'
    await loadWalletData()
    await loadCandidateCards()
    const addedIndex = cards.value.findIndex((card) => String(card.id) === id)
    if (addedIndex >= 0) focusCard(addedIndex)
  } catch (error) {
    cardManageError.value = '카드를 추가하지 못했습니다.'
  } finally {
    isAddingCardId.value = ''
  }
}

async function handleDeleteActiveCard() {
  if (!activeCard.value || isDeletingCard.value) return
  isCardManageMenuOpen.value = false
  const ok = window.confirm(`${activeCard.value.name} 카드를 보유 목록에서 삭제할까요?`)
  if (!ok) return

  isDeletingCard.value = true
  cardManageError.value = ''
  try {
    await deleteOwnedCard(activeCard.value.id)
    cardManageMessage.value = '보유 카드에서 삭제했습니다.'
    activeCardIndex.value = Math.max(activeCardIndex.value - 1, 0)
    await loadWalletData()
  } catch (error) {
    cardManageError.value = '카드를 삭제하지 못했습니다.'
  } finally {
    isDeletingCard.value = false
  }
}

async function deleteActiveCardFromMenu() {
  await handleDeleteActiveCard()
}

onMounted(async () => {
  try {
    await loadWalletData()
  } catch (error) {
    console.warn('대시보드 API를 불러오지 못해 기본 데이터를 사용합니다.', error)
  }
})
</script>

<style scoped>
.dashboard-header {
  position: relative;
  flex-shrink: 0;
  overflow: visible;
  border: 0;
  border-radius: 0;
  padding: clamp(18px, 5vw, 24px) clamp(16px, 4.8vw, 20px) clamp(8px, 2.6vw, 11px);
  color: #17202b;
  background: transparent !important;
  box-shadow: none;
  isolation: isolate;
}

:global(.app-backdrop .phone-shell .dashboard-header) {
  border: 0 !important;
  border-radius: 0 !important;
  padding-bottom: clamp(8px, 2.6vw, 11px) !important;
  background: transparent !important;
  box-shadow: none !important;
  color: #17202b !important;
}

:global(.app-backdrop .phone-shell .dashboard-header :is(h1, h2, h3, strong, b)) {
  color: #17202b !important;
}

:global(.app-backdrop .phone-shell .dashboard-header :is(p, span, small)) {
  color: #6f7d8c !important;
}

:global(.app-backdrop .phone-shell .dashboard-header .brand-lockup) {
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  backdrop-filter: none !important;
}

.dashboard-header::before,
.dashboard-header::after {
  position: absolute;
  z-index: 0;
  display: block;
  content: '';
  pointer-events: none;
}

.dashboard-header::before {
  display: none;
}

.dashboard-header::after {
  display: none;
}

.header-top {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.brand-lockup {
  display: flex;
  min-width: 0;
  align-items: center;
  flex: 1;
  border: 0 !important;
  background: transparent !important;
  color: inherit !important;
  box-shadow: none !important;
  text-decoration: none;
  backdrop-filter: none !important;
}

.brand-copy {
  display: grid;
  min-width: 0;
  gap: 2px;
}

.brand-logo-shell {
  display: inline-flex;
  width: clamp(116px, 32vw, 142px);
  height: 39px;
  align-items: center;
  justify-content: flex-start;
  border: 0;
  border-radius: 0;
  padding: 0;
  background: transparent;
  box-shadow: none;
  backdrop-filter: none;
}

.brand-wordmark {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: left center;
}

.header-actions {
  display: flex;
  flex-shrink: 0;
  gap: 8px;
  border: 0;
  border-radius: 0;
  padding: 0;
  background: transparent;
  box-shadow: none;
  backdrop-filter: none;
}

.header-actions .icon-button {
  width: 38px;
  height: 38px;
  border-radius: 50% !important;
  border: 0 !important;
  background: rgba(255, 255, 255, 0.84) !important;
  color: #213a56 !important;
  box-shadow: 0 5px 12px rgba(36, 54, 79, 0.08) !important;
  backdrop-filter: blur(10px) saturate(1.05);
  transition: transform 160ms ease, background-color 160ms ease, box-shadow 160ms ease;
}

.header-actions .icon-button:hover {
  background: #fff !important;
  box-shadow: 0 10px 22px rgba(36, 54, 79, 0.13) !important;
  transform: translateY(-1px);
}

.header-actions .icon-button:active {
  transform: translateY(0) scale(0.96);
}

:global(.app-backdrop .phone-shell .dashboard-header .header-actions .icon-button) {
  border-radius: 50% !important;
  border: 0 !important;
  background: rgba(255, 255, 255, 0.84) !important;
  color: #213a56 !important;
  box-shadow: 0 5px 12px rgba(36, 54, 79, 0.08) !important;
  backdrop-filter: blur(10px) saturate(1.05);
}

.month-summary {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: 14px;
  border: 0;
  border-radius: 0;
  margin: 16px 0 0;
  padding: 2px 2px 0;
  background: transparent;
  box-shadow: none;
  backdrop-filter: none;
}

.greet {
  position: relative;
  display: flex;
  min-width: 0;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
  min-height: 43px;
  overflow: visible;
  border: 0;
  border-radius: 0;
  padding: 0;
  background: transparent;
  box-shadow: none;
}

.greet::before {
  position: absolute;
  top: 3px;
  left: 0;
  width: 3px;
  height: 34px;
  border-radius: 50%;
  background: linear-gradient(180deg, #0f5fae, #008c95);
  box-shadow: none;
  content: '';
}

.greet-copy {
  padding-left: 11px;
}

.greet-copy span {
  display: block;
  color: #17202b !important;
  font-size: 12.5px;
  font-weight: 900;
  line-height: 1.24;
}

.greet-copy strong {
  display: block;
  margin-top: 4px;
  color: #8a96a3 !important;
  font-size: 10.5px;
  font-weight: 800;
  line-height: 1.25;
}

.spend-figure {
  display: flex;
  min-height: 43px;
  flex-direction: column;
  justify-content: center;
  border: 0;
  border-radius: 0;
  padding: 0;
  background: transparent;
  box-shadow: none;
  text-align: right;
}

.spend-figure span {
  display: block;
  color: #7a8592 !important;
  font-size: 10.5px;
  font-weight: 850;
}

.spend-figure strong {
  display: block;
  margin-top: 3px;
  color: #17202b !important;
  font-size: clamp(20px, 5.3vw, 23px);
  font-weight: 950;
  letter-spacing: 0;
  white-space: nowrap;
}

:global(.app-backdrop .phone-shell .dashboard-header .spend-figure span) {
  color: #7a8592 !important;
}

:global(.app-backdrop .phone-shell .dashboard-header .spend-figure strong) {
  color: #17202b !important;
}

:global(.app-backdrop .phone-shell .dashboard-header .greet-copy span) {
  color: #24364f !important;
}

:global(.app-backdrop .phone-shell .dashboard-header .greet-copy strong) {
  color: #17202b !important;
}

.dashboard-body {
  padding: 14px clamp(14px, 4.7vw, 20px) 120px;
  background: #f3f6f8;
}

.card-carousel {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  isolation: isolate;
}

.card-carousel::before {
  display: none;
  content: '';
}

.card-carousel::after {
  position: absolute;
  top: clamp(88px, 28vw, 112px);
  left: 50%;
  z-index: 3;
  width: min(160px, 42vw);
  height: 1px;
  border-radius: 999px;
  background: linear-gradient(90deg, transparent, rgba(15, 95, 174, 0.28), rgba(0, 140, 149, 0.24), transparent);
  content: '';
  opacity: 0;
  pointer-events: none;
  transform: translateX(-50%);
}

.card-carousel.is-gliding::after {
  animation: carousel-light-sweep 680ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.card-carousel.is-gliding.glide-prev::after {
  animation-name: carousel-light-sweep-reverse;
}

.card-stage {
  --card-w: clamp(154px, 43.5vw, 174px);
  --card-h: clamp(244px, 69vw, 276px);
  position: relative;
  display: flex;
  width: 100%;
  height: var(--card-h);
  align-items: center;
  justify-content: center;
  margin-top: 8px;
  touch-action: pan-y;
  user-select: none;
}

.slide-card {
  position: absolute;
  top: 0;
  left: 50%;
  width: var(--card-w);
  height: var(--card-h);
  border: 0;
  padding: 0;
  background: transparent;
  cursor: pointer;
  transform-origin: center center;
  transition: transform 480ms cubic-bezier(0.2, 0.85, 0.25, 1), opacity 400ms ease;
  will-change: transform, opacity;
}

.slide-card::before {
  content: '';
  position: absolute;
  inset: -14% -10% -8%;
  z-index: -1;
  background: radial-gradient(58% 48% at 50% 44%, color-mix(in srgb, var(--accent, #2c4e72) 30%, transparent), transparent 72%);
  filter: blur(16px);
  opacity: 0;
  transition: opacity 400ms ease;
  pointer-events: none;
}

.slide-card.is-active::before {
  opacity: 0.7;
}

.fan-card-media.slide-add-media {
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed rgba(44, 78, 114, 0.34);
  background: rgba(255, 255, 255, 0.46);
  color: #2c4e72;
  box-shadow: none;
}

.add-card-prompt {
  display: flex;
  width: 100%;
  min-height: 250px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  text-align: center;
}

.add-card-prompt strong {
  color: #1c3149;
  font-size: 18px;
  font-weight: 900;
}

.add-card-prompt p {
  margin: 3px 0 0;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 700;
}

.fan-card-media {
  position: relative;
  display: block;
  width: var(--card-w);
  height: var(--card-h);
  overflow: hidden;
  border-radius: clamp(13px, 3.6vw, 17px);
  background: transparent;
  box-shadow: 0 18px 32px rgba(36, 54, 79, 0.22);
}

.fan-card-image {
  position: absolute;
  inset: 0;
  display: block;
  width: 100%;
  height: 100%;
  opacity: 1;
  transition: opacity 240ms ease;
}

.fan-card-image.is-landscape {
  inset: auto;
  top: 50%;
  left: 50%;
  width: var(--card-h);
  height: var(--card-w);
  transform: translate(-50%, -50%) rotate(90deg);
  transform-origin: center;
}

.fan-card-image img {
  position: absolute;
  inset: 0;
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.fan-card-image.is-ready {
  opacity: 1;
}


.card-stack {
  display: flex;
  gap: 14px;
  overflow-x: auto;
  padding-bottom: 2px;
  perspective: 1100px;
  scroll-behavior: smooth;
  scroll-snap-type: x mandatory;
  scroll-snap-stop: always;
  overscroll-behavior-x: contain;
  scrollbar-width: none;
}

.card-stack::-webkit-scrollbar {
  display: none;
}

.card-carousel-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 18px;
  margin-top: -2px;
}

.carousel-edge-button {
  position: absolute;
  top: clamp(92px, 29vw, 118px);
  z-index: 4;
  display: inline-flex;
  width: 40px;
  height: 40px;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: rgba(36, 54, 79, 0.58);
  filter: drop-shadow(0 5px 8px rgba(255, 255, 255, 0.72)) drop-shadow(0 8px 14px rgba(36, 54, 79, 0.1));
  transition: transform 160ms ease, color 160ms ease, opacity 160ms ease, filter 160ms ease;
}

.carousel-edge-button svg {
  width: 20px;
  height: 20px;
  stroke-width: 2.35;
}

.carousel-edge-button:hover {
  color: rgba(36, 54, 79, 0.86);
  filter: drop-shadow(0 5px 8px rgba(255, 255, 255, 0.82)) drop-shadow(0 10px 18px rgba(36, 54, 79, 0.14));
}

.carousel-edge-button:active {
  transform: scale(0.9);
}

.card-carousel.is-gliding .carousel-edge-button {
  opacity: 0.72;
  pointer-events: none;
}

.card-carousel.is-gliding.glide-next .carousel-edge-right,
.card-carousel.is-gliding.glide-prev .carousel-edge-left {
  transform: translateX(2px) scale(0.96);
}

.card-carousel.is-gliding.glide-prev .carousel-edge-left {
  transform: translateX(-2px) scale(0.96);
}

.carousel-edge-left {
  left: max(6px, calc(50% - 182px));
}

.carousel-edge-right {
  right: max(6px, calc(50% - 182px));
}

.card-dots {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
}

.card-dots button {
  display: inline-flex;
  width: 40px;
  height: 40px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: transparent;
}

.card-dots button::before {
  display: block;
  width: 7px;
  height: 7px;
  border-radius: inherit;
  background: #d2d2d7;
  content: '';
  transition: width 160ms ease, background-color 160ms ease;
}

.card-dots button.active::before {
  width: 18px;
  background: #20242a;
}

.card-dots button:disabled {
  cursor: default;
}

.card-manage-toolbar {
  position: absolute;
  top: clamp(6px, 2.8vw, 12px);
  right: clamp(6px, 3vw, 14px);
  z-index: 8;
  display: flex;
  justify-content: center;
  margin: 0;
}

.wallet-icon-button {
  display: inline-flex;
  width: 40px;
  height: 40px;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 50%;
  padding: 0;
  background: transparent;
  color: rgba(36, 54, 79, 0.72);
  box-shadow: none;
  backdrop-filter: none;
  transition: transform 160ms ease, color 160ms ease, opacity 160ms ease;
}

.wallet-icon-button svg {
  width: 18px;
  height: 18px;
  stroke-width: 2.45;
}

.wallet-icon-button:active {
  transform: scale(0.96);
}

.wallet-icon-button:hover {
  color: #0f5fae;
}

.wallet-icon-button:disabled {
  opacity: 0.45;
}

.card-manage-menu {
  position: absolute;
  top: 38px;
  right: 0;
  display: grid;
  min-width: 136px;
  gap: 2px;
  border: 1px solid rgba(36, 54, 79, 0.11);
  border-radius: 16px;
  padding: 6px;
  background: rgba(248, 251, 253, 0.82);
  box-shadow: 0 18px 36px rgba(36, 54, 79, 0.13);
  backdrop-filter: blur(20px) saturate(1.08);
}

.card-manage-menu button {
  display: grid;
  min-height: 38px;
  grid-template-columns: 18px minmax(0, 1fr);
  align-items: center;
  gap: 7px;
  border: 0;
  border-radius: 12px;
  padding: 0 9px;
  background: transparent;
  color: #24364f;
  font-size: 12px;
  font-weight: 850;
  text-align: left;
  transition: background-color 160ms ease, color 160ms ease, transform 160ms ease;
}

.card-manage-menu button:hover:not(:disabled) {
  background: rgba(36, 54, 79, 0.07);
  color: #0f5fae;
}

.card-manage-menu button:active:not(:disabled) {
  transform: scale(0.98);
}

.card-manage-menu button.danger {
  color: #b3261e;
}

.card-manage-menu button.danger:hover:not(:disabled) {
  background: rgba(179, 38, 30, 0.07);
  color: #d92d20;
}

.card-manage-menu button:disabled {
  color: rgba(36, 54, 79, 0.34);
}

.card-manage-menu svg {
  justify-self: center;
  stroke-width: 2.35;
}

.card-manage-note {
  margin: 8px 0 0;
  color: #0f5fae;
  font-size: 11px;
  font-weight: 800;
  text-align: center;
}

.card-manage-note.error {
  color: #d92d20;
}

.pay-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 11px;
  flex: 0 0 100%;
  min-width: 100%;
  max-width: 100%;
  min-height: clamp(206px, 57vw, 236px);
  overflow: visible;
  scroll-snap-align: start;
  border: 0;
  border-radius: 0;
  padding: 10px 8px 0;
  background: transparent;
  color: #20242a;
  box-shadow: none;
  cursor: pointer;
  transition: opacity 260ms ease, transform 260ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.card-stack.is-gliding .pay-card {
  pointer-events: none;
}

.card-carousel.is-gliding .pay-card.is-active .card-art::after {
  animation: card-shadow-swipe 740ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.card-tone-blue {
  --accent: #0f5fae;
  --accent-soft: #e8f1fb;
  --accent-border: #bfd3ee;
}

.card-tone-purple {
  --accent: #20242a;
  --accent-soft: #e7edf4;
  --accent-border: #cfd9e5;
}

.card-tone-teal {
  --accent: #008c95;
  --accent-soft: #e2f5f5;
  --accent-border: #b8e2e0;
}

.card-art {
  position: relative;
  display: flex;
  width: 100%;
  height: clamp(184px, 52vw, 214px);
  align-items: center;
  justify-content: center;
  perspective: 900px;
  transform-style: preserve-3d;
  transform-origin: center center;
  will-change: transform, opacity, filter;
}

.side-card-preview {
  position: absolute;
  top: 48%;
  z-index: 0;
  display: flex;
  width: clamp(62px, 20vw, 88px);
  height: clamp(112px, 34vw, 148px);
  align-items: center;
  justify-content: center;
  border: 0;
  padding: 0;
  background: transparent;
  cursor: pointer;
  filter: saturate(0.82);
  opacity: 0.24;
  transition: opacity 180ms ease, transform 180ms ease, filter 180ms ease;
}

.side-card-preview-left {
  left: max(4px, calc(50% - 164px));
  transform: translateY(-50%) rotate(-4deg) scale(0.9);
}

.side-card-preview-right {
  right: max(4px, calc(50% - 164px));
  transform: translateY(-50%) rotate(4deg) scale(0.9);
}

.side-card-preview:hover {
  filter: saturate(0.9);
  opacity: 0.36;
}

.side-card-preview-left:hover {
  transform: translateY(-50%) translateX(-2px) rotate(-4deg) scale(0.92);
}

.side-card-preview-right:hover {
  transform: translateY(-50%) translateX(2px) rotate(4deg) scale(0.92);
}

.card-carousel.is-gliding .side-card-preview {
  filter: saturate(0.92);
}

.card-carousel.is-gliding.glide-next .side-card-preview-right {
  animation: side-card-call-next 680ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.card-carousel.is-gliding.glide-prev .side-card-preview-left {
  animation: side-card-call-prev 680ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.side-card-preview img {
  display: block;
  width: clamp(58px, 18vw, 82px);
  height: auto;
  max-height: clamp(104px, 32vw, 140px);
  object-fit: contain;
  filter: drop-shadow(0 18px 22px rgba(36, 54, 79, 0.12));
}

.side-card-preview img.is-landscape {
  width: clamp(84px, 26vw, 116px);
  max-height: none;
  transform: rotate(90deg);
}

.card-art::after {
  position: absolute;
  left: 50%;
  bottom: 15px;
  width: 176px;
  height: 20px;
  border-radius: 999px;
  background: rgba(36, 54, 79, 0.18);
  content: '';
  filter: blur(20px);
  transform: translateX(-50%);
}

.card-art img {
  position: relative;
  z-index: 1;
  display: block;
  width: clamp(120px, 35vw, 144px);
  height: auto;
  max-height: clamp(176px, 50vw, 208px);
  object-fit: contain;
  opacity: 0;
  --card-ready-transform: translateY(0);
  backface-visibility: hidden;
  transform-origin: center;
  transform-style: preserve-3d;
  transform: var(--card-ready-transform);
  filter: drop-shadow(0 26px 32px rgba(36, 54, 79, 0.19));
  transition: opacity 180ms ease, transform 260ms cubic-bezier(0.2, 0.8, 0.2, 1), filter 180ms ease;
}

.card-art img.is-ready {
  opacity: 1;
}

.card-art img.is-portrait {
  --card-ready-transform: translateY(-4px);
  transform: var(--card-ready-transform);
}

.card-art img.is-landscape {
  width: clamp(160px, 48vw, 190px);
  max-height: none;
  --card-ready-transform: translateY(-4px) rotate(90deg);
  transform: var(--card-ready-transform);
}

.card-carousel.is-gliding.glide-next .pay-card.is-active .card-art {
  animation: card-rotate-out-next 740ms cubic-bezier(0.2, 0.78, 0.2, 1);
}

.card-carousel.is-gliding.glide-prev .pay-card.is-active .card-art {
  animation: card-rotate-out-prev 740ms cubic-bezier(0.2, 0.78, 0.2, 1);
}

.card-carousel.is-gliding.glide-next .pay-card.is-motion-target .card-art {
  animation: card-rotate-in-next 740ms cubic-bezier(0.2, 0.78, 0.2, 1);
}

.card-carousel.is-gliding.glide-prev .pay-card.is-motion-target .card-art {
  animation: card-rotate-in-prev 740ms cubic-bezier(0.2, 0.78, 0.2, 1);
}

.card-art .side-card-preview img {
  z-index: auto;
  width: clamp(58px, 18vw, 82px);
  max-height: clamp(104px, 32vw, 140px);
  opacity: 1;
  filter: drop-shadow(0 18px 22px rgba(36, 54, 79, 0.12));
  transform: none;
}

.card-art .side-card-preview img.is-portrait {
  transform: none;
}

.card-art .side-card-preview img.is-landscape {
  width: clamp(84px, 26vw, 116px);
  max-height: none;
  transform: rotate(90deg);
}

@keyframes card-rotate-out-next {
  0% {
    opacity: 1;
    transform: translate3d(0, 0, 0) rotateY(0deg) rotateZ(0deg) scale(1);
    filter: drop-shadow(0 26px 32px rgba(36, 54, 79, 0.19));
  }
  42% {
    opacity: 0.86;
    transform: translate3d(-26px, -8px, 18px) rotateY(28deg) rotateZ(-1.5deg) scale(0.99);
    filter: drop-shadow(0 38px 42px rgba(36, 54, 79, 0.24));
  }
  72% {
    opacity: 0.58;
    transform: translate3d(-58px, 5px, -42px) rotateY(52deg) rotateZ(-2.5deg) scale(0.92);
  }
  100% {
    opacity: 0.36;
    transform: translate3d(-82px, 10px, -72px) rotateY(68deg) rotateZ(-3deg) scale(0.86);
    filter: drop-shadow(0 16px 22px rgba(36, 54, 79, 0.1)) saturate(0.88);
  }
}

@keyframes card-rotate-out-prev {
  0% {
    opacity: 1;
    transform: translate3d(0, 0, 0) rotateY(0deg) rotateZ(0deg) scale(1);
    filter: drop-shadow(0 26px 32px rgba(36, 54, 79, 0.19));
  }
  42% {
    opacity: 0.86;
    transform: translate3d(26px, -8px, 18px) rotateY(-28deg) rotateZ(1.5deg) scale(0.99);
    filter: drop-shadow(0 38px 42px rgba(36, 54, 79, 0.24));
  }
  72% {
    opacity: 0.58;
    transform: translate3d(58px, 5px, -42px) rotateY(-52deg) rotateZ(2.5deg) scale(0.92);
  }
  100% {
    opacity: 0.36;
    transform: translate3d(82px, 10px, -72px) rotateY(-68deg) rotateZ(3deg) scale(0.86);
    filter: drop-shadow(0 16px 22px rgba(36, 54, 79, 0.1)) saturate(0.88);
  }
}

@keyframes card-rotate-in-next {
  0% {
    opacity: 0.32;
    transform: translate3d(82px, 10px, -72px) rotateY(-68deg) rotateZ(3deg) scale(0.86);
    filter: drop-shadow(0 12px 18px rgba(36, 54, 79, 0.08)) saturate(0.78) blur(0.3px);
  }
  42% {
    opacity: 0.9;
    transform: translate3d(24px, -8px, 18px) rotateY(-26deg) rotateZ(1.2deg) scale(0.99);
    filter: drop-shadow(0 40px 44px rgba(36, 54, 79, 0.25)) saturate(1.05);
  }
  72% {
    opacity: 1;
    transform: translate3d(-5px, -3px, 8px) rotateY(5deg) rotateZ(-0.5deg) scale(1.015);
  }
  100% {
    opacity: 1;
    transform: translate3d(0, 0, 0) rotateY(0deg) rotateZ(0deg) scale(1);
    filter: drop-shadow(0 26px 32px rgba(36, 54, 79, 0.19));
  }
}

@keyframes card-rotate-in-prev {
  0% {
    opacity: 0.32;
    transform: translate3d(-82px, 10px, -72px) rotateY(68deg) rotateZ(-3deg) scale(0.86);
    filter: drop-shadow(0 12px 18px rgba(36, 54, 79, 0.08)) saturate(0.78) blur(0.3px);
  }
  42% {
    opacity: 0.9;
    transform: translate3d(-24px, -8px, 18px) rotateY(26deg) rotateZ(-1.2deg) scale(0.99);
    filter: drop-shadow(0 40px 44px rgba(36, 54, 79, 0.25)) saturate(1.05);
  }
  72% {
    opacity: 1;
    transform: translate3d(5px, -3px, 8px) rotateY(-5deg) rotateZ(0.5deg) scale(1.015);
  }
  100% {
    opacity: 1;
    transform: translate3d(0, 0, 0) rotateY(0deg) rotateZ(0deg) scale(1);
    filter: drop-shadow(0 26px 32px rgba(36, 54, 79, 0.19));
  }
}

@keyframes card-shadow-swipe {
  0%,
  100% {
    opacity: 1;
    transform: translateX(-50%) scaleX(1);
  }
  42% {
    opacity: 0.72;
    transform: translateX(-50%) scaleX(1.18);
  }
}

@keyframes side-card-call-next {
  0%,
  100% {
    opacity: 0.24;
    transform: translateY(-50%) rotate(4deg) scale(0.9);
  }
  46% {
    opacity: 0.44;
    transform: translateY(-50%) translateX(-8px) rotate(2deg) scale(0.99);
  }
}

@keyframes side-card-call-prev {
  0%,
  100% {
    opacity: 0.24;
    transform: translateY(-50%) rotate(-4deg) scale(0.9);
  }
  46% {
    opacity: 0.44;
    transform: translateY(-50%) translateX(8px) rotate(-2deg) scale(0.99);
  }
}

@keyframes carousel-light-sweep {
  0% {
    opacity: 0;
    transform: translateX(-76%) scaleX(0.5);
  }
  34% {
    opacity: 1;
  }
  100% {
    opacity: 0;
    transform: translateX(-24%) scaleX(1);
  }
}

@keyframes carousel-light-sweep-reverse {
  0% {
    opacity: 0;
    transform: translateX(-24%) scaleX(0.5);
  }
  34% {
    opacity: 1;
  }
  100% {
    opacity: 0;
    transform: translateX(-76%) scaleX(1);
  }
}

.card-detail-stage {
  position: relative;
  display: flex;
  width: 100%;
  min-height: 250px;
  justify-content: center;
  margin-top: -4px;
  perspective: 1100px;
}

.card-detail-panel {
  position: relative;
  display: flex;
  width: 100%;
  max-width: 320px;
  min-height: 250px;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin: 0 auto;
  will-change: opacity, transform, filter;
  transition: opacity 260ms ease, transform 260ms ease, filter 260ms ease;
  transform-origin: center 18%;
  transform-style: preserve-3d;
}

.card-detail-spin-enter-active {
  transition: opacity 240ms ease, transform 300ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.card-detail-spin-leave-active {
  position: absolute;
  inset: 0;
  margin-inline: auto;
  pointer-events: none;
  transition: opacity 150ms ease, transform 220ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.card-detail-spin-enter-from,
.card-carousel.glide-prev .card-detail-spin-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.card-detail-spin-enter-to,
.card-detail-spin-leave-from {
  opacity: 1;
  transform: translateX(0);
}

.card-carousel.glide-next .card-detail-spin-leave-to,
.card-carousel.glide-prev .card-detail-spin-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.card-info {
  width: 100%;
  max-width: 320px;
  min-width: 0;
  text-align: center;
}

.card-bottom {
  display: flex;
  width: 100%;
  max-width: 316px;
  min-width: 0;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

.issuer-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.issuer-row span {
  color: var(--accent);
  font-size: 12px;
  font-weight: 800;
}

.issuer-row em {
  flex-shrink: 0;
  border-radius: 999px;
  padding: 4px 8px;
  background: rgba(248, 251, 253, 0.58);
  color: var(--accent);
  font-size: 10px;
  font-style: normal;
  font-weight: 900;
  box-shadow: inset 0 0 0 1px var(--accent-border), inset 0 1px 0 rgba(255, 255, 255, 0.62);
  backdrop-filter: blur(12px) saturate(1.05);
}

.card-info strong {
  display: block;
  margin: 6px 0 5px;
  color: #20242a;
  font-size: clamp(21px, 6vw, 25px);
  font-weight: 900;
  line-height: 1.12;
  word-break: keep-all;
  overflow-wrap: anywhere;
}

.benefit-summary {
  min-height: 20px;
  margin: 0;
  color: #6e6e73;
  font-size: clamp(13px, 3.8vw, 14px);
  font-weight: 800;
  line-height: 1.5;
  word-break: keep-all;
  overflow-wrap: anywhere;
}

.spend-progress {
  border-block: 1px solid rgba(32, 36, 42, 0.1);
  border-radius: 0;
  padding: 11px 0 10px;
  background: transparent;
  box-shadow: none;
  backdrop-filter: none;
}

.progress-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 9px;
}

.progress-head span {
  color: #5f6b77;
  font-size: 12px;
  font-weight: 700;
}

.progress-head b {
  color: #20242a;
  font-size: 18px;
  font-weight: 900;
}

.spend-progress.is-no-performance .progress-head {
  margin-bottom: 8px;
}

.spend-progress.is-no-performance .progress-head b {
  font-size: 15px;
  white-space: nowrap;
}

.progress-track {
  height: 4px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(36, 54, 79, 0.11);
}

.progress-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #2c4e72, #1c3149);
}

.progress-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0;
  margin-top: 11px;
}

.progress-meta.single {
  grid-template-columns: 1fr;
}

.progress-meta span {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 3px;
}

.progress-meta small {
  color: #7a8795;
  font-size: 10px;
  font-weight: 750;
  line-height: 1.2;
}

.progress-meta b {
  min-width: 0;
  color: #20242a;
  font-size: 12px;
  font-weight: 900;
  line-height: 1.25;
  overflow-wrap: anywhere;
}

.progress-meta span:last-child {
  align-items: flex-end;
  text-align: right;
}

.progress-meta.single span {
  align-items: center;
  text-align: center;
}

.progress-meta.no-requirement {
  margin-top: 0;
  padding-top: 8px;
  border-top: 1px solid rgba(32, 36, 42, 0.08);
}

.benefit-chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0;
  width: fit-content;
  max-width: 100%;
  margin: 0 auto;
  overflow: visible;
  border: 0;
  border-radius: 999px;
  padding: 0;
  background: transparent;
  box-shadow: none;
  backdrop-filter: none;
}

.benefit-chips span {
  position: relative;
  border: 0;
  border-radius: 0;
  padding: 0 10px;
  background: transparent;
  color: #4a5663;
  font-size: 11px;
  font-weight: 750;
  line-height: 1.2;
  word-break: keep-all;
}

.benefit-chips span + span {
  border-left: 0;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
  margin-top: 14px;
  padding: 12px 0;
  border-block: 1px solid rgba(32, 36, 42, 0.085);
}

.dashboard-body .quick-grid .quick-action + .quick-action {
  border-left: 1px solid rgba(32, 36, 42, 0.14) !important;
}

.quick-action {
  display: flex;
  min-height: 64px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #3f4b58;
  font-size: 11px;
  font-weight: 850;
  line-height: 1.2;
  text-decoration: none;
  word-break: keep-all;
}

.dashboard-body .quick-grid .quick-action {
  border-radius: 0 !important;
  border-top: 0 !important;
  border-right: 0 !important;
  border-bottom: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  backdrop-filter: none !important;
}

.dashboard-body .quick-grid .quick-action:hover {
  background: transparent !important;
  box-shadow: none !important;
  backdrop-filter: none !important;
}

.quick-action svg {
  width: 20px;
  height: 20px;
  stroke-width: 2.25;
}

.payment-advice-section {
  margin-top: 18px;
}

.payment-advice-card {
  display: block;
  overflow: hidden;
  border: 1px solid rgba(15, 95, 174, 0.12);
  border-radius: 18px;
  padding: 14px;
  background:
    radial-gradient(circle at 92% 0%, rgba(0, 140, 149, 0.1), transparent 34%),
    linear-gradient(145deg, #ffffff 0%, #f8fbfe 100%);
  color: inherit;
  text-decoration: none;
  box-shadow: 0 10px 24px rgba(36, 54, 79, 0.08);
}

.advice-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.advice-topline span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: #0f5fae;
  font-size: 11px;
  font-weight: 900;
}

.advice-topline b {
  flex-shrink: 0;
  border-radius: 999px;
  padding: 5px 8px;
  background: rgba(0, 140, 149, 0.1);
  color: #008c95;
  font-size: 11px;
  font-weight: 950;
}

.advice-main {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 48px;
  align-items: center;
  gap: 12px;
}

.advice-copy {
  min-width: 0;
}

.advice-copy span {
  display: block;
  color: #7a8795;
  font-size: 11px;
  font-weight: 800;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.advice-copy strong {
  display: block;
  margin-top: 4px;
  color: #17202b;
  font-size: 15px;
  font-weight: 950;
  line-height: 1.25;
  word-break: keep-all;
}

.advice-copy p {
  margin: 6px 0 0;
  color: #536170;
  font-size: 12px;
  font-weight: 750;
  line-height: 1.45;
  word-break: keep-all;
}

.advice-performance {
  display: inline-flex;
  width: fit-content;
  margin-top: 8px;
  border-radius: 999px;
  padding: 5px 8px;
  background: rgba(15, 95, 174, 0.08);
  color: #0f5fae;
  font-size: 10.5px;
  font-weight: 900;
  line-height: 1;
}

.advice-performance.is-waiting {
  background: rgba(249, 115, 22, 0.1);
  color: #c2410c;
}

.advice-performance.is-ready {
  background: rgba(0, 140, 149, 0.1);
  color: #007780;
}

.advice-card-image {
  position: relative;
  display: block;
  width: 40px;
  height: 56px;
  justify-self: end;
  overflow: hidden;
  border-radius: 7px;
  background: #e8edf2;
  box-shadow: 0 8px 18px rgba(36, 54, 79, 0.16);
}

.advice-card-image img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.advice-card-image img.is-landscape {
  inset: auto;
  top: 50%;
  left: 50%;
  width: 56px;
  height: 40px;
  transform: translate(-50%, -50%) rotate(90deg);
}

.advice-route {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 24px minmax(0, 1fr);
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  border-top: 1px solid rgba(32, 36, 42, 0.08);
  padding-top: 11px;
}

.advice-route span,
.advice-route strong {
  min-width: 0;
  overflow: hidden;
  color: #6f7d8c;
  font-size: 11px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.advice-route i {
  display: block;
  height: 1px;
  border-radius: 999px;
  background: linear-gradient(90deg, transparent, rgba(15, 95, 174, 0.48), transparent);
}

.advice-route strong {
  color: #24364f;
  text-align: right;
}

.section-block {
  margin-top: 20px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.section-head h2 {
  margin: 0;
  color: #20242a;
  font-size: 15px;
  font-weight: 900;
}

.section-head a {
  color: #0f5fae;
  font-size: 12px;
  font-weight: 800;
  text-decoration: none;
}

.tx-card {
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  backdrop-filter: none;
}

.tx-card button {
  display: grid;
  width: 100%;
  grid-template-columns: 42px minmax(0, 1fr) 24px 92px;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(32, 36, 42, 0.08);
  padding: 14px 2px;
  background: transparent;
  text-align: left;
}

.tx-card button > span:first-child {
  display: inline-flex;
  width: 42px;
  height: 42px;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  line-height: 1;
}

.tx-card button:last-child {
  border-bottom: 0;
}

.tx-card strong {
  display: block;
  color: #20242a;
  font-size: 13px;
  font-weight: 900;
}

.tx-card small {
  color: #6e6e73;
  font-size: 11px;
  font-weight: 700;
}

.tx-mini-card {
  position: relative;
  display: block;
  justify-self: center;
  width: 15px;
  height: 24px;
  overflow: hidden;
  border-radius: 3px;
  background: #e8edf2;
  box-shadow: 0 1px 3px rgba(36, 54, 79, 0.2);
}

.tx-mini-card img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.tx-mini-card img.is-landscape {
  inset: auto;
  top: 50%;
  left: 50%;
  width: 24px;
  height: 15px;
  transform: translate(-50%, -50%) rotate(90deg);
}

.tx-card b {
  color: #20242a;
  font-size: 13px;
  font-weight: 900;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.tx-card b.plus {
  color: #008c95;
}

.card-picker-backdrop {
  position: absolute;
  inset: 0;
  z-index: 20;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  background: rgba(20, 28, 38, 0.28);
  backdrop-filter: blur(10px);
}

.card-picker-sheet {
  display: flex;
  width: 100%;
  max-height: min(78dvh, 700px);
  flex-direction: column;
  border: 1px solid rgba(36, 54, 79, 0.12);
  border-radius: 28px 28px 0 0;
  padding: 18px 16px 14px;
  background: rgba(248, 251, 253, 0.84);
  box-shadow: 0 -22px 50px rgba(36, 54, 79, 0.18);
  backdrop-filter: blur(24px) saturate(1.1);
}

.card-picker-sheet header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.card-picker-sheet header span {
  color: #0f5fae;
  font-size: 11px;
  font-weight: 900;
}

.card-picker-sheet header h2 {
  margin: 3px 0 0;
  color: #20242a;
  font-size: 18px;
  font-weight: 950;
  line-height: 1.25;
}

.picker-close-button {
  display: inline-flex;
  width: 42px;
  height: 42px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  border: 1px solid rgba(36, 54, 79, 0.11);
  background: rgba(248, 251, 253, 0.56);
  color: #24364f;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.58), 0 10px 24px rgba(36, 54, 79, 0.06);
  backdrop-filter: blur(16px) saturate(1.08);
}

.card-search-form {
  display: grid;
  grid-template-columns: 22px minmax(0, 1fr);
  align-items: center;
  gap: 8px;
  min-height: 48px;
  border: 1px solid rgba(36, 54, 79, 0.11);
  border-radius: 16px;
  padding: 0 13px;
  background: rgba(248, 251, 253, 0.58);
  color: #5f6b77;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.58);
  backdrop-filter: blur(16px) saturate(1.08);
}

.card-search-form input {
  width: 100%;
  border: 0;
  outline: 0;
  background: transparent;
  color: #20242a;
  font-size: 14px;
  font-weight: 750;
}

.card-search-form input::placeholder {
  color: #8a9aad;
}

.candidate-card-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: auto;
  padding: 14px 2px 2px;
}

.candidate-empty {
  margin: 28px 0 30px;
  color: #6e6e73;
  font-size: 13px;
  font-weight: 800;
  text-align: center;
}

.candidate-card-row {
  display: grid;
  grid-template-columns: 74px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  min-height: 96px;
  border: 1px solid rgba(36, 54, 79, 0.1);
  border-radius: 20px;
  padding: 10px;
  background: rgba(248, 251, 253, 0.58);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.58), 0 12px 26px rgba(36, 54, 79, 0.055);
  backdrop-filter: blur(16px) saturate(1.08);
}

.candidate-card-image {
  display: flex;
  width: 74px;
  height: 74px;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 16px;
  background: rgba(232, 241, 251, 0.48);
  box-shadow: inset 0 0 0 1px rgba(36, 54, 79, 0.07);
}

.candidate-card-image img {
  max-width: 62px;
  max-height: 62px;
  object-fit: contain;
  filter: drop-shadow(0 10px 12px rgba(36, 54, 79, 0.12));
}

.candidate-card-copy {
  min-width: 0;
}

.candidate-card-copy span {
  color: #0f5fae;
  font-size: 11px;
  font-weight: 900;
}

.candidate-card-copy strong {
  display: block;
  margin-top: 3px;
  color: #20242a;
  font-size: 14px;
  font-weight: 950;
  line-height: 1.25;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.candidate-card-copy p {
  display: -webkit-box;
  margin: 5px 0 0;
  overflow: hidden;
  color: #6e6e73;
  font-size: 11.5px;
  font-weight: 750;
  line-height: 1.35;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.candidate-card-row > button {
  display: inline-flex;
  width: 40px;
  height: 40px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 0;
  background: transparent;
  color: #24364f;
  box-shadow: none;
  backdrop-filter: none;
  transition: transform 160ms ease, color 160ms ease, opacity 160ms ease;
}

.candidate-card-row > button:hover:not(:disabled) {
  color: #0f5fae;
}

.candidate-card-row > button:active {
  transform: scale(0.96);
}

.candidate-card-row > button:disabled {
  background: transparent;
  color: rgba(36, 54, 79, 0.42);
  box-shadow: none;
  opacity: 1;
}

@media (max-width: 380px) {
  .dashboard-header {
    border-radius: 0;
    padding-inline: 16px;
  }

  .header-top {
    gap: 10px;
  }

  .brand-logo-shell {
    width: 118px;
    height: 38px;
  }

  .header-actions {
    gap: 5px;
  }

  .header-actions .icon-button {
    width: 34px;
    height: 34px;
  }

  .month-summary {
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 10px;
  }

  .month-summary span {
    font-size: 10px;
  }

  .greet-copy span {
    font-size: 12px;
  }

  .greet-copy strong {
    max-width: 164px;
  }

  .spend-figure strong {
    font-size: 20px;
  }

  .pay-card {
    min-height: 196px;
    gap: 8px;
    padding-inline: 4px;
  }

  .benefit-chips {
    gap: 6px;
  }

  .benefit-chips span {
    border-left: 0 !important;
    padding-inline: 0;
    font-size: 10px;
  }

  .quick-grid {
    gap: 6px;
  }

  .quick-action {
    min-height: 58px;
    gap: 5px;
    font-size: 10px;
  }

  .quick-action svg {
    width: 18px;
    height: 18px;
  }

  .card-manage-toolbar {
    top: 4px;
    left: 8px;
  }

  .wallet-icon-button {
    width: 38px;
    height: 38px;
  }

  .card-manage-menu {
    top: 36px;
    min-width: 130px;
  }
}

@media (max-width: 340px) {
  .pay-card {
    min-height: 176px;
    gap: 8px;
  }

  .card-art {
    height: 160px;
  }

  .card-detail-panel {
    min-height: 244px;
  }

  .card-bottom {
    gap: 8px;
    margin-top: 3px;
  }

  .spend-progress {
    padding: 8px 0;
  }

  .progress-head {
    margin-bottom: 7px;
  }

  .progress-meta {
    margin-top: 8px;
  }

  .card-carousel-controls {
    margin-top: -2px;
  }

  .quick-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 5px;
    margin-top: 10px;
  }

  .quick-action {
    min-height: 52px;
    flex-direction: column;
    gap: 4px;
    font-size: 9.5px;
  }

  .quick-action svg {
    width: 17px;
    height: 17px;
  }

  .tx-card button {
    grid-template-columns: 28px minmax(0, 1fr) auto;
    gap: 8px;
    padding-inline: 10px;
  }
}

</style>
