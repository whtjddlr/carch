<template>
  <section class="screen">
    <header class="create-top">
      <button class="icon-button app-back-button" type="button" aria-label="뒤로가기" @click="showCancel = true">
        <ArrowLeft :size="18" />
      </button>
      <div>
        <h1>목표 지출 계획 만들기</h1>
      </div>
    </header>

    <div class="screen-scroll scrollbar-hide create-body">
      <PlanLoadingSkeleton
        v-if="isParsing"
        :messages="['계획 내용을 정리하고 있어요', '품목과 예상 금액을 확인하고 있습니다', '잠시만 기다려주세요']"
      />
      <PlanLoadingSkeleton
        v-else-if="isGenerating"
        :messages="['보유 카드의 혜택 조건과 월 한도를 비교하고 있어요.', '혜택 최대화, 예산 안정, 다음 달 조건 준비 계획을 만들고 있습니다.']"
      />

      <template v-else-if="currentStep === 0">
        <div class="step-copy">
          <h2 class="step-subtitle">예산과 결제 시기만 알려주세요</h2>
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
          <h2 class="step-subtitle">예상 품목을 확인하세요</h2>
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
          <button class="primary-button" type="button" @click="submitStepTwo">카드 추천 보기</button>
        </div>
      </template>

      <template v-else>
        <div class="step-copy">
          <h2>이 지출, 이렇게 결제하세요</h2>
        </div>
        <PlanResultSplit
          :budget="Number(planForm.budget)"
          :total-amount="recommendedScenario?.totalAmount || totalItemAmount"
          :owned-items="ownedItems"
          :new-cards="newCardRecos"
          @open-card="openNewCard"
        />
        <div class="step-actions sticky-actions">
          <button class="outline-button" type="button" @click="currentStep = 1">이전</button>
          <button class="primary-button" type="button" :disabled="!selectedScenarioId" @click="savePlan">이 계획으로 저장</button>
        </div>
      </template>
    </div>

    <div v-if="showCancel" class="modal-scrim cancel-scrim" @click.self="showCancel = false">
      <div class="sheet cancel-sheet" role="dialog" aria-modal="true" aria-labelledby="cancel-title">
        <div class="cancel-copy">
          <span>작성 중인 계획</span>
          <h2 id="cancel-title">계획 작성을 취소할까요?</h2>
          <p>입력한 품목, 예산, 기간 정보가 저장되지 않고 사라집니다.</p>
        </div>
        <div class="cancel-actions">
          <button class="cancel-keep-button" type="button" @click="showCancel = false">계속 작성</button>
          <button class="cancel-danger-button" type="button" @click="cancelCreate">작성 취소</button>
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
import PlanResultSplit from '@/components/plans/PlanResultSplit.vue'
import PlanWarningAlert from '@/components/plans/PlanWarningAlert.vue'
import { cards as mockCards, exampleChips, expenseModes, strategies } from '@/data/mockData'
import { fetchCardRecommendationBundle } from '@/services/api'
import { usePurchasePlan } from '@/composables/usePurchasePlan'

// 카드명 → 이미지 매핑(보유 카드 추천 썸네일용)
const cardImageByName = {}
mockCards.forEach((card) => { if (card?.name) cardImageByName[card.name] = card.imageUrl })

// 신규 발급 이벤트(데모) — 발급 시 현금성 캐시백 지원
const ISSUE_EVENTS = {
  'LOCA LIKIT': 150000,
  'LOCA LIKIT Eat': 130000,
  '카드의정석2 SHOPPER': 120000,
  'LOCA 100': 100000,
  '우리카드 7CORE': 130000,
}
function issueEventFor(name) {
  return ISSUE_EVENTS[name] ?? 100000
}

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

// 신규 발급 추천 (추천 번들 재사용)
const newCardRecos = ref([])

const recommendedScenario = computed(() => scenarios.value.find((s) => s.recommended) || scenarios.value[0] || null)

function paymentLabel(item) {
  const months = Number(item?.installmentMonths || 0)
  if (item?.paymentType === 'installment' || months > 1) return `${months || 2}개월 할부`
  return '일시불'
}

// 보유 카드 결제 배정 — 항목마다 1·2순위 카드를 비교해 보여줌
const ownedItems = computed(() => {
  const scenario = recommendedScenario.value
  if (!scenario) return []
  const payMap = {}
  extractedItems.value.forEach((it) => { payMap[it.name] = paymentLabel(it) })
  // 계획에 등장하는 보유 카드 풀(시나리오 카드 요약 → 없으면 월별 배정에서 수집)
  const pool = (scenario.cardSummary || []).map((c) => c.cardName).filter(Boolean)
  const fromPlan = (scenario.monthlyPlan || []).flatMap((m) => m.items || []).map((it) => it.card)
  const cardPool = [...new Set([...pool, ...fromPlan])].filter(Boolean)

  return (scenario.monthlyPlan || [])
    .flatMap((m) => m.items || [])
    .map((it) => {
      const amount = Number(it.amount || 0)
      const primary = it.card
      const other = cardPool.find((c) => c !== primary)
      const baseBenefit = Number(it.benefit || 0)
      const options = [
        { card: primary, image: cardImageByName[primary] || '', benefit: baseBenefit, rank: 1 },
      ]
      if (other) {
        options.push({ card: other, image: cardImageByName[other] || '', benefit: Math.round(baseBenefit * 0.6), rank: 2 })
      }
      return {
        name: it.name,
        amount,
        payment: payMap[it.name] || '일시불',
        options,
      }
    })
})

