<template>
  <section class="screen">
    <header class="create-top">
      <button class="muted-icon" type="button" aria-label="닫기" @click="showCancel = true">
        <ArrowLeft :size="19" />
      </button>
      <h1>목표 지출 계획 만들기</h1>
      <span />
    </header>
    <PlanStepIndicator :step="currentStep" />

    <div class="screen-scroll scrollbar-hide create-body">
      <PlanLoadingSkeleton
        v-if="isParsing"
        :messages="['계획 내용을 정리하고 있어요', '품목과 예상 금액을 확인하고 있습니다', '잠시만 기다려주세요']"
      />
      <PlanLoadingSkeleton
        v-else-if="isGenerating"
        :messages="['보유 카드의 실적과 혜택 한도를 비교하고 있어요.', '혜택 최대화, 예산 안정, 실적 균형 계획을 만들고 있습니다.']"
      />

      <template v-else-if="currentStep === 0">
        <div class="step-copy">
          <h2>어떤 목표 지출을 계획하고 있나요?</h2>
          <p>여행, 가전, 이사처럼 월 예산과 별도로 관리할 지출을 입력해주세요.</p>
        </div>
        <PlanWarningAlert v-if="error" :message="error" tone="warning" />
        <PlanPromptForm
          :raw-prompt="rawPrompt"
          :plan-form="planForm"
          :examples="exampleChips"
          :expense-modes="expenseModes"
          :strategies="strategies"
          :errors="errors"
          @update:raw-prompt="rawPrompt = $event"
          @update:plan-form="Object.assign(planForm, $event)"
          @submit="submitStepOne"
        />
      </template>

      <template v-else-if="currentStep === 1">
        <div class="step-copy">
          <h2>AI가 정리한 품목을 확인하세요</h2>
          <p>금액과 구매 월을 수정한 뒤 카드 사용 계획을 만들 수 있습니다.</p>
        </div>
        <PlanBudgetSummary :budget="Number(planForm.budget)" :total="totalItemAmount" />

        <div class="item-section-head">
          <strong>AI가 인식한 품목 {{ extractedItems.length }}개</strong>
          <button type="button" @click="addItem">
            <Plus :size="15" />
            품목 추가
          </button>
        </div>
        <PlanWarningAlert v-if="errors.items" :message="errors.items" tone="danger" />
        <div class="item-list">
          <ExtractedPlanItem
            v-for="item in extractedItems"
            :key="item.id"
            :item="item"
            @update="updateItem"
            @remove="removeItem"
          />
        </div>
        <div class="step-actions">
          <button class="outline-button" type="button" @click="currentStep = 0">이전</button>
          <button class="primary-button" type="button" @click="submitStepTwo">카드 사용 계획 만들기</button>
        </div>
      </template>

      <template v-else>
        <div class="step-copy">
          <h2>시나리오를 선택해주세요</h2>
          <p>3가지 계획을 비교하고 가장 잘 맞는 계획을 선택하세요.</p>
        </div>
        <PlanScenarioComparison
          :scenarios="scenarios"
          :selected-scenario-id="selectedScenarioId"
          @select="selectedScenarioId = $event"
          @view-detail="viewDraftDetail"
        />
        <div class="step-actions sticky-actions">
          <button class="outline-button" type="button" @click="currentStep = 1">이전</button>
          <button class="primary-button" type="button" :disabled="!selectedScenarioId" @click="savePlan">최종 저장</button>
        </div>
      </template>
    </div>

    <div v-if="showCancel" class="modal-scrim" @click.self="showCancel = false">
      <div class="sheet">
        <h2>계획 작성을 취소할까요?</h2>
        <p>지금까지 입력한 내용이 사라집니다.</p>
        <div class="sheet-actions">
          <button class="outline-button" type="button" @click="showCancel = false">계속 작성</button>
          <button class="danger-button" type="button" @click="cancelCreate">취소하기</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Plus } from 'lucide-vue-next'
import ExtractedPlanItem from '@/components/plans/ExtractedPlanItem.vue'
import PlanBudgetSummary from '@/components/plans/PlanBudgetSummary.vue'
import PlanLoadingSkeleton from '@/components/plans/PlanLoadingSkeleton.vue'
import PlanPromptForm from '@/components/plans/PlanPromptForm.vue'
import PlanScenarioComparison from '@/components/plans/PlanScenarioComparison.vue'
import PlanStepIndicator from '@/components/plans/PlanStepIndicator.vue'
import PlanWarningAlert from '@/components/plans/PlanWarningAlert.vue'
import { exampleChips, expenseModes, strategies } from '@/data/mockData'
import { usePurchasePlan } from '@/composables/usePurchasePlan'

const router = useRouter()
const route = useRoute()
const showCancel = ref(false)
const errors = reactive({})
const {
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
  parsePlan,
  generateScenarios,
  saveSelectedPlan,
  resetWizard,
} = usePurchasePlan()

const monthDiff = computed(() => {
  const [startYear, startMonth] = String(planForm.startMonth || '').split('-').map(Number)
  const [endYear, endMonth] = String(planForm.endMonth || '').split('-').map(Number)
  if (!startYear || !endYear) return 0
  return (endYear - startYear) * 12 + (endMonth - startMonth)
})

