<template>
  <div class="example-wrap">
    <span class="example-hint"><Lightbulb :size="12" /> 예시</span>
    <div class="chip-row">
      <button
        v-for="chip in examples"
        :key="chip.label"
        class="example-chip"
        type="button"
        :aria-label="`예시 입력: ${chip.label}`"
        @click="$emit('select', chip.text)"
      >
        <component :is="iconFor(chip.label)" :size="15" />
        {{ chip.label }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { Gift, Laptop, Lightbulb, Plane, ShoppingBag, Truck } from 'lucide-vue-next'

defineEmits(['select'])
defineProps({
  examples: { type: Array, required: true },
})

const ICONS = {
  '노트북 교체': Laptop,
  '여행 경비': Plane,
  '이사 준비': Truck,
  '기념일 선물': Gift,
}
const iconFor = (label) => ICONS[label] || ShoppingBag
</script>

<style scoped>
.example-wrap {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.example-hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #97a1ad;
  font-size: 11px;
  font-weight: 800;
}

.chip-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.example-chip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 44px;
  border: 1px solid #d6e6fb;
  border-radius: 14px;
  padding: 10px 12px;
  background: #eef5ff;
  color: #0f5fae;
  font-size: 12.5px;
  font-weight: 800;
}
</style>
