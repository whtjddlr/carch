// 남주현 데모용 월별 소비 데이터.
// 카테고리 합 = 카드 합 = 총소비가 항상 일치하도록 빌더에서 자동 계산한다.
// (2026-06은 백엔드 실데이터를 쓰므로 여기엔 그 이전 달들을 둔다)

// 카테고리 → 주 사용 카드 매핑 (6월 카드 사용 패턴과 동일)
//  10612 카드의정석2 SHOPPER / 10106 LOCA LIKIT Eat / 10029 LOCA 100
const CATEGORY_CARD = {
  쇼핑: '10612',
  뷰티: '10612',
  통신: '10612',
  구독: '10612',
  교육: '10029',
  교통: '10029',
  문화: '10029',
  생활: '10029',
  식비: '10106',
  카페: '10106',
  편의점: '10106',
}

// 월별 카테고리 지출(원) — 손으로 큐레이션한 데모(연말 쇼핑/문화 ↑, 새학기 교육 ↑ 등)
const MONTHLY_CATEGORIES = {
  '2025-10': { 식비: 96000, 카페: 39000, 쇼핑: 132000, 교통: 41000, 교육: 48000, 뷰티: 38000, 통신: 69000, 생활: 61000, 편의점: 23000, 문화: 19000, 구독: 9900 },
  '2025-11': { 식비: 88000, 카페: 35000, 쇼핑: 168000, 교통: 39000, 교육: 52000, 뷰티: 51000, 통신: 69000, 생활: 57000, 편의점: 21000, 문화: 22000, 구독: 9900 },
  '2025-12': { 식비: 104000, 카페: 44000, 쇼핑: 246000, 교통: 36000, 교육: 30000, 뷰티: 62000, 통신: 69000, 생활: 88000, 편의점: 27000, 문화: 41000, 구독: 9900 },
  '2026-01': { 식비: 79000, 카페: 31000, 쇼핑: 96000, 교통: 44000, 교육: 168000, 뷰티: 33000, 통신: 69000, 생활: 64000, 편의점: 19000, 문화: 16000, 구독: 9900 },
  '2026-02': { 식비: 84000, 카페: 33000, 쇼핑: 110000, 교통: 47000, 교육: 142000, 뷰티: 29000, 통신: 69000, 생활: 59000, 편의점: 18000, 문화: 14000, 구독: 9900 },
  '2026-03': { 식비: 99000, 카페: 42000, 쇼핑: 158000, 교통: 52000, 교육: 76000, 뷰티: 47000, 통신: 69000, 생활: 63000, 편의점: 24000, 문화: 28000, 구독: 9900 },
  '2026-04': { 식비: 92000, 카페: 40000, 쇼핑: 184000, 교통: 49000, 교육: 58000, 뷰티: 73000, 통신: 69000, 생활: 60000, 편의점: 22000, 문화: 31000, 구독: 9900 },
  '2026-05': { 식비: 87000, 카페: 37000, 쇼핑: 212000, 교통: 45000, 교육: 64000, 뷰티: 68000, 통신: 69000, 생활: 62000, 편의점: 23000, 문화: 26000, 구독: 9900 },
}

const MONTHLY_INCOME = 860000

const ALL_KEYS = Object.keys(MONTHLY_CATEGORIES).sort()

function sumValues(map) {
  return Object.values(map).reduce((sum, value) => sum + Number(value || 0), 0)
}

// 각 카테고리의 전체 평균 (반복 지출/스파이크 판단용)
const CATEGORY_AVERAGE = (() => {
  const totals = {}
  const counts = {}
  ALL_KEYS.forEach((key) => {
    Object.entries(MONTHLY_CATEGORIES[key]).forEach(([category, amount]) => {
      totals[category] = (totals[category] || 0) + amount
      counts[category] = (counts[category] || 0) + 1
    })
  })
  const avg = {}
  Object.keys(totals).forEach((category) => {
    avg[category] = Math.round(totals[category] / counts[category])
  })
  return avg
})()

const OVERALL_BASELINE = Math.round(
  ALL_KEYS.reduce((sum, key) => sum + sumValues(MONTHLY_CATEGORIES[key]), 0) / ALL_KEYS.length,
)

export function demoMonthKeys() {
  return [...ALL_KEYS]
}

export function hasDemoMonth(monthKey) {
  return Boolean(MONTHLY_CATEGORIES[monthKey])
}

export function demoMonthSummary(monthKey) {
  const categories = MONTHLY_CATEGORIES[monthKey]
  if (!categories) return null

  const byCategory = Object.entries(categories)
    .map(([category, amount]) => ({ category, amount }))
    .sort((a, b) => b.amount - a.amount)
  const totalExpense = sumValues(categories)

  const cardMap = {}
  byCategory.forEach(({ category, amount }) => {
    const cardId = CATEGORY_CARD[category] || '10106'
    cardMap[cardId] = (cardMap[cardId] || 0) + amount
  })
  const byCard = Object.entries(cardMap).map(([cardId, amount]) => ({ cardId, amount }))

  const index = ALL_KEYS.indexOf(monthKey)
  const prevKey = index > 0 ? ALL_KEYS[index - 1] : null
  const prevTotal = prevKey ? sumValues(MONTHLY_CATEGORIES[prevKey]) : totalExpense

  // 이번 달에 평소보다 크게 늘어난 카테고리 → 반복 여부 확인 후보
  const reviewCandidates = byCategory
    .map((item) => ({
      ...item,
      ratio: CATEGORY_AVERAGE[item.category] ? item.amount / CATEGORY_AVERAGE[item.category] : 1,
    }))
    .filter((item) => item.ratio >= 1.3 && item.amount >= 40000)
    .sort((a, b) => b.ratio - a.ratio)
    .slice(0, 4)
    .map((item) => ({
      category: item.category,
      currentAmount: item.amount,
      baselineReference: CATEGORY_AVERAGE[item.category] || item.amount,
    }))

  const expectedSaving = Math.max(8000, Math.round((totalExpense - OVERALL_BASELINE) / 24 / 1000) * 1000)

  return {
    totalExpense,
    totalIncome: MONTHLY_INCOME,
    byCategory,
    byCard,
    period: { currentMonth: monthKey },
    spendingTrend: {
      currentMonth: monthKey,
      total: {
        deltaFromPrevious: totalExpense - prevTotal,
        deltaFromBaseline: totalExpense - OVERALL_BASELINE,
      },
      reviewCandidates,
      oneTimeCandidates: [],
    },
    aiAnalysis: {
      savingOpportunities: [{ amount: expectedSaving }],
      cardInsights: byCard.map((item) => ({
        cardId: item.cardId,
        cardName: `카드 ${item.cardId}`,
        amount: item.amount,
        fit: '보통',
      })),
    },
  }
}

// 직전 달 카테고리 맵(증감 비교용) — 데모에 있으면 그 값을, 없으면 null
export function demoMonthCategories(monthKey) {
  return MONTHLY_CATEGORIES[monthKey] || null
}
