<template>
  <div class="desktop-page">
    <header class="landing-nav">
      <RouterLink class="brand" to="/">
        <span><CreditCard :size="18" /></span>
        CARCH
      </RouterLink>
      <div class="nav-actions">
        <RouterLink to="/login">로그인</RouterLink>
        <RouterLink class="primary-button" to="/signup">시작하기</RouterLink>
      </div>
    </header>

    <section class="landing-hero">
      <div class="hero-copy">
        <p class="eyebrow">국내 1위 카드 관리 서비스</p>
        <h1>CARCH</h1>
        <p class="lead">모든 카드를 한 곳에서 관리하고, AI 목표 지출 플래너로 큰 지출까지 계획하세요.</p>
        <div class="hero-actions">
          <RouterLink class="primary-button" to="/signup">무료로 시작하기</RouterLink>
          <RouterLink class="outline-button" to="/cards">앱 둘러보기</RouterLink>
        </div>
      </div>
      <div class="phone-preview" aria-label="CARCH 앱 미리보기">
        <div class="preview-screen">
          <div class="preview-header blue-gradient">
            <small>안녕하세요</small>
            <strong>김지훈님</strong>
            <div class="preview-stat">
              <span>이번 달 총 지출</span>
              <b>784,000원</b>
            </div>
          </div>
          <div class="preview-card blue-gradient">
            <span>VISA</span>
            <b>4521 **** **** 7892</b>
            <small>KIM JIHUN · 12/27</small>
          </div>
          <div class="preview-list">
            <div v-for="tx in transactions.slice(0, 4)" :key="tx.id">
              <span>{{ tx.icon }}</span>
              <strong>{{ tx.merchant }}</strong>
              <b>{{ krw(tx.amt) }}</b>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { CreditCard } from 'lucide-vue-next'
import { krw, transactions } from '@/data/mockData'
</script>

<style scoped>
.landing-nav {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #dbe4ee;
  padding: 16px clamp(20px, 5vw, 72px);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: #17202b;
  font-size: 20px;
  font-weight: 900;
  text-decoration: none;
}

.brand span {
  display: inline-flex;
  width: 34px;
  height: 34px;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: #0f5fae;
  color: #fff;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.nav-actions a {
  color: #6e6e73;
  font-size: 14px;
  font-weight: 800;
  text-decoration: none;
}

.nav-actions .primary-button {
  color: #fff;
}

.landing-hero {
  display: grid;
  min-height: calc(100dvh - 67px);
  grid-template-columns: minmax(0, 1fr) minmax(280px, 380px);
  align-items: center;
  gap: clamp(32px, 8vw, 96px);
  padding: clamp(36px, 8vw, 96px) clamp(20px, 8vw, 108px);
  background: #e7edf4;
}

.eyebrow {
  display: inline-flex;
  border-radius: 999px;
  margin: 0 0 22px;
  padding: 7px 12px;
  background: rgba(37, 99, 235, 0.1);
  color: #0f5fae;
  font-size: 12px;
  font-weight: 900;
}

h1 {
  margin: 0 0 16px;
  color: #17202b;
  font-size: clamp(52px, 10vw, 96px);
  font-weight: 900;
  letter-spacing: 0;
  line-height: 1;
}

.lead {
  max-width: 520px;
  margin: 0 0 28px;
  color: #6e6e73;
  font-size: clamp(17px, 2vw, 21px);
  line-height: 1.6;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.hero-actions a {
  text-decoration: none;
}

.phone-preview {
  justify-self: center;
  width: min(100%, 320px);
  border-radius: 42px;
  padding: 10px;
  background: #0f172a;
  box-shadow: 0 36px 80px rgba(16, 24, 40, 0.28);
}

.preview-screen {
  overflow: hidden;
  border-radius: 34px;
  background: #fbfdff;
}

.preview-header {
  padding: 28px 22px;
  color: #fff;
}

.preview-header small,
.preview-header span {
  display: block;
  color: rgba(255, 255, 255, 0.68);
  font-size: 12px;
}

.preview-header strong {
  display: block;
  margin-bottom: 14px;
  font-size: 22px;
  font-weight: 900;
}

.preview-stat {
  border-radius: 16px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.16);
}

.preview-card {
  margin: -18px 20px 18px;
  border-radius: 18px;
  padding: 18px;
  color: #fff;
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.28);
}

.preview-card span,
.preview-card small {
  display: block;
  color: rgba(255, 255, 255, 0.72);
  font-size: 11px;
}

.preview-card b {
  display: block;
  margin: 18px 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  letter-spacing: 0;
}

.preview-list {
  padding: 0 20px 24px;
}

.preview-list div {
  display: grid;
  grid-template-columns: 34px 1fr auto;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid #dbe4ee;
  padding: 11px 0;
}

.preview-list strong,
.preview-list b {
  color: #17202b;
  font-size: 13px;
}

@media (max-width: 760px) {
  .landing-hero {
    grid-template-columns: 1fr;
  }
}
</style>
