export const gradients = {
  blue: '#0f5fae',
  purple: '#24364f',
  pink: '#8a9aad',
  teal: '#008c95',
}

export const colors = {
  primary: '#0F5FAE',
  success: '#008C95',
  warning: '#C49A49',
  danger: '#D94A3A',
  surface: '#FBFDFF',
  muted: '#E7EDF4',
  border: '#DBE4EE',
  text: '#17202b',
  subtle: '#6e6e73',
}

export const user = {
  name: '남주현',
  email: 'juhyun@carch.kr',
  phone: '010-2577-0623',
  initials: '남',
}

export const cards = [
  {
    id: '10106',
    cardAdId: 10106,
    name: 'LOCA LIKIT Eat',
    issuer: '롯데카드',
    titleDescription: '식비와 카페 지출이 반복되는 생활권에 맞춘 카드',
    benefitSummary: '카페·음식점 생활권 집중 할인',
    benefits: ['카페 할인', '음식점 할인', '생활 영역 특화', '전월 실적 40만원'],
    benefitItems: [
      {
        type: 'discount_rate',
        scope: '카페',
        label: '카페 5%',
        ratePercent: 5,
        paymentMethodRules: { installmentBenefitEligible: true, interestFreeInstallmentEligible: true, source: 'demo_rule' },
      },
      {
        type: 'discount_rate',
        scope: '식비',
        label: '음식점 5%',
        ratePercent: 5,
        paymentMethodRules: { installmentBenefitEligible: true, interestFreeInstallmentEligible: true, source: 'demo_rule' },
      },
    ],
    annualFee: 10000,
    previousMonthMinSpend: 400000,
    previousMonthSpend: 460500,
    currentMonthSpend: 121100,
    imageUrl: '/card-images/10106.png',
    num: '5379 **** **** 7892',
    exp: '12/27',
    holder: 'NAM JUHYUN',
    limit: 1800000,
    spent: 121100,
    grad: 'teal',
    brand: 'VISA',
    lastSpent: 460500,
  },
  {
    id: '10612',
    cardAdId: 10612,
    name: '카드의정석2 SHOPPER',
    issuer: '우리카드',
    titleDescription: '생활잡화점, 뷰티편집숍까지 쇼핑할인 최대 15%',
    benefitSummary: '쇼핑 최대 15% 할인',
    benefits: ['온라인 쇼핑 10% 할인', '오프라인 쇼핑 10% 할인', '쇼핑멤버십 50% 할인'],
    benefitItems: [
      {
        type: 'discount_rate',
        scope: '쇼핑',
        label: '온라인 쇼핑 10%',
        ratePercent: 10,
        excludedPaymentMethods: ['interest_free_installment'],
        paymentMethodRules: { installmentBenefitEligible: true, interestFreeInstallmentEligible: false, source: 'demo_rule' },
      },
      {
        type: 'discount_rate',
        scope: '뷰티',
        label: '뷰티 10%',
        ratePercent: 10,
        excludedPaymentMethods: ['interest_free_installment'],
        paymentMethodRules: { installmentBenefitEligible: true, interestFreeInstallmentEligible: false, source: 'demo_rule' },
      },
    ],
    annualFee: 28000,
    previousMonthMinSpend: 500000,
    previousMonthSpend: 176000,
    currentMonthSpend: 551500,
    imageUrl: '/card-images/10612.png',
    num: '5412 **** **** 3345',
    exp: '08/26',
    holder: 'NAM JUHYUN',
    limit: 3000000,
    spent: 551500,
    grad: 'purple',
    brand: 'MASTERCARD',
    lastSpent: 176000,
  },
  {
    id: '10029',
    cardAdId: 10029,
    name: 'LOCA 100',
    issuer: '롯데카드',
    titleDescription: '일상 가맹점과 이동 지출을 넓게 받쳐주는 기본 카드',
    benefitSummary: '언제나 1.5% 할인',
    benefits: ['언제나 1.5% 할인', '주유소 최대 1% 할인', '대중교통 최대 1% 할인'],
    benefitItems: [
      {
        type: 'discount_rate',
        scope: '일상 가맹점',
        label: '일상 가맹점 1.5%',
        ratePercent: 1.5,
      },
    ],
    annualFee: 20000,
    previousMonthMinSpend: 750000,
    previousMonthSpend: 364100,
    currentMonthSpend: 379350,
    imageUrl: '/card-images/10029.png',
    num: '4521 **** **** 8810',
    exp: '03/28',
    holder: 'NAM JUHYUN',
    limit: 2000000,
    spent: 379350,
    grad: 'blue',
    brand: 'VISA',
    lastSpent: 364100,
  },
]

