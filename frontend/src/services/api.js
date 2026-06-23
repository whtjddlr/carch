import axios from 'axios'

const envNumber = (value, fallback) => {
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
export const DEFAULT_API_TIMEOUT_MS = envNumber(import.meta.env.VITE_API_TIMEOUT_MS, 8000)
export const AI_REQUEST_TIMEOUT_MS = envNumber(import.meta.env.VITE_AI_TIMEOUT_MS, 50000)

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: DEFAULT_API_TIMEOUT_MS,
})

const gradients = ['blue', 'purple', 'teal']
const networkByCardId = {
  10029: 'VISA',
  10612: 'MASTERCARD',
  10609: 'VISA',
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

export const normalizeCard = (card, index = 0, transactions = []) => {
  const id = String(card.id || card.cardAdId || card.card_ad_id)
  const statementTransactions = currentMonthTransactions(transactions)
  const spent = statementTransactions
    .filter((tx) => String(tx.cardId || tx.card_id) === id && Number(tx.amount ?? tx.amt) < 0)
    .reduce((sum, tx) => sum + Math.abs(Number(tx.amount ?? tx.amt) || 0), 0)

  return {
    ...card,
    id,
    name: card.name || card.cardName || card.card_name,
    issuer: card.issuer || card.issuerName || card.issuer_name,
    annualFee: card.annualFee ?? card.domesticAnnualFee ?? card.domestic_annual_fee ?? 0,
    previousMonthMinSpend: card.previousMonthMinSpend ?? card.previous_month_min_spend,
    imageUrl: card.imageUrl || card.image_url,
    benefitSummary: card.benefitSummary || card.titleDescription || card.title_description,
    benefits: card.benefits || [],
    grad: card.grad || gradients[index % gradients.length],
    brand: card.brand || networkByCardId[id] || 'CARD',
    spent,
    limit: card.limit || 5000000,
    num: card.num || `${id.slice(-4)} **** **** ${String(7000 + index * 137).slice(-4)}`,
    exp: card.exp || '12/27',
    holder: card.holder || 'NAM JUHYUN',
    lastSpent: card.lastSpent || spent,
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
  icon: tx.icon || '💳',
  addr: tx.addr || tx.address || '-',
})

export async function fetchOwnedCards() {
  const response = await api.get('/api/owned-cards/')
  return response.data.results || []
}

export async function fetchCards(params = {}) {
  const response = await api.get('/api/cards/', { params })
  return response.data.results || []
}

export async function addOwnedCard(cardId) {
  const response = await api.post('/api/owned-cards/', { cardId })
  return response.data
}

export async function deleteOwnedCard(cardId) {
  const response = await api.delete(`/api/owned-cards/${cardId}/`)
  return response.data
}

export async function fetchCard(id) {
  const response = await api.get(`/api/cards/${id}/`)
  return response.data
}

export async function fetchTransactions(params = {}) {
  const response = await api.get('/api/transactions/', { params })
  return (response.data.results || []).map(normalizeTransaction)
}

export async function parseTransaction(rawText) {
  const response = await api.post('/api/transactions/parse/', { rawText }, { timeout: AI_REQUEST_TIMEOUT_MS })
  return normalizeTransaction(response.data)
}

export async function createTransaction(payload) {
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
  const response = await api.get('/api/recommendations/cards/', { params })
  return response.data
}

export async function fetchCardRecommendations() {
  const data = await fetchCardRecommendationBundle()
  return data.results || []
}

export async function fetchSpendingSummary({ ai = false, refresh = false, recurringCategories = [] } = {}) {
  const params = applyCategoryOverrides({}, recurringCategories)
  if (ai) params.ai = 1
  if (refresh) params.refresh = 1
  const response = await api.get('/api/analytics/spending-summary/', {
    params,
    timeout: ai && refresh ? AI_REQUEST_TIMEOUT_MS : DEFAULT_API_TIMEOUT_MS,
  })
  return response.data
}

export async function fetchAnalysisRecords(params = {}) {
  const response = await api.get('/api/analytics/records/', { params })
  return response.data.results || []
}

export async function fetchAiContract() {
  const response = await api.get('/api/ai/contract/')
  return response.data
}

export async function fetchAiStatus() {
  const response = await api.get('/api/ai/status/')
  return response.data
}

export async function sendChatMessage(payload) {
  const response = await api.post('/api/chat/', payload, { timeout: AI_REQUEST_TIMEOUT_MS })
  return response.data
}

export async function fetchCommunityPosts(params = {}) {
  const response = await api.get('/api/community/posts/', { params })
  return response.data.results || []
}

export async function fetchCommunityPost(id) {
  const response = await api.get(`/api/community/posts/${id}/`)
  return response.data
}

export async function createCommunityPost(payload) {
  const response = await api.post('/api/community/posts/', payload)
  return response.data
}

export async function updateCommunityPost(id, payload) {
  const response = await api.patch(`/api/community/posts/${id}/`, payload)
  return response.data
}

export async function deleteCommunityPost(id) {
  const response = await api.delete(`/api/community/posts/${id}/`)
  return response.data
}

export async function toggleCommunityPostLike(id) {
  const response = await api.post(`/api/community/posts/${id}/like/`)
  return response.data
}

export async function createCommunityComment(postId, payload) {
  const response = await api.post(`/api/community/posts/${postId}/comments/`, payload)
  return response.data
}

export async function deleteCommunityComment(id) {
  const response = await api.delete(`/api/community/comments/${id}/`)
  return response.data
}
