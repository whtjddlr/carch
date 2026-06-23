<template>
  <section class="screen chat-screen">
    <header class="chat-header blue-gradient">
      <AppBackButton fallback="/cards" />
      <div>
        <span class="eyebrow">
          <Sparkles :size="13" />
          {{ isSending ? '응답 생성 중' : 'CARCH AI' }}
        </span>
        <h1>AI 카드 상담</h1>
      </div>
      <Bot :size="28" />
    </header>

    <div ref="scrollRef" class="screen-scroll scrollbar-hide chat-body">
      <div v-for="message in messages" :key="message.id" class="message-row" :class="message.role">
        <div class="message-bubble">
          <p>{{ message.content }}</p>
          <RouterLink v-if="message.relatedRoute" class="related-link" :to="message.relatedRoute">
            관련 화면 보기
            <ArrowRight :size="13" />
          </RouterLink>
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
        placeholder="카드, 소비, 구매 계획을 질문하세요"
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
import { ArrowRight, Bot, SendHorizontal, Sparkles } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { sendChatMessage } from '@/services/api'

const starterReplies = ['이번 달 소비 분석해줘', '나한테 맞는 카드 추천해줘', '혼수가전 구매 계획 도와줘']
const messages = ref([
  {
    id: 'assistant-welcome',
    role: 'assistant',
    content: '안녕하세요. 최근 결제내역과 카드 데이터를 기준으로 소비 분석, 카드 추천, 구매 계획을 같이 도와드릴게요.',
    quickReplies: starterReplies,
    relatedRoute: '',
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
        aiMode: response.aiMode,
      }),
    )
  } catch (error) {
    console.warn('챗봇 API 호출 실패', error)
    messages.value.push(
      makeMessage('assistant', '지금은 챗봇 API 연결이 불안정합니다. 결제내역 추가나 소비 분석 화면에서 먼저 확인해 주세요.', {
        quickReplies: ['소비 분석 보기', '결제내역 추가하기', '카드 추천 보기'],
        relatedRoute: '/analytics/cards',
        aiMode: 'mock',
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
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  padding: 24px 20px 26px;
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
}

.chat-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 16px;
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
