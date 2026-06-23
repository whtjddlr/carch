<template>
  <section class="screen">
    <header class="utility-header blue-gradient">
      <AppBackButton :fallback="backFallback" />
      <button
        v-if="isCardDetail && selectedCard"
        type="button"
        class="card-delete-button"
        style="background: #e5484d !important; color: #fff !important; border: 0 !important; box-shadow: 0 6px 16px rgba(217, 45, 32, 0.36) !important;"
        :disabled="isDeletingCard"
        aria-label="카드 삭제"
        @click="deleteCard"
      >
        <Trash2 :size="18" />
      </button>
      <h1>{{ pageTitle }}</h1>
      <p>{{ pageDescription }}</p>
    </header>

    <div class="screen-scroll scrollbar-hide utility-body">
      <article v-if="isCardDetail && selectedCard" class="app-card card-detail-card">
        <div class="detail-card-art">
          <img v-if="selectedCard.imageUrl" :src="selectedCard.imageUrl" :alt="selectedCard.name" />
          <CreditCard v-else :size="42" />
        </div>
        <div class="detail-head">
          <span>{{ selectedCard.issuer }}</span>
          <h2>{{ selectedCard.name }}</h2>
          <p>{{ selectedCard.titleDescription }}</p>
        </div>
        <div class="detail-grid">
          <div>
            <span>연회비</span>
            <strong>{{ krw(selectedCard.annualFee) }}</strong>
          </div>
          <div>
            <span>전월실적</span>
            <strong>{{ selectedCard.previousMonthMinSpend ? krw(selectedCard.previousMonthMinSpend) : '없음' }}</strong>
          </div>
          <div>
            <span>이번 달 사용</span>
            <strong>{{ krw(selectedCard.spent) }}</strong>
          </div>
          <div>
            <span>한도</span>
            <strong>{{ krw(selectedCard.limit) }}</strong>
          </div>
        </div>
        <section class="benefit-list">
          <h3>대표 혜택</h3>
          <ul>
            <li v-for="benefit in selectedCard.benefits" :key="benefit">{{ benefit }}</li>
          </ul>
        </section>
        <RouterLink class="primary-button w-100" :to="`/cards/apply/${selectedCard.id}`">신청 화면 보기</RouterLink>
      </article>

      <article v-else-if="props.type === 'cardApply' && selectedCard" class="app-card apply-card">
        <div class="apply-card-head">
          <div>
            <span>{{ selectedCard.issuer }}</span>
            <h2>{{ selectedCard.name }}</h2>
            <p>{{ selectedCard.benefitSummary || selectedCard.titleDescription }}</p>
          </div>
          <div class="apply-thumb">
            <img v-if="selectedCard.imageUrl" :src="selectedCard.imageUrl" :alt="selectedCard.name" />
            <CreditCard v-else :size="26" />
          </div>
        </div>
        <div class="apply-steps">
          <div v-for="(step, index) in applySteps" :key="step.title" class="apply-step">
            <span>{{ index + 1 }}</span>
            <div>
              <strong>{{ step.title }}</strong>
              <p>{{ step.description }}</p>
            </div>
          </div>
        </div>
        <button class="primary-button w-100" type="button" @click="applySubmitted = true">
          {{ applySubmitted ? '신청 초안 저장 완료' : '신청 초안 저장' }}
        </button>
        <p class="helper-text">실제 카드 발급 전에는 약관 동의, 본인 인증, 심사 단계가 추가됩니다.</p>
      </article>

      <article v-else-if="props.type === 'transaction' && selectedTransaction" class="app-card transaction-detail-card">
        <div class="transaction-hero">
          <span class="merchant-icon">{{ selectedTransaction.icon }}</span>
          <p>{{ selectedTransaction.cat }}</p>
          <h2>{{ selectedTransaction.merchant }}</h2>
          <strong :class="{ plus: selectedTransaction.amt > 0 }">
            {{ selectedTransaction.amt > 0 ? '+' : '-' }}{{ krw(selectedTransaction.amt) }}
          </strong>
        </div>
        <div class="detail-list">
          <div>
            <CalendarDays :size="16" />
            <span>승인 일시</span>
            <b>{{ selectedTransaction.date }} {{ selectedTransaction.time }}</b>
          </div>
          <div>
            <CreditCard :size="16" />
            <span>사용 카드</span>
            <b>{{ transactionCardName }}</b>
          </div>
          <div>
            <MapPin :size="16" />
            <span>가맹점</span>
            <b>{{ selectedTransaction.addr }}</b>
          </div>
        </div>
        <div class="utility-actions">
          <RouterLink class="outline-button" to="/transactions">목록으로</RouterLink>
          <RouterLink class="primary-button" :to="planFromTransactionPath">목표 지출에 추가</RouterLink>
        </div>
      </article>

      <form v-else-if="props.type === 'budgetNew'" class="app-card form-card" @submit.prevent="saveBudgetDraft">
        <div class="form-preview">
          <span :style="{ background: budgetForm.color }">
            <component :is="budgetIconComponent" :size="20" />
          </span>
          <div>
            <strong>{{ budgetForm.name || '새 예산' }}</strong>
            <p>월 예산 {{ budgetForm.amount ? krw(budgetForm.amount) : '0원' }}</p>
          </div>
        </div>
        <label>
          <span class="field-label">카테고리명</span>
          <input v-model.trim="budgetForm.name" class="form-field" type="text" placeholder="예: 식비, 교통, 카페" />
        </label>
        <label>
          <span class="field-label">월 예산 금액</span>
          <input v-model.number="budgetForm.amount" class="form-field" type="number" min="0" placeholder="0" />
        </label>
        <div class="color-picker" aria-label="예산 색상 선택">
          <button
            v-for="color in budgetColors"
            :key="color"
            type="button"
            :aria-label="`예산 색상 ${color}`"
            :class="{ active: budgetForm.color === color }"
            :style="{ background: color }"
            @click="budgetForm.color = color"
          />
        </div>
        <button class="primary-button w-100" type="submit" :disabled="!canSaveBudget">
          {{ budgetSaved ? '저장 완료' : '예산 저장' }}
        </button>
      </form>

      <section v-else-if="props.type === 'report'" class="report-view">
        <div class="report-summary app-card">
          <span>6월 카드 소비</span>
          <strong>{{ krw(reportTotalSpent) }}</strong>
          <p>가장 큰 지출 카테고리는 {{ topCategory?.cat || '-' }}입니다.</p>
        </div>
        <div class="metric-list">
          <article v-for="metric in reportMetrics" :key="metric.label" class="app-card-sm metric-panel">
            <span>{{ metric.label }}</span>
            <strong>{{ metric.value }}</strong>
          </article>
        </div>
        <section class="app-card report-section">
          <h2>카테고리별 지출</h2>
          <div v-for="item in reportCategories" :key="item.cat" class="report-row">
            <div>
              <span>{{ item.cat }}</span>
              <b>{{ krw(item.amount) }}</b>
            </div>
            <div class="report-track">
              <i :style="{ width: `${item.percent}%` }" />
            </div>
          </div>
        </section>
        <RouterLink class="primary-button w-100" to="/analytics">AI 분석 보기</RouterLink>
      </section>

      <section v-else-if="props.type === 'notifications'" class="notification-view">
        <button class="muted-button mark-read-button" type="button" @click="markAllNotificationsRead">
          모두 읽음 처리
        </button>
        <article
          v-for="notice in notificationItems"
          :key="notice.id"
          class="app-card notification-card"
          :class="{ read: notice.read, actionable: notice.route }"
          :role="notice.route ? 'button' : undefined"
          :tabindex="notice.route ? 0 : undefined"
          @click="openNotice(notice)"
          @keydown.enter.prevent="openNotice(notice)"
          @keydown.space.prevent="openNotice(notice)"
        >
          <div class="notice-icon">
            <component :is="notificationIcon(notice.type)" :size="18" />
          </div>
          <div>
            <div class="notice-title-row">
              <strong>{{ notice.title }}</strong>
              <span>{{ notice.time }}</span>
            </div>
            <p>{{ notice.body }}</p>
          </div>
        </article>
      </section>

      <section v-else-if="props.type === 'settings'" class="settings-view">
        <article class="profile-summary app-card">
          <div class="profile-avatar">{{ user.initials }}</div>
          <div>
            <strong>{{ user.name }}</strong>
            <span>{{ user.email }}</span>
          </div>
          <RouterLink to="/settings/profile" aria-label="프로필 수정">수정</RouterLink>
        </article>
        <RouterLink
          v-for="item in settingItems"
          :key="item.label"
          class="app-card setting-row"
          :to="item.path"
          :aria-label="`${item.label} 화면으로 이동`"
        >
          <component :is="item.icon" :size="18" />
          <div>
            <strong>{{ item.label }}</strong>
            <span>{{ item.description }}</span>
          </div>
          <ChevronRight :size="17" />
        </RouterLink>
      </section>

      <section v-else-if="props.type === 'security'" class="security-view">
        <article class="app-card security-card">
          <ShieldCheck :size="30" />
          <div>
            <strong>보안 상태 양호</strong>
            <p>로그인과 개인정보 보호 항목을 확인하세요.</p>
          </div>
        </article>
        <article v-for="item in securityItems" :key="item.label" class="app-card setting-row security-row">
          <component :is="item.icon" :size="18" />
          <div>
            <strong>{{ item.label }}</strong>
            <span>{{ item.description }}</span>
          </div>
          <CheckCircle2 :size="17" />
        </article>
      </section>

      <form v-else-if="props.type === 'profile'" class="app-card form-card" @submit.prevent="saveProfileDraft">
        <div class="profile-edit-head">
          <div class="profile-avatar large">{{ profileForm.initials || '김' }}</div>
          <div>
            <strong>프로필 정보</strong>
            <p>카드 추천과 커뮤니티에 표시되는 기본 정보입니다.</p>
          </div>
        </div>
        <label>
          <span class="field-label">이름</span>
          <input v-model.trim="profileForm.name" class="form-field" type="text" />
        </label>
        <label>
          <span class="field-label">이메일</span>
          <input v-model.trim="profileForm.email" class="form-field" type="email" />
        </label>
        <label>
          <span class="field-label">휴대폰</span>
          <input v-model.trim="profileForm.phone" class="form-field" type="tel" />
        </label>
        <button class="primary-button w-100" type="submit">
          {{ profileSaved ? '저장 완료' : '변경사항 저장' }}
        </button>
      </form>

      <section v-else-if="props.type === 'search'" class="search-view">
        <label class="search-box">
          <Search :size="18" />
          <input
            v-model.trim="searchTerm"
            type="search"
            aria-label="통합 검색"
            placeholder="카드, 거래, 커뮤니티 검색"
            autofocus
          />
        </label>
        <div class="search-tabs">
          <button
            v-for="type in searchTypes"
            :key="type.value"
            type="button"
            :class="{ active: searchType === type.value }"
            @click="searchType = type.value"
          >
            {{ type.label }}
          </button>
        </div>
        <article v-if="searchLoading" class="app-card empty-card search-status">
          <Search :size="28" />
          <strong>검색 중입니다</strong>
          <p>카드, 거래, 커뮤니티를 함께 확인하고 있어요.</p>
        </article>
        <article v-else-if="searchError" class="app-card empty-card search-status">
          <Search :size="28" />
          <strong>검색을 불러오지 못했어요</strong>
          <p>잠시 후 다시 시도해 주세요.</p>
        </article>
        <RouterLink
          v-if="!searchLoading && !searchError"
          v-for="result in searchResults"
          :key="`${result.type}-${result.id}`"
          class="app-card search-result"
          :to="result.path"
        >
          <component :is="result.icon" :size="18" />
          <div>
            <strong>{{ result.title }}</strong>
            <span>{{ result.description }}</span>
            <small v-if="result.badge">{{ result.badge }}</small>
          </div>
          <ChevronRight :size="17" />
        </RouterLink>
        <article v-if="!searchLoading && !searchError && searchResults.length === 0" class="app-card empty-card">
          <Search :size="28" />
          <strong>검색 결과가 없어요</strong>
          <p>카드명, 가맹점명, 커뮤니티 제목으로 검색해보세요.</p>
        </article>
      </section>

      <article v-else class="app-card utility-card">
        <component :is="content.icon" :size="34" />
        <h2>{{ content.title }}</h2>
        <p>{{ content.body }}</p>
        <div v-if="content.planLink" class="utility-actions">
          <RouterLink class="primary-button" to="/plans">목표 지출 계획</RouterLink>
          <RouterLink class="outline-button" to="/plans/new">목표 지출 만들기</RouterLink>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  BarChart3,
  Bell,
  BookOpen,
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  CreditCard,
  Edit3,
  Lock,
  MapPin,
  MessageSquare,
  PieChart,
  Receipt,
  Search,
  Settings,
  ShieldCheck,
  Target,
  Trash2,
  User,
  WalletCards,
} from 'lucide-vue-next'
import {
  budgetCategories,
  cards as mockCards,
  communityPosts as mockCommunityPosts,
  krw,
  notifications,
  transactions as mockTransactions,
  user,
} from '@/data/mockData'
import AppBackButton from '@/components/AppBackButton.vue'
import { deleteOwnedCard, fetchCard, fetchOwnedCards, fetchSearchResults, fetchTransactions, normalizeCard } from '@/services/api'

