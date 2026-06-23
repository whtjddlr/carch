<template>
  <section class="screen">
    <header class="dashboard-header blue-gradient">
      <div class="header-top">
        <div class="brand-lockup">
          <span class="brand-mark" aria-hidden="true">C</span>
          <div>
            <h1>Carch</h1>
            <p>카드를 읽고 소비를 설계하는 지갑</p>
          </div>
        </div>
        <div class="header-actions">
          <RouterLink class="icon-button" to="/search" aria-label="검색">
            <Search :size="18" />
          </RouterLink>
          <RouterLink class="icon-button" to="/notifications" aria-label="알림">
            <Bell :size="18" />
          </RouterLink>
          <RouterLink class="icon-button" to="/settings" aria-label="설정">
            <Settings :size="18" />
          </RouterLink>
        </div>
      </div>
    </header>

    <div class="screen-scroll scrollbar-hide dashboard-body">
      <div class="month-summary">
        <div>
          <span>이번 달 총 지출</span>
          <strong>{{ totalSpendLabel }}</strong>
        </div>
        <i />
        <div>
          <span>보유 카드</span>
          <strong>{{ cards.length }}장</strong>
        </div>
      </div>

      <div class="card-carousel" :class="[{ 'is-gliding': isCarouselGliding }, `glide-${carouselDirection}`]">
        <div
          ref="cardStackRef"
          class="card-stack"
          :class="{ 'is-gliding': isCarouselGliding }"
          @scroll.passive="syncActiveCard"
        >
          <article
            v-for="(card, index) in cards"
            :key="card.id"
            class="pay-card"
            :class="[
              `card-tone-${card.grad}`,
              { 'is-active': activeCardIndex === index, 'is-motion-target': motionTargetIndex === index },
            ]"
            @click="!isCarouselGliding && router.push(`/cards/${card.id}`)"
          >
            <div class="card-art" v-if="card.imageUrl">
              <button
                v-if="cards.length > 1 && activeCardIndex === index && previousPreviewCard?.imageUrl"
                type="button"
                class="side-card-preview side-card-preview-left"
                aria-label="이전 카드 보기"
                :disabled="isCarouselGliding"
                @click.stop="moveCard(-1)"
              >
                <img
                  :src="previousPreviewCard.imageUrl"
                  :alt="previousPreviewCard.name"
                  :class="cardImageClass(previousPreviewCard)"
                  @load="setImageOrientation(previousPreviewCard.id, $event)"
                />
              </button>
              <button
                v-if="cards.length > 1 && activeCardIndex === index && nextPreviewCard?.imageUrl"
                type="button"
                class="side-card-preview side-card-preview-right"
                aria-label="다음 카드 보기"
                :disabled="isCarouselGliding"
                @click.stop="moveCard(1)"
              >
                <img
                  :src="nextPreviewCard.imageUrl"
                  :alt="nextPreviewCard.name"
                  :class="cardImageClass(nextPreviewCard)"
                  @load="setImageOrientation(nextPreviewCard.id, $event)"
                />
              </button>
              <img
                :src="card.imageUrl"
                :alt="card.name"
                :class="cardImageClass(card)"
                @load="setImageOrientation(card.id, $event)"
              />
            </div>
          </article>
        </div>

        <button
          v-if="cards.length > 1"
          type="button"
          class="carousel-edge-button carousel-edge-left"
          aria-label="이전 카드"
          :disabled="isCarouselGliding"
          @click="moveCard(-1)"
        >
          <ChevronLeft :size="18" />
        </button>
        <button
          v-if="cards.length > 1"
          type="button"
          class="carousel-edge-button carousel-edge-right"
          aria-label="다음 카드"
          :disabled="isCarouselGliding"
          @click="moveCard(1)"
        >
          <ChevronRight :size="18" />
        </button>

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
              <div class="spend-progress">
                <div class="progress-head">
                  <span>실적 달성률</span>
                  <b>{{ spendProgress(detailCard) }}%</b>
                </div>
                <div class="progress-track">
                  <i :style="{ width: `${spendProgress(detailCard)}%` }" />
                </div>
                <div v-if="detailCard.previousMonthMinSpend" class="progress-meta">
                  <span>
                    <small>사용 금액</small>
                    <b>{{ krw(detailCard.spent) }}</b>
                  </span>
                  <span>
                    <small>남은 실적</small>
                    <b>{{ remainingSpend(detailCard) > 0 ? krw(remainingSpend(detailCard)) : '충족' }}</b>
                  </span>
                </div>
                <div v-else class="progress-meta single">
                  <span>
                    <small>실적 조건</small>
                    <b>없이 적용</b>
                  </span>
                </div>
              </div>
              <div class="benefit-chips">
                <span v-for="benefit in benefitTags(detailCard)" :key="benefit">{{ benefit }}</span>
              </div>
            </div>
          </div>
          </Transition>
        </div>

        <div v-if="cards.length > 1" class="card-carousel-controls" aria-label="보유 카드 이동">
          <div class="card-dots">
            <button
              v-for="(_, index) in cards"
              :key="index"
              type="button"
              :class="{ active: activeCardIndex === index }"
              :aria-label="`${index + 1}번째 카드 보기`"
              :disabled="isCarouselGliding"
              @click="goToCard(index)"
            />
          </div>
        </div>

        <div class="card-manage-toolbar" aria-label="보유 카드 관리">
          <button type="button" class="wallet-icon-button is-add" aria-label="카드 추가" @click="openCardPicker">
            <PlusCircle :size="16" />
          </button>
          <button
            type="button"
            class="wallet-icon-button danger"
            :aria-label="isDeletingCard ? '카드 삭제 중' : '현재 카드 삭제'"
            :disabled="!activeCard || isDeletingCard"
            @click="handleDeleteActiveCard"
          >
            <Trash2 :size="16" />
          </button>
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

      <section class="section-block">
        <div class="section-head">
          <h2>최근 거래</h2>
          <RouterLink to="/transactions">전체보기</RouterLink>
        </div>
        <article class="app-card tx-card">
          <button v-for="tx in transactions.slice(0, 5)" :key="tx.id" type="button" @click="router.push(`/transactions/${tx.id}`)">
            <span>{{ tx.icon }}</span>
            <div>
              <strong>{{ tx.merchant }}</strong>
              <small>{{ tx.cat }} · {{ tx.time }}</small>
            </div>
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
import { BarChart3, Bell, CalendarDays, Check, ChevronLeft, ChevronRight, PlusCircle, Search, Settings, Sparkles, Trash2, X } from 'lucide-vue-next'
import { cards as mockCards, krw, transactions as mockTransactions } from '@/data/mockData'
import { addOwnedCard, deleteOwnedCard, fetchCards, fetchOwnedCards, fetchTransactions, normalizeCard } from '@/services/api'

