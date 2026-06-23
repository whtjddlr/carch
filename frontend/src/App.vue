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
                <component :is="item.icon" :size="item.primary ? 20 : 19" />
              </span>
              <span>{{ item.label }}</span>
            </RouterLink>
          </div>
        </nav>
      </main>
    </div>
  </RouterView>
</template>

<script setup>
import { nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Bot, CreditCard, Receipt, Target, Users } from 'lucide-vue-next'

const currentRoute = useRoute()
const navItems = [
  { path: '/cards', icon: CreditCard, label: '카드', matches: ['/cards', '/recommendations', '/analytics'] },
  { path: '/transactions', icon: Receipt, label: '거래내역', matches: ['/transactions'] },
  { path: '/chat', icon: Bot, label: 'AI', primary: true },
  { path: '/budget', icon: Target, label: '예산', matches: ['/budget'] },
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