const props = defineProps({
  type: { type: String, default: 'default' },
})

const route = useRoute()
const router = useRouter()
const backFallback = computed(() => {
  const map = {
    card: '/cards',
    cardApply: '/cards',
    transaction: '/transactions',
    budgetNew: '/budget',
    report: '/analytics',
    notifications: '/cards',
    settings: '/cards',
    profile: '/settings',
    security: '/settings',
    search: '/cards',
  }
  return map[props.type] || '/cards'
})

const apiCard = ref(null)
const transactionRows = ref(mockTransactions)
const cardRows = ref(mockCards)
const communityRows = ref(mockCommunityPosts)
const applySubmitted = ref(false)
const budgetSaved = ref(false)
const profileSaved = ref(false)
const searchTerm = ref('')
const searchType = ref('all')
const searchRows = ref([])
const searchLoading = ref(false)
const searchError = ref('')
const searchLoaded = ref(false)
let searchRequestId = 0
const readNotificationIds = ref(new Set(notifications.filter((notice) => notice.read).map((notice) => notice.id)))

const isCardDetail = computed(() => props.type === 'card')
const needsCard = computed(() => props.type === 'card' || props.type === 'cardApply')
const selectedCard = computed(() => {
  if (!needsCard.value) return null
  return apiCard.value || cardRows.value.find((card) => String(card.id) === String(route.params.id))
})

