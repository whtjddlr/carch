<template>
  <section class="screen auth-callback-screen">
    <div class="callback-panel">
      <div class="brand-mark">C</div>
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
  await completeOAuthLogin({ token })
  router.replace(next.startsWith('/') ? next : '/cards')
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
  width: 54px;
  height: 54px;
  place-items: center;
  border-radius: 18px;
  background: var(--carch-navy);
  color: #fff;
  font-size: 24px;
  font-weight: 900;
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