const router = useRouter()
const cards = ref(mockCards)
const transactions = ref(mockTransactions)
const cardStackRef = ref(null)
const activeCardIndex = ref(0)
const isCarouselGliding = ref(false)
const carouselDirection = ref('next')
const motionTargetIndex = ref(null)
const imageOrientations = ref({})
const isCardPickerOpen = ref(false)
const cardSearch = ref('')
const candidateCards = ref([])
const isLoadingCandidateCards = ref(false)
const cardManageMessage = ref('')
const cardManageError = ref('')
const isDeletingCard = ref(false)
const isAddingCardId = ref('')
const totalSpent = computed(() => cards.value.reduce((sum, card) => sum + card.spent, 0))
const totalSpendLabel = computed(() => krw(totalSpent.value))
const activeCard = computed(() => cards.value[activeCardIndex.value] || cards.value[0] || null)
const detailCard = computed(() => {
  if (isCarouselGliding.value && motionTargetIndex.value !== null) {
    return cards.value[motionTargetIndex.value] || activeCard.value
  }
  return activeCard.value
})
const previousPreviewCard = computed(() => {
  if (cards.value.length < 2) return null
  return cards.value[(activeCardIndex.value - 1 + cards.value.length) % cards.value.length]
})
const nextPreviewCard = computed(() => {
  if (cards.value.length < 2) return null
  return cards.value[(activeCardIndex.value + 1) % cards.value.length]
})
const quickActions = [
  { label: '결제 추가', path: '/transactions/new', icon: PlusCircle, color: '#0f5fae' },
  { label: '소비 분석', path: '/analytics/cards', icon: BarChart3, color: '#20242a' },
  { label: '카드 추천', path: '/recommendations/new', icon: Sparkles, color: '#008c95' },
  { label: '목표 지출', path: '/plans/new', icon: CalendarDays, color: '#24364f' },
]
let cardGlideTimer = null
let cardSearchTimer = null

