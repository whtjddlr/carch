<template>
  <div class="chip-row">
    <button
      v-for="chip in examples"
      :key="chip.label"
      class="example-chip"
      type="button"
      :aria-label="`예시 입력: ${chip.label}`"
      @click="$emit('select', chip.text)"
    >
      {{ chip.label }}
    </button>
  </div>
</template>

<script setup>
defineEmits(['select'])
defineProps({
  examples: { type: Array, required: true },
})
</script>

<style scoped>
.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.example-chip {
  min-height: 40px;
  border: 1px solid #dbe4ee;
  border-radius: 999px;
  padding: 9px 13px;
  background: #e8f1ff;
  color: #0f5fae;
  font-size: 12px;
  font-weight: 800;
}
</style>
