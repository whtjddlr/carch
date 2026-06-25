<template>
  <section class="screen">
    <header class="utility-header blue-gradient">
      <AppBackButton :fallback="backFallback" />
      <button
        v-if="isCardDetail && selectedCard"
        type="button"
        class="card-delete-button"
        style="background: transparent !important; color: #e5484d !important; border: 0 !important; box-shadow: none !important;"
        :disabled="isDeletingCard"
        aria-label="카드 삭제"
        @click="deleteCard"
      >
        <Trash2 :size="18" />
      </button>
      <div v-if="!isCardDetail">
        <h1>{{ pageTitle }}</h1>
      </div>
      <button
        v-if="isTransactionDetail && selectedTransaction"
        type="button"
        class="transaction-delete-button"
        style="background: rgba(229, 72, 77, 0.1) !important; color: #e5484d !important; border: 1px solid rgba(229, 72, 77, 0.24) !important; box-shadow: none !important;"
        :disabled="isDeletingTransaction"
        aria-label="거래내역 삭제"
        @click="deleteTransactionRow"
      >
        <Trash2 :size="18" />
      </button>
    </header>

    <div class="screen-scroll scrollbar-hide utility-body">
      <article v-if="isCardDetail && selectedCard" class="app-card card-detail-card">
        <div class="detail-card-art">
          <img
            v-if="selectedCard.imageUrl"
            :src="selectedCard.imageUrl"
            :alt="selectedCard.name"
            :class="detailCardOrientation ? `is-${detailCardOrientation}` : ''"
            @load="onDetailImageLoad"
          />
          <CreditCard v-else :size="42" />
        </div>
        <div class="detail-head">
          <span>{{ selectedCard.issuer }}</span>
          <h2>{{ selectedCard.name }}</h2>
          <p>{{ selectedCard.titleDescription }}</p>
        </div>
        <div class="detail-grid">
          <div class="metric">
            <span class="metric-ic"><WalletCards :size="16" /></span>
            <div class="metric-text">
              <span>연회비</span>
              <strong>{{ krw(selectedCard.annualFee) }}</strong>
            </div>
          </div>
          <div class="metric">
            <span class="metric-ic"><Target :size="16" /></span>
            <div class="metric-text">
              <span>혜택 조건</span>
              <strong>{{ selectedCard.previousMonthMinSpend ? `전월 ${krw(selectedCard.previousMonthMinSpend)}` : '전월실적 없음' }}</strong>
            </div>
          </div>
          <div class="metric">
            <span class="metric-ic"><Receipt :size="16" /></span>
            <div class="metric-text">
              <span>이번 달 사용</span>
              <strong>{{ krw(selectedCard.spent) }}</strong>
            </div>
          </div>
          <div class="metric">
            <span class="metric-ic"><PieChart :size="16" /></span>
            <div class="metric-text">
              <span>한도</span>
              <strong>{{ krw(selectedCard.limit) }}</strong>
            </div>
          </div>
        </div>
        <section class="benefit-list">
          <div class="benefit-list-head">
            <h3><CheckCircle2 :size="15" /> 대표 혜택</h3>
          </div>
          <div v-if="selectedCardBenefitRows.length" class="benefit-rows">
            <div v-for="row in selectedCardBenefitRows" :key="row.id" class="benefit-row">
              <span class="benefit-emoji">{{ row.icon }}</span>
              <div class="benefit-row-main">
                <div class="benefit-row-top">
                  <strong>{{ row.field }}</strong>
                  <b>{{ row.value }}</b>
                </div>
                <span v-if="row.cap" class="benefit-row-cap">{{ row.cap }}</span>
              </div>
            </div>
          </div>
          <ul v-else>
            <li v-for="benefit in selectedCard.benefits" :key="benefit">{{ benefit }}</li>
          </ul>
        </section>
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
        <a
          v-if="selectedCardOfficialUrl"
          class="primary-button w-100"
          :href="selectedCardOfficialUrl"
          target="_blank"
          rel="noopener noreferrer"
        >
          카드사 상세페이지로 이동
        </a>
        <button v-else class="primary-button w-100" type="button" disabled>
          카드사 상세페이지 준비 중
        </button>
        <p class="helper-text">카드사 공식 페이지에서 신청 조건, 약관, 발급 가능 여부를 확인하세요.</p>
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
        <div class="utility-actions transaction-actions">
          <RouterLink class="primary-button transaction-list-button" to="/transactions">목록으로</RouterLink>
        </div>
      </article>

      <article v-else-if="props.type === 'transaction' && isTransactionLoading" class="app-card utility-card transaction-empty-card">
        <Receipt :size="32" />
        <h2>거래내역을 불러오는 중</h2>
        <p>잠시만 기다려주세요.</p>
      </article>

      <article v-else-if="props.type === 'transaction'" class="app-card utility-card transaction-empty-card">
        <Receipt :size="32" />
        <h2>거래내역을 찾을 수 없어요</h2>
        <p>삭제됐거나 더 이상 사용하지 않는 거래 링크입니다.</p>
        <div class="utility-actions transaction-actions">
          <RouterLink class="primary-button transaction-list-button" to="/transactions">목록으로</RouterLink>
        </div>
      </article>

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
          <div class="profile-avatar">
            <img v-if="displayProfile.avatarUrl" :src="displayProfile.avatarUrl" alt="프로필 사진" />
            <b v-else>{{ displayProfile.initials }}</b>
          </div>
          <div>
            <strong>{{ displayProfile.name }}</strong>
            <span>{{ displayProfile.email }}</span>
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
        <button
          class="app-card setting-row logout-row"
          type="button"
          :disabled="isLoggingOut"
          @click="handleLogout"
        >
          <LogOut :size="18" />
          <div>
            <strong>{{ isLoggingOut ? '로그아웃 중' : '로그아웃' }}</strong>
            <span>현재 계정 세션을 종료합니다.</span>
          </div>
          <ChevronRight :size="17" />
        </button>
      </section>

      <section v-else-if="props.type === 'notificationSettings'" class="notification-settings-view">
        <article
          v-for="item in notificationSettingItems"
          :key="item.id"
          class="app-card notification-setting-row"
        >
          <div class="notification-setting-icon">
            <component :is="notificationIcon(item.id)" :size="18" />
          </div>
          <div>
            <strong>{{ item.label }}</strong>
            <span class="notification-setting-description">{{ item.description }}</span>
          </div>
          <label class="switch-control">
            <input
              v-model="item.enabled"
              type="checkbox"
              :aria-label="`${item.label} 알림`"
            />
            <span aria-hidden="true" />
          </label>
        </article>
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
          <div class="profile-avatar large">
            <img v-if="profileForm.avatarUrl" :src="profileForm.avatarUrl" alt="프로필 사진 미리보기" />
            <b v-else>{{ profileInitials }}</b>
          </div>
          <div>
            <strong>프로필 정보</strong>
            <p>카드 추천과 커뮤니티에 표시되는 기본 정보입니다.</p>
          </div>
        </div>
        <section class="profile-photo-panel">
          <div>
            <strong>프로필 사진</strong>
            <p>1MB 이하의 이미지를 등록할 수 있습니다.</p>
          </div>
          <div class="profile-photo-actions">
            <label class="profile-photo-upload">
              사진 선택
              <input type="file" accept="image/*" @change="handleProfileImageChange" />
            </label>
            <button
              v-if="profileForm.avatarUrl"
              class="muted-button profile-photo-remove"
              type="button"
              @click="removeProfileImage"
            >
              삭제
            </button>
          </div>
          <p v-if="profileImageError" class="field-error">{{ profileImageError }}</p>
        </section>
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
        <article v-if="searchLoading && hasSearchTerm" class="app-card empty-card search-status">
          <Search :size="28" />
          <strong>검색 중입니다</strong>
          <p>카드, 거래, 커뮤니티를 함께 확인하고 있어요.</p>
        </article>
        <article v-else-if="searchError && hasSearchTerm" class="app-card empty-card search-status">
          <Search :size="28" />
          <strong>검색을 불러오지 못했어요</strong>
          <p>잠시 후 다시 시도해 주세요.</p>
        </article>
        <article v-else-if="!hasSearchTerm" class="app-card empty-card search-status search-idle">
          <Search :size="28" />
          <strong>찾고 싶은 내용을 입력해 주세요</strong>
          <p>카드명, 혜택, 가맹점, 거래 내역까지 한 번에 찾을 수 있어요.</p>
          <div class="search-suggestion-chips" aria-label="추천 검색어">
            <button
              v-for="suggestion in searchSuggestions"
              :key="suggestion"
              type="button"
              @click="searchTerm = suggestion"
            >
              {{ suggestion }}
            </button>
          </div>
        </article>
        <template v-else>
          <RouterLink
            v-for="result in searchResults"
            :key="`${result.type}-${result.id}`"
            class="app-card search-result"
            :to="result.path"
          >
            <span class="search-result-media" :class="searchResultMediaClass(result)">
              <img
                v-if="searchResultImage(result)"
                :src="searchResultImage(result)"
                :alt="`${result.title} 카드 이미지`"
                @load="rememberSearchImageOrientation(result, $event)"
              />
              <component v-else :is="result.icon" :size="18" />
            </span>
            <div>
              <strong>{{ result.title }}</strong>
              <span>{{ result.description }}</span>
              <small v-if="result.badge">{{ result.badge }}</small>
            </div>
            <ChevronRight :size="17" />
          </RouterLink>
        </template>
        <article v-if="hasSearchTerm && !searchLoading && !searchError && searchResults.length === 0" class="app-card empty-card">
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

    <footer v-if="isCardDetail && selectedCard" class="detail-cta-bar">
      <a
        v-if="selectedCardOfficialUrl"
        class="primary-button w-100"
        :href="selectedCardOfficialUrl"
        target="_blank"
        rel="noopener noreferrer"
      >
        카드사 상세페이지 보기
      </a>
      <button v-else class="primary-button w-100" type="button" disabled>
        카드사 상세페이지 준비 중
      </button>
    </footer>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Bell,
  CalendarDays,
  CheckCircle2,
  CreditCard,
  Edit3,
  LogOut,
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
import { deleteOwnedCard, deleteTransaction, fetchCard, fetchOwnedCards, fetchSearchResults, fetchTransactions, normalizeCard } from '@/services/api'
import { logout } from '@/services/auth'

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
    notifications: '/cards',
    settings: '/cards',
    notificationSettings: '/settings',
    profile: '/settings',
    security: '/settings',
    search: '/cards',
  }
  return map[props.type] || '/cards'
})

