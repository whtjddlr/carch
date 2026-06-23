<template>
  <button class="icon-button app-back-button" type="button" :aria-label="ariaLabel" @click="goBack">
    <ArrowLeft :size="18" />
  </button>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ArrowLeft } from 'lucide-vue-next'

const props = defineProps({
  fallback: { type: String, default: '/cards' },
  ariaLabel: { type: String, default: '뒤로가기' },
})

const router = useRouter()

function goBack() {
  if (window.history.state?.back) {
    router.back()
    return
  }
  router.push(props.fallback)
}
</script>

<style scoped>
.app-back-button {
  flex: 0 0 auto;
}
</style>