onMounted(() => {
  if (route.query.source) {
    resetWizard()
    const modeLabel = route.query.mode === 'edit' ? '수정' : '다시 계산'
    const title = String(route.query.title || '기존 목표 지출 계획')
    rawPrompt.value = `${title}을 ${modeLabel}하고 싶어요. 예산과 기간, 구매 품목을 다시 검토해주세요.`
    planForm.title = title
    planForm.budget = Number(route.query.budget || planForm.budget)
  }

  if (route.query.expenseMode) {
    planForm.expenseMode = String(route.query.expenseMode)
  }

  if (route.query.merchantName || route.query.amount) {
    rawPrompt.value = `${route.query.merchantName || '추천 결제'}를 목표 지출 계획에 추가하고 싶어요.`
    extractedItems.value = [
      {
        id: `i${Date.now()}`,
        name: String(route.query.merchantName || '추천 결제'),
        category: String(route.query.category || '기타'),
        amount: Number(route.query.amount || 0),
        targetMonth: planForm.startMonth,
        required: true,
        flexible: true,
      },
    ]
  }
})

const clearErrors = () => {
  Object.keys(errors).forEach((key) => delete errors[key])
}

const validateStepOne = () => {
  clearErrors()
  if (!rawPrompt.value.trim() && extractedItems.value.length === 0) {
    errors.prompt = '자연어 입력 또는 수동 품목이 하나 이상 필요합니다.'
  }
  if (!Number(planForm.budget) || Number(planForm.budget) < 1) {
    errors.budget = '예산은 1원 이상 입력해주세요.'
  }
  if (monthDiff.value < 0) {
    errors.endMonth = '종료 월은 시작 월보다 빠를 수 없습니다.'
  }
  if (monthDiff.value > 2) {
    errors.endMonth = '최대 계획 기간은 3개월입니다.'
  }
  if (extractedItems.value.length > 6) {
    errors.items = '품목은 최대 6개까지 입력할 수 있습니다.'
  }
  return Object.keys(errors).length === 0
}

const submitStepOne = async () => {
  if (!validateStepOne()) return
  if (extractedItems.value.length && !rawPrompt.value.trim()) {
    currentStep.value = 1
    return
  }
  await parsePlan()
}

const updateItem = (updated) => {
  extractedItems.value = extractedItems.value.map((item) => (item.id === updated.id ? updated : item))
}

const removeItem = (id) => {
  extractedItems.value = extractedItems.value.filter((item) => item.id !== id)
}

const addItem = () => {
  if (extractedItems.value.length >= 6) {
    errors.items = '품목은 최대 6개까지 입력할 수 있습니다.'
    return
  }
  delete errors.items
  extractedItems.value = [
    ...extractedItems.value,
    {
      id: `i${Date.now()}`,
      name: '',
      category: '기타',
      amount: 0,
      targetMonth: planForm.startMonth,
      required: true,
      flexible: true,
    },
  ]
}

const submitStepTwo = async () => {
  clearErrors()
  if (extractedItems.value.length === 0) {
    errors.items = '품목을 하나 이상 입력해주세요.'
    return
  }
  if (extractedItems.value.length > 6) {
    errors.items = '품목은 최대 6개까지 입력할 수 있습니다.'
    return
  }
  await generateScenarios()
}

const viewDraftDetail = () => {
  if (currentPlan.value?.id) router.push(`/plans/${currentPlan.value.id}`)
}

const savePlan = async () => {
  const id = await saveSelectedPlan()
  if (id) {
    resetWizard()
    router.push(`/plans/${id}`)
  }
}

const cancelCreate = () => {
  resetWizard()
  if (window.history.state?.back) {
    router.back()
  } else {
    router.push('/plans')
  }
}
</script>

<style scoped>
.create-top {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #dbe4ee;
  padding: 18px 20px 12px;
  background: #fff;
}

.muted-icon {
  display: flex;
  width: 38px;
  height: 38px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #e7edf4;
  color: #17202b;
}

.create-top h1 {
  margin: 0;
  color: #17202b;
  font-size: 16px;
  font-weight: 900;
}

.create-top span {
  width: 38px;
}

.create-body {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 20px;
}

.step-copy h2 {
  margin: 0 0 5px;
  color: #17202b;
  font-size: 19px;
  font-weight: 900;
}

.step-copy p {
  margin: 0;
  color: #6e6e73;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.5;
}

.item-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.item-section-head strong {
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
}

.item-section-head button {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: transparent;
  color: #0f5fae;
  font-size: 12px;
  font-weight: 900;
}

.item-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.sticky-actions {
  border-top: 1px solid #dbe4ee;
  margin: 4px -20px -20px;
  padding: 14px 20px 20px;
  background: #fbfdff;
}

.sheet h2 {
  margin: 0 0 7px;
  color: #17202b;
  font-size: 18px;
  font-weight: 900;
}

.sheet p {
  margin: 0 0 20px;
  color: #6e6e73;
  font-size: 13px;
  font-weight: 700;
}

.sheet-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
</style>
