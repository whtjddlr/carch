import axios from 'axios'
import {
  cards as seedCards,
  clone,
  communityPosts as seedCommunityPosts,
  recommendations as seedRecommendations,
  transactions as seedTransactions,
  user as seedUser,
} from '@/data/mockData'

const envNumber = (value, fallback) => {
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
export const DEFAULT_API_TIMEOUT_MS = envNumber(import.meta.env.VITE_API_TIMEOUT_MS, 8000)
export const AI_REQUEST_TIMEOUT_MS = envNumber(import.meta.env.VITE_AI_TIMEOUT_MS, 50000)
export const USE_MOCK_API = ['true', '1', 'yes'].includes(String(import.meta.env.VITE_USE_MOCK_API || '').toLowerCase())
export const DEV_AUTO_LOGIN_ENABLED = import.meta.env.DEV && !['false', '0', 'no'].includes(String(import.meta.env.VITE_DEV_AUTO_LOGIN || 'true').toLowerCase())

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: DEFAULT_API_TIMEOUT_MS,
})

const mockAuthUser = {
  id: 'mock-user',
  name: seedUser.name,
  email: seedUser.email,
  initials: seedUser.initials,
}

export async function fetchAuthProviders() {
  if (USE_MOCK_API) {
    await delay(80)
    return {
      email: { enabled: true },
      providers: [
        { id: 'kakao', label: '카카오', enabled: true, requiresSecret: false, startUrl: '/api/auth/oauth/kakao/start/' },
        { id: 'naver', label: '네이버', enabled: true, requiresSecret: true, startUrl: '/api/auth/oauth/naver/start/' },
      ],
    }
  }
  const response = await api.get('/api/auth/providers/')
  return response.data
}

export async function loginWithEmail(payload) {
  if (USE_MOCK_API) {
    await delay(180)
    return { ok: true, token: 'mock-auth-token', provider: 'email', user: { ...mockAuthUser, email: payload.email || mockAuthUser.email } }
  }
  const response = await api.post('/api/auth/email/login/', payload)
  return response.data
}

export async function loginAsDevAdmin() {
  if (USE_MOCK_API) {
    await delay(80)
    return {
      ok: true,
      token: 'mock-dev-admin-token',
      provider: 'dev-admin',
      devAutoLogin: true,
      user: {
        ...mockAuthUser,
        name: 'CARCH 관리자',
        email: 'admin@carch.local',
        initials: 'C',
      },
    }
  }
  const response = await api.post('/api/auth/dev-login/')
  return response.data
}

export async function signupWithEmail(payload) {
  if (USE_MOCK_API) {
    await delay(220)
    return {
      ok: true,
      token: 'mock-auth-token',
      provider: 'email',
      user: {
        ...mockAuthUser,
        name: payload.name || mockAuthUser.name,
        email: payload.email || mockAuthUser.email,
      },
    }
  }
  const response = await api.post('/api/auth/email/signup/', payload)
  return response.data
}

export async function fetchCurrentUser() {
  if (USE_MOCK_API) {
    await delay(80)
    return { authenticated: true, user: mockAuthUser }
  }
  const response = await api.get('/api/auth/me/')
  return response.data
}

export async function logoutAuth() {
  if (USE_MOCK_API) {
    await delay(80)
    return { ok: true }
  }
  const response = await api.post('/api/auth/logout/')
  return response.data
}

const gradients = ['blue', 'purple', 'teal']
const networkByCardId = {
  10029: 'VISA',
  10071: 'VISA',
  10106: 'VISA',
  10107: 'VISA',
  10612: 'MASTERCARD',
}
const preferredCardImages = {}
const extraMockCards = [
  {
    id: '10107',
    cardAdId: 10107,
    name: 'LOCA LIKIT Shop',
    issuer: '롯데카드',
    titleDescription: '온라인 쇼핑과 편의점 지출에 맞춘 카드',
    benefitSummary: '온라인 쇼핑·편의점 집중 할인',
    benefits: ['온라인 쇼핑 할인', '편의점 할인', '생활 쇼핑 특화'],
    annualFee: 10000,
    previousMonthMinSpend: 400000,
    imageUrl: '/card-images/10107.png',
    grad: 'purple',
    brand: 'VISA',
  },
  {
    id: '10071',
    cardAdId: 10071,
    name: 'LOCA LIKIT',
    issuer: '롯데카드',
    titleDescription: '카페와 생활 결제를 넓게 챙기는 카드',
    benefitSummary: '카페·생활 결제 특화 할인',
    benefits: ['카페 할인', '생활 영역 할인', '전월 실적 40만원'],
    annualFee: 10000,
    previousMonthMinSpend: 400000,
    imageUrl: '/card-images/10071.png',
    grad: 'teal',
    brand: 'VISA',
  },
]
const landscapeCardImageNames = ['10029.png']
const portraitCardImageNames = ['10071.png', '10106.png', '10107.png', '10612.png', '2960card.png', '707card.png']

const cardIdentity = (card = {}) => String(card.id || card.cardAdId || card.card_ad_id || card.toCardId || '')
const preferredCardImageUrl = (card = {}, fallback = '') => preferredCardImages[cardIdentity(card)] || fallback

const inferCardImageOrientation = (imageUrl = '') => {
  const normalizedUrl = String(imageUrl).split('?')[0].toLowerCase()
  if (landscapeCardImageNames.some((name) => normalizedUrl.endsWith(`/${name}`))) return 'landscape'
  if (portraitCardImageNames.some((name) => normalizedUrl.endsWith(`/${name}`))) return 'portrait'
  return ''
}