const isDeletingCard = ref(false)
async function deleteCard() {
  if (!selectedCard.value || isDeletingCard.value) return
  if (!window.confirm(`${selectedCard.value.name} 카드를 보유 목록에서 삭제할까요?`)) return
  isDeletingCard.value = true
  try {
    await deleteOwnedCard(selectedCard.value.id)
    router.push('/cards')
  } catch (error) {
    isDeletingCard.value = false
    window.alert('카드를 삭제하지 못했습니다.')
  }
}

const selectedTransaction = computed(() => {
  if (props.type !== 'transaction') return null
  return transactionRows.value.find((tx) => String(tx.id) === String(route.params.id))
})

const transactionCardName = computed(() => {
  const card = cardRows.value.find((item) => String(item.id) === String(selectedTransaction.value?.cardId))
  return card?.name || '카드 정보 없음'
})

const planFromTransactionPath = computed(() => {
  const tx = selectedTransaction.value
  if (!tx) return '/plans/new'
  const query = new URLSearchParams({
    merchantName: tx.merchant,
    category: tx.cat,
    amount: String(Math.abs(tx.amt)),
  })
  return `/plans/new?${query.toString()}`
})

const budgetForm = reactive({
  name: '',
  amount: null,
  color: '#0f5fae',
})

const profileForm = reactive({
  name: user.name,
  email: user.email,
  phone: user.phone,
  initials: user.initials,
})

