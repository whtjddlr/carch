<template>
  <div class="empty-state">
    <div class="empty-icon">
      <CalendarDays :size="30" />
    </div>
    <h2>{{ title }}</h2>
    <p>{{ description }}</p>
    <button class="primary-button" type="button" @click="$emit('action')">{{ actionLabel }}</button>
  </div>
</template>

<script setup>
import { CalendarDays } from 'lucide-vue-next'

defineEmits(['action'])
defineProps({
  title: { type: String, default: '아직 만든 목표 지출 계획이 없어요' },
  description: {
    type: String,
    default: '월 예산과 별도로 관리할 구매 목표를 입력하면 보유 카드에 맞는 사용 계획을 만들어드려요.',
  },
  actionLabel: { type: String, default: '첫 계획 만들기' },
})
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64px 24px;
  text-align: center;
}

.empty-icon {
  display: flex;
  width: 68px;
  height: 68px;
  align-items: center;
  justify-content: center;
  border-radius: 22px;
  margin-bottom: 18px;
  background: #e8f1ff;
  color: #0f5fae;
}

h2 {
  margin: 0 0 8px;
  color: #17202b;
  font-size: 17px;
  font-weight: 900;
}

p {
  max-width: 290px;
  margin: 0 0 24px;
  color: #6e6e73;
  font-size: 14px;
  line-height: 1.55;
}
</style>