const transactionMonth = (tx) => String(tx.date || tx.approvedAt || tx.approved_at || '').slice(0, 7)

export const latestTransactionMonth = (transactions = []) =>
  transactions
    .map(transactionMonth)
    .filter(Boolean)
    .sort()
    .at(-1) || ''

export const currentMonthTransactions = (transactions = [], month = latestTransactionMonth(transactions)) =>
  month ? transactions.filter((tx) => transactionMonth(tx) === month) : transactions

const applyPreferredCardImage = (card = {}) => {
  const imageUrl = preferredCardImageUrl(card, card.imageUrl || card.image_url)
  return {
    ...card,
    imageUrl,
    image_url: imageUrl,
    imageOrientation: card.imageOrientation || card.image_orientation || inferCardImageOrientation(imageUrl),
    image_orientation: card.image_orientation || card.imageOrientation || inferCardImageOrientation(imageUrl),
  }
}

export const normalizeCard = (card, index = 0, transactions = []) => {
  const preferredCard = applyPreferredCardImage(card)
  const id = String(preferredCard.id || preferredCard.cardAdId || preferredCard.card_ad_id)
  const imageUrl = preferredCard.imageUrl || preferredCard.image_url
  const statementTransactions = currentMonthTransactions(transactions)
  const spent = statementTransactions
    .filter((tx) => String(tx.cardId || tx.card_id) === id && Number(tx.amount ?? tx.amt) < 0)
    .reduce((sum, tx) => sum + Math.abs(Number(tx.amount ?? tx.amt) || 0), 0)

  return {
    ...preferredCard,
    id,
    name: preferredCard.name || preferredCard.cardName || preferredCard.card_name,
    issuer: preferredCard.issuer || preferredCard.issuerName || preferredCard.issuer_name,
    annualFee: preferredCard.annualFee ?? preferredCard.domesticAnnualFee ?? preferredCard.domestic_annual_fee ?? 0,
    previousMonthMinSpend: preferredCard.previousMonthMinSpend ?? preferredCard.previous_month_min_spend,
    imageUrl,
    imageOrientation: preferredCard.imageOrientation || preferredCard.image_orientation || inferCardImageOrientation(imageUrl),
    benefitSummary: preferredCard.benefitSummary || preferredCard.titleDescription || preferredCard.title_description,
    benefits: preferredCard.benefits || [],
    grad: preferredCard.grad || gradients[index % gradients.length],
    brand: preferredCard.brand || networkByCardId[id] || 'CARD',
    spent,
    limit: preferredCard.limit || 5000000,
    num: preferredCard.num || `${id.slice(-4)} **** **** ${String(7000 + index * 137).slice(-4)}`,
    exp: preferredCard.exp || '12/27',
    holder: preferredCard.holder || 'NAM JUHYUN',
    lastSpent: preferredCard.lastSpent || spent,
  }
}

export const normalizeTransaction = (tx) => ({
  ...tx,
  id: tx.id,
  cardId: String(tx.cardId || tx.card_id),
  merchant: tx.merchant || tx.merchantName || tx.merchant_name,
  merchantName: tx.merchantName || tx.merchant || tx.merchant_name,
  cat: tx.cat || tx.category,
  category: tx.category || tx.cat,
  amt: Number(tx.amt ?? tx.amount ?? 0),
  amount: Number(tx.amount ?? tx.amt ?? 0),
  date: tx.date || String(tx.approvedAt || tx.approved_at || '').slice(0, 10),
  time: tx.time || String(tx.approvedAt || tx.approved_at || '').slice(11, 16),
  paymentType: tx.paymentType || tx.payment_type || 'lump_sum',
  payment_type: tx.payment_type || tx.paymentType || 'lump_sum',
  installmentMonths: Number(tx.installmentMonths ?? tx.installment_months ?? 0),
  installment_months: Number(tx.installment_months ?? tx.installmentMonths ?? 0),
  isInterestFreeInstallment: Boolean(tx.isInterestFreeInstallment ?? tx.is_interest_free_installment ?? false),
  is_interest_free_installment: Boolean(tx.is_interest_free_installment ?? tx.isInterestFreeInstallment ?? false),
  icon: tx.icon || '💳',
  addr: tx.addr || tx.address || '-',
})

const delay = (ms = 180) => new Promise((resolve) => setTimeout(resolve, ms))
const cardCatalogSeed = [...clone(seedCards), ...clone(extraMockCards)]
let mockOwnedCards = clone(seedCards).map(applyPreferredCardImage)
let mockCardCatalog = cardCatalogSeed.map(applyPreferredCardImage)
let mockTransactions = clone(seedTransactions).map(normalizeTransaction)
let mockCommunityPosts = clone(seedCommunityPosts).map((post) => ({
  ...post,
  editable: true,
  commentItems: post.commentItems || [
    { id: `${post.id}-comment-1`, author: '남주현', avatar: '남', date: '방금 전', body: '혜택 비교 흐름이 잘 보입니다.', editable: true },
  ],
}))
let mockAnalysisRecords = []

const mockSearchText = (...values) => values.map((value) => String(value || '').toLowerCase()).join(' ')
const mockScore = (query, ...values) => {
  if (!query) return 1
  const q = String(query).toLowerCase()
  const text = mockSearchText(...values)
  if (text.includes(q)) return 10
  return q.split(/\s+/).filter(Boolean).reduce((sum, token) => sum + (text.includes(token) ? 2 : 0), 0)
}

const filterByQuery = (rows, query, fields) => {
  const q = String(query || '').trim()
  return rows
    .map((row) => ({ row, score: mockScore(q, ...fields.map((field) => row[field])) }))
    .filter((item) => !q || item.score > 0)
    .sort((a, b) => b.score - a.score)
    .map((item) => item.row)
}

