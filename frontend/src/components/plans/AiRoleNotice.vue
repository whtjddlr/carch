<template>
  <div class="ai-notice">
    <Info :size="16" />
    <p>{{ text }}</p>
  </div>
</template>

<script setup>
import { Info } from 'lucide-vue-next'

defineProps({
  text: {
    type: String,
    default: 'AI는 입력 내용을 품목·금액·기간으로 정리합니다. 카드 혜택과 예상 금액은 검수된 카드 규칙으로 계산됩니다.',
  },
})
</script>

<style scoped>
.ai-notice {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  border: 1px solid rgba(37, 99, 235, 0.16);
  border-radius: 16px;
  padding: 14px;
  background: #e8f1ff;
  color: #0f5fae;
}

.ai-notice p {
  margin: 0;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.55;
}
</style>
