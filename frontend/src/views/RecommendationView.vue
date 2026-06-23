<template>
  <section class="screen">
    <template v-if="isDetail">
      <header class="recommend-header purple-gradient">
        <AppBackButton fallback="/recommendations/new" />
        <p>AI 분석 결과</p>
        <h1>{{ recommendation.name }}</h1>
        <strong>{{ recommendation.match }}% 매칭</strong>
      </header>
      <div class="screen-scroll scrollbar-hide recommendation-body">
        <article class="app-card result-card">
          <div v-if="recommendation.imageUrl" class="recommendation-art">
            <img :src="recommendation.imageUrl" :alt="recommendation.name" />
          </div>
          <div class="issuer-line">
            <span>{{ recommendation.issuer }}</span>
            <span>{{ recommendation.previousMonthMinSpend ? `전월 ${krw(recommendation.previousMonthMinSpend)}` : '전월실적 없음' }}</span>
          </div>
          <h2>{{ recommendation.benefit }}</h2>
          <p>연회비 {{ krw(recommendation.annualFee) }}</p>
          <div class="tag-row">
            <span v-for="tag in recommendation.tags" :key="tag">{{ tag }}</span>
          </div>
          <ul>
            <li v-for="highlight in recommendation.highlights" :key="highlight">{{ highlight }}</li>
          </ul>
          <button class="primary-button w-100" type="button">추천 카드 확정</button>
          <RouterLink
            class="outline-button w-100"
            :to="{ path: '/plans/new', query: planQuery }"
          >
            이 결제를 목표 지출에 추가
          </RouterLink>
        </article>
      </div>
    </template>

    <template v-else>
      <header class="recommend-header purple-gradient">
        <AppBackButton fallback="/cards" />
        <p>AI 카드 추천</p>
        <h1>나에게 맞는<br />카드 찾기</h1>
      </header>
      <div class="screen-scroll scrollbar-hide recommendation-body">
        <article class="app-card quiz-card">
          <h2>{{ questions[step].q }}</h2>
          <button
            v-for="option in questions[step].opts"
            :key="option"
            class="option-button"
            type="button"
            @click="next"
          >
            {{ option }}
          </button>
        </article>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppBackButton from '@/components/AppBackButton.vue'
import { krw, recommendations } from '@/data/mockData'
import { fetchCardRecommendations } from '@/services/api'

const route = useRoute()
const router = useRouter()
const step = ref(0)
const recommendationItems = ref(recommendations)
const isDetail = computed(() => Boolean(route.params.id))
const recommendation = computed(() => recommendationItems.value.find((item) => item.id === route.params.id) || recommendationItems.value[0])
const planQuery = computed(() => ({
  merchantName: route.query.merchantName || recommendation.value.name,
  category: route.query.category || recommendation.value.tags[0],
  amount: route.query.amount || recommendation.value.annualFee,
}))

const questions = [
  { q: '주로 어디서 많이 소비하시나요?', opts: ['온라인 쇼핑', '식비 / 외식', '교통 / 주유', '여행 / 해외'] },
  { q: '월 카드 사용액은?', opts: ['30만원 미만', '30~50만원', '50~100만원', '100만원 이상'] },
  { q: '선호하는 혜택 유형은?', opts: ['현금 캐시백', '포인트 적립', '즉시 할인', '상관없음'] },
]

const next = () => {
  if (step.value < questions.length - 1) {
    step.value += 1
    return
  }
  router.push('/recommendations/r1')
}

onMounted(async () => {
  try {
    const apiRecommendations = await fetchCardRecommendations()
    recommendationItems.value = apiRecommendations.map((card, index) => ({
      id: `r${index + 1}`,
      cardAdId: card.cardAdId,
      issuer: card.issuer,
      name: card.name,
      match: card.match,
      benefit: card.benefitSummary,
      annualFee: card.annualFee,
      previousMonthMinSpend: card.previousMonthMinSpend,
      tags: [card.issuer, card.previousMonthMinSpend ? `전월 ${krw(card.previousMonthMinSpend)}` : '무실적'],
      grad: card.grad || ['blue', 'purple', 'teal'][index % 3],
      imageUrl: card.imageUrl,
      highlights: card.highlights?.length ? card.highlights : card.benefits,
    }))
  } catch (error) {
    console.warn('카드 추천 API를 불러오지 못해 mock 데이터를 사용합니다.', error)
  }
})
</script>

<style scoped>
.recommend-header {
  padding: 24px 20px 32px;
  color: #fff;
}

.recommend-header p {
  margin: 18px 0 4px;
  color: rgba(255, 255, 255, 0.68);
  font-size: 12px;
  font-weight: 700;
}

.recommend-header h1 {
  margin: 0;
  font-size: 27px;
  font-weight: 900;
  line-height: 1.25;
}

.recommend-header strong {
  display: inline-flex;
  border-radius: 999px;
  margin-top: 12px;
  padding: 5px 10px;
  background: rgba(255, 255, 255, 0.18);
  font-size: 12px;
  font-weight: 900;
}

.recommendation-body {
  padding: 20px;
}

.quiz-card,
.result-card {
  padding: 20px;
}

h2 {
  margin: 0 0 18px;
  color: #17202b;
  font-size: 19px;
  font-weight: 900;
}

.option-button {
  width: 100%;
  border: 1px solid #dbe4ee;
  border-radius: 14px;
  margin-bottom: 10px;
  padding: 14px;
  background: #fff;
  color: #17202b;
  font-size: 14px;
  font-weight: 800;
  text-align: left;
}

.result-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.recommendation-art {
  display: flex;
  height: 168px;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 16px;
  padding: 16px;
  background: #e7edf4;
}

.recommendation-art img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  filter: drop-shadow(0 12px 20px rgba(16, 24, 40, 0.16));
}

.issuer-line {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.issuer-line span {
  border-radius: 999px;
  padding: 5px 9px;
  background: #e8f1ff;
  color: #0f5fae;
  font-size: 11px;
  font-weight: 900;
}

.result-card p {
  margin: 0;
  color: #6e6e73;
  font-size: 13px;
  font-weight: 800;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.tag-row span {
  border-radius: 999px;
  padding: 5px 9px;
  background: #f5f3ff;
  color: #24364f;
  font-size: 11px;
  font-weight: 900;
}

ul {
  margin: 0;
  padding-left: 18px;
  color: #4a5663;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.8;
}

.outline-button {
  text-decoration: none;
}
</style>
