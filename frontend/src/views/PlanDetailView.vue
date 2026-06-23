<template>
  <section class="screen">
    <template v-if="plan">
      <header class="detail-header blue-gradient">
        <div class="top-line">
          <AppBackButton fallback="/plans" />
          <h1>{{ plan.title }}</h1>
          <button class="icon-button" type="button" @click="askDelete = true">
            <Trash2 :size="16" />
          </button>
        </div>
        <div class="summary-panel">
          <div class="title-row">
            <strong>{{ plan.title }}</strong>
            <span>{{ plan.type }}</span>
            <span>{{ plan.status }}</span>
          </div>
          <p>{{ monthLabel(plan.startMonth) }} ~ {{ monthLabel(plan.endMonth) }} · {{ selectedScenario?.type || '시나리오 없음' }}</p>
          <div class="summary-grid">
            <div>
              <span>총예산</span>
              <b>{{ krw(plan.totalBudget) }}</b>
            </div>
            <div>
              <span>구매 예정액</span>
              <b>{{ krw(selectedScenario?.totalAmount || 0) }}</b>
            </div>
            <div>
              <span>전체 예상 혜택</span>
              <b class="success">+{{ krw(selectedScenario?.totalBenefit || 0) }}</b>
            </div>
            <div>
              <span>예산 잔액</span>
              <b :class="{ danger: budgetDiff < 0 }">{{ budgetDiff < 0 ? '-' : '+' }}{{ krw(budgetDiff) }}</b>
            </div>
          </div>
          <div class="header-actions">
            <button type="button" @click="openPlanWizard('recalculate')">
              <RotateCcw :size="14" />
              다시 계산
            </button>
            <button type="button" @click="openPlanWizard('edit')">
              <Edit3 :size="14" />
              수정
            </button>
          </div>
        </div>
      </header>

      <div class="screen-scroll scrollbar-hide detail-body">
        <MonthlyPlanTimeline :months="selectedScenario?.monthlyPlan || []" />
        <PlanCardUsageSummary :cards="selectedScenario?.cardSummary || []" />
        <article v-if="selectedScenario?.aiExplanation" class="app-card ai-explain">
          <div class="ai-title">
            <Sparkles :size="16" />
            <h2>이렇게 계획한 이유</h2>
          </div>
          <p>{{ selectedScenario.aiExplanation }}</p>
          <AiRoleNotice text="AI는 계획을 이해하기 쉽게 설명하며, 혜택 금액과 카드 배정은 룰 기반 계산 결과입니다." />
        </article>
        <p class="disclaimer">
          본 계획은 등록된 카드 혜택과 예상 구매 금액에 따른 시뮬레이션입니다.
          실제 혜택은 카드사 정책, 결제 시점, 가맹점 및 이용 조건에 따라 달라질 수 있습니다.
        </p>
      </div>

      <div v-if="askDelete" class="modal-scrim" @click.self="askDelete = false">
        <div class="sheet">
          <h2>계획을 삭제할까요?</h2>
          <p>삭제된 계획은 복구할 수 없습니다.</p>
          <div class="sheet-actions">
            <button class="outline-button" type="button" @click="askDelete = false">취소</button>
            <button class="danger-button" type="button" @click="deletePlan">삭제</button>
          </div>
        </div>
      </div>
    </template>

    <div v-else class="screen-scroll detail-body">
      <PlanEmptyState
        title="계획을 찾을 수 없어요"
        description="목록에서 다시 선택하거나 새 목표 지출 계획을 만들어보세요."
        action-label="계획 목록 보기"
        @action="router.push('/plans')"
      />
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Edit3, RotateCcw, Sparkles, Trash2 } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import AiRoleNotice from '@/components/plans/AiRoleNotice.vue'
import MonthlyPlanTimeline from '@/components/plans/MonthlyPlanTimeline.vue'
import PlanCardUsageSummary from '@/components/plans/PlanCardUsageSummary.vue'
import PlanEmptyState from '@/components/plans/PlanEmptyState.vue'
import { krw, monthLabel } from '@/data/mockData'
import { usePurchasePlan } from '@/composables/usePurchasePlan'

const route = useRoute()
const router = useRouter()
const askDelete = ref(false)
const plan = ref(null)
const { loadPlans, loadPlan, removePlan } = usePurchasePlan()

onMounted(async () => {
  await loadPlans()
  plan.value = await loadPlan(route.params.id)
})

const selectedScenario = computed(() => plan.value?.scenarios.find((scenario) => scenario.id === plan.value.selectedScenarioId) || plan.value?.scenarios[0])
const budgetDiff = computed(() => Number(plan.value?.totalBudget || 0) - Number(selectedScenario.value?.totalAmount || 0))

const openPlanWizard = (mode) => {
  const query = new URLSearchParams({
    source: String(plan.value.id),
    mode,
    title: plan.value.title,
    budget: String(plan.value.totalBudget),
  })
  router.push(`/plans/new?${query.toString()}`)
}

const deletePlan = async () => {
  await removePlan(plan.value.id)
  router.push('/plans')
}
</script>

<style scoped>
.detail-header {
  flex-shrink: 0;
  padding: 22px 20px;
  color: #fff;
}

.top-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 18px;
}

.top-line h1 {
  min-width: 0;
  margin: 0;
  overflow: hidden;
  color: #fff;
  font-size: 16px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.summary-panel {
  border-radius: 18px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.16);
}

.title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 7px;
}

.title-row strong {
  color: #fff;
  font-size: 16px;
  font-weight: 900;
}

.title-row span {
  border-radius: 999px;
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
  font-size: 10px;
  font-weight: 900;
}

.summary-panel > p {
  margin: 10px 0 12px;
  color: rgba(255, 255, 255, 0.68);
  font-size: 12px;
  font-weight: 700;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.summary-grid div {
  border-radius: 12px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.12);
}

.summary-grid span {
  display: block;
  color: rgba(255, 255, 255, 0.62);
  font-size: 10px;
  font-weight: 700;
}

.summary-grid b {
  display: block;
  margin-top: 3px;
  color: #fff;
  font-size: 13px;
  font-weight: 900;
}

.summary-grid .success {
  color: #86efac;
}

.summary-grid .danger {
  color: #fecaca;
}

.header-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 12px;
}

.header-actions button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  border-radius: 11px;
  padding: 9px 10px;
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
  font-size: 12px;
  font-weight: 900;
}

.detail-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
}

.ai-explain {
  padding: 16px;
}

.ai-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  color: #24364f;
}

.ai-title h2 {
  margin: 0;
  color: #17202b;
  font-size: 15px;
  font-weight: 900;
}

.ai-explain > p {
  margin: 0 0 14px;
  color: #4a5663;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.6;
}

.disclaimer {
  border-radius: 14px;
  margin: 0 0 10px;
  padding: 14px;
  background: #e7edf4;
  color: #6e6e73;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.6;
  text-align: center;
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
