<template>
  <article class="allocation-card app-card">
    <span class="ac-thumb">
      <img
        v-if="cardImage"
        :src="cardImage"
        :alt="item.card"
        :class="ori"
        @load="onThumb"
      />
      <CreditCard v-else :size="18" />
    </span>
    <div class="ac-body">
      <div class="ac-line">
        <strong>{{ item.name }}</strong>
        <b class="ac-amount">{{ krw(item.amount) }}</b>
      </div>
      <div class="ac-line">
        <span class="ac-card">{{ item.card }}</span>
        <em class="ac-benefit">혜택 +{{ krw(item.benefit) }}</em>
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed, ref } from 'vue'
import { CreditCard } from 'lucide-vue-next'
import { cards as mockCards, krw } from '@/data/mockData'

const props = defineProps({
  item: { type: Object, required: true },
})

const cardImage = computed(() => {
  const found = mockCards.find((c) => c?.name === props.item.card)
  return found?.imageUrl || ''
})

// 세로 카드 이미지는 가로 썸네일에 맞춰 회전
const ori = ref('')
function onThumb(event) {
  const img = event.target
  ori.value = img.naturalWidth > img.naturalHeight ? 'is-landscape' : 'is-portrait'
}
</script>

<style scoped>
.allocation-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 14px;
}

.ac-thumb {
  position: relative;
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 48px;
  height: 31px;
  overflow: hidden;
  border-radius: 7px;
  background: #e8edf2;
  color: #8a9aad;
  box-shadow: 0 2px 8px rgba(36, 54, 79, 0.18);
}

.ac-thumb img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.ac-thumb img.is-portrait {
  inset: auto;
  top: 50%;
  left: 50%;
  width: 31px;
  height: 48px;
  max-width: none;
  transform: translate(-50%, -50%) rotate(-90deg);
}

.ac-body {
  flex: 1 1 auto;
  min-width: 0;
}

.ac-line {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}

.ac-line + .ac-line {
  margin-top: 4px;
}

.ac-line strong {
  overflow: hidden;
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ac-amount {
  flex: 0 0 auto;
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
  font-variant-numeric: tabular-nums;
}

.ac-card {
  overflow: hidden;
  color: #6e7885;
  font-size: 12px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ac-benefit {
  flex: 0 0 auto;
  color: #15a34a;
  font-size: 12.5px;
  font-weight: 900;
  font-style: normal;
  font-variant-numeric: tabular-nums;
}
</style>