export const transactions = [
  { id: 't1', cardId: '10106', merchant: '컴포즈커피 역삼센터필드점', cat: '카페', amt: -3800, date: '2026-06-23', time: '08:42', icon: '☕', addr: '서울 강남구 테헤란로 231' },
  { id: 't2', cardId: '10106', merchant: '샐러디 역삼점', cat: '식비', amt: -10900, date: '2026-06-23', time: '12:18', icon: '🥗', addr: '서울 강남구 테헤란로 152' },
  { id: 't3', cardId: '10612', merchant: '스포애니 봉천점', cat: '헬스', amt: -59000, date: '2026-06-22', time: '21:20', icon: '🏋️', addr: '서울 관악구 봉천로 463' },
  { id: 't4', cardId: '10029', merchant: '카카오T 봉천→역삼', cat: '교통', amt: -13600, date: '2026-06-22', time: '08:06', icon: '🚕', addr: '봉천동 → 역삼동' },
  { id: 't5', cardId: '10612', merchant: '올리브영 강남타운점', cat: '뷰티', amt: -38500, date: '2026-06-21', time: '18:34', icon: '💄', addr: '서울 강남구 강남대로 408' },
  { id: 't6', cardId: '10029', merchant: 'CGV 용산아이파크몰', cat: '문화', amt: -32000, date: '2026-06-21', time: '20:10', icon: '🎬', addr: '서울 용산구 한강대로23길 55' },
  { id: 't7', cardId: '10612', merchant: '무신사 스토어', cat: '쇼핑', amt: -86400, date: '2026-06-20', time: '23:41', icon: '🛍️', addr: '온라인 결제', paymentType: 'installment', installmentMonths: 3, isInterestFreeInstallment: true },
  { id: 't8', cardId: '10612', merchant: '쿠팡 로켓배송', cat: '쇼핑', amt: -74200, date: '2026-06-20', time: '00:27', icon: '📦', addr: '온라인 결제' },
  { id: 't9', cardId: '10106', merchant: '인하대학교 생활협동조합', cat: '식비', amt: -7800, date: '2026-06-19', time: '13:05', icon: '🍱', addr: '인천 미추홀구 인하로 100' },
  { id: 't10', cardId: '10029', merchant: '공항철도·수도권전철', cat: '교통', amt: -6250, date: '2026-06-19', time: '09:12', icon: '🚇', addr: '봉천역 ↔ 인하대역' },
  { id: 't11', cardId: '10106', merchant: '스타벅스 인하대점', cat: '카페', amt: -5900, date: '2026-06-19', time: '15:36', icon: '☕', addr: '인천 미추홀구 인하로 67' },
  { id: 't12', cardId: '10106', merchant: 'GS25 봉천역점', cat: '편의점', amt: -6800, date: '2026-06-18', time: '23:12', icon: '🏪', addr: '서울 관악구 남부순환로 1728' },
  { id: 't13', cardId: '10106', merchant: '배달의민족 봉천동', cat: '식비', amt: -24500, date: '2026-06-18', time: '20:28', icon: '🍕', addr: '온라인 결제' },
  { id: 't14', cardId: '10612', merchant: '네이버플러스 멤버십', cat: '구독', amt: -4900, date: '2026-06-18', time: '00:10', icon: '📱', addr: '온라인 결제' },
  { id: 't15', cardId: '10029', merchant: '토익스피킹 응시료', cat: '교육', amt: -84000, date: '2026-06-17', time: '16:22', icon: '📚', addr: '온라인 결제' },
  { id: 't16', cardId: '10029', merchant: '링글 영어회화', cat: '교육', amt: -29000, date: '2026-06-17', time: '10:15', icon: '🗣️', addr: '온라인 결제' },
  { id: 't17', cardId: '10029', merchant: '교보문고 강남점', cat: '교육', amt: -18500, date: '2026-06-16', time: '19:04', icon: '📖', addr: '서울 강남구 강남대로 465' },
  { id: 't18', cardId: '10029', merchant: '단기 알바비 입금', cat: '수입', amt: 860000, date: '2026-06-16', time: '09:00', icon: '💰', addr: '-' },
  { id: 't19', cardId: '10106', merchant: '스타벅스 역삼포스코점', cat: '카페', amt: -6200, date: '2026-06-16', time: '08:31', icon: '☕', addr: '서울 강남구 테헤란로 440' },
  { id: 't20', cardId: '10106', merchant: '배달의민족 야근식사', cat: '식비', amt: -28600, date: '2026-06-15', time: '20:42', icon: '🍕', addr: '온라인 결제' },
  { id: 't21', cardId: '10106', merchant: '노티드 강남카카오점', cat: '카페', amt: -4800, date: '2026-06-15', time: '15:18', icon: '☕', addr: '서울 강남구 강남대로 429' },
  { id: 't22', cardId: '10106', merchant: '김밥천국 역삼점', cat: '식비', amt: -8200, date: '2026-06-14', time: '12:07', icon: '🍱', addr: '서울 강남구 논현로 508' },
  { id: 't23', cardId: '10029', merchant: 'CU 봉천중앙점', cat: '편의점', amt: -7200, date: '2026-06-14', time: '22:36', icon: '🏪', addr: '서울 관악구 봉천로 392' },
  { id: 't24', cardId: '10029', merchant: 'GS25 역삼타워점', cat: '편의점', amt: -6500, date: '2026-06-13', time: '18:52', icon: '🏪', addr: '서울 강남구 테헤란로 328' },
  { id: 't25', cardId: '10612', merchant: '마켓컬리 새벽배송', cat: '쇼핑', amt: -65300, date: '2026-06-13', time: '00:12', icon: '📦', addr: '온라인 결제' },
  { id: 't26', cardId: '10612', merchant: '오늘의집 책상·조명', cat: '쇼핑', amt: -128000, date: '2026-06-12', time: '22:16', icon: '🛍️', addr: '온라인 결제', paymentType: 'installment', installmentMonths: 6, isInterestFreeInstallment: false },
  { id: 't27', cardId: '10612', merchant: '쿠팡 면접 소품', cat: '쇼핑', amt: -52000, date: '2026-06-12', time: '10:24', icon: '📦', addr: '온라인 결제' },
  { id: 't28', cardId: '10029', merchant: '수도권전철 정기 이동', cat: '교통', amt: -7800, date: '2026-06-11', time: '08:11', icon: '🚇', addr: '봉천역 ↔ 역삼역' },
  { id: 't29', cardId: '10029', merchant: '카카오T 심야 귀가', cat: '교통', amt: -18600, date: '2026-06-10', time: '23:58', icon: '🚕', addr: '역삼동 → 봉천동' },
  { id: 't30', cardId: '10106', merchant: '버거킹 강남역점', cat: '식비', amt: -9700, date: '2026-06-10', time: '12:41', icon: '🍔', addr: '서울 강남구 강남대로 396' },
  { id: 't31', cardId: '10106', merchant: '스타벅스 선릉역점', cat: '카페', amt: -5600, date: '2026-06-09', time: '15:03', icon: '☕', addr: '서울 강남구 선릉로 427' },
  { id: 't32', cardId: '10029', merchant: '넷플릭스 정기결제', cat: '구독', amt: -17000, date: '2026-06-09', time: '00:04', icon: '📺', addr: '온라인 결제' },
  { id: 't33', cardId: '10612', merchant: '올리브영 선릉역점', cat: '뷰티', amt: -43200, date: '2026-06-08', time: '18:33', icon: '💄', addr: '서울 강남구 선릉로 517' },
  { id: 't34', cardId: '10029', merchant: 'SKT 휴대폰 요금', cat: '통신', amt: -69000, date: '2026-06-05', time: '09:00', icon: '📱', addr: '자동납부' },
  { id: 't35', cardId: '10106', merchant: '이디야커피 봉천점', cat: '카페', amt: -4200, date: '2026-06-04', time: '08:56', icon: '☕', addr: '서울 관악구 봉천로 365' },
  { id: 't36', cardId: '10029', merchant: '서울도시가스 요금', cat: '생활', amt: -64000, date: '2026-06-03', time: '09:00', icon: '🏠', addr: '자동납부' },
]

