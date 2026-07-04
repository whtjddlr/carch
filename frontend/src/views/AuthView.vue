<template>
  <section class="screen auth-screen">
    <div class="auth-hero">
      <div class="brand-mark">
        <img src="/brand/carch-wordmark-transparent.png" alt="Carch" />
      </div>
      <p>카드를 읽고 소비를 설계하는 지갑</p>
    </div>

    <form class="auth-form" @submit.prevent="submitEmail">
      <div class="auth-title">
        <strong>{{ isSignup ? '회원가입' : '로그인' }}</strong>
      </div>

      <label v-if="isSignup">
        <span>이름</span>
        <input v-model.trim="form.name" class="form-field" type="text" autocomplete="name" placeholder="남주현" />
      </label>
      <label>
        <span>{{ identityLabel }}</span>
        <input
          v-model.trim="form.email"
          class="form-field"
          :type="identityInputType"
          :autocomplete="identityAutocomplete"
          :placeholder="identityPlaceholder"
        />
      </label>
      <label>
        <span>비밀번호</span>
        <input
          v-model="form.password"
          class="form-field"
          type="password"
          autocomplete="current-password"
          placeholder="8자 이상"
        />
      </label>

      <p v-if="message" class="auth-message" :class="{ danger: messageTone === 'danger' }">{{ message }}</p>

      <button class="primary-button w-100" type="submit" :disabled="loading">
        {{ loading ? '확인 중' : isSignup ? '회원가입' : '로그인' }}
      </button>

      <button
        v-if="showQuickStart"
        class="demo-login-button"
        type="button"
        :disabled="loading"
        @click="submitDemoLogin"
      >
        카치 바로 시작
      </button>

      <div v-if="showSocialLogin" class="auth-divider"><span>또는</span></div>

      <div v-if="showSocialLogin" class="social-buttons">
        <button
          v-for="provider in providers"
          :key="provider.id"
          class="social-button"
          :class="provider.id"
          type="button"
          :disabled="!provider.enabled || loading"
          @click="startSocial(provider)"
        >
          <span class="social-symbol">
            <svg v-if="provider.id === 'kakao'" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M12 3.6c-4.97 0-9 3.18-9 7.1 0 2.53 1.66 4.75 4.16 6.04-.18.65-.66 2.4-.76 2.77-.12.46.17.45.35.33.15-.1 2.33-1.58 3.28-2.23.63.09 1.27.14 1.97.14 4.97 0 9-3.18 9-7.1S16.97 3.6 12 3.6z"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M14.45 12.42 9.36 5.1H5.2v13.8h4.39v-7.32l5.09 7.32h4.16V5.1h-4.39z"/>
            </svg>
          </span>
          <b>{{ provider.label }} 로그인</b>
        </button>
      </div>

      <RouterLink class="auth-link" :to="{ path: isSignup ? '/login' : '/signup', query: route.query }">
        {{ isSignup ? '이미 계정이 있습니다' : '새 계정을 만듭니다' }}
      </RouterLink>
      <RouterLink class="privacy-link" to="/privacy">
        개인정보 처리방침
      </RouterLink>
    </form>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchAuthProviders, IS_DEMO_CHANNEL, IS_SERVICE_CHANNEL, USE_MOCK_API } from '@/services/api'
import { completeOAuthLogin, emailLogin, emailSignup, oauthStartUrl } from '@/services/auth'
import { isNativeRuntime } from '@/services/secureStorage'

const props = defineProps({
  mode: { type: String, default: 'login' },
})

const router = useRouter()
const route = useRoute()
const isSignup = computed(() => props.mode === 'signup')
const nextPath = computed(() => String(route.query.next || '/cards'))
const identityLabel = computed(() => (isSignup.value || IS_SERVICE_CHANNEL ? '이메일' : '아이디'))
const identityInputType = computed(() => (isSignup.value || IS_SERVICE_CHANNEL ? 'email' : 'text'))
const identityAutocomplete = computed(() => (isSignup.value || IS_SERVICE_CHANNEL ? 'email' : 'username'))
const identityPlaceholder = computed(() => (isSignup.value || IS_SERVICE_CHANNEL ? 'name@carch.kr' : 'skawngus'))
const loading = ref(false)
const message = ref(String(route.query.error || ''))
const messageTone = ref(message.value ? 'danger' : 'info')
const isNativeApp = isNativeRuntime()
const showQuickStart = computed(() => IS_DEMO_CHANNEL && !isSignup.value && !isNativeApp)
const showSocialLogin = computed(() => !IS_SERVICE_CHANNEL && !isNativeApp)
const providers = ref([
  { id: 'kakao', label: '카카오', enabled: false },
  { id: 'naver', label: '네이버', enabled: false },
])
const form = reactive({
  name: '',
  email: '',
  password: '',
})

onMounted(async () => {
  if (isNativeApp || IS_SERVICE_CHANNEL) return
  try {
    const data = await fetchAuthProviders()
    providers.value = data.providers || providers.value
  } catch {
    message.value = '로그인 설정을 불러오지 못했습니다.'
    messageTone.value = 'danger'
  }
})