const apiCard = ref(null)
const transactionRows = ref(mockTransactions)
const isTransactionLoading = ref(props.type === 'transaction')
const cardRows = ref(mockCards)
const communityRows = ref(mockCommunityPosts)
const profileSaved = ref(false)
const profileImageError = ref('')
const isLoggingOut = ref(false)
const searchTerm = ref('')
const searchType = ref('all')
const searchRows = ref([])
const searchLoading = ref(false)
const searchError = ref('')
const searchLoaded = ref(false)
const searchImageOrientations = ref({})
const detailCardOrientation = ref('')

function onDetailImageLoad(event) {
  const image = event.target
  detailCardOrientation.value = image.naturalWidth >= image.naturalHeight ? 'landscape' : 'portrait'
}
let searchRequestId = 0
const normalizedSearchTerm = computed(() => searchTerm.value.trim())
const hasSearchTerm = computed(() => normalizedSearchTerm.value.length > 0)
const readNotificationIds = ref(new Set(notifications.filter((notice) => notice.read).map((notice) => notice.id)))

const isCardDetail = computed(() => props.type === 'card')
const needsCard = computed(() => props.type === 'card' || props.type === 'cardApply')
const selectedCard = computed(() => {
  if (!needsCard.value) return null
  return apiCard.value || cardRows.value.find((card) => String(card.id) === String(route.params.id))
})
const selectedCardOfficialUrl = computed(() => cardOfficialUrl(selectedCard.value))
const selectedCardBenefitDetails = computed(() => cardBenefitDetails(selectedCard.value))
const selectedCardBenefitSummary = computed(() => summarizeCardBenefits(selectedCardBenefitDetails.value))
const selectedCardBenefitRows = computed(() => {
  const rows = []
  const seen = new Set()
  selectedCardBenefitDetails.value.forEach((detail) => {
    const raw = compactText(detail.field || detail.scope)
    if (!raw) return
    const { label, icon } = classifyBenefitField(raw)
    if (seen.has(label)) return
    seen.add(label)
    const monthly = detail.conditions.find((condition) => condition.label === '월 한도')
    rows.push({
      id: detail.id,
      field: label,
      icon,
      value: detail.valueLabel,
      cap: monthly ? `월 최대 ${monthly.value}` : '',
    })
  })
  return rows.slice(0, 5)
})

