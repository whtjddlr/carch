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
              <small>현재 사용 대비</small>
              <b :class="{ positive: recommendation.economics.monthlyDelta > 0 }">
                {{ signedKrw(recommendation.economics.monthlyDelta) }}
              </b>
            </span>
          </div>

          <div class="payback-panel">
            <span>연회비 반영</span>
            <strong>{{ signedKrw(recommendation.economics.monthlyDelta) }}</strong>
            <p>연간 기준 {{ signedKrw(recommendation.economics.annualDelta) }}</p>
          </div>

          <div v-if="recommendation.performanceFill" class="performance-fill-detail">
            <span>실적을 채우면</span>
            <strong>{{ signedKrw(recommendation.performanceFill.monthlyGain) }} / 월</strong>
            <p>
              {{ krw(recommendation.performanceFill.remaining) }}을 더 채우면
              채운 금액 대비 {{ recommendation.performanceFill.efficiency }}%의 추가 혜택률입니다.
            </p>
          </div>

          <div class="tag-row">
            <span v-for="tag in recommendation.spendingFit.styleTags" :key="tag">{{ tag }}</span>
          </div>

          <ul>
            <li v-for="highlight in recommendation.highlights" :key="highlight">{{ highlight }}</li>
          </ul>

          <RouterLink class="primary-button w-100" to="/cards">내 카드와 비교하기</RouterLink>
          <RouterLink class="outline-button w-100" to="/analytics">소비분석 다시 보기</RouterLink>
        </article>
      </div>
    </template>

    <template v-else>
      <header class="recommend-header blue-gradient">
        <AppBackButton fallback="/cards" />
        <p>카드 추천</p>
        <h1>결제 방향만 바꿔도<br />혜택이 커집니다</h1>
      </header>

      <div class="screen-scroll scrollbar-hide recommendation-body">
        <article v-if="routingSuggestions.length" class="app-card routing-card">
          <div class="routing-title">
            <span>{{ primaryRouting.scopeLabel }}</span>
            <strong>{{ primaryRouting.title }}</strong>
            <p>{{ primaryRouting.body }}</p>
          </div>

          <div class="routing-flow">
            <div class="route-card-mini muted">
              <small>현재</small>
              <b>{{ primaryRouting.fromCardName }}</b>
            </div>
            <ArrowRight :size="18" stroke-width="2.4" />
            <div class="route-card-mini target">
              <img v-if="primaryRouting.toImageUrl" :src="primaryRouting.toImageUrl" :alt="primaryRouting.toCardName" />
              <small>추천</small>
              <b>{{ primaryRouting.toCardName }}</b>
            </div>
          </div>

          <div class="routing-metrics">
            <span>
              <small>대상 지출</small>
              <b>{{ krw(primaryRouting.amount) }}</b>
            </span>
            <span>
              <small>월 개선</small>
              <b>{{ signedKrw(primaryRouting.monthlyGain) }}</b>
            </span>
            <span>
              <small>분야</small>
              <b>{{ primaryRouting.category }}</b>
            </span>
          </div>

          <button type="button" class="route-action" @click="goToSuggestion(primaryRouting)">
            추천 카드 보기
            <ArrowRight :size="16" stroke-width="2.5" />
          </button>

          <div v-if="routingSuggestions.length > 1" class="routing-more">
            <button
              v-for="item in routingSuggestions.slice(1)"
              :key="item.id"
              type="button"
              @click="goToSuggestion(item)"
            >
              <span>{{ item.category }}</span>
              <b>{{ signedKrw(item.monthlyGain) }}</b>
            </button>
          </div>
        </article>

        <article v-if="bundle?.profile" class="app-card profile-card">
          <div>
            <span>계산 기준</span>
            <strong>{{ bundle.profile.styleTags?.join(' · ') || '소비 분석 중' }}</strong>
            <p>
              반복적으로 쓰는 {{ krw(bundle.profile.totalExpense) }}을 기준으로 계산했습니다.
              <template v-if="oneTimeCount"> 일시적인 지출 {{ oneTimeCount }}건은 덜 반영했습니다.</template>
            </p>
          </div>
        </article>

        <article v-if="!routingSuggestions.length && bundle?.alert?.show && recommendationItems[0]" class="app-card alert-card">
          <span>추천 알림</span>
          <strong>{{ bundle.alert.title }}</strong>
          <p>{{ bundle.alert.body }}</p>
        </article>

        <div class="section-heading">
          <h2>추천 카드</h2>
          <span>혜택 큰 순</span>
        </div>

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
              <div v-if="item.performanceFill" class="fill-economics">
                <span>
                  <small>실적까지</small>
                  <b>{{ krw(item.performanceFill.remaining) }}</b>
                </span>
                <span>
                  <small>채우면</small>
                  <b>{{ signedKrw(item.performanceFill.monthlyGain) }}/월</b>
                </span>
                <span>
                  <small>추가 효율</small>
                  <b>{{ item.performanceFill.efficiency }}%</b>
                </span>
              </div>
              <div v-else class="mini-economics">
                <b>{{ signedKrw(item.economics.monthlyDelta) }}</b>
                <small>월 개선 예상</small>
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
import { ArrowRight } from 'lucide-vue-next'
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
const routingSuggestions = computed(() => {
  const items = bundle.value?.routingSuggestions || []
  return items
    .filter((item) => Number(item.monthlyGain || 0) > 0)
    .slice(0, 4)
})
const primaryRouting = computed(() => routingSuggestions.value[0] || {})
const oneTimeCount = computed(() => bundle.value?.profile?.spendingTrend?.oneTimeCandidates?.length || 0)