const isNetworkFallbackError = (error) => !error?.response
const LOCAL_FALLBACK_DELAY_MS = 700

const withTimedLocalFallback = (requestPromise, fallbackFactory) => Promise.race([
  requestPromise,
  delay(LOCAL_FALLBACK_DELAY_MS).then(fallbackFactory),
])

const localCardCatalogRows = (params = {}) => {
  const rows = filterByQuery(mockCardCatalog, params.search || params.q || '', ['name', 'issuer', 'benefitSummary', 'titleDescription'])
  return clone(rows.slice(0, Number(params.limit || 24))).map(applyPreferredCardImage)
}

const localTransactionRows = (params = {}) => {
  let rows = [...mockTransactions]
  if (params.cardId) rows = rows.filter((tx) => String(tx.cardId) === String(params.cardId))
  if (params.category) rows = rows.filter((tx) => String(tx.category) === String(params.category))
  return clone(rows).map(normalizeTransaction)
}

const addMockOwnedCard = (cardId) => {
  const id = String(cardId)
  const card = mockCardCatalog.find((item) => String(item.id) === id || String(item.cardAdId) === id)
  if (!card) throw new Error('Card not found in local catalog.')
  if (!mockOwnedCards.some((item) => String(item.id) === String(card.id))) {
    mockOwnedCards = [...mockOwnedCards, applyPreferredCardImage(clone(card))]
  }
  return { ok: true, card: clone(card) }
}

const monthlyRows = () => currentMonthTransactions(mockTransactions)

const categoryIcon = (category = '') => ({
  카페: '☕',
  식비: '🥗',
  쇼핑: '🛍️',
  교통: '🚇',
  헬스: '🏋️',
  교육: '📚',
  편의점: '🏪',
  뷰티: '💄',
  문화: '🎬',
  구독: '📱',
  수입: '💰',
}[category] || '💳')

const sumBy = (rows, keyGetter, valueGetter) => {
  const map = new Map()
  rows.forEach((row) => {
    const key = keyGetter(row)
    map.set(key, (map.get(key) || 0) + valueGetter(row))
  })
  return [...map.entries()].map(([key, amount]) => ({ key, amount }))
}