// 혜택 분야 원문을 깔끔한 카테고리 라벨 + 어울리는 아이콘으로 분류
function classifyBenefitField(raw) {
  const text = String(raw || '')
  const rules = [
    [/배달/, '배달앱', '🛵'],
    [/카페|커피|베이커리|디저트|스타벅스/, '카페', '☕'],
    [/음식|외식|식당|맛집|푸드|레스토랑/, '음식점', '🍽️'],
    [/편의점/, '편의점', '🏪'],
    [/교육|학원|학습|어학|등록금|학교|유치원/, '교육', '✏️'],
    [/해외|국내외|글로벌/, '국내외', '🌐'],
    [/항공|여행|면세|숙박|호텔/, '여행', '✈️'],
    [/통신|휴대폰|모바일|요금제/, '통신', '📱'],
    [/주유|충전소/, '주유', '⛽'],
    [/교통|대중교통|지하철|버스|택시|주차/, '교통', '🚇'],
    [/병원|의료|약국|건강|치과/, '의료', '🏥'],
    [/마트|마켓|백화점|쿠팡|이마트|온라인쇼핑/, '쇼핑', '🛒'],
    [/쇼핑|아울렛/, '쇼핑', '🛍️'],
    [/뷰티|화장품|미용/, '뷰티', '💄'],
    [/영화|공연|도서|서점|문화/, '문화', '🎬'],
    [/구독|스트리밍|넷플릭스|ott/i, '구독', '📺'],
    [/관리비|공과금|아파트|관리/, '생활', '🏠'],
    [/주말|평일|상시|언제나|전월|기본/, '기본 적립', '💰'],
  ]
  for (const [re, label, icon] of rules) {
    if (re.test(text)) return { label, icon }
  }
  const clean = text.replace(/\s*(업종|가맹점|에서|최대|이용|결제|할인|적립).*$/, '').trim()
  return { label: clean || '기타', icon: '💳' }
}

