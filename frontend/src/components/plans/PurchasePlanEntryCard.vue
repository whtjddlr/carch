<template>
  <article class="entry-card app-card">
    <div class="entry-icon">
      <CalendarDays :size="21" />
    </div>
    <div class="entry-body">
      <h3>큰 지출 계획이 있나요?</h3>
      <p>혼수, 이사, 여행처럼 월 예산 밖의 지출이 예정되어 있다면 보유 카드에 맞는 목표 지출 계획을 만들어보세요.</p>
      <div class="entry-actions">
        <RouterLink class="primary-button" to="/plans/new">목표 지출 계획 만들기</RouterLink>
        <RouterLink class="entry-link" to="/plans">저장된 계획 보기</RouterLink>
      </div>
    </div>
  </article>
</template>

<script setup>
import { CalendarDays } from 'lucide-vue-next'
</script>

<style scoped>
.entry-card {
  display: flex;
  gap: 12px;
  padding: 16px;
}

.entry-icon {
  display: flex;
  width: 42px;
  height: 42px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: #e8f1ff;
  color: #0f5fae;
}

h3 {
  margin: 0 0 5px;
  color: #17202b;
  font-size: 15px;
  font-weight: 900;
}

p {
  margin: 0 0 12px;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.55;
}

.entry-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.entry-actions .primary-button {
  padding: 9px 13px;
  font-size: 12px;
  text-decoration: none;
}

.entry-link {
  color: #0f5fae;
  font-size: 12px;
  font-weight: 800;
  text-decoration: none;
}
</style>
