export const gradients = {
  blue: '#0f5fae',
  purple: '#24364f',
  pink: '#8a9aad',
  teal: '#008c95',
}

export const colors = {
  primary: '#0B63CE',
  success: '#008E98',
  warning: '#C49A49',
  danger: '#D92D20',
  surface: '#FBFDFF',
  muted: '#E7EDF4',
  border: '#DBE4EE',
  text: '#17202b',
  subtle: '#6e6e73',
}

export const user = {
  name: '김지훈',
  email: 'jihun@carch.kr',
  phone: '010-1234-5678',
  initials: '김',
}

export const cards = [
  {
    id: '10029',
    cardAdId: 10029,
    name: 'LOCA 100',
    issuer: '롯데카드',
    titleDescription: '선넘은 카드의 일당백 할인 혜택',
    benefitSummary: '언제나 1.5% 할인',
    benefits: ['언제나 1.5% 할인', '주유소 최대 1% 할인', '대중교통 최대 1% 할인'],
    annualFee: 20000,
    previousMonthMinSpend: 750000,
    imageUrl: '/card-images/10029.png',
    num: '4521 **** **** 7892',
    exp: '12/27',
    holder: 'KIM JIHUN',
    limit: 5000000,
    spent: 485000,
    grad: 'blue',
    brand: 'VISA',
    lastSpent: 620000,
  },
  {
    id: '10612',
    cardAdId: 10612,
    name: '카드의정석2 SHOPPER',
    issuer: '우리카드',
    titleDescription: '생활잡화점, 뷰티편집숍까지 쇼핑할인 최대 15%',
    benefitSummary: '쇼핑 최대 15% 할인',
    benefits: ['온라인 쇼핑 10% 할인', '오프라인 쇼핑 10% 할인', '쇼핑멤버십 50% 할인'],
    annualFee: 28000,
    previousMonthMinSpend: 500000,
    imageUrl: '/card-images/10612.png',
    num: '5412 **** **** 3345',
    exp: '08/26',
    holder: 'KIM JIHUN',
    limit: 3000000,
    spent: 210000,
    grad: 'purple',
    brand: 'MASTERCARD',
    lastSpent: 380000,
  },
  {
    id: '10609',
    cardAdId: 10609,
    name: '이마트 신한카드',
    issuer: '신한카드',
    titleDescription: '이마트에서는 크게, 일상에서는 꾸준한 할인',
    benefitSummary: '이마트 계열 15% 할인',
    benefits: ['이마트 계열 15% 할인', '국내외 가맹점 0.5% 적립', '전월 실적 40만원'],
    annualFee: 18000,
    previousMonthMinSpend: 400000,
    imageUrl: '/card-images/10609.png',
    num: '3591 **** **** 8810',
    exp: '03/28',
    holder: 'KIM JIHUN',
    limit: 2000000,
    spent: 89000,
    grad: 'teal',
    brand: 'VISA',
    lastSpent: 142000,
  },
]

export const transactions = [
  { id: 't1', cardId: '10029', merchant: '스타벅스 강남역점', cat: '카페', amt: -5500, date: '2026-06-22', time: '09:14', icon: '☕', addr: '서울 강남구 강남대로 396' },
  { id: 't2', cardId: '10612', merchant: '쿠팡', cat: '쇼핑', amt: -89000, date: '2026-06-22', time: '01:33', icon: '📦', addr: '온라인 결제' },
  { id: 't3', cardId: '10612', merchant: 'GS25', cat: '편의점', amt: -3200, date: '2026-06-21', time: '22:48', icon: '🏪', addr: '서울 서초구 서초대로 77' },
  { id: 't4', cardId: '10612', merchant: '올리브영', cat: '뷰티', amt: -32500, date: '2026-06-21', time: '14:22', icon: '💄', addr: '서울 강남구 테헤란로 231' },
  { id: 't5', cardId: '10029', merchant: '맥도날드', cat: '식비', amt: -8700, date: '2026-06-21', time: '12:05', icon: '🍔', addr: '서울 강남구 강남대로 112' },
  { id: 't6', cardId: '10609', merchant: 'CGV 강남', cat: '문화', amt: -15000, date: '2026-06-20', time: '19:30', icon: '🎬', addr: '서울 강남구 강남대로 438' },
  { id: 't7', cardId: '10609', merchant: '이마트', cat: '마트', amt: -67800, date: '2026-06-20', time: '16:14', icon: '🛒', addr: '서울 강남구 양재대로 2' },
  { id: 't8', cardId: '10029', merchant: '카카오택시', cat: '교통', amt: -12500, date: '2026-06-19', time: '23:45', icon: '🚕', addr: '강남역 → 합정역' },
  { id: 't9', cardId: '10029', merchant: '배달의민족', cat: '식비', amt: -24000, date: '2026-06-19', time: '20:02', icon: '🍕', addr: '온라인 결제' },
  { id: 't10', cardId: '10612', merchant: '넷플릭스', cat: '구독', amt: -17000, date: '2026-06-18', time: '00:00', icon: '📺', addr: '온라인 결제' },
  { id: 't11', cardId: '10029', merchant: '급여 입금', cat: '수입', amt: 3200000, date: '2026-06-17', time: '09:00', icon: '💰', addr: '-' },
  { id: 't12', cardId: '10612', merchant: '편의점 CU', cat: '편의점', amt: -4800, date: '2026-06-16', time: '08:31', icon: '🏪', addr: '서울 강남구 선릉로 100' },
]