const budgetColors = ['#0f5fae', '#008c95', '#d92d20', '#24364f', '#c49a49', '#5f6b77']
const canSaveBudget = computed(() => budgetForm.name.length > 0 && Number(budgetForm.amount) > 0)
const budgetIconComponent = computed(() => Target)

const applySteps = [
  { title: '카드 정보 확인', description: '연회비, 전월실적, 대표 혜택을 검토합니다.' },
  { title: '본인 인증', description: '실제 서비스에서는 휴대폰 또는 공동인증서 인증이 들어갑니다.' },
  { title: '신청 제출', description: '심사 결과와 발급 상태를 알림으로 확인합니다.' },
]

const reportExpenseRows = computed(() => transactionRows.value.filter((tx) => Number(tx.amt) < 0))
const reportTotalSpent = computed(() => reportExpenseRows.value.reduce((sum, tx) => sum + Math.abs(Number(tx.amt) || 0), 0))
const reportCategories = computed(() => {
  const map = new Map()
  reportExpenseRows.value.forEach((tx) => {
    const key = tx.cat || '기타'
    map.set(key, (map.get(key) || 0) + Math.abs(Number(tx.amt) || 0))
  })
  return [...map.entries()]
    .map(([cat, amount]) => ({
      cat,
      amount,
      percent: reportTotalSpent.value ? Math.round((amount / reportTotalSpent.value) * 100) : 0,
    }))
    .sort((a, b) => b.amount - a.amount)
})
const topCategory = computed(() => reportCategories.value[0])
const reportMetrics = computed(() => [
  { label: '거래 건수', value: `${reportExpenseRows.value.length}건` },
  { label: '평균 결제', value: krw(Math.round(reportTotalSpent.value / Math.max(reportExpenseRows.value.length, 1))) },
  { label: '예산 사용률', value: `${budgetUsePercent.value}%` },
])

const budgetUsePercent = computed(() => {
  const totalBudget = budgetCategories.reduce((sum, category) => sum + category.budget, 0)
  return Math.min(Math.round((reportTotalSpent.value / totalBudget) * 100), 100)
})

const notificationItems = computed(() =>
  notifications.map((notice) => ({
    ...notice,
    read: readNotificationIds.value.has(notice.id),
    route: {
      payment: '/transactions/t1',
      budget: '/budget/current',
      recommend: '/recommendations/new',
    }[notice.type],
  })),
)

