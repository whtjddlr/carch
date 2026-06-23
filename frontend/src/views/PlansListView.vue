<template>
  <section class="screen">
    <header class="plans-header blue-gradient">
      <AppBackButton fallback="/budget" />
      <div>
        <h1>목표 지출 계획</h1>
        <p>월 예산과 별도로 큰 지출과 카드 사용 계획을 관리하세요.</p>
      </div>
    </header>

    <div class="screen-scroll scrollbar-hide plans-body">
      <PlanEmptyState v-if="plans.length === 0" @action="createNew" />
      <div v-else class="plan-list">
        <div v-for="plan in plans" :key="plan.id" class="plan-row">
          <PurchasePlanCard :plan="plan" @open="openPlan" @menu="toggleMenu" />
          <div v-if="menuOpen === plan.id" class="plan-menu">
            <button type="button" @click="openPlan(plan.id)">계획 보기</button>
            <button type="button" @click="renamePlan(plan)">이름 변경</button>
            <button class="danger" type="button" @click="askDelete(plan)">삭제</button>
          </div>
        </div>
      </div>
    </div>

    <button class="floating-action-button" type="button" aria-label="새 목표 지출 계획" @click="createNew">
      <Plus :size="20" />
    </button>

    <div v-if="deleteTarget" class="modal-scrim" @click.self="deleteTarget = null">
      <div class="sheet">
        <h2>계획을 삭제할까요?</h2>
        <p>삭제된 계획은 복구할 수 없습니다.</p>
        <div class="sheet-actions">
          <button class="outline-button" type="button" @click="deleteTarget = null">취소</button>
          <button class="danger-button" type="button" @click="deleteSelected">삭제</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import PlanEmptyState from '@/components/plans/PlanEmptyState.vue'
import PurchasePlanCard from '@/components/plans/PurchasePlanCard.vue'
import { usePurchasePlan } from '@/composables/usePurchasePlan'

const router = useRouter()
const menuOpen = ref('')
const deleteTarget = ref(null)
const { plans, loadPlans, removePlan, updatePlan, resetWizard } = usePurchasePlan()

onMounted(loadPlans)

const createNew = () => {
  resetWizard()
  router.push('/plans/new')
}

const openPlan = (id) => {
  router.push(`/plans/${id}`)
}

const toggleMenu = (id) => {
  menuOpen.value = menuOpen.value === id ? '' : id
}

const renamePlan = async (plan) => {
  const title = window.prompt('새 계획 이름을 입력해주세요.', plan.title)
  if (!title || title.trim() === plan.title) {
    menuOpen.value = ''
    return
  }
  await updatePlan(plan.id, { title: title.trim() })
  menuOpen.value = ''
}

const askDelete = (plan) => {
  deleteTarget.value = plan
  menuOpen.value = ''
}

const deleteSelected = async () => {
  if (!deleteTarget.value) return
  await removePlan(deleteTarget.value.id)
  deleteTarget.value = null
}
</script>

<style scoped>
.plans-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  padding: 24px 20px;
  color: #fff;
}

h1 {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 900;
}

.plans-header p {
  margin: 0;
  color: rgba(255, 255, 255, 0.68);
  font-size: 12px;
  font-weight: 700;
}

.plans-body {
  padding: 18px 20px 116px;
}

.plan-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.plan-row {
  position: relative;
}

.plan-menu {
  position: absolute;
  top: 46px;
  right: 12px;
  z-index: 5;
  overflow: hidden;
  min-width: 140px;
  border: 1px solid #dbe4ee;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 10px 24px rgba(16, 24, 40, 0.14);
}

.plan-menu button {
  display: block;
  width: 100%;
  border-bottom: 1px solid #dbe4ee;
  padding: 11px 14px;
  background: #fff;
  color: #17202b;
  font-size: 13px;
  font-weight: 800;
  text-align: left;
}

.plan-menu button:last-child {
  border-bottom: 0;
}

.plan-menu .danger {
  color: #d92d20;
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