export const budgetCategories = [
  { id: 'b1', name: '식비', icon: '🍔', budget: 300000, spent: 210000, color: '#D92D20' },
  { id: 'b2', name: '쇼핑', icon: '🛍️', budget: 200000, spent: 89000, color: '#24364f' },
  { id: 'b3', name: '교통', icon: '🚕', budget: 100000, spent: 87500, color: '#0B63CE' },
  { id: 'b4', name: '카페', icon: '☕', budget: 80000, spent: 45500, color: '#C49A49' },
  { id: 'b5', name: '문화', icon: '🎬', budget: 100000, spent: 15000, color: '#008E98' },
  { id: 'b6', name: '구독', icon: '📺', budget: 50000, spent: 17000, color: '#8A9AAD' },
  { id: 'b7', name: '뷰티', icon: '💄', budget: 80000, spent: 32500, color: '#C49A49' },
]

export const communityPosts = [
  { id: 'c1', title: 'LOCA 100 vs 카드의정석2 SHOPPER 비교 후기', body: '6개월 사용 후 솔직한 후기 작성합니다. LOCA 100은 일상 할인 폭이 안정적이고, 카드의정석2 SHOPPER는 쇼핑 혜택이 매력적이에요.', author: '이승민', avatar: '이', date: '2026-06-22', likes: 47, comments: 12, liked: false, tags: ['카드비교', '롯데카드'] },
  { id: 'c2', title: '월 30만원으로 카드 혜택 최대화하는 법', body: '실적 채우기 어려운 분들을 위한 가이드입니다. 필수 지출 항목부터 카드 혜택을 최대로 누리는 방법을 공유합니다.', author: '박서연', avatar: '박', date: '2026-06-21', likes: 89, comments: 23, liked: true, tags: ['카드전략', '혜택최대화'] },
  { id: 'c3', title: '이마트 신한카드 이 혜택 아셨나요?', body: '많은 분들이 모르고 있는 이마트 신한카드의 마트 혜택과 기본 적립 조건을 소개합니다.', author: '최민준', avatar: '최', date: '2026-06-20', likes: 34, comments: 8, liked: false, tags: ['신한카드', '마트'] },
]

export const notifications = [
  { id: 'n1', type: 'payment', title: '결제 알림', body: '스타벅스 강남역점에서 5,500원이 결제되었습니다.', time: '방금 전', read: false },
  { id: 'n2', type: 'budget', title: '예산 경고', body: '교통 예산의 87.5%를 사용했습니다. 잔여 12,500원', time: '1시간 전', read: false },
  { id: 'n3', type: 'recommend', title: '새로운 카드 추천', body: '지출 패턴 분석 결과 맞춤 카드 2종이 추천되었습니다.', time: '3시간 전', read: false },
]