const settingItems = [
  { label: '알림 설정', description: '결제, 예산, 추천 알림 관리', path: '/notifications', icon: Bell },
  { label: '월간 보고서', description: '이번 달 소비 리포트 확인', path: '/reports/monthly', icon: BarChart3 },
  { label: '목표 지출 계획', description: '월 예산 밖의 큰 지출과 카드 배분', path: '/plans', icon: CalendarDays },
  { label: '보안', description: '로그인과 개인정보 보호 설정', path: '/settings/security', icon: Lock },
]

const securityItems = [
  { label: '로그인 보호', description: '현재 기기에서 안전하게 로그인 중입니다.', icon: Lock },
  { label: '개인정보 관리', description: '프로필 정보와 알림 권한을 분리해 관리합니다.', icon: User },
  { label: '데이터 보관', description: '분석 기록은 DB 저장 기준으로 관리됩니다.', icon: ShieldCheck },
]

const searchTypes = [
  { label: '전체', value: 'all' },
  { label: '카드', value: 'card' },
  { label: '거래', value: 'transaction' },
  { label: '커뮤니티', value: 'community' },
]

const searchIconMap = {
  card: CreditCard,
  transaction: Receipt,
  community: MessageSquare,
}

const searchableItems = computed(() => [
  ...cardRows.value.map((card) => ({
    id: card.id,
    type: 'card',
    title: card.name,
    description: `${card.issuer} · ${card.benefitSummary}`,
    path: `/cards/${card.id}`,
    icon: CreditCard,
  })),
  ...transactionRows.value.map((tx) => ({
    id: tx.id,
    type: 'transaction',
    title: tx.merchant,
    description: `${tx.cat} · ${tx.date} · ${tx.amt > 0 ? '+' : '-'}${krw(tx.amt)}`,
    path: `/transactions/${tx.id}`,
    icon: Receipt,
  })),
  ...communityRows.value.map((post) => ({
    id: post.id,
    type: 'community',
    title: post.title,
    description: `${post.author} · 댓글 ${post.comments}`,
    path: `/community/${post.id}`,
    icon: MessageSquare,
  })),
])

const localSearchResults = computed(() => {
  const term = searchTerm.value.toLowerCase()
  return searchableItems.value
    .filter((item) => searchType.value === 'all' || item.type === searchType.value)
    .filter((item) => !term || `${item.title} ${item.description}`.toLowerCase().includes(term))
    .slice(0, 12)
})

const searchResults = computed(() => {
  if (props.type === 'search' && searchLoaded.value) {
    return searchRows.value.map((item) => ({
      ...item,
      id: item.id || `${item.type}-${item.title}`,
      path: item.path || '/search',
      description: item.description || item.badge || '',
      icon: searchIconMap[item.type] || Search,
    }))
  }
  return localSearchResults.value
})

const content = computed(() => {
  const map = {
    card: { title: '카드 상세', description: '카드별 사용 현황', body: `선택한 카드 ID: ${route.params.id}`, icon: CreditCard },
    cardApply: { title: '카드 신청', description: '신청 정보를 확인하세요.', body: '카드 목록에서 신청할 카드를 다시 선택해주세요.', icon: CreditCard },
    transaction: { title: '거래 상세', description: '거래처와 결제 정보를 확인하세요.', body: `거래 ID: ${route.params.id}`, icon: BookOpen, planLink: true },
    budgetNew: { title: '예산 추가', description: '새 예산 카테고리를 추가하세요.', body: '카테고리명과 월 예산을 입력하는 화면입니다.', icon: Target },
    report: { title: '월간 보고서', description: '이번 달 소비 요약', body: '월간 리포트입니다.', icon: BookOpen },
    notifications: { title: '알림', description: '중요한 카드 알림', body: '결제 알림, 예산 경고, 추천 알림을 모아 보여줍니다.', icon: Bell },
    settings: { title: '설정', description: '사용자 메뉴', body: '사용자 메뉴입니다.', icon: Settings, planLink: true },
    profile: { title: '프로필 수정', description: '내 정보를 관리하세요.', body: '프로필 정보를 입력하고 저장할 수 있습니다.', icon: User },
    security: { title: '보안', description: '로그인과 개인정보 보호 설정', body: '보안 설정을 확인하세요.', icon: ShieldCheck },
    search: { title: '검색', description: '거래와 카드를 검색하세요.', body: '검색어를 입력하세요.', icon: Search },
  }
  return map[props.type] || { title: 'CARCH', description: '경로 확인', body: '이동 경로를 다시 확인해주세요.', icon: BookOpen }
})

const pageTitle = computed(() => {
  if (isCardDetail.value && selectedCard.value) return selectedCard.value.name
  if (props.type === 'cardApply' && selectedCard.value) return '카드 신청'
  if (props.type === 'transaction' && selectedTransaction.value) return '거래 상세'
  return content.value.title
})

