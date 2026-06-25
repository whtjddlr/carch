<template>
  <article class="plan-item">
    <span class="pi-ico"><component :is="itemIcon" :size="16" /></span>
    <input
      class="pi-name"
      :value="item.name"
      aria-label="품목명"
      placeholder="품목명을 입력하세요"
      @input="patch('name', $event.target.value)"
    />
    <label class="pi-amount">
      <input
        :value="item.amount || ''"
        type="number"
        min="0"
        inputmode="numeric"
        aria-label="예상 금액"
        placeholder="0"
        @input="patch('amount', Number($event.target.value))"
      />
      <span>원</span>
    </label>
    <button class="pi-del" type="button" aria-label="품목 삭제" @click="$emit('remove', item.id)">
      <Trash2 :size="15" />
    </button>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import {
  Armchair, BookOpen, Bus, Camera, Dumbbell, Gift, Laptop, Package,
  Plane, Shirt, ShoppingBasket, Smartphone, Trash2, UtensilsCrossed,
} from 'lucide-vue-next'

const emit = defineEmits(['update', 'remove'])
const props = defineProps({
  item: { type: Object, required: true },
})

// 품목명·분야에 맞춘 아이콘 추정
const ICON_RULES = [
  [/노트북|랩탑|맥북|컴퓨터|모니터|태블릿|아이패드/, Laptop],
  [/폰|휴대폰|스마트폰|아이폰|갤럭시|이어폰|충전|파우치|케이스|가전|전자/, Smartphone],
  [/침대|매트리스|소파|가구|책상|의자|수납|선반|장롱/, Armchair],
  [/재킷|자켓|정장|셔츠|코트|니트|바지|슬랙스|옷|의류/, Shirt],
  [/구두|신발|운동화|스니커즈/, Shirt],
  [/항공|비행기|여행|숙소|호텔|여권/, Plane],
  [/사진|카메라|렌즈|촬영/, Camera],
  [/교통|이동|버스|지하철|기차|ktx|택시/i, Bus],
  [/식|음식|식비|외식|카페|맛집|선물세트/, UtensilsCrossed],
  [/선물|기념일|꽃|케이크/, Gift],
  [/책|교재|강의|학원|응시료|어학|교육|시험/, BookOpen],
  [/헬스|운동|요가|필라테스|장비/, Dumbbell],
  [/생활|용품|세제|마트|장보기/, ShoppingBasket],
]

const itemIcon = computed(() => {
  const text = `${props.item?.name || ''} ${props.item?.category || ''}`
  const hit = ICON_RULES.find(([re]) => re.test(text))
  return hit ? hit[1] : Package
})

const patch = (field, value) => {
  emit('update', { ...props.item, [field]: value })
}
</script>

<style scoped>
.plan-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 13px 2px;
  border-bottom: 1px solid rgba(36, 54, 79, 0.08);
}

.plan-item:last-child {
  border-bottom: 0;
}

.pi-ico {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: rgba(15, 95, 174, 0.1);
  color: #0f5fae;
}

.pi-name {
  flex: 1 1 auto;
  min-width: 0;
  border: 0;
  background: transparent;
  color: #17202b;
  font-size: 14px;
  font-weight: 800;
  outline: none;
}

.pi-name::placeholder {
  color: #b3bdc9;
  font-weight: 700;
}

.pi-amount {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 4px;
}

.pi-amount input {
  width: 100px;
  border: 1px solid #dbe4ee;
  border-radius: 10px;
  padding: 8px 10px;
  background: #fbfdff;
  color: #17202b;
  font-size: 13px;
  font-weight: 700;
  text-align: right;
  outline: none;
  font-variant-numeric: tabular-nums;
}

.pi-amount input:focus {
  border-color: #0f5fae;
}

.pi-amount span {
  color: #6e6e73;
  font-size: 12px;
  font-weight: 800;
}

.pi-del {
  display: inline-flex;
  flex: 0 0 auto;
  width: 30px;
  height: 30px;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 9px;
  background: transparent;
  color: #c0392b !important;
}

.pi-del:active {
  background: #fef3f2;
}
</style>