export const budgetCategories = [
  { id: 'b1', name: '식비', icon: '🥗', budget: 260000, spent: 43200, color: '#2c638f' },
  { id: 'b2', name: '쇼핑', icon: '🛍️', budget: 180000, spent: 160600, color: '#24364f' },
  { id: 'b3', name: '교통', icon: '🚇', budget: 80000, spent: 19850, color: '#0f5fae' },
  { id: 'b4', name: '카페', icon: '☕', budget: 70000, spent: 9700, color: '#C49A49' },
  { id: 'b5', name: '헬스', icon: '🏋️', budget: 80000, spent: 59000, color: '#008c95' },
  { id: 'b6', name: '교육', icon: '📚', budget: 150000, spent: 131500, color: '#8a9aad' },
  { id: 'b7', name: '데이트·문화', icon: '🎬', budget: 120000, spent: 70500, color: '#d76a52' },
  { id: 'b8', name: '구독', icon: '📱', budget: 30000, spent: 4900, color: '#5B6777' },
]

export const communityPosts = [
  { id: 'c1', title: 'LOCA LIKIT Eat vs 카드의정석2 SHOPPER 비교 후기', body: '6개월 사용 후 솔직한 후기 작성합니다. LIKIT Eat는 식비와 카페 결제 관리가 편하고, 카드의정석2 SHOPPER는 쇼핑 혜택이 매력적이에요.', author: '이승민', avatar: '이', date: '2026-06-22', likes: 47, comments: 12, liked: false, tags: ['카드비교', '생활카드'] },
  { id: 'c2', title: '월 30만원으로 카드 혜택 최대화하는 법', body: '실적 채우기 어려운 분들을 위한 가이드입니다. 필수 지출 항목부터 카드 혜택을 최대로 누리는 방법을 공유합니다.', author: '박서연', avatar: '박', date: '2026-06-21', likes: 89, comments: 23, liked: true, tags: ['카드전략', '혜택최대화'] },
  { id: 'c3', title: 'LOCA 100을 보조 카드로 두는 방식', body: '주력 할인 카드가 애매한 결제는 LOCA 100 같은 기본 할인 카드로 받쳐두는 방식이 깔끔했습니다.', author: '최민준', avatar: '최', date: '2026-06-20', likes: 34, comments: 8, liked: false, tags: ['롯데카드', '생활'] },
]