function cardOfficialUrl(card) {
  const rawUrl = String(card?.officialUrl || card?.official_url || card?.naverUrl || card?.naver_url || '').trim()
  if (!rawUrl) return ''
  if (/^https?:\/\//i.test(rawUrl)) return rawUrl
  return `https://${rawUrl}`
}

function numberValue(value) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

function compactText(value) {
  return String(value || '').replace(/\s+/g, ' ').trim()
}

function benefitScopeLabel(item = {}) {
  const scope = compactText(item.scope || item.category || item.name)
  if (scope) return scope
  const category = Array.isArray(item.categories) ? compactText(item.categories[0]) : ''
  return category || '공통 혜택'
}

function benefitFieldLabel(item = {}) {
  const scope = benefitScopeLabel(item)
  const text = scope.toLowerCase()
  if (/배달/.test(scope)) return '배달앱'
  if (/음식|외식|식당/.test(scope)) return '음식점'
  if (/커피|카페|스타벅스/.test(scope)) return '카페'
  if (/쇼핑|쿠팡|마켓|멤버십/.test(scope)) return '쇼핑'
  if (/편의점|gs25|cu|세븐/.test(text)) return '편의점'
  return scope.replace(/\s*가맹점$/, '')
}

function benefitValueLabel(item = {}) {
  const type = String(item.type || item.benefitType || item.benefit_type || '')
  const rate = numberValue(item.ratePercent ?? item.rate_percent)
  const amount = numberValue(item.amountKrw ?? item.amount_krw)
  if (rate > 0) {
    const verb = type.includes('point') ? '적립' : '할인'
    return `최대 ${Number(rate.toFixed(1)).toString()}% ${verb}`
  }
  if (amount > 0) return `${krw(amount)} 할인`
  return compactText(item.label) || '혜택 조건 확인'
}

function benefitCaption(item = {}) {
  const merchants = Array.isArray(item.targetMerchants) ? item.targetMerchants.map(compactText).filter(Boolean) : []
  if (merchants.length) return `적용처: ${merchants.slice(0, 3).join(', ')}`
  const categories = Array.isArray(item.categories) ? item.categories.map(compactText).filter(Boolean) : []
  if (categories.length) return `적용 분야: ${categories.slice(0, 3).join(', ')}`
  const line = Array.isArray(item.conditionLines) ? compactText(item.conditionLines[0]) : ''
  return line
}

function benefitPaymentCondition(item = {}) {
  const excluded = new Set(item.excludedPaymentMethods || item.excluded_payment_methods || [])
  const rules = item.paymentMethodRules || item.payment_method_rules || {}
  if (excluded.has('installment') || rules.installmentBenefitEligible === false) return '할부 제외'
  if (excluded.has('interest_free_installment') || rules.interestFreeInstallmentEligible === false) return '무이자 제외'
  if (rules.source && rules.source !== 'not_detected') return '결제방식 확인됨'
  return ''
}

function benefitConditions(item = {}, card = {}) {
  const previousMonth = numberValue(item.requiredPreviousMonthSpendKrw ?? item.required_previous_month_spend_krw ?? card.previousMonthMinSpend ?? card.previous_month_min_spend)
  const monthlyLimit = numberValue(item.monthlyBenefitLimitKrw ?? item.monthly_benefit_limit_krw)
  const yearlyLimit = numberValue(item.yearlyBenefitLimitKrw ?? item.yearly_benefit_limit_krw)
  const perTransactionLimit = numberValue(
    item.perTransactionLimitKrw
      ?? item.per_transaction_limit_krw
      ?? item.perTransactionBenefitLimitKrw
      ?? item.per_transaction_benefit_limit_krw,
  )
  const minPayment = numberValue(item.minPaymentAmountKrw ?? item.min_payment_amount_krw)
  const paymentCondition = benefitPaymentCondition(item)
  const conditions = []

  if (monthlyLimit > 0) conditions.push({ label: '월 한도', value: krw(monthlyLimit) })
  if (perTransactionLimit > 0) conditions.push({ label: '1회 한도', value: krw(perTransactionLimit) })
  if (yearlyLimit > 0) conditions.push({ label: '연 한도', value: krw(yearlyLimit) })
  if (minPayment > 0) conditions.push({ label: '최소 결제', value: `${krw(minPayment)} 이상` })
  conditions.push({ label: '전월 실적', value: previousMonth > 0 ? krw(previousMonth) : '없음' })
  if (paymentCondition) conditions.push({ label: '결제 조건', value: paymentCondition })

  return conditions
}

function benefitBadges(item = {}) {
  const badges = []
  if (item.hasSharedMonthlyLimit || item.has_shared_monthly_limit) badges.push('통합한도 포함')
  if (item.verified) badges.push('검증됨')
  if (item.needsManualReview || item.needs_manual_review || item.manualInputAllowed) badges.push('확인 필요')
  return badges
}

function cardBenefitDetails(card = {}) {
  const items = Array.isArray(card?.benefitItems) ? card.benefitItems : (card?.benefit_items || [])
  return items
    .map((item, index) => ({
      id: item.id || item.benefitId || item.benefit_id || `${card.id || 'card'}-${index}`,
      scope: benefitScopeLabel(item),
      field: benefitFieldLabel(item),
      valueLabel: benefitValueLabel(item),
      caption: benefitCaption(item),
      conditions: benefitConditions(item, card),
      badges: benefitBadges(item),
    }))
    .slice(0, 5)
}

function conditionKey(condition = {}) {
  return `${condition.label}:${condition.value}`
}

function commonBenefitConditions(details = []) {
  if (!details.length) return []
  const [first, ...rest] = details
  return first.conditions.filter((condition) => (
    rest.every((detail) => detail.conditions.some((item) => conditionKey(item) === conditionKey(condition)))
  ))
}

function uniqueBenefitFields(details = []) {
  const fields = []
  const seen = new Set()
  details.forEach((detail) => {
    const field = compactText(detail.field || detail.scope)
    if (!field || seen.has(field)) return
    seen.add(field)
    fields.push(field)
  })
  return fields.slice(0, 6)
}

function summarizeCardBenefits(details = []) {
  const first = details[0] || {}
  const badgeSet = new Set()
  const hasManualReview = details.some((detail) => detail.badges.includes('확인 필요'))
  const allVerified = details.length > 0 && details.every((detail) => detail.badges.includes('검증됨'))
  const hasSharedLimit = details.some((detail) => detail.badges.includes('통합한도 포함'))

  if (allVerified) badgeSet.add('검증됨')
  if (hasManualReview) badgeSet.add('일부 확인 필요')
  if (hasSharedLimit) badgeSet.add('통합한도 포함')

  return {
    title: '공통 조건',
    valueLabel: first.valueLabel || '혜택 조건 확인',
    commonConditions: commonBenefitConditions(details),
    fields: uniqueBenefitFields(details),
    badges: [...badgeSet],
  }
}

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

const isTransactionDetail = computed(() => props.type === 'transaction' && !!selectedTransaction.value)
const isDeletingTransaction = ref(false)

async function deleteTransactionRow() {
  if (!selectedTransaction.value || isDeletingTransaction.value) return
  if (!window.confirm('이 거래내역을 삭제할까요?')) return
  isDeletingTransaction.value = true
  try {
    await deleteTransaction(selectedTransaction.value.id)
    router.replace('/transactions')
  } catch (error) {
    isDeletingTransaction.value = false
    window.alert('거래내역을 삭제하지 못했습니다.')
  }
}

const transactionCardName = computed(() => {
  const card = cardRows.value.find((item) => String(item.id) === String(selectedTransaction.value?.cardId))
  return card?.name || '카드 정보 없음'
})

const PROFILE_SETTINGS_KEY = 'carch.profile.v1'
const PROFILE_IMAGE_MAX_BYTES = 1024 * 1024

function profileInitialsFrom(name, email) {
  const source = String(name || email || '').trim()
  if (!source) return user.initials || '김'
  const compact = source.replace(/\s+/g, '')
  return compact.slice(0, 2).toUpperCase()
}

function readProfileSettings() {
  const defaults = {
    name: user.name,
    email: user.email,
    phone: user.phone,
    initials: user.initials,
    avatarUrl: '',
  }
  if (typeof window === 'undefined') return defaults

  try {
    const saved = JSON.parse(window.localStorage.getItem(PROFILE_SETTINGS_KEY) || '{}')
    return {
      ...defaults,
      name: saved.name || defaults.name,
      email: saved.email || defaults.email,
      phone: saved.phone || defaults.phone,
      initials: saved.initials || defaults.initials,
      avatarUrl: saved.avatarUrl || '',
    }
  } catch (error) {
    return defaults
  }
}

const savedProfile = readProfileSettings()
const profileForm = reactive({
  ...savedProfile,
})

const profileInitials = computed(() => profileInitialsFrom(profileForm.name, profileForm.email))
const displayProfile = computed(() => ({
  name: user.name,
  email: user.email,
  phone: user.phone,
  ...profileForm,
  initials: profileInitials.value,
}))

const applySteps = [
  { title: '카드 정보 확인', description: '연회비, 혜택 조건, 대표 혜택을 검토합니다.' },
  { title: '본인 인증', description: '실제 서비스에서는 휴대폰 또는 공동인증서 인증이 들어갑니다.' },
  { title: '신청 제출', description: '심사 결과와 발급 상태를 알림으로 확인합니다.' },
]

const firstTransactionPath = computed(() => {
  const id = transactionRows.value[0]?.id || mockTransactions[0]?.id || 't1'
  return `/transactions/${id}`
})

const notificationItems = computed(() =>
  notifications.map((notice) => ({
    ...notice,
    read: readNotificationIds.value.has(notice.id),
    route: {
      payment: firstTransactionPath.value,
      budget: '/budget/current',
      recommend: '/recommendations/new',
    }[notice.type],
  })),
)

const NOTIFICATION_SETTINGS_KEY = 'carch.notificationSettings.v1'
const defaultNotificationSettings = [
  { id: 'payment', label: '결제 알림', description: '카드 승인과 취소 내역을 받습니다.', enabled: true },
  { id: 'budget', label: '예산 경고', description: '카테고리 예산 임박과 초과 알림을 받습니다.', enabled: true },
  { id: 'recommend', label: '추천 인사이트', description: '카드 교체와 혜택 추천을 받습니다.', enabled: true },
  { id: 'community', label: '커뮤니티 반응', description: '내 글의 댓글과 좋아요 알림을 받습니다.', enabled: false },
]

function readNotificationSettings() {
  if (typeof window === 'undefined') {
    return defaultNotificationSettings.map((item) => ({ ...item }))
  }

  try {
    const savedItems = JSON.parse(window.localStorage.getItem(NOTIFICATION_SETTINGS_KEY) || '[]')
    const savedMap = new Map(
      Array.isArray(savedItems)
        ? savedItems.map((item) => [item.id, Boolean(item.enabled)])
        : [],
    )
    return defaultNotificationSettings.map((item) => ({
      ...item,
      enabled: savedMap.has(item.id) ? savedMap.get(item.id) : item.enabled,
    }))
  } catch (error) {
    return defaultNotificationSettings.map((item) => ({ ...item }))
  }
}

const notificationSettingItems = ref(readNotificationSettings())

watch(
  notificationSettingItems,
  (items) => {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(
      NOTIFICATION_SETTINGS_KEY,
      JSON.stringify(items.map(({ id, enabled }) => ({ id, enabled }))),
    )
  },
  { deep: true },
)

const settingItems = [
  { label: '알림 설정', description: '결제, 예산, 추천 알림 관리', path: '/settings/notifications', icon: Bell },
  { label: '보안', description: '로그인과 개인정보 보호 설정', path: '/settings/security', icon: Lock },
]

const securityItems = [
  { label: '로그인 보호', description: '현재 기기에서 안전하게 로그인 중입니다.', icon: Lock },
  { label: '개인정보 관리', description: '프로필 정보와 알림 권한을 분리해 관리합니다.', icon: User },
  { label: '데이터 보관', description: '분석 기록을 안전하게 보관합니다.', icon: ShieldCheck },
]

const searchTypes = [
  { label: '전체', value: 'all' },
  { label: '카드', value: 'card' },
  { label: '거래', value: 'transaction' },
  { label: '커뮤니티', value: 'community' },
]
const searchSuggestions = ['LOCA LIKIT Eat', '쇼핑 할인', '컴포즈커피']

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
    imageUrl: card.imageUrl,
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
  const term = normalizedSearchTerm.value.toLowerCase()
  if (!term) return []
  return searchableItems.value
    .filter((item) => searchType.value === 'all' || item.type === searchType.value)
    .filter((item) => `${item.title} ${item.description}`.toLowerCase().includes(term))
    .slice(0, 12)
})