function buildMockSpendingSummary({ recurringCategories = [] } = {}) {
  const rows = monthlyRows()
  const expenses = rows.filter((tx) => Number(tx.amount) < 0)
  const income = rows.filter((tx) => Number(tx.amount) > 0)
  const totalExpense = expenses.reduce((sum, tx) => sum + Math.abs(Number(tx.amount || 0)), 0)
  const totalIncome = income.reduce((sum, tx) => sum + Number(tx.amount || 0), 0)
  const byCategory = sumBy(expenses, (tx) => tx.category, (tx) => Math.abs(Number(tx.amount || 0)))
    .map(({ key, amount }) => ({ category: key, amount }))
  const byCard = sumBy(expenses, (tx) => String(tx.cardId), (tx) => Math.abs(Number(tx.amount || 0)))
    .map(({ key, amount }) => ({ cardId: key, amount }))

  const baseline = {
    쇼핑: { previous: 82400, average: 78033, median: 79650 },
    교육: { previous: 35500, average: 33217, median: 33650 },
    식비: { previous: 139400, average: 133533, median: 134750 },
    교통: { previous: 73600, average: 70417, median: 70350 },
    카페: { previous: 20500, average: 19050, median: 19000 },
    뷰티: { previous: 29700, average: 30117, median: 29950 },
    문화: { previous: 38500, average: 34917, median: 34750 },
    헬스: { previous: 59000, average: 56000, median: 59000 },
    편의점: { previous: 0, average: 0, median: 0 },
    구독: { previous: 4900, average: 4900, median: 4900 },
  }
  const recurringSet = new Set(recurringCategories)
  const categoryChanges = byCategory
    .map((item) => {
      const ref = baseline[item.category] || { previous: item.amount, average: item.amount, median: item.amount }
      const baselineReference = ref.median || ref.average || 0
      const detectedOneTimeCandidate = ['교육', '쇼핑'].includes(item.category) && item.amount > baselineReference * 1.8
      const userConfirmedRecurring = recurringSet.has(item.category)
      const oneTimeCandidate = detectedOneTimeCandidate && !userConfirmedRecurring
      const recommendationWeight = oneTimeCandidate ? (item.category === '교육' ? 0.45 : 0.5) : 1
      return {
        category: item.category,
        currentAmount: item.amount,
        previousAmount: ref.previous,
        baselineAverage: Math.round(ref.average),
        baselineMedian: Math.round(ref.median),
        baselineReference: Math.round(baselineReference),
        deltaFromPrevious: item.amount - ref.previous,
        deltaFromBaseline: Math.round(item.amount - baselineReference),
        changeRateFromBaseline: baselineReference ? Math.round(((item.amount - baselineReference) / baselineReference) * 100) : null,
        adjustedAmount: Math.round(item.amount * recommendationWeight),
        recommendationWeight,
        status: oneTimeCandidate ? 'one-time' : item.amount > baselineReference ? 'increase' : item.amount < baselineReference ? 'decrease' : 'stable',
        oneTimeCandidate,
        detectedOneTimeCandidate,
        userConfirmedRecurring,
      }
    })
    .sort((a, b) => Math.abs(b.deltaFromBaseline) - Math.abs(a.deltaFromBaseline))
  const adjustedForRecommendation = categoryChanges.reduce((sum, item) => sum + Number(item.adjustedAmount || 0), 0)
  const previousTotal = 483500
  const baselineAverageTotal = 463183
  const topCategory = [...byCategory].sort((a, b) => b.amount - a.amount)[0] || { category: '소비', amount: 0 }
  const oneTimeCandidates = categoryChanges.filter((item) => item.oneTimeCandidate)
  const spendingTrend = {
    currentMonth: '2026-06',
    previousMonth: '2026-05',
    baselineMonths: ['2026-05', '2026-04', '2026-03', '2026-02', '2026-01', '2025-12'],
    basisLabel: '최근 6개월 기준',
    total: {
      current: totalExpense,
      previous: previousTotal,
      baselineAverage: baselineAverageTotal,
      deltaFromPrevious: totalExpense - previousTotal,
      deltaFromBaseline: totalExpense - baselineAverageTotal,
      adjustedForRecommendation,
    },
    categoryChanges,
    oneTimeCandidates,
    reviewCandidates: oneTimeCandidates,
  }
  const aiAnalysis = {
    schemaVersion: 'spending-analysis-v2',
    summaryTitle: '이번 달 소비 진단',
    headline: `${topCategory.category} 지출 비중이 가장 높습니다.`,
    narrative: '최근 6개월 소비 흐름을 기준으로 반복 지출과 일회성 지출을 구분했습니다.',
    primaryInsight: {
      label: '핵심 진단',
      title: `${topCategory.category} 중심 소비`,
      body: '반복 지출 기준으로 카드 혜택 개선 여지를 확인했습니다.',
      severity: 'attention',
      metricLabel: '분석 금액',
      metricValue: topCategory.amount,
    },
    summaryCards: [
      { label: '총 지출', value: `${totalExpense.toLocaleString('ko-KR')}원`, caption: '2026.06 기준', tone: 'navy' },
      { label: '우선 점검', value: topCategory.category, caption: '가장 큰 카테고리', tone: 'teal' },
    ],
    savingOpportunities: [
      {
        title: `${topCategory.category} 결제 카드 조정`,
        amount: 16060,
        reason: `${topCategory.category} 지출 비중이 높아 혜택이 큰 카드와 비교할 가치가 있습니다.`,
        action: '추천 카드와 현재 카드의 다음 달 혜택 조건을 함께 확인하세요.',
        severity: 'attention',
        route: '/recommendations/new',
      },
    ],
    categoryInsights: byCategory
      .slice()
      .sort((a, b) => b.amount - a.amount)
      .slice(0, 3)
      .map((item) => ({
        category: item.category,
        amount: item.amount,
        shareLabel: item.category === topCategory.category ? '최대 지출' : '주요 지출',
        insight: `${item.category} 지출 흐름을 확인하세요.`,
      })),
    cardInsights: mockOwnedCards.map((card) => ({
      cardId: String(card.id),
      cardName: card.name,
      amount: byCard.find((row) => String(row.cardId) === String(card.id))?.amount || 0,
      fit: '보통',
      insight: `${card.name}의 이번 달 사용액과 다음 달 혜택 조건을 확인하세요.`,
      action: '조건 확인',
    })),
    warnings: ['실제 혜택은 카드사 기준에 따라 달라질 수 있습니다.'],
    nextActions: ['상위 지출 확인', '카드 혜택 비교'],
    actionButtons: [
      { label: '카드 추천 보기', route: '/recommendations/new', intent: 'recommendation' },
      { label: '결제내역 추가', route: '/transactions/new', intent: 'data-entry' },
    ],
    aiMode: 'mock',
    confidence: 0.82,
  }

  return {
    totalExpense,
    totalIncome,
    byCategory,
    byCard,
    period: {
      currentMonth: '2026-06',
      previousMonth: '2026-05',
      baselineMonths: spendingTrend.baselineMonths,
    },
    spendingTrend,
    aiAnalysis,
    aiAnalysisRecordId: 'mock-analysis-1',
    aiAnalysisCached: true,
    aiAnalysisCreatedAt: '2026-06-23T10:00:00+09:00',
  }
}