const pageDescription = computed(() => {
  if (isCardDetail.value && selectedCard.value) return selectedCard.value.issuer
  if (props.type === 'cardApply' && selectedCard.value) return selectedCard.value.name
  if (props.type === 'transaction' && selectedTransaction.value) return selectedTransaction.value.merchant
  return content.value.description
})

function saveBudgetDraft() {
  if (!canSaveBudget.value) return
  budgetSaved.value = true
  window.setTimeout(() => router.push('/budget'), 550)
}

function saveProfileDraft() {
  profileSaved.value = true
  window.setTimeout(() => {
    profileSaved.value = false
  }, 1200)
}

function markAllNotificationsRead() {
  readNotificationIds.value = new Set(notifications.map((notice) => notice.id))
}

function openNotice(notice) {
  if (!notice.route) return
  readNotificationIds.value = new Set([...readNotificationIds.value, notice.id])
  router.push(notice.route)
}

function notificationIcon(type) {
  const map = {
    payment: Receipt,
    budget: Target,
    recommend: ShieldCheck,
    community: MessageSquare,
    system: CheckCircle2,
  }
  return map[type] || Bell
}

async function loadSearchResults() {
  if (props.type !== 'search') return
  const requestId = ++searchRequestId
  searchLoading.value = true
  searchError.value = ''

  try {
    const data = await fetchSearchResults({
      q: searchTerm.value,
      type: searchType.value,
      limit: searchType.value === 'card' ? 24 : 12,
    })
    if (requestId !== searchRequestId) return
    searchRows.value = data.results || []
    searchLoaded.value = true
  } catch (error) {
    if (requestId !== searchRequestId) return
    console.warn('Search API request failed. Falling back to local rows.', error)
    searchRows.value = []
    searchLoaded.value = true
    searchError.value = '검색 결과를 불러오지 못했습니다.'
  } finally {
    if (requestId === searchRequestId) {
      searchLoading.value = false
    }
  }
}

let searchDebounceTimer = null
watch([searchTerm, searchType], () => {
  if (props.type !== 'search') return
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(loadSearchResults, 180)
}, { immediate: true })

onMounted(async () => {
  try {
    if (needsCard.value) {
      const [card, transactions] = await Promise.all([
        fetchCard(route.params.id),
        fetchTransactions({ cardId: route.params.id }),
      ])
      apiCard.value = normalizeCard(card, 0, transactions)
    }

    if (props.type === 'transaction' || props.type === 'report') {
      const [transactions, ownedCards] = await Promise.all([
        fetchTransactions(),
        fetchOwnedCards(),
      ])
      transactionRows.value = transactions
      cardRows.value = ownedCards.map((card, index) => normalizeCard(card, index, transactions))
    }
  } catch (error) {
    console.warn('상세 화면 API를 불러오지 못해 mock 데이터를 사용합니다.', error)
  }
})
</script>

<style scoped>
.utility-header {
  position: relative;
  padding: 24px 20px;
  color: #fff;
}

.card-delete-button {
  position: absolute;
  top: 18px;
  right: 18px;
  z-index: 2;
  display: inline-flex;
  width: 40px;
  height: 40px;
  align-items: center;
  justify-content: center;
  border: 0 !important;
  border-radius: 12px !important;
  background: #e5484d !important;
  color: #fff !important;
  box-shadow: 0 6px 16px rgba(217, 45, 32, 0.34) !important;
  cursor: pointer;
  transition: transform 150ms ease, background-color 150ms ease;
}

.card-delete-button:active {
  transform: scale(0.94);
}

.card-delete-button:disabled {
  opacity: 0.5;
}

.utility-header h1 {
  margin: 20px 0 4px;
  font-size: 22px;
  font-weight: 900;
}

.utility-header p {
  margin: 0;
  color: rgba(255, 255, 255, 0.68);
  font-size: 12px;
  font-weight: 700;
}

.utility-body {
  padding: 20px 20px 112px;
}

.utility-card {
  display: flex;
  min-height: 280px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  color: #0f5fae;
  text-align: center;
}

.utility-card h2 {
  margin: 16px 0 8px;
  color: #17202b;
  font-size: 18px;
  font-weight: 900;
}

.utility-card p {
  margin: 0 0 18px;
  color: #6e6e73;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.55;
}

.outline-button,
.primary-button,
.muted-button {
  text-decoration: none;
}

.w-100 {
  width: 100%;
}

.helper-text {
  margin: 10px 0 0;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.5;
}

.utility-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.utility-actions a {
  flex: 1;
  min-width: 132px;
  text-decoration: none;
}

.card-detail-card,
.apply-card,
.transaction-detail-card,
.form-card,
.report-summary,
.report-section {
  padding: 18px;
}

