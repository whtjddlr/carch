<template>
  <section class="screen privacy-screen">
    <header class="privacy-header">
      <AppBackButton fallback="/settings" />
      <div>
        <span>CARCH</span>
        <h1>개인정보 처리방침</h1>
        <p>시행일: 2026년 7월 3일</p>
      </div>
    </header>

    <div class="screen-scroll scrollbar-hide privacy-body">
      <article class="app-card privacy-card">
        <h2>수집하는 정보</h2>
        <p>회원가입과 로그인에 필요한 이메일, 이름, 인증 세션 정보를 수집합니다.</p>
        <p>{{ collectedDataText }}</p>
      </article>

      <article class="app-card privacy-card">
        <h2>이용 목적</h2>
        <p>{{ purposeText }}</p>
        <p>AI 상담은 사용자가 요청한 질문에 답변하기 위한 컨텍스트로만 사용합니다.</p>
      </article>

      <article class="app-card privacy-card">
        <h2>보관 및 삭제</h2>
        <p>계정 데이터는 사용자가 계정을 유지하는 동안 보관합니다.</p>
        <p>{{ deletionText }}</p>
      </article>

      <article class="app-card privacy-card">
        <h2>제3자 제공</h2>
        <p>서비스 운영에 필요한 백엔드, 데이터베이스, 배포 인프라 외에 개인정보를 판매하거나 임의 제공하지 않습니다.</p>
        <p>카드 추천 결과는 실제 카드사 정책과 다를 수 있으며, 최종 조건은 카드사 공식 안내를 확인해야 합니다.</p>
      </article>

      <article class="app-card privacy-card">
        <h2>문의</h2>
        <p>개인정보 처리와 계정 삭제 관련 문의는 앱 설정의 계정 삭제 기능 또는 서비스 운영자에게 요청할 수 있습니다.</p>
      </article>
    </div>
  </section>
</template>

<script setup>
import AppBackButton from '@/components/AppBackButton.vue'

const collectedDataText = '사용자가 직접 입력한 카드, 거래내역, 예산, 소비계획, 커뮤니티 글, AI 상담 내용을 서비스 제공에 사용합니다.'
const purposeText = '소비 분석, 카드 추천, 예산 관리, 지출 계획, 커뮤니티 기능, 계정 인증과 보안 유지에 사용합니다.'
const deletionText = '설정 화면에서 계정 삭제를 요청하면 계정과 연결된 인증 세션, 거래내역, 보유 카드, 분석 기록, 소비계획, 커뮤니티 활동 데이터가 삭제됩니다.'
</script>

<style scoped>
.privacy-screen {
  background: var(--carch-page);
}

.privacy-header {
  padding: 22px 20px 18px;
  background: #24364f;
  color: #fff;
}

.privacy-header > div {
  margin-top: 18px;
}

.privacy-header span {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  font-weight: 900;
}

.privacy-header h1 {
  margin: 4px 0;
  font-size: 23px;
  font-weight: 900;
}

.privacy-header p {
  margin: 0;
  color: rgba(255, 255, 255, 0.72);
  font-size: 12px;
  font-weight: 700;
}

.privacy-body {
  display: grid;
  gap: 12px;
  padding: 18px 20px 112px;
}

.privacy-card {
  display: grid;
  gap: 8px;
}

.privacy-card h2 {
  margin: 0;
  color: #17202b;
  font-size: 15px;
  font-weight: 900;
}

.privacy-card p {
  margin: 0;
  color: #5b6777;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.58;
}
</style>