function buildMockRecommendationBundle(options = {}) {
  const summary = buildMockSpendingSummary(options)
  const profile = {
    totalExpense: summary.spendingTrend.total.adjustedForRecommendation,
    categoryRows: summary.spendingTrend.categoryChanges.map((item) => ({ category: item.category, amount: item.adjustedAmount })),
    byCard: summary.byCard,
    topCategory: summary.byCategory.slice().sort((a, b) => b.amount - a.amount)[0]?.category || '쇼핑',
    recommendationTopCategory: summary.spendingTrend.recurringCategories?.[0]?.category || '식비',
    styleTags: ['생활비 관리형', '쇼핑 집중형', '실적 관리형'],
    period: summary.period,
    spendingTrend: summary.spendingTrend,
  }
  const oneTimeCategorySet = new Set((summary.spendingTrend.oneTimeCandidates || []).map((item) => item.category))
  const results = [
    {
      id: 'r1',
      cardAdId: '10107',
      issuer: '롯데카드',
      name: 'LOCA LIKIT Shop',
      match: 87,
      benefit: '온라인 쇼핑·편의점 집중 할인',
      annualFee: 10000,
      previousMonthMinSpend: 400000,
      tags: ['쇼핑', '편의점'],
      imageUrl: '/card-images/10107.png',
      highlights: ['온라인 쇼핑 할인', '편의점 할인', '생활 쇼핑 특화'],
      reason: '반복 지출 기준으로 연회비를 반영해도 월 9,624원의 순혜택 개선이 예상됩니다.',
      economics: {
        expectedMonthlyBenefit: 12624,
        monthlyAnnualFee: 1000,
        monthlyNetBenefit: 11624,
        monthlyDelta: 9624,
        annualDelta: 115488,
        remainingSpendForBenefit: 0,
        eligibleRatio: 1,
        potentialMonthlyBenefit: 12624,
        potentialMonthlyNetBenefit: 11624,
      },
      spendingFit: { styleTags: ['생활비', '쇼핑', '이동'] },
    },
    ...seedRecommendations
      .filter((item) => !['10107', '10106', '10612', '10029'].includes(String(item.cardAdId)))
      .map((item, index) => ({
      ...clone(item),
      id: `r${index + 2}`,
      match: Math.max(76, Number(item.match || 82) - index * 2),
      reason: item.reason || '보유 카드와 주요 소비 카테고리를 기준으로 비교했습니다.',
      economics: {
        expectedMonthlyBenefit: 9000 - index * 1000,
        monthlyAnnualFee: Math.round(Number(item.annualFee || 0) / 12),
        monthlyNetBenefit: 6500 - index * 800,
        monthlyDelta: index === 0 ? 2811 : 0,
        annualDelta: index === 0 ? 33732 : 0,
        remainingSpendForBenefit: index === 0 ? 147225 : 0,
        eligibleRatio: index === 0 ? 0 : 1,
        potentialMonthlyBenefit: 9000 - index * 1000,
        potentialMonthlyNetBenefit: (9000 - index * 1000) - Math.round(Number(item.annualFee || 0) / 12),
      },
      spendingFit: { styleTags: item.tags || [] },
    })),
  ]
  const routingSuggestions = [
    {
      id: 'route-store-10106-10107',
      category: '편의점',
      amount: 6800,
      monthlyGain: 540,
      fromCardId: '10106',
      fromCardName: 'LOCA LIKIT Eat',
      fromIssuer: '롯데카드',
      toCardId: '10107',
      toCardName: 'LOCA LIKIT Shop',
      toIssuer: '롯데카드',
      toImageUrl: '/card-images/10107.png',
      scope: 'candidate',
      scopeLabel: '비교 카드',
      title: '편의점은 LOCA LIKIT Shop',
      body: '반복되는 편의점 결제를 분리하면 월 540원의 추가 혜택이 예상됩니다.',
    },
    {
      id: 'route-shopping-10612-10107',
      category: '쇼핑',
      amount: 79650,
      monthlyGain: 2965,
      fromCardId: '10612',
      fromCardName: '카드의정석2 SHOPPER',
      fromIssuer: '우리카드',
      toCardId: '10107',
      toCardName: 'LOCA LIKIT Shop',
      toIssuer: '롯데카드',
      toImageUrl: '/card-images/10107.png',
      scope: 'candidate',
      scopeLabel: '비교 카드',
      title: '쇼핑은 LOCA LIKIT Shop',
      body: '반복 쇼핑으로 확인된 금액만 반영해 월 2,965원의 개선을 계산했습니다.',
    },
  ].filter((item) => !oneTimeCategorySet.has(item.category))
  return {
    count: results.length,
    profile,
    baseline: {
      cardId: 'current-portfolio',
      cardName: '현재 사용 조합',
      monthlyNetBenefit: 2000,
      expectedMonthlyBenefit: 5600,
      potentialMonthlyBenefit: 5600,
      monthlyAnnualFee: 3600,
    },
    results,
    recommendations: results,
    routingSuggestions,
    oneTimeAdjustments: summary.spendingTrend.oneTimeCandidates,
    alert: {
      show: true,
      title: '카드 사용을 조정하면 혜택이 개선될 수 있습니다',
      body: '현재 소비 기준 월 9,624원의 순혜택 개선이 예상됩니다.',
      severity: 'attention',
    },
  }
}

function buildMockSearchResults(params = {}) {
  const query = String(params.q || params.search || '').trim()
  const type = params.type || 'all'
  const limit = Math.max(1, Math.min(Number(params.limit || 12), 50))
  const cardLimit = type === 'card' ? limit : Math.min(8, limit)
  const ownedIds = new Set(mockOwnedCards.map((card) => String(card.id)))
  const cardItems = filterByQuery(mockCardCatalog, query, ['name', 'issuer', 'benefitSummary', 'titleDescription'])
    .slice(0, cardLimit)
    .map((card) => ({
      id: String(card.id),
      type: 'card',
      title: card.name,
      description: [card.issuer, card.benefitSummary].filter(Boolean).join(' · '),
      path: ownedIds.has(String(card.id)) ? `/cards/${card.id}` : `/cards/apply/${card.id}`,
      badge: ownedIds.has(String(card.id)) ? '보유중' : '',
      imageUrl: card.imageUrl,
      meta: { issuer: card.issuer, benefitSummary: card.benefitSummary, owned: ownedIds.has(String(card.id)) },
    }))
  const transactionItems = filterByQuery(mockTransactions, query, ['merchant', 'category', 'date', 'addr'])
    .slice(0, 5)
    .map((tx) => ({
      id: tx.id,
      type: 'transaction',
      title: tx.merchant,
      description: [tx.category, tx.date, `${Math.abs(tx.amount).toLocaleString('ko-KR')}원`].join(' · '),
      path: `/transactions/${tx.id}`,
      badge: tx.amount > 0 ? '입금' : '결제',
      meta: { category: tx.category, date: tx.date, amount: tx.amount },
    }))
  const communityItems = filterByQuery(mockCommunityPosts, query, ['title', 'body', 'author'])
    .slice(0, 5)
    .map((post) => ({
      id: post.id,
      type: 'community',
      title: post.title,
      description: `${post.author} · ${post.body.slice(0, 42)}`,
      path: `/community/${post.id}`,
      badge: `댓글 ${post.comments || post.commentItems?.length || 0}`,
      meta: { author: post.author, tags: post.tags || [] },
    }))
  const sections = []
  if (type === 'all' || type === 'card') sections.push({ type: 'card', title: '카드', count: cardItems.length, items: cardItems })
  if (type === 'all' || type === 'transaction') sections.push({ type: 'transaction', title: '거래', count: transactionItems.length, items: transactionItems })
  if (type === 'all' || type === 'community') sections.push({ type: 'community', title: '커뮤니티', count: communityItems.length, items: communityItems })
  const results = sections.flatMap((section) => section.items).slice(0, limit)
  return { query, type, count: results.length, sections: sections.filter((section) => section.items.length), results }
}