export const notifications = [
  { id: 'n1', type: 'payment', title: '결제 알림', body: '컴포즈커피 역삼센터필드점에서 3,800원이 결제되었습니다.', time: '방금 전', read: false },
  { id: 'n2', type: 'budget', title: '쇼핑 예산 점검', body: '면접 준비 쇼핑 지출이 예산의 89%에 도달했습니다.', time: '1시간 전', read: false },
  { id: 'n3', type: 'recommend', title: '카드 교체 인사이트', body: '역삼 생활권과 온라인 쇼핑 비중을 반영한 추천이 갱신되었습니다.', time: '3시간 전', read: false },
]

export const recommendations = [
  { id: 'r1', cardAdId: 10107, issuer: '롯데카드', name: 'LOCA LIKIT Shop', match: 94, benefit: '온라인 쇼핑·편의점 집중 할인', annualFee: 10000, previousMonthMinSpend: 400000, tags: ['쇼핑', '편의점'], grad: 'purple', imageUrl: '/card-images/10107.png', highlights: ['온라인 쇼핑 할인', '편의점 할인', '생활 쇼핑 특화', '전월 실적 40만원'] },
  { id: 'r2', cardAdId: 10071, issuer: '롯데카드', name: 'LOCA LIKIT', match: 88, benefit: '카페·생활 결제 특화 할인', annualFee: 10000, previousMonthMinSpend: 400000, tags: ['카페', '생활'], grad: 'teal', imageUrl: '/card-images/10071.png', highlights: ['카페 할인', '생활 영역 할인', '전월 실적 40만원'] },
  { id: 'r3', cardAdId: 10029, issuer: '롯데카드', name: 'LOCA 100', match: 82, benefit: '일상 가맹점 기본 할인', annualFee: 20000, previousMonthMinSpend: 750000, tags: ['생활', '교통'], grad: 'blue', imageUrl: '/card-images/10029.png', highlights: ['언제나 1.5% 할인', '대중교통 최대 1%', '전월 실적 75만원'] },
]

