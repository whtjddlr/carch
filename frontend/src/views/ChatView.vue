<template>
  <section class="screen chat-screen">
    <header class="chat-header blue-gradient">
      <AppBackButton fallback="/cards" />
      <div>
        <span class="eyebrow">데이터 기반 소비 코치</span>
        <h1>카치에게 물어보기</h1>
      </div>
    </header>

    <div ref="scrollRef" class="screen-scroll scrollbar-hide chat-body">
      <section v-if="messages.length === 1" class="chat-starter-panel">
        <span>지금 데이터로 바로 판단</span>
        <strong>보유 카드 사용과 새 카드 발급을 나눠 답해드려요.</strong>
        <div class="starter-grid">
          <button type="button" :disabled="isSending" @click="sendMessage('이번 달은 보유 카드 중 어디에 쓰는 게 좋아?')">
            보유 카드
          </button>
          <button type="button" :disabled="isSending" @click="sendMessage('새로 발급받을 만한 카드는 따로 있어?')">
            새 카드
          </button>
          <button type="button" :disabled="isSending" @click="sendMessage('소비계획이 있으면 카드 추천이 어떻게 바뀌어?')">
            계획 반영
          </button>
        </div>
      </section>

      <div v-for="message in messages" :key="message.id" class="message-row" :class="message.role">
        <div class="message-bubble">
          <p>{{ message.content }}</p>
          <div v-if="message.summaryChips?.length" class="message-chips">
            <span v-for="chip in message.summaryChips" :key="`${chip.label}-${chip.value}`" :class="`tone-${chip.tone || 'gray'}`">
              <small>{{ chip.label }}</small>
              <strong>{{ chip.value }}</strong>
            </span>
          </div>
          <RouterLink v-if="message.relatedRoute" class="related-link" :to="message.relatedRoute">
            관련 화면 보기
            <ArrowRight :size="13" />
          </RouterLink>
          <div v-if="message.actionButtons?.length" class="message-actions">
            <RouterLink v-for="button in message.actionButtons" :key="`${button.label}-${button.route}`" :to="button.route">
              {{ button.label }}
            </RouterLink>
          </div>
          <div v-if="message.quickReplies?.length" class="quick-replies">
            <button
              v-for="reply in message.quickReplies"
              :key="reply"
              type="button"
              :disabled="isSending"
              :aria-label="`빠른 질문: ${reply}`"
              @click="sendMessage(reply)"
            >
              {{ reply }}
            </button>
          </div>
          <small v-if="message.role === 'assistant' && message.aiMode" class="message-meta">
            {{ aiModeLabel(message.aiMode) }}
          </small>
        </div>
      </div>

      <div v-if="isSending" class="message-row assistant">
        <div class="message-bubble typing">
          <span />
          <span />
          <span />
        </div>
      </div>
    </div>

    <form class="chat-composer" @submit.prevent="sendMessage()">
      <input
        v-model="draft"
        type="text"
        aria-label="AI에게 질문 입력"
        autocomplete="off"
        placeholder="예: 이번 달 식비는 어떤 카드로 쓸까?"
        :disabled="isSending"
      />
      <button type="submit" :disabled="isSending || !draft.trim()" aria-label="전송">
        <SendHorizontal :size="18" />
      </button>
    </form>
  </section>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import { ArrowRight, SendHorizontal } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { sendChatMessage } from '@/services/api'

const starterReplies = ['보유 카드 사용 추천', '새 카드 발급 추천', '소비계획 반영하기']
const messages = ref([
  {
    id: 'assistant-welcome',
    role: 'assistant',
    content: '최근 결제내역, 보유 카드, 소비계획을 함께 보고 답합니다. 보유 카드 사용 전략과 새 카드 발급 추천은 구분해서 안내할게요.',
    quickReplies: starterReplies,
    relatedRoute: '',
    summaryChips: [
      { label: '응답 기준', value: '내 데이터', tone: 'teal' },
      { label: '추천 구분', value: '사용/발급', tone: 'navy' },
    ],
    aiMode: 'local',
  },
])
const draft = ref('')
const isSending = ref(false)
const scrollRef = ref(null)

function makeMessage(role, content, extra = {}) {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    role,
    content,
    ...extra,
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (scrollRef.value) {
      scrollRef.value.scrollTop = scrollRef.value.scrollHeight
    }
  })
}

function aiModeLabel(mode) {
  if (mode === 'gms_proxy') return 'FastAPI proxy가 LLM 응답을 검증한 결과'
  if (mode === 'guardrail_blocked') return 'FastAPI Guardrail이 차단한 요청'
  if (mode === 'gms') return 'LLM이 계산 결과를 해석한 응답'
  if (mode === 'rule_fallback') return '검증된 계산 결과로 보정한 응답'
  if (mode === 'mock') return '저장된 데이터 기반 기본 응답'
  return '앱 데이터 기반 응답'
}

async function sendMessage(text = draft.value) {
  const content = String(text || '').trim()
  if (!content || isSending.value) return

  messages.value.push(makeMessage('user', content))
  draft.value = ''
  isSending.value = true
  scrollToBottom()

  const history = messages.value.slice(-8).map((message) => ({
    role: message.role,
    content: message.content,
  }))

  try {
    const response = await sendChatMessage({ message: content, history })
    messages.value.push(
      makeMessage('assistant', response.reply || '답변을 만들지 못했습니다. 다시 질문해 주세요.', {
        quickReplies: response.quickReplies || [],
        relatedRoute: response.relatedRoute || '',
        summaryChips: response.summaryChips || [],
        actionButtons: response.actionButtons || [],
        messageType: response.messageType || 'general',
        confidence: response.confidence,
        aiMode: response.aiMode,
      }),
    )
  } catch (error) {
    console.warn('챗봇 API 호출 실패', error)
    messages.value.push(
      makeMessage('assistant', '현재는 저장된 데이터를 기준으로 안내합니다. 결제내역 추가나 소비 분석 화면에서 먼저 확인하시기 바랍니다.', {
        quickReplies: ['소비 분석 보기', '결제내역 추가하기', '카드 추천 보기'],
        relatedRoute: '/analytics',
        summaryChips: [{ label: '응답 기준', value: '저장된 데이터', tone: 'gray' }],
        actionButtons: [{ label: '소비 분석 보기', route: '/analytics' }],
        messageType: 'general',
        aiMode: 'rule_fallback',
      }),
    )
  } finally {
    isSending.value = false
    scrollToBottom()
  }
}
</script>

