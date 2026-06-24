<template>
  <main class="app-landing" :class="{ 'is-leaving': isLeaving }" aria-label="Carch launch">
    <section class="launch-card">
      <div class="logo-stage">
        <span class="logo-glass">
          <img src="/brand/carch-wordmark-transparent.png" alt="Carch" />
        </span>
      </div>
    </section>
  </main>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isLeaving = ref(false)
let launchTimer
let routeTimer

function openWallet() {
  isLeaving.value = true
  routeTimer = window.setTimeout(() => {
    router.replace('/cards')
  }, 320)
}

function cancelAutoLaunch() {
  window.clearTimeout(launchTimer)
  window.clearTimeout(routeTimer)
}

onMounted(() => {
  launchTimer = window.setTimeout(openWallet, 3000)
})

onBeforeUnmount(cancelAutoLaunch)
</script>

<style scoped>
.app-landing {
  display: grid;
  min-height: 100dvh;
  place-items: center;
  padding: 28px;
  background:
    radial-gradient(circle at 50% 35%, rgba(255, 255, 255, 0.82), transparent 34%),
    linear-gradient(180deg, rgba(44, 78, 114, 0.08), transparent 36%),
    #f3f6f8;
  color: #20242a;
  transition: opacity 320ms ease, transform 320ms ease, filter 320ms ease;
}

.app-landing.is-leaving {
  opacity: 0;
  transform: scale(1.012);
  filter: blur(5px);
}

.launch-card {
  display: grid;
  width: min(78vw, 330px);
  place-items: center;
  margin-top: -16vh;
  animation: card-rise 760ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
}

.logo-stage {
  display: grid;
  width: 100%;
  place-items: center;
  animation: logo-float 3.8s ease-in-out 820ms infinite;
}

.logo-glass {
  display: grid;
  width: 100%;
  place-items: center;
  line-height: 0;
  overflow: visible;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  animation: logo-reveal 860ms cubic-bezier(0.2, 0.8, 0.2, 1) 160ms both;
}

.logo-glass img {
  display: block;
  width: 100%;
  height: auto;
  aspect-ratio: 827 / 309;
  object-fit: contain;
  object-position: center;
}

@keyframes card-rise {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.985);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes logo-reveal {
  from {
    opacity: 0;
    transform: translateY(6px) scale(0.94);
    filter: blur(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
    filter: blur(0);
  }
}

@keyframes logo-float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-6px);
  }
}

@media (max-width: 480px) {
  .app-landing {
    padding: 0;
  }

  .launch-card {
    width: min(76vw, 318px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .app-landing,
  .launch-card,
  .logo-stage,
  .logo-glass {
    animation: none;
    transition: none;
  }
}
</style>
