<template>
  <section class="screen">
    <template v-if="isDetail && recommendation">
      <header class="recommend-header blue-gradient">
        <AppBackButton fallback="/recommendations/new" />
        <p>소비 기반 카드 추천</p>
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
          <p>{{ recommendation.reason }}</p>

          <div class="economics-grid">
            <span>
              <small>예상 월 혜택</small>
              <b>{{ krw(recommendation.economics.expectedMonthlyBenefit) }}</b>
            </span>
            <span>
              <small>월 환산 연회비</small>
              <b>{{ krw(recommendation.economics.monthlyAnnualFee) }}</b>
            </span>
            <span>
              <small>월 순혜택</small>
              <b>{{ krw(recommendation.economics.monthlyNetBenefit) }}</b>
            </span>
            <span>
              <small>현재 카드 대비</small>
              <b :class="{ positive: recommendation.economics.monthlyDelta > 0 }">
                {{ signedKrw(recommendation.economics.monthlyDelta) }}
              </b>
            </span>
          </div>

          <div class="payback-panel">
            <span>연회비 회수</span>
            <strong>{{ recommendation.economics.paybackMonths ? `약 ${recommendation.economics.paybackMonths}개월` : '추가 연회비 부담 낮음' }}</strong>
            <p>연간 예상 차이 {{ signedKrw(recommendation.economics.annualDelta) }}</p>
          </div>

          <div class="tag-row">
            <span v-for="tag in recommendation.spendingFit.styleTags" :key="tag">{{ tag }}</span>
          </div>

          <ul>
            <li v-for="highlight in recommendation.highlights" :key="highlight">{{ highlight }}</li>
          </ul>

          <RouterLink class="primary-button w-100" to="/cards">내 카드와 비교하기</RouterLink>
          <RouterLink class="outline-button w-100" to="/analytics/cards">소비분석 다시 보기</RouterLink>
        </article>
      </div>
    </template>

    <template v-else>
      <header class="recommend-header blue-gradient">
        <AppBackButton fallback="/cards" />
        <p>AI 카드 추천</p>
        <h1>소비 스타일에 맞는<br />순혜택 카드</h1>
      </header>

      <div class="screen-scroll scrollbar-hide recommendation-body">
        <article v-if="bundle?.profile" class="app-card profile-card">
          <div>
            <span>소비 스타일</span>
            <strong>{{ bundle.profile.styleTags?.join(' · ') || '소비 분석 중' }}</strong>
            <p>총 지출 {{ krw(bundle.profile.totalExpense) }} 기준으로 연회비를 반영한 순혜택을 계산했어요.</p>
          </div>
        </article>

        <article v-if="bundle?.alert?.show && recommendationItems[0]" class="app-card alert-card">
          <span>추천 알림</span>
          <strong>{{ bundle.alert.title }}</strong>
          <p>{{ bundle.alert.body }}</p>
        </article>

        <div class="recommend-list">
          <article
            v-for="item in recommendationItems"
            :key="item.id"
            class="app-card recommend-card"
            @click="router.push(`/recommendations/${item.id}`)"
          >
            <img v-if="item.imageUrl" :src="item.imageUrl" :alt="item.name" />
            <div>
              <span>{{ item.issuer }}</span>
              <h2>{{ item.name }}</h2>
              <p>{{ item.reason }}</p>
              <div class="mini-economics">
                <b>{{ signedKrw(item.economics.monthlyDelta) }}</b>
                <small>월 순혜택 차이</small>
              </div>
            </div>
          </article>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppBackButton from '@/components/AppBackButton.vue'
import { krw, recommendations } from '@/data/mockData'
import { fetchCardRecommendationBundle } from '@/services/api'

const route = useRoute()
const router = useRouter()
const bundle = ref(null)
const defaultEconomics = {
  expectedMonthlyBenefit: 0,
  monthlyAnnualFee: 0,
  monthlyNetBenefit: 0,
  monthlyDelta: 0,
  annualDelta: 0,
  paybackMonths: null,
}

const recommendationItems = ref(recommendations.map(normalizeRecommendation))
const isDetail = computed(() => Boolean(route.params.id))
const recommendation = computed(() => recommendationItems.value.find((item) => item.id === route.params.id) || recommendationItems.value[0])

