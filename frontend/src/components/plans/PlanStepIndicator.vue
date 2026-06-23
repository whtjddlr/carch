<template>
  <div class="step-indicator">
    <div v-for="(label, index) in labels" :key="label" class="step-node">
      <div class="dot" :class="{ active: index <= step, done: index < step }">
        <Check v-if="index < step" :size="13" />
        <span v-else>{{ index + 1 }}</span>
      </div>
      <span :class="{ active: index <= step }">{{ label }}</span>
      <i v-if="index < labels.length - 1" :class="{ active: index < step }" />
    </div>
  </div>
</template>

<script setup>
import { Check } from 'lucide-vue-next'

defineProps({
  step: { type: Number, required: true },
})

const labels = ['목표 입력', '품목 확인', '계획 비교']
</script>

<style scoped>
.step-indicator {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border-bottom: 1px solid #dbe4ee;
  background: #fff;
  padding: 12px 18px;
}

.step-node {
  position: relative;
  display: flex;
  min-width: 0;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.dot {
  z-index: 1;
  display: flex;
  width: 26px;
  height: 26px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #e7edf4;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 900;
}

.dot.active {
  background: #0f5fae;
  color: #fff;
}

.step-node > span {
  color: #6e6e73;
  font-size: 10px;
  font-weight: 800;
}

.step-node > span.active {
  color: #0f5fae;
}

.step-node i {
  position: absolute;
  top: 13px;
  right: calc(-50% + 14px);
  left: calc(50% + 14px);
  height: 2px;
  border-radius: 999px;
  background: #dbe4ee;
}

.step-node i.active {
  background: #0f5fae;
}
</style>