function signedKrw(value) {
  const amount = Number(value || 0)
  return `${amount > 0 ? '+' : amount < 0 ? '-' : ''}${krw(Math.abs(amount))}`
}

function buildPerformanceFill(economics = {}) {
  const remaining = Number(economics.remainingSpendForBenefit || 0)
  const eligibleRatio = Number(economics.eligibleRatio ?? 1)
  const currentNet = Number(economics.monthlyNetBenefit || 0)
  const currentGross = Number(economics.expectedMonthlyBenefit || 0)
  const potentialGross = Number(economics.potentialMonthlyBenefit || 0)
  const monthlyAnnualFee = Number(economics.monthlyAnnualFee || 0)
  if (remaining <= 0 || eligibleRatio >= 1 || potentialGross <= 0) return null

  const fullGross = potentialGross
  const fullNet = fullGross - monthlyAnnualFee
  const monthlyGain = Math.max(0, fullNet - currentNet)
  if (monthlyGain <= 0) return null

  return {
    remaining,
    monthlyGain,
    fullNet,
    efficiency: Number(((monthlyGain / remaining) * 100).toFixed(1)),
  }
}

function normalizeRecommendation(item) {
  const economics = { ...defaultEconomics, ...(item.economics || {}) }
  return {
    ...item,
    benefit: item.benefit || item.benefitSummary || '소비 패턴에 맞춘 혜택 카드',
    highlights: item.highlights?.length ? item.highlights : item.benefits || item.tags || [],
    reason: item.reason || '소비 스타일과 주요 지출 카테고리를 기준으로 추천합니다.',
    economics,
    performanceFill: buildPerformanceFill(economics),
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

function goToSuggestion(item) {
  const matched = recommendationItems.value.find((card) => String(card.cardAdId) === String(item.toCardId))
  router.push(matched ? `/recommendations/${matched.id}` : '/cards')
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

.routing-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 18px;
  border-color: rgba(34, 55, 78, 0.12);
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 18px 38px rgba(34, 55, 78, 0.1);
}

.routing-title span {
  color: #008c95;
  font-size: 11px;
  font-weight: 900;
}

.routing-title strong {
  display: block;
  margin-top: 5px;
  color: #17202b;
  font-size: 20px;
  font-weight: 950;
  letter-spacing: 0;
}

.routing-title p {
  max-width: 28em;
  margin: 6px 0 0;
  color: #52606d;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.55;
}

.routing-flow {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 24px minmax(0, 1fr);
  gap: 8px;
  align-items: center;
  color: #008c95;
}

.route-card-mini {
  position: relative;
  min-height: 86px;
  overflow: hidden;
  border: 1px solid rgba(34, 55, 78, 0.1);
  border-radius: 18px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.68);
}

.route-card-mini.target {
  border-color: rgba(0, 140, 149, 0.22);
  background: rgba(238, 249, 248, 0.82);
}

.route-card-mini img {
  position: absolute;
  right: 10px;
  bottom: -12px;
  width: 48px;
  height: 66px;
  object-fit: contain;
  opacity: 0.82;
  filter: drop-shadow(0 10px 14px rgba(34, 55, 78, 0.16));
}

.route-card-mini small {
  display: block;
  color: #8a96a3;
  font-size: 10px;
  font-weight: 900;
}

.route-card-mini b {
  position: relative;
  z-index: 1;
  display: block;
  max-width: calc(100% - 34px);
  margin-top: 7px;
  color: #17202b;
  font-size: 13px;
  font-weight: 950;
  line-height: 1.35;
}

.route-card-mini.muted b {
  color: #5f6b77;
}

.routing-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.routing-metrics span {
  min-height: 66px;
  border-radius: 16px;
  padding: 12px;
  background: rgba(245, 248, 250, 0.82);
}

.routing-metrics small {
  display: block;
  color: #7a8592;
  font-size: 10px;
  font-weight: 900;
}

.routing-metrics b {
  display: block;
  margin-top: 7px;
  color: #17202b;
  font-size: 14px;
  font-weight: 950;
}

.routing-metrics span:nth-child(2) b {
  color: #008c95;
}

.route-action {
  display: inline-flex;
  min-height: 44px;
  width: fit-content;
  align-items: center;
  justify-content: center;
  gap: 7px;
  border: 0;
  border-radius: 999px;
  padding: 0 16px;
  background: #22374e;
  color: #fff;
  font-size: 12px;
  font-weight: 950;
  cursor: pointer;
  touch-action: manipulation;
}

.routing-more {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.routing-more button {
  display: inline-flex;
  min-height: 40px;
  align-items: center;
  gap: 7px;
  border: 1px solid rgba(34, 55, 78, 0.1);
  border-radius: 999px;
  padding: 0 12px;
  background: rgba(255, 255, 255, 0.58);
  color: #52606d;
  font-size: 11px;
  font-weight: 900;
  cursor: pointer;
  touch-action: manipulation;
}

.routing-more b {
  color: #008c95;
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 18px 2px 10px;
}

.section-heading h2 {
  margin: 0;
  color: #17202b;
  font-size: 16px;
  font-weight: 950;
}

.section-heading span {
  color: #8a96a3;
  font-size: 11px;
  font-weight: 900;
}

.recommend-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
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

.fill-economics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
  margin-top: 10px;
}

.fill-economics span {
  display: block;
  min-width: 0;
  border-radius: 12px;
  padding: 8px 9px;
  background: rgba(237, 247, 246, 0.82);
}

.fill-economics small {
  display: block;
  color: #6e6e73;
  font-size: 9px;
  font-weight: 900;
  white-space: nowrap;
}

.fill-economics b {
  display: block;
  overflow: hidden;
  margin-top: 4px;
  color: #008c95;
  font-size: 12px;
  font-weight: 950;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.performance-fill-detail {
  border-radius: 16px;
  padding: 14px;
  background: rgba(237, 247, 246, 0.84);
}

.performance-fill-detail span {
  display: block;
  color: #008c95;
  font-size: 11px;
  font-weight: 900;
}

.performance-fill-detail strong {
  display: block;
  margin-top: 5px;
  color: #17202b;
  font-size: 18px;
  font-weight: 950;
}

.performance-fill-detail p {
  margin: 5px 0 0;
  color: #52606d;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.5;
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

/* ── 카드 메인 페이지 톤 통일 (플랫/헤어라인) ── */
.result-card,
.routing-card,
.profile-card,
.alert-card,
.recommend-card,
.recommendation-art,
.payback-panel,
.performance-fill-detail,
.route-card-mini {
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  backdrop-filter: none !important;
}

.economics-grid > div,
.mini-economics > div,
.routing-metrics li {
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}

.recommendation-art {
  height: 200px;
}

.recommend-card {
  margin-top: 0 !important;
  border-top: 1px solid rgba(32, 36, 42, 0.085) !important;
  padding: 14px 0 2px !important;
}
</style>