.detail-card-art {
  position: relative;
  display: flex;
  height: 200px;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 14px;
  padding: 0;
  background: #e7edf4;
  color: #0f5fae;
}

.detail-card-art img,
.apply-thumb img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  filter: drop-shadow(0 12px 20px rgba(16, 24, 40, 0.16));
}

.card-detail-card .detail-card-art img {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 174px;
  height: 276px;
  object-fit: cover;
  border-radius: 12px;
  transform: translate(-50%, -50%) rotate(90deg);
  filter: drop-shadow(0 16px 24px rgba(16, 24, 40, 0.22));
}

.detail-head {
  margin-top: 16px;
}

.detail-head span,
.apply-card-head span,
.report-summary span,
.plan-entry span {
  color: #0f5fae;
  font-size: 12px;
  font-weight: 900;
}

.detail-head h2,
.apply-card-head h2 {
  margin: 5px 0 6px;
  color: #17202b;
  font-size: 20px;
  font-weight: 900;
  line-height: 1.25;
}

.detail-head p,
.apply-card-head p {
  margin: 0;
  color: #6e6e73;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.55;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-top: 16px;
}

.detail-grid div,
.metric-panel {
  padding: 12px;
}

.detail-grid span,
.metric-panel span {
  display: block;
  color: #6e6e73;
  font-size: 11px;
  font-weight: 800;
}

.detail-grid strong,
.metric-panel strong {
  display: block;
  margin-top: 3px;
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
}

.benefit-list {
  margin: 16px 0;
}

.benefit-list h3,
.report-section h2 {
  margin: 0 0 8px;
  color: #17202b;
  font-size: 15px;
  font-weight: 900;
}

.benefit-list ul {
  margin: 0;
  padding-left: 18px;
  color: #4a5663;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.8;
}

.apply-card-head {
  display: grid;
  grid-template-columns: 1fr 96px;
  gap: 14px;
  align-items: center;
}

.apply-thumb {
  display: flex;
  height: 84px;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 12px;
  padding: 10px;
  background: #f3f6fb;
  color: #0f5fae;
}

.apply-steps {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 18px 0;
}

.apply-step {
  display: grid;
  grid-template-columns: 30px 1fr;
  gap: 10px;
}

.apply-step > span {
  display: inline-flex;
  width: 30px;
  height: 30px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #e8f1ff;
  color: #0f5fae;
  font-size: 12px;
  font-weight: 900;
}

.apply-step strong {
  display: block;
  color: #17202b;
  font-size: 13px;
  font-weight: 900;
}

.apply-step p {
  margin: 3px 0 0;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.45;
}

.transaction-hero {
  text-align: center;
}

.merchant-icon {
  display: inline-flex;
  width: 52px;
  height: 52px;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: #e8f1ff;
  font-size: 24px;
}

.transaction-hero p {
  margin: 12px 0 4px;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 800;
}

.transaction-hero h2 {
  margin: 0;
  color: #17202b;
  font-size: 21px;
  font-weight: 900;
}

.transaction-hero strong {
  display: block;
  margin-top: 10px;
  color: #17202b;
  font-size: 26px;
  font-weight: 900;
}

.transaction-hero strong.plus {
  color: #008c95;
}

.detail-list {
  margin: 20px 0;
  border-top: 1px solid #eef2f7;
}

.detail-list div {
  display: grid;
  grid-template-columns: 18px 78px 1fr;
  gap: 8px;
  align-items: center;
  border-bottom: 1px solid #eef2f7;
  padding: 13px 0;
}

.detail-list svg {
  color: #6e6e73;
}

.detail-list span {
  color: #6e6e73;
  font-size: 12px;
  font-weight: 800;
}

.detail-list b {
  min-width: 0;
  color: #17202b;
  font-size: 13px;
  font-weight: 900;
  text-align: right;
  overflow-wrap: anywhere;
}

.form-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-preview,
.profile-edit-head,
.profile-summary {
  display: flex;
  align-items: center;
  gap: 12px;
}

.form-preview > span {
  display: inline-flex;
  width: 44px;
  height: 44px;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  color: #fff;
}

.form-preview strong,
.profile-edit-head strong,
.profile-summary strong {
  display: block;
  color: #17202b;
  font-size: 15px;
  font-weight: 900;
}

.form-preview p,
.profile-edit-head p,
.profile-summary span {
  margin: 3px 0 0;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 700;
}

.color-picker {
  display: flex;
  gap: 9px;
}

.color-picker button {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.5);
}

.color-picker button.active {
  outline: 3px solid rgba(29, 78, 216, 0.16);
  outline-offset: 2px;
}

