<template>
  <div class="loading-wrap" aria-live="polite">
    <LoaderCircle class="spin" :size="34" />
    <Transition name="fade" mode="out-in">
      <p :key="activeMessage">{{ activeMessage }}</p>
    </Transition>
    <div class="skeleton-lines">
      <span v-for="width in [100, 84, 68]" :key="width" :style="{ width: `${width}%` }" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { LoaderCircle } from 'lucide-vue-next'

const props = defineProps({
  messages: { type: Array, required: true },
})

const index = ref(0)
let timer

const activeMessage = computed(() => props.messages[index.value] || props.messages[0])

onMounted(() => {
  timer = window.setInterval(() => {
    index.value = (index.value + 1) % props.messages.length
  }, 1400)
})

onUnmounted(() => window.clearInterval(timer))
</script>

<style scoped>
.loading-wrap {
  display: flex;
  min-height: 360px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 28px;
  color: #0f5fae;
}

.spin {
  animation: spin 1s linear infinite;
}

.loading-wrap p {
  min-height: 22px;
  margin: 18px 0 0;
  color: #17202b;
  font-size: 14px;
  font-weight: 800;
  text-align: center;
}

.skeleton-lines {
  width: 100%;
  margin-top: 24px;
}

.skeleton-lines span {
  display: block;
  height: 12px;
  margin: 10px auto;
  border-radius: 999px;
  background: #dbe4ee;
  animation: pulse 1.4s ease-in-out infinite;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes pulse {
  50% {
    opacity: 0.45;
  }
}
</style>