export async function fetchOwnedCards() {
  if (USE_MOCK_API) {
    await delay()
    return clone(mockOwnedCards)
  }
  const request = api.get('/api/owned-cards/')
    .then((response) => response.data.results || [])
    .catch((error) => {
      if (!isNetworkFallbackError(error)) throw error
      console.warn('Owned card API request failed. Falling back to local rows.', error)
      return clone(mockOwnedCards)
    })
  return withTimedLocalFallback(request, () => clone(mockOwnedCards))
}

export async function fetchCards(params = {}) {
  if (USE_MOCK_API) {
    await delay()
    return localCardCatalogRows(params)
  }
  const request = api.get('/api/cards/', { params })
    .then((response) => {
      const rows = (response.data.results || []).map(applyPreferredCardImage)
      if (rows.length || params.search || params.q) return rows
      return localCardCatalogRows(params)
    })
    .catch((error) => {
      if (!isNetworkFallbackError(error)) throw error
      console.warn('Card catalog API request failed. Falling back to local rows.', error)
      return localCardCatalogRows(params)
    })
  return withTimedLocalFallback(request, () => localCardCatalogRows(params))
}

export async function addOwnedCard(cardId) {
  if (!USE_MOCK_API) {
    try {
      const response = await api.post('/api/owned-cards/', { cardId }, { timeout: Math.min(DEFAULT_API_TIMEOUT_MS, 1800) })
      return response.data
    } catch (error) {
      if (!isNetworkFallbackError(error)) throw error
      console.warn('Add owned card API request failed. Falling back to local rows.', error)
      return addMockOwnedCard(cardId)
    }
  }
  if (USE_MOCK_API) {
    await delay(120)
    const id = String(cardId)
    const card = mockCardCatalog.find((item) => String(item.id) === id || String(item.cardAdId) === id)
    if (!card) throw new Error('카드를 찾을 수 없습니다.')
    if (!mockOwnedCards.some((item) => String(item.id) === String(card.id))) {
      mockOwnedCards = [...mockOwnedCards, applyPreferredCardImage(clone(card))]
    }
    return { ok: true, card: clone(card) }
  }
}

export async function deleteOwnedCard(cardId) {
  if (!USE_MOCK_API) {
    try {
      const response = await api.delete(`/api/owned-cards/${cardId}/`, { timeout: Math.min(DEFAULT_API_TIMEOUT_MS, 1800) })
      return response.data
    } catch (error) {
      if (!isNetworkFallbackError(error)) throw error
      console.warn('Delete owned card API request failed. Falling back to local rows.', error)
      mockOwnedCards = mockOwnedCards.filter((card) => String(card.id) !== String(cardId))
      return { ok: true }
    }
  }
  if (USE_MOCK_API) {
    await delay(120)
    mockOwnedCards = mockOwnedCards.filter((card) => String(card.id) !== String(cardId))
    return { ok: true }
  }
}

export async function fetchCard(id) {
  if (USE_MOCK_API) {
    await delay()
    const card = mockCardCatalog.find((item) => String(item.id) === String(id) || String(item.cardAdId) === String(id))
    if (!card) throw new Error('카드를 찾을 수 없습니다.')
    return clone(applyPreferredCardImage(card))
  }
  const response = await api.get(`/api/cards/${id}/`)
  return applyPreferredCardImage(response.data)
}

export async function fetchTransactions(params = {}) {
  if (USE_MOCK_API) {
    await delay()
    return localTransactionRows(params)
  }
  const request = api.get('/api/transactions/', { params })
    .then((response) => (response.data.results || []).map(normalizeTransaction))
    .catch((error) => {
      if (!isNetworkFallbackError(error)) throw error
      console.warn('Transaction API request failed. Falling back to local rows.', error)
      return localTransactionRows(params)
    })
  return withTimedLocalFallback(request, () => localTransactionRows(params))
}

export async function fetchSearchResults(params = {}) {
  if (USE_MOCK_API) {
    await delay()
    return clone(buildMockSearchResults(params))
  }
  const response = await api.get('/api/search/', { params })
  return response.data
}

