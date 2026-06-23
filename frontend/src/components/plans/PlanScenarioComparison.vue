<template>
  <section class="scenario-list">
    <PlanScenarioCard
      v-for="scenario in scenarios"
      :key="scenario.id"
      :scenario="scenario"
      :selected="scenario.id === selectedScenarioId"
      @select="$emit('select', $event)"
      @view-detail="$emit('view-detail', $event)"
    />
  </section>
</template>

<script setup>
import PlanScenarioCard from './PlanScenarioCard.vue'

defineEmits(['select', 'view-detail'])
defineProps({
  scenarios: { type: Array, required: true },
  selectedScenarioId: { type: String, default: '' },
})
</script>

<style scoped>
.scenario-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
</style>
