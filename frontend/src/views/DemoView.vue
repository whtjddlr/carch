<template>
  <section class="screen demo-screen">
    <div class="demo-panel">
      <img src="/brand/carch-wordmark-transparent.png" alt="Carch" />
      <strong>{{ statusTitle }}</strong>
      <p>{{ statusMessage }}</p>
      <RouterLink v-if="failed" class="demo-link" :to="{ path: '/login', query: { next: nextPath } }">
        로그인 화면으로 이동
      </RouterLink>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { emailLogin } from '@/services/auth'

const DEMO_CREDENTIALS = {
  email: 'skawngus',
  password: 'skawngus',
}

const route = useRoute()
const router = useRouter()
const failed = ref(false)
const nextPath = computed(() => {
  const next = String(route.query.next || '/cards')
  return next.startsWith('/') ? next : '/cards'
})
const statusTitle = computed(() => (failed.value ? '앱을 열지 못했습니다' : '카치를 여는 중'))
const statusMessage = computed(() => (
  failed.value
    ? '잠시 후 다시 시도하거나 로그인 화면에서 시작해 주세요.'
    : '잠시만 기다려 주세요. 곧 카드 홈으로 이동합니다.'
))

onMounted(async () => {
  failed.value = false
  try {
    await emailLogin(DEMO_CREDENTIALS)
    router.replace(nextPath.value)
  } catch {
    failed.value = true
  }
})
</script>

<style scoped>
.demo-screen {
  display: grid;
  min-height: 100%;
  place-items: center;
  background:
    radial-gradient(circle at 50% 0%, rgba(15, 95, 174, 0.1), transparent 42%),
    #f3f6f8;
  padding: 28px;
}

.demo-panel {
  display: flex;
  width: min(100%, 300px);
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
}

.demo-panel img {
  width: 210px;
  max-width: 80%;
  transform: translateX(-10px);
}

.demo-panel strong {
  color: #20242a;
  font-size: 18px;
  font-weight: 900;
  line-height: 1.35;
}

.demo-panel p {
  margin: 0;
  color: #6e6e73;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.55;
}

.demo-link {
  display: inline-flex;
  min-height: 42px;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: #24364f;
  color: #fff;
  font-size: 13px;
  font-weight: 900;
  padding: 0 16px;
  text-decoration: none;
}
</style>