export const recommendations = [
  { id: 'r1', cardAdId: 10612, issuer: '우리카드', name: '카드의정석2 SHOPPER', match: 94, benefit: '온라인·오프라인 쇼핑 최대 15% 할인', annualFee: 28000, previousMonthMinSpend: 500000, tags: ['쇼핑', '간편결제'], grad: 'purple', imageUrl: '/card-images/10612.png', highlights: ['온라인 쇼핑 10% 할인', '오프라인 쇼핑 10% 할인', '쇼핑멤버십 50% 할인', '전월 실적 50만원'] },
  { id: 'r2', cardAdId: 10029, issuer: '롯데카드', name: 'LOCA 100', match: 89, benefit: '일상 가맹점 언제나 1.5% 할인', annualFee: 20000, previousMonthMinSpend: 750000, tags: ['생활', '교통'], grad: 'blue', imageUrl: '/card-images/10029.png', highlights: ['언제나 1.5% 할인', '주유소 최대 1% 할인', '대중교통 최대 1% 할인', '전월 실적 75만원'] },
  { id: 'r3', cardAdId: 10609, issuer: '신한카드', name: '이마트 신한카드', match: 84, benefit: '이마트 계열 이용금액 15% 할인', annualFee: 18000, previousMonthMinSpend: 400000, tags: ['마트', '신한카드'], grad: 'teal', imageUrl: '/card-images/10609.png', highlights: ['이마트 계열 15% 할인', '국내외 가맹점 0.5% 적립', '전월 실적 40만원', 'VISA 연회비 18,000원'] },
]

export const planTypes = ['혼수', '이사', '여행', '육아', '기타']
export const strategies = ['혜택 최대화', '예산 안정', '카드 실적 균형']
export const expenseModes = [
  {
    id: 'within-budget',
    label: '예산 안에서 준비',
    title: '생활비 안에서 모으기',
    description: '월 예산 일부를 따로 떼어 큰 지출을 준비합니다.',
  },
  {
    id: 'planned-extra',
    label: '예산 밖 예정 지출',
    title: '따로 나갈 돈으로 관리',
    description: '여행, 가전, 이사처럼 월 예산과 별도로 계획합니다.',
  },
  {
    id: 'unexpected-extra',
    label: '추가 지출로 기록',
    title: '갑자기 생긴 지출',
    description: '수리비나 긴급 결제처럼 예상 밖 지출로 분리합니다.',
  },
]

export const exampleChips = [
  { label: '혼수가전 700만 원', text: '10월 결혼 예정이고 혼수가전 예산은 700만 원이에요.\n7월부터 9월까지 냉장고, TV, 세탁기와 건조기를 구매하고 싶어요.' },
  { label: '이사 가구 500만 원', text: '새 집으로 이사를 가는데 가구 예산이 500만 원이에요.\n8월부터 10월 사이에 소파, 침대, 식탁을 구매할 계획입니다.' },
  { label: '유럽여행 400만 원', text: '11월 유럽여행 예산은 400만 원이에요.\n9월에 항공권, 10월에 숙박과 여행자보험을 준비하려고 합니다.' },
  { label: '출산 준비 300만 원', text: '내년 3월 출산 예정이고 준비 예산은 300만 원이에요.\n12월부터 2월까지 유모차, 카시트, 아기용품을 구매할 계획입니다.' },
]