.report-view,
.notification-view,
.settings-view,
.search-view {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.report-summary strong {
  display: block;
  margin-top: 4px;
  color: #17202b;
  font-size: 28px;
  font-weight: 900;
}

.report-summary p {
  margin: 8px 0 0;
  color: #6e6e73;
  font-size: 13px;
  font-weight: 700;
}

.metric-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.report-row + .report-row {
  margin-top: 12px;
}

.report-row div:first-child {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
}

.report-row span {
  color: #4a5663;
  font-size: 13px;
  font-weight: 900;
}

.report-row b {
  color: #17202b;
  font-size: 13px;
  font-weight: 900;
}

.report-track {
  height: 6px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(23, 32, 43, 0.1);
}

.report-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #0f5fae;
}

.mark-read-button {
  align-self: flex-end;
}

.notification-card {
  display: grid;
  grid-template-columns: 38px 1fr;
  gap: 12px;
  padding: 14px;
  text-align: left;
}

.notification-card.read {
  opacity: 0.66;
}

.notification-card.actionable {
  cursor: pointer;
}

.notification-card.actionable:focus-visible {
  outline: 3px solid rgba(15, 95, 174, 0.18);
  outline-offset: 2px;
}

.notice-icon {
  display: inline-flex;
  width: 38px;
  height: 38px;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: #e8f1ff;
  color: #0f5fae;
}

.notice-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.notice-title-row strong {
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
}

.notice-title-row span {
  flex-shrink: 0;
  color: #8a9aad;
  font-size: 11px;
  font-weight: 800;
}

.notification-card p {
  margin: 5px 0 0;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.45;
}

.profile-summary {
  padding: 15px;
}

.profile-avatar {
  display: inline-flex;
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: #172554;
  color: #fff;
  font-size: 16px;
  font-weight: 900;
}

.profile-avatar.large {
  width: 56px;
  height: 56px;
  border-radius: 18px;
  font-size: 20px;
}

.profile-summary > div:nth-child(2) {
  min-width: 0;
  flex: 1;
}

.profile-summary a {
  display: inline-flex;
  min-width: 44px;
  min-height: 40px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  color: #0f5fae;
  font-size: 12px;
  font-weight: 900;
  text-decoration: none;
}

.security-view {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.security-card {
  display: flex;
  align-items: center;
  gap: 13px;
  padding: 18px;
  color: #0f5fae;
}

.security-card strong {
  display: block;
  color: #17202b;
  font-size: 16px;
  font-weight: 900;
}

.security-card p {
  margin: 4px 0 0;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.45;
}

.security-row > svg:last-child {
  color: #008c95;
}

.setting-row {
  display: grid;
  grid-template-columns: 24px 1fr 18px;
  gap: 12px;
  align-items: center;
  padding: 14px 15px;
  color: inherit;
  text-decoration: none;
}

.setting-row > svg:first-child {
  color: #0f5fae;
}

.setting-row strong {
  display: block;
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
}

.setting-row span {
  display: block;
  margin-top: 3px;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 700;
}

.setting-row > svg:last-child {
  color: #8a9aad;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #dbe4ee;
  border-radius: 12px;
  padding: 0 13px;
  background: #fff;
  color: #6e6e73;
}

.search-box input {
  min-width: 0;
  flex: 1;
  border: 0;
  padding: 14px 0;
  background: transparent;
  color: #17202b;
  font-size: 14px;
  font-weight: 800;
  outline: none;
}

.search-tabs {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 6px;
}

.search-tabs button {
  min-height: 42px;
  border-radius: 999px;
  padding: 9px 6px;
  background: #fff;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 900;
}

.search-tabs button.active {
  background: #e8f1ff;
  color: #0f5fae;
}

.search-result {
  display: grid;
  grid-template-columns: 22px 1fr 18px;
  gap: 10px;
  align-items: center;
  padding: 14px;
  color: inherit;
  text-decoration: none;
}

.search-result > svg:first-child {
  color: #0f5fae;
}

.search-result strong {
  display: block;
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
}

.search-result span {
  display: block;
  margin-top: 3px;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 700;
}

.search-result small {
  display: inline-flex;
  width: fit-content;
  margin-top: 8px;
  border-radius: 999px;
  padding: 4px 8px;
  background: rgba(15, 95, 174, 0.08);
  color: #0f5fae;
  font-size: 11px;
  font-weight: 900;
}

.search-status {
  min-height: 150px;
}

.empty-card {
  display: flex;
  min-height: 190px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  color: #0f5fae;
  text-align: center;
}

.empty-card strong {
  margin-top: 12px;
  color: #17202b;
  font-size: 15px;
  font-weight: 900;
}

.empty-card p {
  margin: 6px 0 0;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 700;
}
</style>