function openNewCard() {
  router.push('/recommendations/new')
}

async function loadNewCardRecos() {
  try {
    const bundle = await fetchCardRecommendationBundle()
    const planTotal = totalItemAmount.value || Number(planForm.budget) || 0
    newCardRecos.value = (bundle?.results || []).slice(0, 2).map((r, i) => {
      const b = (r.benefitItems || [])[0]
      const rate = Number(b?.ratePercent || 0)
      const scope = b?.scope || b?.label || (r.matchedCategories || [])[0] || ''
      // 이 계획(지출)에 이 카드를 쓰면 받는 예상 혜택 = 품목 합계 × 대표 혜택률
      const planBenefit = Math.min(Math.round(planTotal * (rate > 0 ? rate / 100 : 0.01)), 80000)
      return {
        id: r.id || r.cardAdId || `nc${i}`,
        name: r.name,
        imageUrl: r.imageUrl,
        benefitText: scope ? `${scope}${rate > 0 ? ` 최대 ${Math.round(rate)}%` : ''} 혜택` : '카드 혜택',
        planBenefit,
        event: issueEventFor(r.name),
        orientation: '',
      }
    })
  } catch {
    newCardRecos.value = []
  }
}

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
  if (currentStep.value === 2) {
    // 보유 카드 결제 = 추천 시나리오 자동 선택, 신규 발급 추천은 번들에서
    selectedScenarioId.value = recommendedScenario.value?.id || ''
    loadNewCardRecos()
  }
}

const viewDraftDetail = () => {
  if (currentPlan.value?.id) router.push(`/plans/${currentPlan.value.id}`)
}

const savePlan = async () => {
  const id = await saveSelectedPlan()
  if (id) {
    resetWizard()
    router.push('/cards')
  }
}

const cancelCreate = () => {
  resetWizard()
  router.push('/cards')
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
  gap: 14px;
  padding: 18px 20px 116px;
}

.step-copy h2 {
  margin: 0 0 5px;
  color: #17202b;
  font-size: 18px;
  font-weight: 900;
}

.step-copy h2.step-subtitle {
  margin: 0;
  color: #2b3a4d;
  font-size: 15px;
  font-weight: 800;
}

.step-copy p {
  margin: 0;
  color: #6e6e73;
  font-size: 12px;
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
  color: #0f5fae;
  font-size: 12px;
  font-weight: 900;
}

/* 전역 :is(...) button { border:1px !important }(0,3,1)보다 높은 특이성으로 테두리 제거 */
.app-backdrop .phone-shell .item-section-head button {
  border: 0 !important;
  padding: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}

.item-list {
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(36, 54, 79, 0.08);
  border-radius: 16px;
  padding: 2px 14px;
  background: #fff;
  box-shadow: 0 10px 22px rgba(36, 54, 79, 0.05);
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

.cancel-scrim {
  align-items: center;
  padding: 22px;
  background: rgba(23, 32, 43, 0.34);
  backdrop-filter: blur(5px);
}

.cancel-sheet {
  width: min(336px, calc(100vw - 40px));
  border: 1px solid rgba(219, 228, 238, 0.9);
  border-radius: 24px;
  padding: 20px;
  background:
    radial-gradient(circle at 14% 0%, rgba(15, 95, 174, 0.07), transparent 38%),
    linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
  text-align: left;
  box-shadow: 0 22px 56px rgba(36, 54, 79, 0.18);
  animation: cancel-pop 180ms ease both;
  backdrop-filter: none;
}

.cancel-copy {
  margin-top: 4px;
}

.cancel-copy span {
  display: inline-flex;
  min-height: 24px;
  align-items: center;
  border-radius: 999px;
  margin-bottom: 10px;
  padding: 0 9px;
  background: #edf4fb;
  color: #2c638f;
  font-size: 11px;
  font-weight: 900;
}

.sheet h2 {
  margin: 0 0 7px;
  color: #17202b;
  font-size: 18px;
  font-weight: 900;
}

.cancel-sheet h2 {
  margin-bottom: 8px;
  font-size: 18px;
  line-height: 1.25;
}

.sheet p {
  margin: 0 0 20px;
  color: #6e6e73;
  font-size: 13px;
  font-weight: 700;
}

.cancel-sheet p {
  margin-bottom: 20px;
  color: #6f7d8c;
  line-height: 1.5;
}

.sheet-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.cancel-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cancel-keep-button,
.cancel-danger-button {
  display: inline-flex;
  min-height: 44px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 900;
}

.cancel-keep-button {
  background: #24364f;
  color: #fff;
  box-shadow: 0 12px 24px rgba(36, 54, 79, 0.16);
}

.cancel-danger-button {
  border: 0;
  background: transparent;
  color: #b42318;
  box-shadow: none;
}

@keyframes cancel-pop {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.98);
  }

  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>
