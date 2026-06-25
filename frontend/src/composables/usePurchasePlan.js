import { computed, reactive, ref } from 'vue'
import {
  createPurchasePlan,
  deletePurchasePlan,
  generatePlanScenarios,
  getPurchasePlan,
  getPurchasePlans,
  parsePurchasePlan,
  selectPlanScenario,
  updatePurchasePlan,
} from '@/services/purchasePlans'

const plans = ref([])
const currentStep = ref(0)
const rawPrompt = ref('')
const planForm = reactive({
  title: '',
  type: '큰 지출',
  budget: 800000,
  startMonth: '2026-07',
  endMonth: '2026-07',
  strategy: '혜택 최대화',
  expenseMode: 'planned-extra',
})
const extractedItems = ref([])
const scenarios = ref([])
const selectedScenarioId = ref('')
const currentPlan = ref(null)
const isParsing = ref(false)
const isGenerating = ref(false)
const error = ref('')
let didLoad = false

export function usePurchasePlan() {
  const totalItemAmount = computed(() => extractedItems.value.reduce((sum, item) => sum + Number(item.amount || 0), 0))

  const loadPlans = async () => {
    if (didLoad) return
    try {
      plans.value = await getPurchasePlans()
      didLoad = true
    } catch (requestError) {
      // 부팅 중 인증 준비 전 일시적 실패 — 잠깐 후 1회 재시도(라우트는 죽지 않음)
      try {
        await new Promise((resolve) => setTimeout(resolve, 450))
        plans.value = await getPurchasePlans()
        didLoad = true
      } catch (retryError) {
        error.value = retryError?.message || requestError?.message || ''
      }
    }
  }

  const refreshPlans = async () => {
    plans.value = await getPurchasePlans()
    didLoad = true
  }

  const loadPlan = async (id) => {
    const found = plans.value.find((plan) => plan.id === id) || (await getPurchasePlan(id))
    return found
  }

  const parsePlan = async () => {
    isParsing.value = true
    error.value = ''
    try {
      const parsed = await parsePurchasePlan({
        rawPrompt: rawPrompt.value,
        budget: planForm.budget,
        startMonth: planForm.startMonth,
        endMonth: planForm.endMonth,
        strategy: planForm.strategy,
        expenseMode: planForm.expenseMode,
      })
      planForm.title = parsed.title
      planForm.type = parsed.type
      planForm.budget = parsed.totalBudget
      planForm.startMonth = parsed.startMonth
      planForm.endMonth = parsed.endMonth
      extractedItems.value = parsed.items
      currentStep.value = 1
    } catch (requestError) {
      error.value = requestError.message || 'AI 분석에 실패했습니다.'
    } finally {
      isParsing.value = false
    }
  }

  const generateScenarios = async () => {
    isGenerating.value = true
    error.value = ''
    try {
      const draft = await createPurchasePlan({
        title: planForm.title || '새 소비 계획',
        type: planForm.type,
        totalBudget: Number(planForm.budget || 0),
        startMonth: planForm.startMonth,
        endMonth: planForm.endMonth,
        expenseMode: planForm.expenseMode,
        status: '작성 중',
        items: extractedItems.value,
      })
      currentPlan.value = draft
      scenarios.value = await generatePlanScenarios(draft.id)
      currentStep.value = 2
      await refreshPlans()
    } catch (requestError) {
      error.value = requestError.message || '계획 생성에 실패했습니다.'
    } finally {
      isGenerating.value = false
    }
  }

  const saveSelectedPlan = async () => {
    if (!currentPlan.value || !selectedScenarioId.value) return null
    const saved = await selectPlanScenario(currentPlan.value.id, selectedScenarioId.value)
    await refreshPlans()
    return saved.id
  }

  const removePlan = async (id) => {
    await deletePurchasePlan(id)
    await refreshPlans()
  }

  const updatePlan = async (id, payload) => {
    const updated = await updatePurchasePlan(id, payload)
    await refreshPlans()
    return updated
  }

  const resetWizard = () => {
    currentStep.value = 0
    rawPrompt.value = ''
    Object.assign(planForm, {
      title: '',
      type: '큰 지출',
      budget: 800000,
      startMonth: '2026-07',
      endMonth: '2026-08',
      strategy: '혜택 최대화',
      expenseMode: 'planned-extra',
    })
    extractedItems.value = []
    scenarios.value = []
    selectedScenarioId.value = ''
    currentPlan.value = null
    error.value = ''
  }

  return {
    plans,
    currentStep,
    rawPrompt,
    planForm,
    extractedItems,
    scenarios,
    selectedScenarioId,
    currentPlan,
    isParsing,
    isGenerating,
    error,
    totalItemAmount,
    loadPlans,
    refreshPlans,
    loadPlan,
    parsePlan,
    generateScenarios,
    saveSelectedPlan,
    removePlan,
    updatePlan,
    resetWizard,
  }
}