<style scoped>
.chat-screen {
  background: #fbfdff;
}

.chat-header {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  padding: 22px 20px 26px;
  color: #fff;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 6px;
  color: rgba(255, 255, 255, 0.76);
  font-size: 11px;
  font-weight: 900;
}

.chat-header h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 900;
  line-height: 1.2;
}

.chat-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 16px;
}

.chat-starter-panel {
  display: grid;
  gap: 10px;
  border: 1px solid rgba(36, 54, 79, 0.08);
  border-radius: 18px;
  padding: 16px;
  background:
    radial-gradient(circle at 100% 0%, rgba(0, 140, 149, 0.12), transparent 42%),
    #fff;
  box-shadow: 0 12px 24px rgba(36, 54, 79, 0.06);
}

.chat-starter-panel span {
  color: #0f5fae;
  font-size: 11px;
  font-weight: 950;
}

.chat-starter-panel strong {
  color: #17202b;
  font-size: 16px;
  font-weight: 950;
}

.starter-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 7px;
}

.starter-grid button {
  min-height: 42px;
  border-radius: 13px;
  padding: 8px 6px;
  background: rgba(15, 95, 174, 0.08);
  color: #0f5fae;
  font-size: 11px;
  font-weight: 900;
}

.message-row {
  display: flex;
  width: 100%;
}

.message-row.user {
  justify-content: flex-end;
}

.message-bubble {
  max-width: 82%;
  border: 1px solid #dbe4ee;
  border-radius: 18px;
  padding: 12px 13px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(16, 24, 40, 0.04);
}

.message-row.user .message-bubble {
  border-color: #0f5fae;
  background: #0f5fae;
  color: #fff;
}

.message-bubble p {
  margin: 0;
  color: #17202b;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.55;
  word-break: keep-all;
}

.message-row.user .message-bubble p {
  color: #fff;
}

.related-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 9px;
  color: #0f5fae;
  font-size: 12px;
  font-weight: 900;
  text-decoration: none;
}

.message-chips,
.message-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 10px;
}

.message-chips span {
  display: inline-flex;
  min-height: 34px;
  flex-direction: column;
  justify-content: center;
  border: 1px solid rgba(15, 95, 174, 0.12);
  border-radius: 12px;
  padding: 6px 9px;
  background: rgba(232, 241, 255, 0.7);
}

.message-chips small {
  color: #6e6e73;
  font-size: 9px;
  font-weight: 900;
}

.message-chips strong {
  color: #17202b;
  font-size: 11px;
  font-weight: 900;
}

.message-chips .tone-teal strong {
  color: #008c95;
}

.message-chips .tone-navy strong {
  color: #17202b;
}

.message-chips .tone-blue strong {
  color: #0f5fae;
}

.message-chips .tone-gold strong {
  color: #a66f00;
}

.message-chips .tone-danger strong {
  color: #dc2626;
}

.message-actions a {
  min-height: 36px;
  border-radius: 999px;
  padding: 9px 12px;
  background: #17202b;
  color: #fff;
  font-size: 11px;
  font-weight: 900;
  text-decoration: none;
}

.quick-replies {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 10px;
}

.quick-replies button {
  min-height: 40px;
  border-radius: 999px;
  padding: 9px 12px;
  background: #e8f1ff;
  color: #0f5fae;
  font-size: 11px;
  font-weight: 900;
}

.quick-replies button:disabled {
  color: #8a9aad;
}

.message-meta {
  display: block;
  margin-top: 9px;
  color: #8a96a5;
  font-size: 10px;
  font-weight: 800;
  line-height: 1.3;
}

.typing {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-width: 58px;
}

.typing span {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: #8a9aad;
  animation: typing-dot 900ms ease-in-out infinite;
}

.typing span:nth-child(2) {
  animation-delay: 120ms;
}

.typing span:nth-child(3) {
  animation-delay: 240ms;
}

.chat-composer {
  display: grid;
  flex-shrink: 0;
  grid-template-columns: minmax(0, 1fr) 44px;
  gap: 8px;
  border-top: 1px solid #dbe4ee;
  padding: 10px 14px 12px;
  background: #fff;
}

.chat-composer input {
  min-width: 0;
  min-height: 46px;
  border: 1px solid #dbe4ee;
  border-radius: 14px;
  padding: 12px 13px;
  background: #fbfdff;
  color: #17202b;
  font-size: 13px;
  font-weight: 700;
  outline: none;
}

.chat-composer input:focus {
  border-color: #0f5fae;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.chat-composer button {
  display: inline-flex;
  width: 44px;
  height: 44px;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: #0f5fae;
  color: #fff;
}

.chat-composer button:disabled {
  background: #dbe4ee;
  color: #8a9aad;
}

@keyframes typing-dot {
  0%,
  80%,
  100% {
    transform: translateY(0);
    opacity: 0.45;
  }
  40% {
    transform: translateY(-4px);
    opacity: 1;
  }
}
</style>