export async function parseTransaction(rawText) {
  if (USE_MOCK_API) {
    await delay(450)
    const text = String(rawText || '')
    const amountMatch = text.match(/([\d,]+)\s*원?/)
    const amount = amountMatch ? -Math.abs(Number(amountMatch[1].replace(/,/g, ''))) : -3800
    const shopper = /무신사|쿠팡|쇼핑|우리/.test(text)
    const installment = /할부|무이자/.test(text)
    const monthMatch = text.match(/(\d{1,2})\s*개월/)
    const education = /토익|응시|교육|영어|교보/.test(text)
    const cafe = /커피|카페|컴포즈|스타벅스/.test(text)
    const transport = /교통|택시|카카오T|전철|지하철|버스|공항철도/.test(text)
    const merchant = shopper
      ? text.includes('무신사') ? '무신사 스토어' : '쿠팡 로켓배송'
      : education
        ? text.includes('토익') ? '토익스피킹 응시료' : '교보문고 강남점'
        : cafe
          ? '컴포즈커피 역삼센터필드점'
          : '확인 필요 가맹점'
    const category = shopper ? '쇼핑' : education ? '교육' : transport ? '교통' : cafe ? '카페' : '기타'
    const cardId = shopper ? '10612' : transport ? '10029' : '10106'
    return normalizeTransaction({
      id: `parsed-${Date.now()}`,
      cardId,
      merchantName: merchant,
      category,
      amount,
      date: '2026-06-23',
      time: shopper ? '23:41' : '08:42',
      paymentType: installment ? 'installment' : 'lump_sum',
      installmentMonths: installment ? Number(monthMatch?.[1] || 2) : 0,
      isInterestFreeInstallment: /무이자/.test(text),
      icon: categoryIcon(category),
      address: shopper || education ? '온라인 결제' : '서울 강남구 테헤란로 231',
      confidence: 0.86,
    })
  }
  const response = await api.post('/api/transactions/parse/', { rawText }, { timeout: AI_REQUEST_TIMEOUT_MS })
  return normalizeTransaction(response.data)
}

export async function createTransaction(payload) {
  if (USE_MOCK_API) {
    await delay(180)
    const tx = normalizeTransaction({
      id: `tx-${Date.now()}`,
      cardId: payload.cardId,
      merchantName: payload.merchantName,
      category: payload.category,
      amount: payload.amount,
      approvedAt: payload.approvedAt,
      paymentType: payload.paymentType,
      installmentMonths: payload.installmentMonths,
      isInterestFreeInstallment: payload.isInterestFreeInstallment,
      icon: payload.icon || categoryIcon(payload.category),
      address: payload.address,
    })
    mockTransactions = [tx, ...mockTransactions]
    return clone(tx)
  }
  const response = await api.post('/api/transactions/', payload)
  return normalizeTransaction(response.data)
}

const applyCategoryOverrides = (params, categories = []) => {
  const values = Array.isArray(categories) ? categories.filter(Boolean) : []
  if (values.length) params.recurringCategories = values.join(',')
  return params
}

export async function fetchCardRecommendationBundle({ recurringCategories = [] } = {}) {
  const params = applyCategoryOverrides({}, recurringCategories)
  if (USE_MOCK_API) {
    await delay()
    return clone(buildMockRecommendationBundle({ recurringCategories }))
  }
  const normalizeRecommendationBundle = (data) => ({
    ...data,
    results: (data.results || []).map(applyPreferredCardImage),
    routingSuggestions: (data.routingSuggestions || []).map((item) => ({
      ...item,
      toImageUrl: preferredCardImageUrl({ toCardId: item.toCardId }, item.toImageUrl),
    })),
  })
  const fallback = () => clone(buildMockRecommendationBundle({ recurringCategories }))
  const request = api.get('/api/recommendations/cards/', { params })
    .then((response) => normalizeRecommendationBundle(response.data))
    .catch((error) => {
      if (!isNetworkFallbackError(error)) throw error
      console.warn('Card recommendation API request failed. Falling back to local rows.', error)
      return fallback()
    })
  return withTimedLocalFallback(request, fallback)
}

export async function fetchCardRecommendations() {
  const data = await fetchCardRecommendationBundle()
  return data.results || []
}

export async function fetchSpendingSummary({ ai = false, refresh = false, recurringCategories = [] } = {}) {
  const params = applyCategoryOverrides({}, recurringCategories)
  if (USE_MOCK_API) {
    await delay(refresh ? 650 : 220)
    const summary = buildMockSpendingSummary({ ai, refresh, recurringCategories })
    if (refresh) {
      mockAnalysisRecords = [
        {
          id: `mock-analysis-${Date.now()}`,
          title: '이번 달 소비 진단',
          createdAt: new Date().toISOString(),
          summary,
        },
        ...mockAnalysisRecords,
      ].slice(0, 5)
    }
    return clone(summary)
  }
  if (ai) params.ai = 1
  if (refresh) params.refresh = 1
  const request = api.get('/api/analytics/spending-summary/', {
    params,
    timeout: ai && refresh ? AI_REQUEST_TIMEOUT_MS : DEFAULT_API_TIMEOUT_MS,
  })
    .then((response) => response.data)
    .catch((error) => {
      if (!isNetworkFallbackError(error)) throw error
      console.warn('Spending summary API request failed. Falling back to local rows.', error)
      return clone(buildMockSpendingSummary({ ai, refresh, recurringCategories }))
    })

  return withTimedLocalFallback(request, () => clone(buildMockSpendingSummary({ ai, refresh, recurringCategories })))
}

export async function fetchAnalysisRecords(params = {}) {
  if (USE_MOCK_API) {
    await delay()
    return clone(mockAnalysisRecords)
  }
  const response = await api.get('/api/analytics/records/', { params })
  return response.data.results || []
}

export async function fetchAiContract() {
  if (USE_MOCK_API) {
    await delay()
    return {
      mode: 'mock',
      spendingAnalysis: { route: '/analytics', schemaVersion: 'spending-analysis-v2' },
      chat: { schemaVersion: 'chat-response-v2' },
    }
  }
  const response = await api.get('/api/ai/contract/')
  return response.data
}

export async function fetchAiStatus() {
  if (USE_MOCK_API) {
    await delay()
    return { aiMode: 'mock', available: true, provider: 'frontend-fixture' }
  }
  const response = await api.get('/api/ai/status/')
  return response.data
}