function syncActiveCard() {
  const stack = cardStackRef.value
  if (!stack || isCarouselGliding.value) return

  const stackRect = stack.getBoundingClientRect()
  const stackCenter = stackRect.left + stackRect.width / 2
  const items = [...stack.querySelectorAll('.pay-card')]
  const closest = items.reduce(
    (best, item, index) => {
      const itemRect = item.getBoundingClientRect()
      const distance = Math.abs(itemRect.left + itemRect.width / 2 - stackCenter)
      return distance < best.distance ? { index, distance } : best
    },
    { index: activeCardIndex.value, distance: Number.POSITIVE_INFINITY },
  )
  activeCardIndex.value = closest.index
}

function goToCard(index, direction = index > activeCardIndex.value ? 'next' : 'prev') {
  const stack = cardStackRef.value
  const target = stack?.querySelectorAll('.pay-card')[index]
  if (!stack || !target || index === activeCardIndex.value || isCarouselGliding.value) return

  window.clearTimeout(cardGlideTimer)
  carouselDirection.value = direction
  motionTargetIndex.value = index
  isCarouselGliding.value = true
  stack.scrollTo({
    left: target.offsetLeft - stack.offsetLeft,
    behavior: 'smooth',
  })
  cardGlideTimer = window.setTimeout(() => {
    activeCardIndex.value = index
    isCarouselGliding.value = false
    motionTargetIndex.value = null
  }, 740)
}

function moveCard(direction) {
  if (!cards.value.length || isCarouselGliding.value) return

  const nextIndex = (activeCardIndex.value + direction + cards.value.length) % cards.value.length
  goToCard(nextIndex, direction > 0 ? 'next' : 'prev')
}

function spendProgress(card) {
  const target = Number(card.previousMonthMinSpend || 0)
  if (!target) return 100
  return Math.min(100, Math.round((Number(card.spent || 0) / target) * 100))
}

function remainingSpend(card) {
  return Math.max(Number(card.previousMonthMinSpend || 0) - Number(card.spent || 0), 0)
}

function setImageOrientation(cardId, event) {
  const image = event.target
  const orientation = image.naturalWidth > image.naturalHeight ? 'landscape' : 'portrait'
  imageOrientations.value = { ...imageOrientations.value, [cardId]: orientation }
}