export const planTypes = ['큰 지출', '취업 준비', '여행', '기념일', '운동', '전자기기', '학업', '기타']
export const strategies = ['혜택 최대화', '예산 안정', '다음 달 조건 준비']
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
  { label: '취업 준비 80만 원', text: '7월부터 취업 준비 예산 80만 원을 관리하고 싶어요.\n정장 셔츠, 구두, 증명사진, 토익스피킹 응시료를 순서대로 결제할 예정입니다.' },
  { label: '기념일 데이트 45만 원', text: '다음 달 여자친구와 기념일이 있어서 45만 원 정도 준비하려고 해요.\n식사, 영화, 작은 선물까지 포함해서 카드 혜택을 보고 싶습니다.' },
  { label: '헬스 3개월 35만 원', text: '헬스장 3개월권과 보충제, 운동복을 합쳐 35만 원 안에서 계획하고 싶어요.\n정기 지출과 쇼핑 지출을 나눠서 보고 싶습니다.' },
  { label: '노트북 교체 140만 원', text: '코딩 테스트와 과제용 노트북을 140만 원 안에서 교체하려고 해요.\n카드 혜택과 전월 실적을 같이 보면서 결제 월을 정하고 싶습니다.' },
]

export const mockPlans = [
  {
    id: 'p1',
    title: '취업 준비 지출 계획',
    type: '취업 준비',
    totalBudget: 800000,
    startMonth: '2026-07',
    endMonth: '2026-08',
    status: '선택 완료',
    selectedScenarioId: 'sc1',
    createdAt: '2026-06-23',
    progress: 0,
    items: [
      { id: 'i1', name: '정장 셔츠·슬랙스', category: '쇼핑', amount: 210000, targetMonth: '2026-07', required: true, flexible: false },
      { id: 'i2', name: '구두', category: '쇼핑', amount: 160000, targetMonth: '2026-07', required: true, flexible: true },
      { id: 'i3', name: '증명사진', category: '취업', amount: 50000, targetMonth: '2026-07', required: true, flexible: false },
      { id: 'i4', name: '어학 응시료', category: '교육', amount: 84000, targetMonth: '2026-08', required: true, flexible: false },
      { id: 'i5', name: '면접 교통비', category: '교통', amount: 90000, targetMonth: '2026-08', required: false, flexible: true },
    ],
    scenarios: [
      {
        id: 'sc1',
        type: '혜택 최대화',
        recommended: true,
        totalAmount: 594000,
        totalBenefit: 39520,
        budgetDiff: 206000,
        maxMonthlySpend: 420000,
        achievedCards: 2,
        reasons: ['식비와 카페는 LOCA LIKIT Eat로 집중', '쇼핑은 카드의정석2 SHOPPER, 이동과 기타 결제는 LOCA 100으로 분리'],
        warning: null,
        monthlyPlan: [
          { month: '2026-07', items: [
            { name: '정장 셔츠·슬랙스', amount: 210000, card: '카드의정석2 SHOPPER', benefit: 21000, note: '온라인 쇼핑 혜택과 실적을 함께 반영합니다.', status: '구매 예정' },
            { name: '구두', amount: 160000, card: '카드의정석2 SHOPPER', benefit: 16000, note: '쇼핑 지출을 한 카드에 모아 혜택 누락을 줄입니다.', status: '구매 예정' },
            { name: '증명사진', amount: 50000, card: 'LOCA LIKIT Eat', benefit: 1500, note: '소액 오프라인 결제는 생활 카드로 묶어 관리합니다.', status: '예약 예정' },
          ] },
          { month: '2026-08', items: [
            { name: '어학 응시료', amount: 84000, card: 'LOCA 100', benefit: 1260, note: '교육비는 기본 할인 카드에 배정해 지출 흐름을 안정적으로 관리합니다.', status: '결제 예정' },
            { name: '면접 교통비', amount: 90000, card: 'LOCA 100', benefit: 900, note: '면접 동선이 늘어나는 달에는 교통비를 따로 추적합니다.', status: '사용 예정' },
          ] },
        ],
        cardSummary: [
          { cardName: 'LOCA LIKIT Eat', totalAmount: 50000, benefit: 1500, achieved: false, remainingLimit: 348500, itemCount: 1 },
          { cardName: '카드의정석2 SHOPPER', totalAmount: 370000, benefit: 37000, achieved: true, remainingLimit: 0, itemCount: 2 },
          { cardName: 'LOCA 100', totalAmount: 174000, benefit: 2160, achieved: false, remainingLimit: 573840, itemCount: 2 },
        ],
        aiExplanation: '취업 준비 지출은 쇼핑, 생활, 이동으로 나뉩니다. 쇼핑 결제는 SHOPPER에 모아 혜택을 선명하게 만들고, 식비·카페성 소액 결제는 LOCA LIKIT Eat, 이동과 기타 결제는 LOCA 100으로 정리하는 구성이 적합합니다.',
      },
      {
        id: 'sc2',
        type: '예산 안정',
        recommended: false,
        totalAmount: 594000,
        totalBenefit: 18400,
        budgetDiff: 206000,
        maxMonthlySpend: 300000,
        achievedCards: 1,
        reasons: ['7월과 8월 지출을 나누어 현금 흐름 안정', '필수 항목 우선 결제로 예산 초과 위험 축소'],
        warning: null,
        monthlyPlan: [
          { month: '2026-07', items: [{ name: '셔츠·증명사진', amount: 260000, card: '카드의정석2 SHOPPER', benefit: 16000, note: '필수 준비물을 먼저 결제합니다.', status: '구매 예정' }] },
          { month: '2026-08', items: [{ name: '구두·응시료·교통비', amount: 334000, card: 'LOCA 100', benefit: 2400, note: '다음 달 지출로 나누어 부담을 낮춥니다.', status: '구매 예정' }] },
        ],
        cardSummary: [
          { cardName: 'LOCA 100', totalAmount: 334000, benefit: 2400, achieved: false, remainingLimit: 413600, itemCount: 3 },
          { cardName: '카드의정석2 SHOPPER', totalAmount: 260000, benefit: 16000, achieved: false, remainingLimit: 240000, itemCount: 2 },
        ],
        aiExplanation: '혜택 규모는 조금 줄어들지만 취준 기간의 월별 부담을 고르게 유지합니다. 다음 달 면접 일정이 확정될 때 교통비만 조정하면 됩니다.',
      },
      {
        id: 'sc3',
        type: '다음 달 조건 준비',
        recommended: false,
        totalAmount: 594000,
        totalBenefit: 21870,
        budgetDiff: 206000,
        maxMonthlySpend: 360000,
        achievedCards: 2,
        reasons: ['다음 달 혜택 조건을 카드별로 고르게 준비', '교육·교통·쇼핑 지출이 한쪽으로 몰리지 않음'],
        warning: 'LOCA LIKIT Eat는 다음 달 혜택 조건까지 아직 여유가 있습니다.',
        monthlyPlan: [],
        cardSummary: [
          { cardName: 'LOCA LIKIT Eat', totalAmount: 230000, benefit: 6900, achieved: false, remainingLimit: 170000, itemCount: 2 },
          { cardName: '카드의정석2 SHOPPER', totalAmount: 280000, benefit: 18000, achieved: false, remainingLimit: 220000, itemCount: 2 },
          { cardName: 'LOCA 100', totalAmount: 84000, benefit: 1260, achieved: false, remainingLimit: 666000, itemCount: 1 },
        ],
        aiExplanation: '세 카드 모두에 지출을 나누어 다음 달 혜택 조건을 준비합니다. 다만 현재 소비 규모에서는 SHOPPER 중심 전략이 더 높은 절감 효과를 냅니다.',
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
