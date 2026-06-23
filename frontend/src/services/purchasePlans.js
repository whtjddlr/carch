import axios from 'axios'
import { clone, mockPlans } from '@/data/mockData'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
  headers: { 'Content-Type': 'application/json' },
})

const useMockApi = import.meta.env.VITE_USE_MOCK_API === 'true'
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms))
let mockStore = clone(mockPlans)

const normalizeError = (error) => {
  const message = error?.response?.data?.message || error?.message || '요청을 처리하지 못했습니다.'
  return { message, raw: error }
}

const request = async (promise) => {
  try {
    const response = await promise
    return response.data
  } catch (error) {
    throw normalizeError(error)
  }
}

const inferType = (text = '') => {
  if (text.includes('이사')) return '이사'
  if (text.includes('여행')) return '여행'
  if (text.includes('출산') || text.includes('육아')) return '육아'
  if (text.includes('혼수') || text.includes('결혼')) return '혼수'
  return '기타'
}

const buildScenarios = (plan) => {
  const totalAmount = plan.items.reduce((sum, item) => sum + Number(item.amount || 0), 0)
  const budgetDiff = Number(plan.totalBudget || 0) - totalAmount
  const template = clone(mockPlans[0].scenarios)

  return template.map((scenario, index) => ({
    ...scenario,
    id: `sc${index + 1}`,
    totalAmount,
    budgetDiff,
    totalBenefit: index === 0 ? 75000 : index === 1 ? 55000 : 65000,
    maxMonthlySpend: index === 0 ? Math.max(...plan.items.map((item) => Number(item.amount || 0)), 0) : Math.ceil(totalAmount / 3),
    monthlyPlan: scenario.monthlyPlan.length
      ? scenario.monthlyPlan
      : [
          {
            month: plan.startMonth,
            items: plan.items.slice(0, 2).map((item) => ({
              name: item.name,
              amount: Number(item.amount || 0),
              card: 'LOCA 100',
              benefit: 15000,
              note: '월 실적과 혜택 한도를 함께 고려한 배정입니다.',
              status: '구매 예정',
            })),
          },
          {
            month: plan.endMonth,
            items: plan.items.slice(2).map((item) => ({
              name: item.name,
              amount: Number(item.amount || 0),
              card: '카드의정석2 SHOPPER',
              benefit: 10000,
              note: '지출이 특정 카드에 몰리지 않도록 분산했습니다.',
              status: '구매 예정',
            })),
          },
        ],
  }))
}

export async function parsePurchasePlan(payload) {
  try {
    return await request(api.post('/api/v1/purchase-plans/parse/', payload))
  } catch (error) {
    if (!useMockApi) throw error
  }

  await delay(900)
  const text = payload.rawPrompt || payload.prompt || ''
  const type = inferType(text)
  const title = type === '기타' ? '새 소비 계획' : `${type} 구매 계획`
  const startMonth = payload.startMonth || '2026-07'
  const endMonth = payload.endMonth || '2026-09'

  return {
    title,
    type,
    expenseMode: payload.expenseMode || 'planned-extra',
    totalBudget: Number(payload.budget || 7000000),
    startMonth,
    endMonth,
    items: [
      { id: `i${Date.now()}1`, name: type === '여행' ? '항공권' : type === '이사' ? '소파' : '냉장고', category: type === '여행' ? '항공' : type === '이사' ? '가구' : '가전', amount: type === '여행' ? 1600000 : 2500000, targetMonth: startMonth, required: true, flexible: false },
      { id: `i${Date.now()}2`, name: type === '여행' ? '숙박' : type === '이사' ? '침대' : '세탁기', category: type === '여행' ? '숙박' : type === '이사' ? '가구' : '가전', amount: type === '여행' ? 1800000 : 1200000, targetMonth: startMonth, required: true, flexible: true },
      { id: `i${Date.now()}3`, name: type === '여행' ? '여행자보험' : type === '이사' ? '식탁' : '건조기', category: type === '여행' ? '보험' : type === '이사' ? '가구' : '가전', amount: type === '여행' ? 200000 : 1000000, targetMonth: endMonth, required: true, flexible: true },
      { id: `i${Date.now()}4`, name: type === '여행' ? '현지 교통' : type === '이사' ? '수납장' : 'TV', category: type === '여행' ? '교통' : type === '이사' ? '가구' : '가전', amount: type === '여행' ? 400000 : 1800000, targetMonth: endMonth, required: false, flexible: true },
    ],
  }
}

export async function createPurchasePlan(payload) {
  if (!useMockApi) {
    return request(api.post('/api/v1/purchase-plans/', payload))
  }

  await delay(250)
  const plan = {
    id: `p${Date.now()}`,
    title: payload.title || '새 소비 계획',
    type: payload.type || '기타',
    expenseMode: payload.expenseMode || 'planned-extra',
    totalBudget: Number(payload.totalBudget || payload.budget || 0),
    startMonth: payload.startMonth,
    endMonth: payload.endMonth,
    status: payload.status || '작성 중',
    selectedScenarioId: '',
    createdAt: new Date().toISOString().slice(0, 10),
    progress: 0,
    items: clone(payload.items || []),
    scenarios: [],
  }
  mockStore = [plan, ...mockStore]
  return clone(plan)
}

export async function getPurchasePlans() {
  if (!useMockApi) {
    return request(api.get('/api/v1/purchase-plans/'))
  }
  await delay(200)
  return clone(mockStore)
}

export async function getPurchasePlan(id) {
  if (!useMockApi) {
    return request(api.get(`/api/v1/purchase-plans/${id}/`))
  }
  await delay(160)
  return clone(mockStore.find((plan) => plan.id === id))
}

export async function generatePlanScenarios(id) {
  if (!useMockApi) {
    return request(api.post(`/api/v1/purchase-plans/${id}/scenarios/`))
  }
  await delay(1000)
  const plan = mockStore.find((item) => item.id === id)
  if (!plan) throw { message: '계획을 찾을 수 없습니다.' }
  plan.scenarios = buildScenarios(plan)
  plan.status = '계산 완료'
  return clone(plan.scenarios)
}

export async function selectPlanScenario(planId, scenarioId) {
  if (!useMockApi) {
    return request(api.post(`/api/v1/purchase-plans/${planId}/select/`, { scenarioId }))
  }
  await delay(200)
  const plan = mockStore.find((item) => item.id === planId)
  if (!plan) throw { message: '계획을 찾을 수 없습니다.' }
  plan.selectedScenarioId = scenarioId
  plan.status = '선택 완료'
  return clone(plan)
}

export async function updatePurchasePlan(id, payload) {
  if (!useMockApi) {
    return request(api.patch(`/api/v1/purchase-plans/${id}/`, payload))
  }
  await delay(200)
  mockStore = mockStore.map((plan) => (plan.id === id ? { ...plan, ...clone(payload) } : plan))
  return clone(mockStore.find((plan) => plan.id === id))
}

export async function deletePurchasePlan(id) {
  if (!useMockApi) {
    return request(api.delete(`/api/v1/purchase-plans/${id}/`))
  }
  await delay(180)
  mockStore = mockStore.filter((plan) => plan.id !== id)
  return { ok: true }
}