const submitEmail = async () => {
  if (!form.email || !form.password || (isSignup.value && !form.name)) {
    message.value = '필수 정보를 입력해 주세요.'
    messageTone.value = 'danger'
    return
  }
  loading.value = true
  message.value = ''
  try {
    const action = isSignup.value ? emailSignup : emailLogin
    await action({ name: form.name, email: form.email, password: form.password })
    router.replace(nextPath.value.startsWith('/') ? nextPath.value : '/cards')
  } catch (error) {
    message.value = error?.response?.data?.detail || '로그인을 완료하지 못했습니다.'
    messageTone.value = 'danger'
  } finally {
    loading.value = false
  }
}

const submitDemoLogin = async () => {
  loading.value = true
  message.value = ''
  try {
    await emailLogin({ email: 'skawngus', password: 'skawngus' })
    router.replace(nextPath.value.startsWith('/') ? nextPath.value : '/cards')
  } catch (error) {
    message.value = error?.response?.data?.detail || '로그인을 완료하지 못했습니다.'
    messageTone.value = 'danger'
  } finally {
    loading.value = false
  }
}

const startSocial = async (provider) => {
  if (!provider.enabled) {
    message.value = `${provider.label} 로그인 키를 설정해 주세요.`
    messageTone.value = 'danger'
    return
  }
  if (USE_MOCK_API) {
    await completeOAuthLogin({ token: 'mock-auth-token' })
    router.replace(nextPath.value.startsWith('/') ? nextPath.value : '/cards')
    return
  }
  window.location.href = oauthStartUrl(provider.id, nextPath.value)
}
</script>

<style scoped>
.auth-screen {
  background: var(--carch-page);
}

.auth-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 58px 28px 30px;
  color: var(--carch-ink);
}

.brand-mark {
  display: grid;
  width: min(300px, 82vw);
  height: 124px;
  place-items: center;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.brand-mark img {
  display: block;
  width: 84%;
  height: auto;
  object-fit: contain;
  transform: translateX(-16px);
}

.auth-hero h1 {
  margin: 14px 0 4px;
  color: var(--carch-ink);
  font-size: 25px;
  font-weight: 900;
}

.auth-hero p {
  margin: 16px 0 0;
  color: var(--carch-muted);
  font-size: 13px;
  font-weight: 800;
}

.auth-form {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 14px;
  padding: 24px 24px 32px;
  border-top: 1px solid var(--carch-line);
  background: rgba(255, 255, 255, 0.42);
}

.auth-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 2px;
}

.auth-title strong {
  color: var(--carch-ink);
  font-size: 22px;
  font-weight: 900;
}

.auth-title span,
.auth-form label span {
  color: var(--carch-muted);
  font-size: 12px;
  font-weight: 800;
}

.auth-form label {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.form-field {
  min-height: 48px;
  border: 1px solid var(--carch-control-border);
  border-radius: 15px;
  background: rgba(255, 255, 255, 0.62);
  color: var(--carch-ink);
  font-size: 15px;
  font-weight: 800;
  outline: none;
  padding: 0 15px;
}

.form-field:focus {
  border-color: rgba(15, 95, 174, 0.55);
  box-shadow: 0 0 0 4px rgba(15, 95, 174, 0.08);
}

.auth-message {
  min-height: 18px;
  margin: 0;
  color: var(--carch-teal);
  font-size: 12px;
  font-weight: 800;
}

.auth-message.danger {
  color: #d92d20;
}

.auth-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--carch-muted);
  font-size: 11px;
  font-weight: 900;
}

.auth-divider::before,
.auth-divider::after {
  flex: 1;
  height: 1px;
  background: var(--carch-line);
  content: '';
}

.social-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.social-button {
  display: inline-flex;
  min-height: 48px;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 1px solid var(--carch-control-border);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.48);
  color: var(--carch-ink);
  font-size: 12.5px;
  font-weight: 900;
  white-space: nowrap;
}

.social-button:disabled {
  cursor: not-allowed;
}

.demo-login-button {
  min-height: 48px;
  border: 1px solid rgba(15, 95, 174, 0.26);
  border-radius: 16px;
  background: #24364f;
  color: #fff;
  font-size: 13px;
  font-weight: 900;
}

.demo-login-button:disabled {
  opacity: 0.5;
}

.social-symbol {
  display: grid;
  width: 19px;
  height: 19px;
  place-items: center;
}

.social-symbol svg {
  width: 100%;
  height: 100%;
}

.social-button.kakao {
  border-color: #fdd835;
  background: #fee500;
  color: #3c1e1e;
}

.social-button.kakao .social-symbol {
  color: #3c1e1e;
}

.social-button.naver {
  border-color: #02b350;
  background: #03c75a;
  color: #ffffff;
}

.social-button.naver .social-symbol {
  color: #ffffff;
}

.auth-link {
  margin-top: 4px;
  color: var(--carch-blue);
  font-size: 13px;
  font-weight: 900;
  text-align: center;
  text-decoration: none;
}

.privacy-link {
  margin-top: -2px;
  color: #7b8794;
  font-size: 12px;
  font-weight: 800;
  text-align: center;
  text-decoration: none;
}
</style>