export async function sendChatMessage(payload) {
  if (USE_MOCK_API) {
    await delay(500)
    const message = String(payload?.message || '')
    const isRecommend = /추천|카드/.test(message)
    const isPlan = /계획|큰 지출|예산|여행|취업/.test(message)
    return {
      schemaVersion: 'chat-response-v2',
      messageType: isPlan ? 'purchase-plan' : isRecommend ? 'card-recommendation' : 'spending-analysis',
      reply: isPlan
        ? '예정된 지출은 목적과 시점을 나누면 관리가 쉬워집니다. 소비계획에서 예산 안 지출과 별도 예정 지출을 구분해볼 수 있습니다.'
        : isRecommend
          ? '최근 6개월 흐름을 기준으로 반복 지출을 분리했습니다. 식비와 쇼핑 결제 카드를 조정하면 월 9,624원의 순혜택 개선이 예상됩니다.'
          : '이번 달 지출은 506,050원입니다. 쇼핑과 교육 지출이 평소보다 높아 일시적인 지출과 반복 지출을 나누어 비교했습니다.',
      summaryChips: [
        { label: '기준', value: '최근 6개월', tone: 'navy' },
        { label: '다음으로', value: isPlan ? '소비계획' : '혜택 비교', tone: 'teal' },
      ],
      quickReplies: ['소비 분석 보기', '카드 추천 보기', '소비계획 만들기'],
      actionButtons: [
        { label: isPlan ? '소비계획 보기' : isRecommend ? '카드 추천 보기' : '소비 분석 보기', route: isPlan ? '/plans' : isRecommend ? '/recommendations/new' : '/analytics', intent: 'open' },
      ],
      relatedRoute: isPlan ? '/plans' : isRecommend ? '/recommendations/new' : '/analytics',
      aiMode: 'mock',
      confidence: 0.82,
      analysisRecordId: 'mock-chat-analysis',
    }
  }
  const response = await api.post('/api/chat/', payload, { timeout: AI_REQUEST_TIMEOUT_MS })
  return response.data
}

export async function fetchCommunityPosts(params = {}) {
  if (USE_MOCK_API) {
    await delay()
    const query = params.search || params.q || ''
    return clone(filterByQuery(mockCommunityPosts, query, ['title', 'body', 'author']))
  }
  const response = await api.get('/api/community/posts/', { params })
  return response.data.results || []
}

export async function fetchCommunityPost(id) {
  if (USE_MOCK_API) {
    await delay()
    const post = mockCommunityPosts.find((item) => String(item.id) === String(id))
    if (!post) throw new Error('게시글을 찾을 수 없습니다.')
    return clone(post)
  }
  const response = await api.get(`/api/community/posts/${id}/`)
  return response.data
}

export async function createCommunityPost(payload) {
  if (USE_MOCK_API) {
    await delay(180)
    const post = {
      id: `c${Date.now()}`,
      title: payload.title,
      body: payload.body,
      author: '남주현',
      avatar: '남',
      date: '방금 전',
      likes: 0,
      comments: 0,
      liked: false,
      editable: true,
      tags: payload.tags || [],
      commentItems: [],
    }
    mockCommunityPosts = [post, ...mockCommunityPosts]
    return clone(post)
  }
  const response = await api.post('/api/community/posts/', payload)
  return response.data
}

export async function updateCommunityPost(id, payload) {
  if (USE_MOCK_API) {
    await delay(180)
    mockCommunityPosts = mockCommunityPosts.map((post) => (
      String(post.id) === String(id) ? { ...post, ...clone(payload) } : post
    ))
    return clone(mockCommunityPosts.find((post) => String(post.id) === String(id)))
  }
  const response = await api.patch(`/api/community/posts/${id}/`, payload)
  return response.data
}

export async function deleteCommunityPost(id) {
  if (USE_MOCK_API) {
    await delay(120)
    mockCommunityPosts = mockCommunityPosts.filter((post) => String(post.id) !== String(id))
    return { ok: true }
  }
  const response = await api.delete(`/api/community/posts/${id}/`)
  return response.data
}

export async function toggleCommunityPostLike(id) {
  if (USE_MOCK_API) {
    await delay(120)
    const post = mockCommunityPosts.find((item) => String(item.id) === String(id))
    if (!post) throw new Error('게시글을 찾을 수 없습니다.')
    post.liked = !post.liked
    post.likes = Math.max(0, Number(post.likes || 0) + (post.liked ? 1 : -1))
    return clone(post)
  }
  const response = await api.post(`/api/community/posts/${id}/like/`)
  return response.data
}

export async function createCommunityComment(postId, payload) {
  if (USE_MOCK_API) {
    await delay(120)
    const post = mockCommunityPosts.find((item) => String(item.id) === String(postId))
    if (!post) throw new Error('게시글을 찾을 수 없습니다.')
    const comment = {
      id: `comment-${Date.now()}`,
      author: '남주현',
      avatar: '남',
      date: '방금 전',
      body: payload.body,
      editable: true,
    }
    post.commentItems = [...(post.commentItems || []), comment]
    post.comments = post.commentItems.length
    return clone(comment)
  }
  const response = await api.post(`/api/community/posts/${postId}/comments/`, payload)
  return response.data
}

export async function deleteCommunityComment(id) {
  if (USE_MOCK_API) {
    await delay(120)
    mockCommunityPosts = mockCommunityPosts.map((post) => ({
      ...post,
      commentItems: (post.commentItems || []).filter((comment) => String(comment.id) !== String(id)),
      comments: (post.commentItems || []).filter((comment) => String(comment.id) !== String(id)).length,
    }))
    return { ok: true }
  }
  const response = await api.delete(`/api/community/comments/${id}/`)
  return response.data
}
