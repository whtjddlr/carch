<template>
  <main class="app-landing" :class="{ 'is-leaving': isLeaving }" aria-label="Carch launch">
    <section class="launch-card">
      <div class="logo-stage" aria-hidden="true">
        <span class="logo-glass">
          <img src="/card-images/magpie-face.png" alt="" />
        </span>
      </div>

      <div class="launch-copy">
        <p class="overline">CARCH</p>
        <h1>카드를 읽고<br />소비를 설계하는 지갑</h1>
        <p class="lead">소비 흐름에 맞춰 실적, 혜택, 추천까지 차분하게 정리합니다.</p>
      </div>

      <div class="launch-status" aria-live="polite">
        <span></span>
        <p>지갑을 여는 중</p>
      </div>

      <RouterLink class="skip-button" to="/cards" @click="cancelAutoLaunch">바로 열기</RouterLink>
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
  launchTimer = window.setTimeout(openWallet, 1700)
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
  display: flex;
  width: min(100%, 430px);
  min-height: min(720px, calc(100dvh - 56px));
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(36, 54, 79, 0.08);
  border-radius: 34px;
  padding: clamp(34px, 9vw, 56px) 26px;
  background: rgba(250, 252, 255, 0.66);
  box-shadow: 0 26px 70px rgba(36, 54, 79, 0.1);
  text-align: center;
  backdrop-filter: blur(18px) saturate(1.05);
  animation: card-rise 760ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
}

.logo-stage {
  display: grid;
  width: 128px;
  height: 128px;
  place-items: center;
  margin-bottom: 34px;
  animation: logo-float 3.8s ease-in-out 820ms infinite;
}

.logo-glass {
  display: grid;
  width: 104px;
  height: 104px;
  place-items: center;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 32px;
  background: #ffffff;
  box-shadow:
    0 18px 42px rgba(36, 54, 79, 0.14),
    inset 0 1px 0 rgba(255, 255, 255, 0.92);
  animation: logo-reveal 860ms cubic-bezier(0.2, 0.8, 0.2, 1) 160ms both;
}

.logo-glass img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 42%;
}

.launch-copy {
  animation: copy-reveal 760ms ease 360ms both;
}

.overline {
  margin: 0 0 14px;
  color: #008c95;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.16em;
}

h1 {
  margin: 0;
  color: #17202b;
  font-size: clamp(32px, 8vw, 44px);
  font-weight: 900;
  line-height: 1.16;
  letter-spacing: 0;
}

.lead {
  max-width: 290px;
  margin: 18px auto 0;
  color: #6e6e73;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.62;
}

.launch-status {
  display: grid;
  width: min(100%, 210px);
  gap: 12px;
  margin-top: 42px;
  animation: actions-reveal 720ms ease 560ms both;
}

.launch-status span {
  position: relative;
  display: block;
  height: 3px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(36, 54, 79, 0.1);
}

.launch-status span::after {
  position: absolute;
  inset: 0;
  width: 42%;
  border-radius: inherit;
  background: #24364f;
  content: '';
  animation: loading-slide 1.4s ease-in-out infinite;
}

.launch-status p {
  margin: 0;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 900;
}

.skip-button {
  margin-top: 20px;
  color: #516173;
  font-size: 13px;
  font-weight: 900;
  text-decoration: none;
}

@keyframes card-rise {
  from {
    opacity: 0;
    transform: translateY(18px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes logo-reveal {
  from {
    opacity: 0;
    transform: translateY(14px) scale(0.9);
    filter: blur(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
    filter: blur(0);
  }
}

@keyframes copy-reveal {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes actions-reveal {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
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

@keyframes loading-slide {
  0% {
    transform: translateX(-110%);
  }
  48%,
  100% {
    transform: translateX(250%);
  }
}

@media (max-width: 480px) {
  .app-landing {
    padding: 0;
  }

  .launch-card {
    width: 100%;
    min-height: 100dvh;
    border-radius: 0;
    border-inline: 0;
    box-shadow: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .app-landing,
  .launch-card,
  .logo-stage,
  .logo-glass,
  .launch-copy,
  .launch-status {
    animation: none;
    transition: none;
  }
}
</style>
