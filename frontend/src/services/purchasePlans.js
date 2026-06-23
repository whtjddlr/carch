import axios from 'axios'
import { clone, mockPlans } from '@/data/mockData'
import { AI_REQUEST_TIMEOUT_MS, API_BASE_URL, DEFAULT_API_TIMEOUT_MS } from '@/services/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: DEFAULT_API_TIMEOUT_MS,
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
  if (text.includes('혼수') || text.includes('결혼')) return '결혼 준비'
  if (text.includes('면접') || text.includes('취업') || text.includes('정장') || text.includes('토익')) return '취업 준비'
  if (text.includes('기념일') || text.includes('데이트') || text.includes('선물')) return '기념일'
  if (text.includes('헬스') || text.includes('운동') || text.includes('PT') || text.includes('보충제')) return '운동'
  if (text.includes('노트북') || text.includes('태블릿') || text.includes('맥북')) return '전자기기'
  return '큰 지출'
}

const itemTemplates = {
  여행: [
    ['항공권', '항공', 1600000],
    ['숙박', '숙박', 1800000],
    ['여행자보험', '보험', 200000],
    ['현지 교통', '교통', 400000],
  ],
  이사: [
    ['이사 비용', '이사', 350000],
    ['침대', '가구', 600000],
    ['수납장', '가구', 240000],
    ['생활용품', '생활', 180000],
  ],
  '취업 준비': [
    ['정장 셔츠·슬랙스', '쇼핑', 210000],
    ['구두', '쇼핑', 160000],
    ['증명사진', '취업', 50000],
    ['어학 응시료', '교육', 84000],
  ],
  기념일: [
    ['식사 예약', '식비', 180000],
    ['영화·전시', '문화', 50000],
    ['선물', '쇼핑', 180000],
    ['이동비', '교통', 40000],
  ],
  운동: [
    ['헬스장 3개월권', '헬스', 180000],
    ['보충제', '쇼핑', 70000],
    ['운동복', '쇼핑', 80000],
    ['인바디·관리비', '헬스', 20000],
  ],
  전자기기: [
    ['노트북', '전자기기', 1200000],
    ['보호 파우치', '쇼핑', 40000],
    ['마우스·허브', '전자기기', 90000],
    ['AS 보증', '서비스', 70000],
  ],
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
  if (useMockApi) {
    await delay(900)
    const text = payload.rawPrompt || payload.prompt || ''
    const type = inferType(text)
    const title = type === '큰 지출' ? '새 목표 지출 계획' : `${type} 지출 계획`
    const startMonth = payload.startMonth || '2026-07'
    const endMonth = payload.endMonth || '2026-08'
    const templates = itemTemplates[type] || itemTemplates['취업 준비']

    return {
      title,
      type,
      expenseMode: payload.expenseMode || 'planned-extra',
      totalBudget: Number(payload.budget || 800000),
      startMonth,
      endMonth,
      items: templates.map(([name, category, amount], index) => ({
        id: `i${Date.now()}${index + 1}`,
        name,
        category,
        amount,
        targetMonth: index < 2 ? startMonth : endMonth,
        required: index < 3,
        flexible: index !== 0,
      })),
    }
  }

  try {
    return await request(api.post('/api/v1/purchase-plans/parse/', payload, { timeout: AI_REQUEST_TIMEOUT_MS }))
  } catch (error) {
    throw error
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