function signedKrw(value) {
  const amount = Number(value || 0)
  return `${amount > 0 ? '+' : amount < 0 ? '-' : ''}${krw(Math.abs(amount))}`
}

function normalizeRecommendation(item) {
  return {
    ...item,
    benefit: item.benefit || item.benefitSummary || '소비 패턴에 맞춘 혜택 카드',
    highlights: item.highlights?.length ? item.highlights : item.benefits || item.tags || [],
    reason: item.reason || '소비 스타일과 주요 지출 카테고리를 기준으로 추천했어요.',
    economics: { ...defaultEconomics, ...(item.economics || {}) },
    spendingFit: item.spendingFit || { styleTags: item.tags || [] },
    notification: item.notification || {},
  }
}

function mapRecommendation(card, index) {
  return normalizeRecommendation({
    id: `r${index + 1}`,
    cardAdId: card.cardAdId,
    issuer: card.issuer,
    name: card.name,
    match: card.match,
    benefit: card.benefitSummary,
    annualFee: card.annualFee,
    previousMonthMinSpend: card.previousMonthMinSpend,
    tags: card.spendingFit?.styleTags || [card.issuer],
    imageUrl: card.imageUrl,
    highlights: card.highlights?.length ? card.highlights : card.benefits,
    reason: card.reason,
    economics: card.economics,
    spendingFit: card.spendingFit || { styleTags: [] },
    notification: card.notification || {},
  })
}

onMounted(async () => {
  try {
    const data = await fetchCardRecommendationBundle()
    bundle.value = data
    recommendationItems.value = (data.results || []).map(mapRecommendation)
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

.profile-card,
.alert-card,
.result-card,
.recommend-card {
  padding: 18px;
}

.profile-card span,
.alert-card span,
.recommend-card span {
  color: #0f5fae;
  font-size: 11px;
  font-weight: 900;
}

.profile-card strong,
.alert-card strong {
  display: block;
  margin-top: 5px;
  color: #17202b;
  font-size: 17px;
  font-weight: 900;
}

.profile-card p,
.alert-card p,
.result-card p,
.recommend-card p {
  margin: 6px 0 0;
  color: #5f6b77;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.5;
}

.alert-card {
  margin-top: 12px;
  border-color: rgba(0, 140, 149, 0.18);
  background: rgba(240, 253, 250, 0.82);
}

.recommend-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
}

.recommend-card {
  display: grid;
  grid-template-columns: 82px minmax(0, 1fr);
  gap: 14px;
  align-items: center;
  cursor: pointer;
}

.recommend-card img {
  width: 82px;
  height: 112px;
  object-fit: contain;
  filter: drop-shadow(0 12px 18px rgba(16, 24, 40, 0.12));
}

.recommend-card h2,
.result-card h2 {
  margin: 3px 0 0;
  color: #17202b;
  font-size: 18px;
  font-weight: 900;
}

.mini-economics {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  margin-top: 9px;
  border-radius: 999px;
  padding: 7px 10px;
  background: #edf7f6;
}

.mini-economics b,
.economics-grid b.positive {
  color: #008c95;
}

.mini-economics small {
  color: #5f6b77;
  font-size: 10px;
  font-weight: 900;
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
  background: #eef3f7;
}

.recommendation-art img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  filter: drop-shadow(0 12px 20px rgba(16, 24, 40, 0.16));
}

.issuer-line,
.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.issuer-line span,
.tag-row span {
  border-radius: 999px;
  padding: 5px 9px;
  background: #e8f1ff;
  color: #0f5fae;
  font-size: 11px;
  font-weight: 900;
}

.economics-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.economics-grid span,
.payback-panel {
  border-radius: 14px;
  padding: 12px;
  background: #f6f8fb;
}

.economics-grid small,
.payback-panel span {
  display: block;
  color: #6e6e73;
  font-size: 10px;
  font-weight: 900;
}

.economics-grid b,
.payback-panel strong {
  display: block;
  margin-top: 4px;
  color: #17202b;
  font-size: 15px;
  font-weight: 900;
}

.payback-panel p {
  margin-top: 4px;
}

ul {
  margin: 0;
  padding-left: 18px;
  color: #4a5663;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.8;
}

.primary-button,
.outline-button {
  text-decoration: none;
}
</style>