const searchResults = computed(() => {
  if (!hasSearchTerm.value) return []
  if (props.type === 'search' && searchLoaded.value) {
    return searchRows.value.map((item) => ({
      ...item,
      id: item.id || `${item.type}-${item.title}`,
      path: item.path || '/search',
      description: item.description || item.badge || '',
      imageUrl: item.imageUrl || item.image_url || item.meta?.imageUrl || '',
      imageOrientation: item.imageOrientation || item.image_orientation || item.meta?.imageOrientation || '',
      icon: searchIconMap[item.type] || Search,
    }))
  }
  return localSearchResults.value
})

function searchResultImage(result) {
  if (result.type !== 'card') return ''
  return result.imageUrl || result.image_url || ''
}

function searchResultKey(result) {
  return `${result.type}-${result.id || result.title}`
}

function searchResultOrientation(result) {
  return result.imageOrientation || result.image_orientation || searchImageOrientations.value[searchResultKey(result)] || ''
}

function searchResultMediaClass(result) {
  const hasImage = Boolean(searchResultImage(result))
  const orientation = hasImage ? searchResultOrientation(result) : ''
  return {
    'has-card-image': hasImage,
    'is-landscape': orientation === 'landscape',
    'is-portrait': orientation === 'portrait',
  }
}

function rememberSearchImageOrientation(result, event) {
  const image = event.target
  const orientation = image.naturalWidth >= image.naturalHeight ? 'landscape' : 'portrait'
  searchImageOrientations.value = {
    ...searchImageOrientations.value,
    [searchResultKey(result)]: orientation,
  }
}

