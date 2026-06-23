<template>
  <RouterView v-slot="{ Component, route }">
    <Transition v-if="route.meta.fullPage" name="page-fade" mode="out-in">
      <component :is="Component" :key="route.fullPath" />
    </Transition>
    <div v-else class="app-backdrop">
      <main class="phone-shell">
        <Transition name="page-slide" mode="out-in">
          <component :is="Component" :key="route.fullPath" />
        </Transition>
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
import { nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { BarChart3, ClipboardList, Code2, CreditCard, Users } from 'lucide-vue-next'

const isDev = import.meta.env.DEV
const currentRoute = useRoute()
const navItems = [
  { path: '/cards', icon: CreditCard, label: '카드', matches: ['/cards', '/recommendations', '/transactions'] },
  { path: '/analytics/cards', icon: BarChart3, label: '분석', matches: ['/analytics', '/reports'] },
  { path: '/chat', icon: null, label: '카치', primary: true, matches: ['/chat'] },
  { path: '/budget', icon: ClipboardList, label: '소비계획', matches: ['/budget', '/plans'] },
  { path: '/community', icon: Users, label: '커뮤니티', matches: ['/community'] },
]

function isNavActive(path, item) {
  const matches = item.matches || [item.path]
  return matches.some((match) => path.startsWith(match))
}

watch(
  () => currentRoute.fullPath,
  async () => {
    await nextTick()
    const resetScroll = () => {
      document.querySelectorAll('.screen-scroll').forEach((element) => {
        element.scrollTop = 0
      })
    }
    resetScroll()
    window.setTimeout(resetScroll, 240)
  },
  { flush: 'post' },
)
</script>