export const mockPlans = [
  {
    id: 'p1',
    title: '혼수가전 구매 계획',
    type: '혼수',
    totalBudget: 7000000,
    startMonth: '2026-07',
    endMonth: '2026-09',
    status: '선택 완료',
    selectedScenarioId: 'sc1',
    createdAt: '2026-06-20',
    progress: 0,
    items: [
      { id: 'i1', name: '냉장고', category: '가전', amount: 2500000, targetMonth: '2026-07', required: true, flexible: false },
      { id: 'i2', name: '세탁기', category: '가전', amount: 1200000, targetMonth: '2026-08', required: true, flexible: true },
      { id: 'i3', name: '건조기', category: '가전', amount: 1000000, targetMonth: '2026-08', required: true, flexible: true },
      { id: 'i4', name: 'TV', category: '가전', amount: 1800000, targetMonth: '2026-09', required: false, flexible: true },
    ],
    scenarios: [
      {
        id: 'sc1',
        type: '혜택 최대화',
        recommended: true,
        totalAmount: 6500000,
        totalBenefit: 75000,
        budgetDiff: 500000,
        maxMonthlySpend: 2500000,
        achievedCards: 2,
        reasons: ['7월 LOCA 100 생활 할인 우선 활용', '8월 카드의정석2 SHOPPER 쇼핑 혜택 집중'],
        warning: null,
        monthlyPlan: [
          { month: '2026-07', items: [{ name: '냉장고', amount: 2500000, card: 'LOCA 100', benefit: 30000, note: '큰 금액 결제 전 실적 조건을 함께 확인합니다.', status: '구매 예정' }] },
          { month: '2026-08', items: [
            { name: '세탁기', amount: 1200000, card: '카드의정석2 SHOPPER', benefit: 25000, note: '쇼핑 혜택을 받을 수 있는 결제처를 우선 검토합니다.', status: '구매 예정' },
            { name: '건조기', amount: 1000000, card: '카드의정석2 SHOPPER', benefit: 0, note: '동일 카드 월 혜택 한도 초과 여부를 확인해야 합니다.', status: '구매 예정' },
          ] },
          { month: '2026-09', items: [{ name: 'TV', amount: 1800000, card: 'LOCA 100', benefit: 20000, note: '월 혜택 한도가 초기화된 이후 사용하는 계획입니다.', status: '구매 예정' }] },
        ],
        cardSummary: [
          { cardName: 'LOCA 100', totalAmount: 4300000, benefit: 50000, achieved: true, remainingLimit: 100000, itemCount: 2 },
          { cardName: '카드의정석2 SHOPPER', totalAmount: 2200000, benefit: 25000, achieved: true, remainingLimit: 0, itemCount: 2 },
        ],
        aiExplanation: '7월과 9월에는 LOCA 100을 큰 결제에 배정하고, 8월에는 카드의정석2 SHOPPER의 쇼핑 혜택을 우선 확인하는 방식입니다. 실제 카드 DB의 전월 실적과 혜택 유형을 기준으로 더 정교하게 확장할 수 있습니다.',
      },
      {
        id: 'sc2',
        type: '예산 안정',
        recommended: false,
        totalAmount: 6500000,
        totalBenefit: 55000,
        budgetDiff: 500000,
        maxMonthlySpend: 2200000,
        achievedCards: 1,
        reasons: ['월별 지출이 220만원 이하로 분산', '예산 초과 위험 최소화'],
        warning: null,
        monthlyPlan: [
          { month: '2026-07', items: [{ name: '냉장고', amount: 2200000, card: 'LOCA 100', benefit: 25000, note: '예산 분산을 위해 일부 비용을 8월로 이연합니다.', status: '구매 예정' }] },
          { month: '2026-08', items: [{ name: '세탁기·건조기', amount: 2200000, card: '카드의정석2 SHOPPER', benefit: 20000, note: '세트 구매로 배송비를 절감할 수 있습니다.', status: '구매 예정' }] },
          { month: '2026-09', items: [{ name: 'TV', amount: 1800000, card: 'LOCA 100', benefit: 10000, note: '추가 할인 이벤트 기간에 구매를 권장합니다.', status: '구매 예정' }] },
        ],
        cardSummary: [
          { cardName: 'LOCA 100', totalAmount: 4000000, benefit: 35000, achieved: true, remainingLimit: 150000, itemCount: 2 },
          { cardName: '카드의정석2 SHOPPER', totalAmount: 2200000, benefit: 20000, achieved: false, remainingLimit: 50000, itemCount: 1 },
        ],
        aiExplanation: '지출을 3개월에 균등하게 배분하여 특정 월에 지출이 몰리지 않도록 계획했습니다. 예산 초과 위험이 낮고 현금 흐름 관리에 유리합니다.',
      },
      {
        id: 'sc3',
        type: '실적 균형',
        recommended: false,
        totalAmount: 6500000,
        totalBenefit: 65000,
        budgetDiff: 500000,
        maxMonthlySpend: 2300000,
        achievedCards: 2,
        reasons: ['두 카드 모두 월 실적 조건 충족 가능', '혜택 한도 미소진 카드 없음'],
        warning: '9월 LOCA 100 월 혜택 한도 소진 가능성 있음',
        monthlyPlan: [],
        cardSummary: [
          { cardName: 'LOCA 100', totalAmount: 3700000, benefit: 40000, achieved: true, remainingLimit: 0, itemCount: 2 },
          { cardName: '카드의정석2 SHOPPER', totalAmount: 2800000, benefit: 25000, achieved: true, remainingLimit: 30000, itemCount: 2 },
        ],
        aiExplanation: '두 카드의 실적 조건을 함께 고려해 각 월에 최적 카드를 배정했습니다. 한 카드에 지출이 편중되지 않아 다음 달 혜택 한도도 고르게 유지됩니다.',
      },
    ],
  },
]

export const clone = (value) => JSON.parse(JSON.stringify(value))
export const krw = (n) => `${new Intl.NumberFormat('ko-KR').format(Math.abs(Number(n) || 0))}원`
export const monthLabel = (month) => {
  if (!month) return '-'
  const [year, rawMonth] = month.split('-')
  return `${year}년 ${Number(rawMonth)}월`
}
