<template>
  <RouterView v-slot="{ Component, route }">
    <div v-if="routeError" class="app-backdrop">
      <main class="phone-shell">
        <section class="screen route-error-screen">
          <strong>화면을 다시 준비하고 있어요</strong>
          <p>{{ routeErrorMessage }}</p>
          <button type="button" @click="reloadRoute">다시 불러오기</button>
        </section>
      </main>
    </div>
    <component v-else-if="route.meta.fullPage" :is="Component" :key="route.fullPath" />
    <div v-else class="app-backdrop">
      <main class="phone-shell">
        <div class="route-frame">
          <component v-if="Component" :is="Component" :key="route.fullPath" />
          <section v-else class="screen route-error-screen">
            <strong>화면을 준비하지 못했어요</strong>
            <p>연결된 화면을 찾지 못했습니다. 잠시 후 다시 시도해 주세요.</p>
            <button type="button" @click="reloadRoute">다시 불러오기</button>
          </section>
        </div>
        <nav v-if="route.meta.bottomNav" class="bottom-nav" aria-label="하단 내비게이션">
          <div class="bottom-nav-grid">
            <RouterLink
              v-for="item in navItems"
              :key="item.path"
              class="bottom-nav-link"
              :class="{ active: isNavActive(route.path, item), 'is-ai': item.primary }"
              :to="item.path"
            >
              <span class="bottom-nav-icon">
                <component v-if="!item.primary" :is="item.icon" :size="19" />
                <img v-else class="magpie-icon" src="/card-images/magpie-face2.png" alt="카치" />
              </span>
              <span>{{ item.label }}</span>
            </RouterLink>
          </div>
        </nav>
        <RouterLink v-if="isDev" class="dev-fab" to="/dev" aria-label="개발자 패널">
          <Code2 :size="18" />
        </RouterLink>
      </main>
    </div>
  </RouterView>
</template>

<script setup>
import { computed, nextTick, onErrorCaptured, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { BarChart3, ClipboardList, Code2, CreditCard, Users } from 'lucide-vue-next'

const isDev = import.meta.env.DEV
const currentRoute = useRoute()
const routeError = ref(null)
const routeErrorMessage = computed(() => routeError.value?.message || '잠시 후 다시 시도해 주세요.')
const navItems = [
  { path: '/cards', icon: CreditCard, label: '카드', matches: ['/cards', '/recommendations'] },
  { path: '/analytics', icon: BarChart3, label: '분석', matches: ['/analytics'] },
  { path: '/chat', icon: null, label: '카치', primary: true },
  { path: '/budget', icon: ClipboardList, label: '소비계획', matches: ['/budget'] },
  { path: '/community', icon: Users, label: '커뮤니티', matches: ['/community'] },
]

function isNavActive(path, item) {
  const matches = item.matches || [item.path]
  return matches.some((match) => path.startsWith(match))
}

function reloadRoute() {
  routeError.value = null
  window.location.reload()
}

onErrorCaptured((error) => {
  routeError.value = error
  console.error('Route render failed', error)
  return false
})

function resetAppScroll() {
  window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
  document.documentElement.scrollTop = 0
  document.body.scrollTop = 0
  document.querySelectorAll('.screen-scroll').forEach((element) => {
    element.scrollTop = 0
  })
}

onMounted(() => {
  resetAppScroll()
  window.setTimeout(resetAppScroll, 120)
})

watch(
  () => currentRoute.fullPath,
  async () => {
    routeError.value = null
    await nextTick()
    resetAppScroll()
    window.setTimeout(resetAppScroll, 240)
  },
  { flush: 'post' },
)
</script>

<style scoped>
.route-frame {
  display: flex;
  flex: 1 1 auto;
  min-height: 0;
  width: 100%;
  flex-direction: column;
}

.route-frame :deep(.screen) {
  flex: 1 1 auto;
  min-height: 0;
  width: 100%;
}

.route-error-screen {
  display: flex;
  min-height: 100%;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 12px;
  padding: 28px;
  text-align: center;
}

.route-error-screen strong {
  color: #20242a;
  font-size: 18px;
  font-weight: 900;
}

.route-error-screen p {
  max-width: 280px;
  margin: 0;
  color: #6e6e73;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.5;
}

.route-error-screen button {
  min-height: 44px;
  border-radius: 999px;
  padding: 0 18px;
  background: #24364f;
  color: #fff;
  font-size: 14px;
  font-weight: 900;
}
</style>
