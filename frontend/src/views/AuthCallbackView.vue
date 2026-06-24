<template>
  <section class="screen auth-callback-screen">
    <div class="callback-panel">
      <div class="brand-mark">
        <img src="/brand/carch-title-bird.png" alt="Carch" />
      </div>
      <strong>로그인 정보를 확인하고 있습니다</strong>
      <p>잠시 후 CARCH로 이동합니다.</p>
    </div>
  </section>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { completeOAuthLogin } from '@/services/auth'

const route = useRoute()
const router = useRouter()

onMounted(async () => {
  const token = String(route.query.token || '')
  const next = String(route.query.next || '/cards')
  if (!token) {
    router.replace({ path: '/login', query: { error: '소셜 로그인을 완료하지 못했습니다.' } })
    return
  }
  try {
    await completeOAuthLogin({ token })
    router.replace(next.startsWith('/') ? next : '/cards')
  } catch {
    router.replace({ path: '/login', query: { error: '소셜 로그인을 완료하지 못했습니다.' } })
  }
})
</script>

<style scoped>
.auth-callback-screen {
  justify-content: center;
  padding: 28px;
  background: var(--carch-page);
}

.callback-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  text-align: center;
}

.brand-mark {
  display: grid;
  width: 156px;
  height: 64px;
  place-items: center;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 16px 34px rgba(36, 54, 79, 0.1);
}

.brand-mark img {
  display: block;
  width: 82%;
  height: auto;
  object-fit: contain;
}

.callback-panel strong {
  color: var(--carch-ink);
  font-size: 18px;
  font-weight: 900;
}

.callback-panel p {
  margin: 0;
  color: var(--carch-muted);
  font-size: 13px;
  font-weight: 700;
}
</style>
