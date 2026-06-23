<template>
  <section class="screen auth-screen">
    <div class="auth-hero blue-gradient">
      <CreditCard :size="38" />
      <h1>CARCH</h1>
      <p>스마트한 카드 관리의 시작</p>
    </div>
    <form class="auth-form" @submit.prevent="router.push('/cards')">
      <label>
        <span>이메일</span>
        <input class="form-field" type="email" :value="user.email" />
      </label>
      <label>
        <span>비밀번호</span>
        <input class="form-field" type="password" value="password" />
      </label>
      <button class="primary-button w-100" type="submit">{{ mode === 'signup' ? '회원가입' : '로그인' }}</button>
      <RouterLink :to="mode === 'signup' ? '/login' : '/signup'">
        {{ mode === 'signup' ? '이미 계정이 있나요?' : '처음이신가요?' }}
      </RouterLink>
    </form>
  </section>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { CreditCard } from 'lucide-vue-next'
import { user } from '@/data/mockData'

defineProps({
  mode: { type: String, default: 'login' },
})

const router = useRouter()
</script>

<style scoped>
.auth-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 84px 28px 56px;
  color: #fff;
}

.auth-hero h1 {
  margin: 14px 0 4px;
  font-size: 38px;
  font-weight: 900;
}

.auth-hero p {
  margin: 0;
  color: rgba(255, 255, 255, 0.72);
  font-size: 14px;
  font-weight: 700;
}

.auth-form {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 16px;
  padding: 28px 24px;
  background: #fff;
}

.auth-form span {
  display: block;
  margin-bottom: 6px;
  color: #4a5663;
  font-size: 12px;
  font-weight: 800;
}

.auth-form a {
  color: #0f5fae;
  font-size: 13px;
  font-weight: 800;
  text-align: center;
  text-decoration: none;
}
</style>
