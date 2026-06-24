<template>
  <section class="screen">
    <header class="simple-header blue-gradient">
      <AppBackButton fallback="/cards" />
      <div>
        <h1>개발자 패널</h1>
        <p>모든 프론트 화면을 여기서 바로 열 수 있어요.</p>
      </div>
    </header>

    <div class="screen-scroll scrollbar-hide page-padding">
      <p class="dev-note">파라미터 화면은 mock 데이터 샘플 ID로 연결돼 있어요. ({{ routeCount }}개 화면)</p>

      <section v-for="group in groups" :key="group.title" class="dev-group">
        <h2>{{ group.title }}</h2>
        <div class="dev-grid">
          <RouterLink
            v-for="item in group.items"
            :key="item.path"
            class="dev-link"
            :class="{ current: route.path === item.path }"
            :to="item.path"
          >
            <strong>{{ item.label }}</strong>
            <span>{{ item.path }}</span>
          </RouterLink>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppBackButton from '@/components/AppBackButton.vue'

const route = useRoute()

const groups = [
  {
    title: '시작 · 인증',
    items: [
      { label: '랜딩', path: '/' },
      { label: '로그인', path: '/login' },
      { label: '회원가입', path: '/signup' },
    ],
  },
  {
    title: '카드',
    items: [
      { label: '대시보드(메인)', path: '/cards' },
      { label: '카드 상세', path: '/cards/10029' },
      { label: '카드 신청', path: '/cards/apply/10029' },
    ],
  },
  {
    title: '거래내역',
    items: [
      { label: '거래 전체보기', path: '/transactions' },
      { label: '결제 추가', path: '/transactions/new' },
      { label: '거래 상세', path: '/transactions/t1' },
    ],
  },
  {
    title: '소비계획',
    items: [
      { label: '소비계획 홈', path: '/budget' },
      { label: '예산 추가', path: '/budget/new' },
      { label: '예산 상세', path: '/budget/current' },
    ],
  },
  {
    title: '목표 지출',
    items: [
      { label: '목표 지출 목록', path: '/plans' },
      { label: '목표 지출 생성', path: '/plans/new' },
      { label: '목표 지출 상세', path: '/plans/p1' },
    ],
  },
  {
    title: '추천',
    items: [
      { label: '카드 추천', path: '/recommendations/new' },
      { label: '추천 상세', path: '/recommendations/r1' },
    ],
  },
  {
    title: '커뮤니티',
    items: [
      { label: '커뮤니티 목록', path: '/community' },
      { label: '글 작성', path: '/community/new' },
      { label: '게시글 상세', path: '/community/c1' },
      { label: '글 수정', path: '/community/c1/edit' },
    ],
  },
  {
    title: 'AI · 분석',
    items: [
      { label: '카치 AI 채팅', path: '/chat' },
      { label: '분석', path: '/analytics' },
      { label: '월간 리포트', path: '/reports/monthly' },
    ],
  },
  {
    title: '설정 · 기타',
    items: [
      { label: '알림', path: '/notifications' },
      { label: '설정', path: '/settings' },
      { label: '알림 설정', path: '/settings/notifications' },
      { label: '프로필 수정', path: '/settings/profile' },
      { label: '보안 설정', path: '/settings/security' },
      { label: '검색', path: '/search' },
    ],
  },
]

const routeCount = computed(() => groups.reduce((sum, group) => sum + group.items.length, 0))
</script>

<style scoped>
.simple-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 24px 20px;
  color: #fff;
}

.simple-header h1 {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 900;
}

.simple-header p {
  margin: 0;
  color: rgba(255, 255, 255, 0.68);
  font-size: 12px;
  font-weight: 700;
}

.page-padding {
  padding: 18px 20px 116px;
}

.dev-note {
  margin: 0 0 18px;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.5;
}

.dev-group {
  margin-bottom: 22px;
}

.dev-group h2 {
  margin: 0 0 10px;
  color: #2c4e72;
  font-size: 13px;
  font-weight: 900;
  letter-spacing: 0.3px;
}

.dev-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.dev-link {
  display: block;
  border-radius: 13px;
  padding: 12px 13px;
  background: rgba(44, 78, 114, 0.05);
  color: inherit;
  text-decoration: none;
}

.dev-link.current {
  background: linear-gradient(150deg, #2c4e72, #1c3149);
}

.dev-link.current strong,
.dev-link.current span {
  color: #fff;
}

.dev-link strong {
  display: block;
  color: #20242a;
  font-size: 13px;
  font-weight: 900;
}

.dev-link span {
  display: block;
  margin-top: 3px;
  color: #8a9aad;
  font-size: 10px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
</style>