const content = computed(() => {
  const map = {
    card: { title: '카드 상세', description: '카드별 사용 현황', body: `선택한 카드 ID: ${route.params.id}`, icon: CreditCard },
    cardApply: { title: '카드 신청', description: '신청 정보를 확인하세요.', body: '카드 목록에서 신청할 카드를 다시 선택해주세요.', icon: CreditCard },
    transaction: { title: '거래 상세', description: '거래처와 결제 정보를 확인하세요.', body: '거래내역을 확인하세요.', icon: Receipt },
    notifications: { title: '알림', description: '중요한 카드 알림', body: '결제 알림, 예산 경고, 추천 알림을 모아 보여줍니다.', icon: Bell },
    settings: { title: '설정', description: '계정과 앱 설정', body: '계정과 앱 설정 메뉴입니다.', icon: Settings },
    notificationSettings: { title: '알림 설정', description: '받을 알림을 선택하세요.', body: '알림 수신 범위를 조정합니다.', icon: Bell },
    profile: { title: '프로필 수정', description: '내 정보를 관리하세요.', body: '프로필 정보를 입력하고 저장할 수 있습니다.', icon: User },
    security: { title: '보안', description: '로그인과 개인정보 보호 설정', body: '보안 설정을 확인하세요.', icon: ShieldCheck },
    search: { title: '검색', description: '거래와 카드를 검색하세요.', body: '검색어를 입력하세요.', icon: Search },
  }
  return map[props.type] || { title: 'CARCH', description: '경로 확인', body: '이동 경로를 다시 확인해주세요.', icon: CreditCard }
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

function writeProfileSettings() {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(
    PROFILE_SETTINGS_KEY,
    JSON.stringify({
      name: profileForm.name,
      email: profileForm.email,
      phone: profileForm.phone,
      initials: profileInitials.value,
      avatarUrl: profileForm.avatarUrl,
    }),
  )
}

function saveProfileDraft() {
  try {
    profileForm.initials = profileInitials.value
    writeProfileSettings()
  } catch (error) {
    profileImageError.value = '프로필을 저장하지 못했습니다. 이미지 용량을 줄여보세요.'
    return
  }
  profileSaved.value = true
  window.setTimeout(() => {
    profileSaved.value = false
  }, 1200)
}

function handleProfileImageChange(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  profileImageError.value = ''
  if (!file) return

  if (!file.type.startsWith('image/')) {
    profileImageError.value = '이미지 파일만 등록할 수 있습니다.'
    return
  }

  if (file.size > PROFILE_IMAGE_MAX_BYTES) {
    profileImageError.value = '1MB 이하 이미지로 등록해 주세요.'
    return
  }

  const reader = new FileReader()
  reader.onload = () => {
    profileForm.avatarUrl = String(reader.result || '')
  }
  reader.onerror = () => {
    profileImageError.value = '이미지를 불러오지 못했습니다.'
  }
  reader.readAsDataURL(file)
}

function removeProfileImage() {
  profileForm.avatarUrl = ''
  profileImageError.value = ''
}

async function handleLogout() {
  if (isLoggingOut.value) return
  isLoggingOut.value = true
  try {
    await logout()
    router.replace({ name: 'Login', query: { next: '/cards' } })
  } catch (error) {
    isLoggingOut.value = false
    window.alert('로그아웃을 완료하지 못했습니다.')
  }
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
  const query = normalizedSearchTerm.value
  const requestId = ++searchRequestId
  if (!query) {
    searchLoading.value = false
    searchError.value = ''
    searchRows.value = []
    searchLoaded.value = false
    return
  }
  searchLoading.value = true
  searchError.value = ''

  try {
    const data = await fetchSearchResults({
      q: query,
      type: searchType.value,
      limit: searchType.value === 'card' ? 50 : 20,
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
      const [cardResult, transactionResult] = await Promise.allSettled([
        fetchCard(route.params.id),
        fetchTransactions({ cardId: route.params.id }),
      ])
      if (cardResult.status === 'fulfilled') {
        const transactions = transactionResult.status === 'fulfilled' ? transactionResult.value : mockTransactions
        apiCard.value = normalizeCard(cardResult.value, 0, transactions)
      } else {
        throw cardResult.reason
      }
    }

    if (props.type === 'transaction' || props.type === 'notifications') {
      const [transactions, ownedCards] = await Promise.all([
        fetchTransactions(),
        fetchOwnedCards(),
      ])
      transactionRows.value = transactions
      cardRows.value = ownedCards.map((card, index) => normalizeCard(card, index, transactions))
    }
  } catch (error) {
    console.warn('상세 화면 API를 불러오지 못해 mock 데이터를 사용합니다.', error)
  } finally {
    if (props.type === 'transaction') {
      isTransactionLoading.value = false
    }
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
  background: transparent !important;
  color: #e5484d !important;
  box-shadow: none !important;
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

.transaction-actions {
  justify-content: center;
  margin-top: 18px;
}

.transaction-actions .transaction-list-button {
  flex: 0 1 176px;
  min-width: 176px;
  border: 0 !important;
  background: #24364f !important;
  color: #fff !important;
  box-shadow: 0 10px 22px rgba(36, 54, 79, 0.18) !important;
}

.transaction-delete-button {
  display: inline-flex;
  width: 38px;
  height: 38px;
  align-items: center;
  justify-content: center;
  margin-left: auto;
  border: 1px solid rgba(229, 72, 77, 0.24) !important;
  border-radius: 14px;
  background: rgba(229, 72, 77, 0.1) !important;
  color: #e5484d !important;
  box-shadow: none !important;
}

.transaction-delete-button svg {
  color: #e5484d !important;
  stroke: #e5484d !important;
}

.transaction-delete-button:disabled {
  opacity: 0.45;
}

.card-detail-card,
.apply-card,
.transaction-detail-card,
.form-card,
.report-overview-card,
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

.card-detail-card .detail-card-art {
  overflow: visible;
  border-radius: 0;
  background: transparent;
}

.card-detail-card .detail-card-art img {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 280px;
  height: 176px;
  max-width: none;
  object-fit: cover;
  border-radius: 12px;
  transform: translate(-50%, -50%);
  filter: drop-shadow(0 16px 24px rgba(16, 24, 40, 0.22));
  animation: detail-card-rotate-in-landscape 0.6s cubic-bezier(0.34, 1.08, 0.4, 1) both;
}

.card-detail-card .detail-card-art img.is-portrait {
  width: 176px;
  height: 280px;
  transform: translate(-50%, -50%) rotate(-90deg);
  animation: detail-card-rotate-in 0.6s cubic-bezier(0.34, 1.08, 0.4, 1) both;
}

@keyframes detail-card-rotate-in-landscape {
  from {
    transform: translate(-50%, -50%) rotate(90deg);
    opacity: 0;
  }
  to {
    transform: translate(-50%, -50%) rotate(0deg);
    opacity: 1;
  }
}

@keyframes detail-card-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes detail-card-rotate-in {
  from {
    transform: translate(-50%, -50%) rotate(0deg);
    opacity: 0;
  }
  to {
    transform: translate(-50%, -50%) rotate(-90deg);
    opacity: 1;
  }
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

/* Card detail — readable metric panel with icons */
.card-detail-card .detail-grid {
  gap: 14px 10px;
  margin-top: 18px;
  padding: 15px 14px;
  border-radius: 16px;
  background: #f6faff;
}

.card-detail-card .detail-grid .metric {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 0;
}

.card-detail-card .detail-grid .metric-ic {
  display: grid;
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  place-items: center;
  border-radius: 9px;
  background: rgba(15, 95, 174, 0.1);
  color: #0f5fae;
}

.card-detail-card .detail-grid .metric-text {
  min-width: 0;
  padding: 0;
}

.card-detail-card .detail-grid .metric-text span {
  color: #7c8794;
  font-size: 11px;
  font-weight: 800;
}

.card-detail-card .detail-grid .metric-text strong {
  margin-top: 1px;
  color: #17202b;
  font-size: 15px;
  font-weight: 700;
  white-space: nowrap;
}

/* Sticky bottom CTA bar (does not scroll with content) */
.detail-cta-bar {
  flex-shrink: 0;
  padding: 12px 20px;
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
  background: var(--carch-page);
  border-top: 1px solid rgba(36, 54, 79, 0.08);
  box-shadow: 0 -8px 22px rgba(16, 24, 40, 0.06);
}

.utility-body:has(+ .detail-cta-bar) {
  padding-bottom: 18px;
}

.benefit-list {
  margin: 16px 0;
}

.benefit-list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}

.benefit-list h3,
.report-section h2 {
  margin: 0;
  color: #17202b;
  font-size: 15px;
  font-weight: 900;
}

.benefit-list h3 {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.benefit-list h3 svg {
  color: #0f5fae;
}

.benefit-rows {
  display: flex;
  flex-direction: column;
}

.benefit-row {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 11px 2px;
  border-bottom: 1px solid rgba(36, 54, 79, 0.07);
}

.benefit-row:last-child {
  border-bottom: 0;
}

.benefit-emoji {
  flex-shrink: 0;
  font-size: 20px;
  line-height: 1;
}

.benefit-row-main {
  flex: 1;
  min-width: 0;
}

.benefit-row-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}

.benefit-row-top strong {
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
}

.benefit-row-top b {
  flex-shrink: 0;
  color: #0f5fae;
  font-size: 13px;
  font-weight: 750;
}

.benefit-row-cap {
  display: block;
  margin-top: 2px;
  color: #8a95a3;
  font-size: 11px;
  font-weight: 800;
}

.benefit-list-head > span {
  color: #0f5fae;
  font-size: 11px;
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

.benefit-summary-stack {
  display: grid;
  gap: 9px;
}

.benefit-summary-card,
.benefit-fields-card {
  border: 1px solid rgba(15, 95, 174, 0.1);
  border-radius: 16px;
  padding: 12px;
  background: #f8fbff;
}

.benefit-detail-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.benefit-detail-top span {
  min-width: 0;
  color: #526071;
  font-size: 12px;
  font-weight: 850;
  line-height: 1.35;
  word-break: keep-all;
}

.benefit-detail-top strong {
  flex: 0 0 auto;
  color: #0f5fae;
  font-size: 14px;
  font-weight: 950;
  line-height: 1.25;
}

.benefit-summary-card p {
  margin: 7px 0 0;
  color: #6e7885;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.45;
  word-break: keep-all;
}

.benefit-condition-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
  margin-top: 10px;
}

.benefit-condition-grid div {
  min-width: 0;
  border-radius: 0;
  padding: 8px 0 0;
  background: transparent;
  box-shadow: none;
  border-top: 1px solid rgba(36, 54, 79, 0.08);
}

.benefit-condition-grid span {
  display: block;
  color: #8a95a3;
  font-size: 10px;
  font-weight: 850;
}

.benefit-condition-grid b {
  display: block;
  margin-top: 2px;
  color: #17202b;
  font-size: 12px;
  font-weight: 950;
  line-height: 1.25;
}

.benefit-badge-row {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 9px;
}

.benefit-badge-row span {
  border-radius: 999px;
  padding: 4px 7px;
  background: rgba(0, 140, 149, 0.1);
  color: #007780;
  font-size: 10px;
  font-weight: 900;
}

.benefit-fields-card > span {
  display: block;
  color: #6e7885;
  font-size: 11px;
  font-weight: 850;
}

.benefit-field-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.benefit-field-row b {
  border-radius: 999px;
  padding: 6px 9px;
  background: #fff;
  color: #24445f;
  font-size: 12px;
  font-weight: 900;
  box-shadow: inset 0 0 0 1px rgba(36, 54, 79, 0.07);
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
.notification-settings-view,
.settings-view,
.search-view {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.report-card-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.report-overview-card {
  display: flex;
  min-width: 0;
  min-height: auto;
  flex-direction: column;
  align-items: stretch;
  overflow: hidden;
  border: 1px solid rgba(36, 54, 79, 0.08);
  border-radius: 18px !important;
  padding: 16px !important;
  background: rgba(251, 253, 255, 0.86);
}

.report-kicker,
.report-overview-card small {
  color: #0f5fae;
  font-size: 11px;
  font-weight: 900;
}

.report-overview-card small {
  margin-top: 6px;
}

.report-overview-card strong {
  display: block;
  margin-top: 8px;
  color: #17202b;
  font-size: 15px;
  font-weight: 950;
  line-height: 1.25;
}

.report-overview-card > b {
  display: block;
  margin-top: 7px;
  color: #17202b;
  font-size: 24px;
  font-weight: 900;
  line-height: 1.08;
}

.report-overview-card p {
  margin: 9px 0 0;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.45;
  word-break: keep-all;
}

.report-recommend-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 122px;
  grid-template-areas:
    "kicker art"
    "sub art"
    "title art"
    "amount art"
    "copy copy"
    "action action";
  column-gap: 12px;
  align-items: center;
}

.report-recommend-card .report-kicker {
  grid-area: kicker;
}

.report-recommend-card small {
  grid-area: sub;
}

.report-recommend-card strong {
  grid-area: title;
}

.report-recommend-card > b {
  grid-area: amount;
}

.report-recommend-card .report-card-art {
  grid-area: art;
}

.report-recommend-card p {
  grid-area: copy;
}

.report-recommend-card .report-mini-button {
  grid-area: action;
}

.report-card-art {
  display: grid;
  height: 82px;
  place-items: center;
  margin: 10px 0 4px;
}

.report-card-art img {
  display: block;
  max-width: 118px;
  max-height: 78px;
  object-fit: contain;
  filter: drop-shadow(0 10px 16px rgba(36, 54, 79, 0.14));
}

.report-mini-button {
  display: inline-flex;
  min-height: 36px;
  align-items: center;
  justify-content: center;
  margin-top: auto;
  border-radius: 11px;
  padding: 0 12px;
  background: rgba(15, 95, 174, 0.08);
  color: #0f5fae;
  font-size: 11px;
  font-weight: 950;
  text-decoration: none;
}

.report-spending-card em {
  display: block;
  margin-top: 5px;
  color: #0f5fae;
  font-size: 11px;
  font-style: normal;
  font-weight: 900;
}

.report-donut-panel {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr);
  gap: 14px;
  align-items: center;
  margin: 14px 0 14px;
  border-radius: 16px;
  padding: 12px;
  background: rgba(232, 241, 251, 0.55);
}

.report-donut {
  position: relative;
  display: grid;
  width: 96px;
  aspect-ratio: 1;
  place-items: center;
  border-radius: 50%;
  box-shadow: 0 12px 24px rgba(36, 54, 79, 0.08);
}

.report-donut::after {
  position: absolute;
  inset: 19px;
  border-radius: inherit;
  background: #fff;
  content: '';
}

.report-donut span,
.report-donut b {
  position: relative;
  z-index: 1;
  display: block;
  max-width: 48px;
  overflow: hidden;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.report-donut span {
  color: #8a9aad;
  font-size: 9px;
  font-weight: 900;
}

.report-donut b {
  color: #17202b;
  font-size: 12px;
  font-weight: 950;
}

.report-donut-legend {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 8px;
  padding: 0;
  margin: 0;
  list-style: none;
}

.report-donut-legend li {
  display: grid;
  grid-template-columns: 9px minmax(0, 1fr) auto;
  gap: 9px;
  align-items: center;
  min-width: 0;
  min-height: 20px;
}

.report-donut-legend i {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.report-donut-legend span,
.report-donut-legend b {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.report-donut-legend span {
  color: #4a5663;
  font-size: 11px;
  font-weight: 900;
}

.report-donut-legend b {
  color: #8a9aad;
  font-size: 11px;
  font-weight: 850;
  text-align: right;
}

.report-card-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.report-card-title-row a {
  display: inline-flex;
  width: 26px;
  height: 26px;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(15, 95, 174, 0.08);
  color: #0f5fae;
}

.report-planner-card > strong {
  margin-top: 8px;
  font-size: 19px;
}

.report-calendar {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 4px;
  margin-top: 13px;
}

.report-weekday,
.report-day {
  display: inline-flex;
  aspect-ratio: 1;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 10px;
  font-weight: 900;
}

.report-weekday {
  color: #8a9aad;
}

.report-day {
  color: #4a5663;
}

.report-day.empty {
  visibility: hidden;
}

.report-day.active {
  background: rgba(15, 95, 174, 0.1);
  color: #0f5fae;
}

.report-day.latest {
  background: #0f5fae;
  color: #fff;
}

.report-plan-chip {
  display: grid;
  gap: 4px;
  margin-top: auto;
  border-radius: 13px;
  padding: 10px 11px;
  background: rgba(15, 95, 174, 0.07);
}

.report-plan-chip.warning {
  background: rgba(217, 45, 32, 0.08);
}

.report-plan-chip span {
  color: #8a9aad;
  font-size: 10px;
  font-weight: 900;
}

.report-plan-chip b {
  color: #17202b;
  font-size: 12px;
  font-weight: 950;
  line-height: 1.3;
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

@media (max-width: 480px) {
  .report-card-grid {
    grid-template-columns: 1fr;
  }

  .report-planner-card {
    grid-column: 1 / -1;
  }
}

@media (max-width: 360px) {
  .report-donut-panel {
    grid-template-columns: 1fr;
    justify-items: center;
  }

  .report-donut-legend {
    width: 100%;
  }
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

.notification-setting-row {
  display: grid;
  grid-template-columns: 38px 1fr 52px;
  gap: 12px;
  align-items: center;
  padding: 15px;
}

.notification-setting-icon {
  display: inline-flex;
  width: 38px;
  height: 38px;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: #e8f1ff;
  color: #0f5fae;
}

.notification-setting-row strong {
  display: block;
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
}

.notification-setting-description {
  display: block;
  margin-top: 4px;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.4;
}

.switch-control {
  position: relative;
  display: inline-flex;
  width: 48px;
  height: 28px;
  flex-shrink: 0;
  justify-self: end;
  cursor: pointer;
}

.switch-control input {
  position: absolute;
  inset: 0;
  margin: 0;
  opacity: 0;
  cursor: pointer;
}

.switch-control span {
  width: 100%;
  height: 100%;
  border-radius: 999px;
  background: #dbe4ee;
  transition: background 0.18s ease;
}

.switch-control span::after {
  display: block;
  width: 22px;
  height: 22px;
  margin: 3px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 8px rgba(23, 32, 43, 0.16);
  transition: transform 0.18s ease;
  content: '';
}

.switch-control input:checked + span {
  background: #0f5fae;
}

.switch-control input:checked + span::after {
  transform: translateX(20px);
}

.switch-control input:focus-visible + span {
  outline: 3px solid rgba(15, 95, 174, 0.18);
  outline-offset: 3px;
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
  overflow: hidden;
}

.profile-avatar img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-avatar b {
  color: inherit;
  font-size: inherit;
  font-weight: inherit;
}

.profile-avatar.large {
  width: 56px;
  height: 56px;
  border-radius: 18px;
  font-size: 20px;
}

.profile-photo-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  border: 1px solid #e8eef6;
  border-radius: 14px;
  padding: 14px;
  background: #f7f9fc;
}

.profile-photo-panel strong {
  display: block;
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
}

.profile-photo-panel p {
  margin: 4px 0 0;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 700;
}

.profile-photo-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.profile-photo-upload,
.profile-photo-remove {
  display: inline-flex;
  min-height: 38px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 0 14px;
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
}

.profile-photo-upload {
  border: 1px solid rgba(15, 95, 174, 0.22);
  background: #fff;
  color: #0f5fae;
}

.profile-photo-upload input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.profile-photo-remove {
  color: #d92d20;
}

.field-error {
  color: #d92d20 !important;
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

.logout-row {
  width: 100%;
  border: 0;
  background: #fff;
  text-align: left;
  cursor: pointer;
}

.logout-row > svg:first-child,
.logout-row strong,
.logout-row > svg:last-child {
  color: #d92d20;
}

.logout-row:disabled {
  opacity: 0.66;
  cursor: wait;
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
  grid-template-columns: 88px 1fr 18px;
  gap: 12px;
  align-items: center;
  padding: 14px;
  color: inherit;
  text-decoration: none;
}

.search-result-media {
  display: inline-flex;
  width: 44px;
  height: 44px;
  align-items: center;
  justify-content: center;
  justify-self: center;
  border-radius: 12px;
  background: #e8f1ff;
  color: #0f5fae;
  overflow: hidden;
}

.search-result-media.has-card-image {
  width: 76px;
  height: 56px;
  justify-self: center;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  overflow: visible;
}

.search-result-media.has-card-image.is-landscape {
  width: 70px;
  height: 44px;
}

.search-result-media.has-card-image.is-portrait {
  width: 58px;
  height: 66px;
}

.search-result-media img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  filter: drop-shadow(0 4px 8px rgba(23, 32, 43, 0.12));
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

.search-idle {
  border: 1px solid rgba(36, 54, 79, 0.08) !important;
  border-radius: 18px !important;
  background: rgba(255, 255, 255, 0.86) !important;
  box-shadow: 0 12px 24px rgba(36, 54, 79, 0.055) !important;
}

.search-suggestion-chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 7px;
  margin-top: 14px;
}

.search-suggestion-chips button {
  min-height: 34px;
  border-radius: 999px;
  padding: 0 12px;
  background: rgba(15, 95, 174, 0.08);
  color: #0f5fae;
  font-size: 11px;
  font-weight: 900;
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