function cardImageClass(card) {
  const orientation = imageOrientations.value[card.id]
  return {
    'is-ready': Boolean(orientation),
    'is-landscape': orientation === 'landscape',
    'is-portrait': orientation === 'portrait',
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
  const [apiTransactions, apiCards] = await Promise.all([fetchTransactions(), fetchOwnedCards()])
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

async function openCardPicker() {
  isCardPickerOpen.value = true
  cardManageMessage.value = ''
  cardManageError.value = ''
  await loadCandidateCards()
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
    if (addedIndex >= 0) goToCard(addedIndex)
  } catch (error) {
    cardManageError.value = '카드를 추가하지 못했습니다.'
  } finally {
    isAddingCardId.value = ''
  }
}

async function handleDeleteActiveCard() {
  if (!activeCard.value || isDeletingCard.value) return
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

onMounted(async () => {
  try {
    await loadWalletData()
  } catch (error) {
    console.warn('諛깆뿏??API瑜?遺덈윭?ㅼ? 紐삵빐 mock ?곗씠?곕? ?ъ슜?⑸땲??', error)
  }
})
</script>

<style scoped>
.dashboard-header {
  position: relative;
  flex-shrink: 0;
  overflow: visible;
  border-radius: 0;
  padding: clamp(16px, 4.7vw, 22px) clamp(16px, 4.8vw, 20px) 8px;
  color: #20242a;
  background: #f3f6f8 !important;
  isolation: isolate;
}

:global(.app-backdrop .phone-shell .dashboard-header) {
  background: #f3f6f8 !important;
  color: #20242a !important;
}

:global(.app-backdrop .phone-shell .dashboard-header :is(h1, h2, h3, strong, b)) {
  color: #20242a !important;
}

:global(.app-backdrop .phone-shell .dashboard-header :is(p, span, small)) {
  color: #6e6e73 !important;
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
  gap: 14px;
}

.brand-lockup {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10px;
}

.brand-mark {
  position: relative;
  display: inline-flex;
  width: 39px;
  height: 39px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  border-radius: 13px;
  background: #20242a;
  color: #fff !important;
  font-size: 19px;
  font-weight: 950;
  box-shadow: 0 12px 24px rgba(36, 54, 79, 0.13), inset -7px -7px 0 rgba(0, 140, 149, 0.24);
}

.brand-mark::after {
  position: absolute;
  right: 8px;
  bottom: 8px;
  width: 10px;
  height: 2px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  content: '';
}

.header-top h1 {
  margin: 0;
  color: #20242a;
  font-size: 24px;
  font-weight: 900;
  letter-spacing: 0;
}

.header-top p {
  margin: 3px 0 0;
  color: #6e6e73 !important;
  font-size: 10.5px;
  font-weight: 800;
  line-height: 1.25;
  word-break: keep-all;
}

.header-actions {
  display: flex;
  gap: 7px;
  border: 0;
  padding: 0;
  background: transparent;
  box-shadow: none;
  backdrop-filter: none;
}

.header-actions .icon-button {
  width: 42px;
  height: 42px;
  border: 1px solid rgba(36, 54, 79, 0.11) !important;
  background: rgba(248, 251, 253, 0.58) !important;
  color: #24364f !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.58), 0 10px 24px rgba(36, 54, 79, 0.06) !important;
  backdrop-filter: blur(16px) saturate(1.08);
}

:global(.app-backdrop .phone-shell .dashboard-header .header-actions .icon-button) {
  border: 1px solid rgba(36, 54, 79, 0.11) !important;
  background: rgba(248, 251, 253, 0.58) !important;
  color: #24364f !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.58), 0 10px 24px rgba(36, 54, 79, 0.06) !important;
  backdrop-filter: blur(16px) saturate(1.08);
}

.month-summary {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1fr 1px 1fr;
  gap: 16px;
  overflow: visible;
  border-block: 1px solid rgba(32, 36, 42, 0.085);
  border-inline: 0;
  border-radius: 0;
  margin: 0 0 8px;
  padding: 12px 4px;
  background: transparent;
  box-shadow: none;
  backdrop-filter: none;
}

.month-summary::before,
.month-summary::after {
  display: none;
}

.month-summary i {
  align-self: center;
  height: 30px;
  background: rgba(32, 36, 42, 0.1);
}

.month-summary span {
  display: block;
  color: #6e6e73 !important;
  font-size: 10px;
  font-weight: 800;
}

.month-summary strong {
  display: block;
  margin-top: 4px;
  color: #20242a;
  font-size: clamp(18px, 4.9vw, 21px);
  font-weight: 900;
}

.dashboard-body {
  padding: 0 clamp(14px, 4.7vw, 20px) 120px;
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
  top: clamp(2px, 1.4vw, 7px);
  right: clamp(8px, 4vw, 18px);
  z-index: 6;
  display: flex;
  justify-content: center;
  gap: 7px;
  margin: 0;
}

.wallet-icon-button {
  display: inline-flex;
  width: 40px;
  height: 40px;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(36, 54, 79, 0.12);
  border-radius: 50%;
  padding: 0;
  background: rgba(248, 251, 253, 0.56);
  color: #24364f;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.62), 0 12px 26px rgba(36, 54, 79, 0.07);
  backdrop-filter: blur(16px) saturate(1.08);
  transition: transform 160ms ease, background-color 160ms ease, color 160ms ease, box-shadow 160ms ease, opacity 160ms ease;
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
  background: rgba(248, 251, 253, 0.68);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.68), 0 14px 30px rgba(36, 54, 79, 0.085);
}

.wallet-icon-button.is-add {
  border-color: rgba(36, 54, 79, 0.17);
  background: rgba(36, 54, 79, 0.1);
  color: #24364f;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.62), 0 12px 26px rgba(36, 54, 79, 0.065);
}

.wallet-icon-button.is-add:hover {
  background: rgba(36, 54, 79, 0.15);
}

.wallet-icon-button.danger {
  background: rgba(179, 38, 30, 0.065);
  border-color: rgba(179, 38, 30, 0.14);
  color: #b3261e;
}

.wallet-icon-button:disabled {
  opacity: 0.45;
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

.card-detail-spin-enter-active,
.card-detail-spin-leave-active {
  transition: opacity 420ms ease, transform 740ms cubic-bezier(0.2, 0.78, 0.2, 1), filter 420ms ease;
}

.card-detail-spin-leave-active {
  position: absolute;
  inset: 0;
  margin-inline: auto;
  pointer-events: none;
}

.card-detail-spin-enter-from,
.card-carousel.glide-prev .card-detail-spin-leave-to {
  opacity: 0;
  filter: blur(0.4px) saturate(0.88);
  transform: translate3d(52px, -4px, -54px) rotateY(-34deg) rotateZ(1.4deg) scale(0.94);
}

.card-detail-spin-enter-to,
.card-detail-spin-leave-from {
  opacity: 1;
  filter: blur(0);
  transform: translate3d(0, 0, 0) rotateY(0deg) rotateZ(0deg) scale(1);
}

.card-carousel.glide-next .card-detail-spin-leave-to,
.card-carousel.glide-prev .card-detail-spin-enter-from {
  opacity: 0;
  filter: blur(0.4px) saturate(0.88);
  transform: translate3d(-52px, -4px, -54px) rotateY(34deg) rotateZ(-1.4deg) scale(0.94);
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
  background: #0f5fae;
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
  border-left: 1px solid rgba(32, 36, 42, 0.1);
  text-align: right;
}

.progress-meta.single span {
  align-items: center;
  text-align: center;
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
  border-left: 1px solid rgba(32, 36, 42, 0.12);
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-top: 16px;
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

.quick-action.app-card-sm {
  border-color: rgba(36, 54, 79, 0.1) !important;
  background: rgba(248, 251, 253, 0.55) !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.58), 0 12px 26px rgba(36, 54, 79, 0.055) !important;
  backdrop-filter: blur(16px) saturate(1.08);
}

.quick-action.app-card-sm:hover {
  background: rgba(248, 251, 253, 0.68) !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.68), 0 15px 30px rgba(36, 54, 79, 0.07) !important;
}

.quick-action svg {
  width: 20px;
  height: 20px;
  stroke-width: 2.25;
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
  overflow: hidden;
}

.tx-card button {
  display: grid;
  width: 100%;
  grid-template-columns: 32px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(32, 36, 42, 0.075);
  padding: 13px 14px;
  background: transparent;
  text-align: left;
}

.tx-card button > span:first-child {
  display: inline-flex;
  width: 32px;
  height: 32px;
  align-items: center;
  justify-content: center;
  font-size: 16px;
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

.tx-card b {
  color: #20242a;
  font-size: 13px;
  font-weight: 900;
  font-variant-numeric: tabular-nums;
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
  width: 42px;
  height: 42px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 0;
  background: rgba(36, 54, 79, 0.92);
  color: #fff;
  box-shadow: 0 12px 22px rgba(36, 54, 79, 0.16), inset 0 1px 0 rgba(255, 255, 255, 0.26);
  backdrop-filter: blur(12px) saturate(1.08);
}

.candidate-card-row > button:hover:not(:disabled) {
  background: rgba(36, 54, 79, 0.98);
}

.candidate-card-row > button:disabled {
  background: rgba(230, 236, 242, 0.66);
  color: #7a8795;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.52);
}

@media (max-width: 380px) {
  .dashboard-header {
    border-radius: 0;
  }

  .header-top {
    gap: 10px;
  }

  .header-actions {
    gap: 5px;
  }

  .header-actions .icon-button {
    width: 40px;
    height: 40px;
  }

  .month-summary {
    gap: 12px;
    border-radius: 0;
  }

  .month-summary span {
    font-size: 10px;
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
    top: 0;
    right: 8px;
  }

  .wallet-icon-button {
    width: 38px;
    height: 38px;
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
    grid-template-columns: repeat(4, minmax(0, 1fr));
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
