<template>
  <section class="screen chat-screen">
    <header class="chat-header">
      <AppBackButton fallback="/cards" />
      <h1>카치AI</h1>
      <button class="support-button" type="button" aria-label="고객센터">
        <Headphones :size="18" />
      </button>
    </header>

    <div ref="scrollRef" class="screen-scroll scrollbar-hide chat-body">
      <img class="chat-watermark" src="/brand/carch-wordmark-transparent.png" alt="" aria-hidden="true" />
      <div v-for="message in messages" :key="message.id" class="message-row" :class="message.role">
        <img
          v-if="message.role === 'assistant'"
          class="assistant-avatar"
          :src="assistantAvatarFor(message)"
          alt="카치"
        />
        <div class="message-stack">
          <span v-if="message.role === 'assistant'" class="assistant-name">카치</span>
          <div class="message-bubble">
            <p class="message-copy">
              <template v-for="(part, index) in messageParts(message.content)" :key="`${message.id}-${index}`">
                <br v-if="part.type === 'br'">
                <strong v-else-if="part.type === 'card'" class="message-card-name">{{ part.text }}</strong>
                <span v-else>{{ part.text }}</span>
              </template>
            </p>
          </div>
          <div v-if="cleanQuickReplies(message).length" class="quick-replies">
            <button
              v-for="reply in cleanQuickReplies(message)"
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
        <img class="assistant-avatar is-speaking" src="/brand/kachi-talk-singing.png" alt="카치" />
        <div class="message-stack">
          <span class="assistant-name">카치</span>
          <div class="message-bubble typing">
            <span />
            <span />
            <span />
          </div>
        </div>
      </div>
    </div>

    <form class="chat-composer" @submit.prevent="sendMessage()">
      <input
        v-model="draft"
        type="text"
        aria-label="AI에게 질문 입력"
        autocomplete="off"
        placeholder="예: 이번 달 카드 사용 괜찮아?"
        :disabled="isSending"
      />
      <button type="submit" :disabled="isSending || !draft.trim()" aria-label="전송">
        <SendHorizontal :size="18" />
      </button>
    </form>
  </section>
</template>

<script setup>
import { nextTick, onMounted, ref, watch } from 'vue'
import { Headphones, SendHorizontal } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { sendChatMessage } from '@/services/api'

const starterReplies = ['보유 카드 개선', '맞춤 카드 추천']
const chatMessagesStorageKey = 'carch.chat.messages.v1'
const chatDraftStorageKey = 'carch.chat.draft.v1'

function initialMessages() {
  return [{
    id: 'assistant-welcome',
    role: 'assistant',
    content: '어떤 게 궁금하세요?\n자유롭게 입력해주세요!',
    avatarIndex: 3,
    quickReplies: starterReplies,
    aiMode: '',
  }]
}

const messages = ref(loadSavedMessages())
const draft = ref(loadSavedDraft())
const isSending = ref(false)
const scrollRef = ref(null)
const assistantAvatars = [
  '/brand/kachi-talk-singing.png',
  '/brand/kachi-talk-giggle.png',
  '/brand/kachi-talk-laugh.png',
  '/brand/kachi-talk-happy.png',
]
const quickReplyLabels = {
  '보유 카드': '보유 카드 개선',
  '보유 카드 사용': '보유 카드 개선',
  '보유 카드 사용 추천': '보유 카드 개선',
  '보유 카드 추천 보기': '보유 카드 개선',
  '보유 카드와 비교': '보유 카드 개선',
  '카드 추천 보기': '맞춤 카드 추천',
  '새 카드': '맞춤 카드 추천',
  '새 카드 발급 추천': '맞춤 카드 추천',
  '새 카드 추천 보기': '맞춤 카드 추천',
  '소비계획 반영하기': '소비계획 보기',
  '계획 반영': '소비계획 보기',
  '소비계획 만들기': '소비계획 보기',
}
const cardNameTokens = [
  '카드의정석2 SHOPPER',
  '카드의정석 SHOPPER',
  '카드의정석2',
  'LOCA LIKIT Eat',
  'LOCA LIKIT Shop',
  'LOCA LIKIT',
  'LOCA 100',
  '우리카드 7CORE',
  'SHOPPER',
].sort((a, b) => b.length - a.length)
const cardNamePattern = new RegExp(`(${cardNameTokens.map(escapeRegExp).join('|')})`, 'g')

function makeMessage(role, content, extra = {}) {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    role,
    content,
    ...extra,
  }
}

function makeAssistantMessage(content, extra = {}) {
  const avatarIndex = messages.value.filter((message) => message.role === 'assistant').length % assistantAvatars.length
  return makeMessage('assistant', content, { avatarIndex, ...extra })
}

function normalizeMessageForStorage(message) {
  if (!message || typeof message !== 'object') return null
  const role = message.role === 'user' ? 'user' : 'assistant'
  const content = String(message.content || '').trim()
  if (!content) return null
  return {
    id: String(message.id || `${role}-${Date.now()}-${Math.random().toString(16).slice(2)}`),
    role,
    content: content.slice(0, 2000),
    avatarIndex: Number.isInteger(message.avatarIndex) ? message.avatarIndex : undefined,
    quickReplies: Array.isArray(message.quickReplies)
      ? message.quickReplies.map((reply) => String(reply || '').trim()).filter(Boolean).slice(0, 4)
      : [],
    messageType: message.messageType || 'general',
  }
}

function loadSavedMessages() {
  try {
    const raw = window.sessionStorage.getItem(chatMessagesStorageKey)
    const parsed = JSON.parse(raw || '[]')
    const saved = Array.isArray(parsed)
      ? parsed.map(normalizeMessageForStorage).filter(Boolean)
      : []
    return saved.length ? saved : initialMessages()
  } catch {
    return initialMessages()
  }
}

function loadSavedDraft() {
  try {
    return window.sessionStorage.getItem(chatDraftStorageKey) || ''
  } catch {
    return ''
  }
}

function saveMessages() {
  try {
    const payload = messages.value.map(normalizeMessageForStorage).filter(Boolean)
    window.sessionStorage.setItem(chatMessagesStorageKey, JSON.stringify(payload))
  } catch {
    // Storage can fail in private browsing; the chat should still work.
  }
}

function assistantAvatarFor(message) {
  if (Number.isInteger(message.avatarIndex)) {
    return assistantAvatars[message.avatarIndex % assistantAvatars.length]
  }
  const source = String(message.id || message.content || '')
  let hash = 0
  for (const char of source) hash = (hash + char.charCodeAt(0)) % assistantAvatars.length
  return assistantAvatars[hash]
}

function cleanQuickReplies(message) {
  const replies = message?.quickReplies || []
  const cleaned = []
  for (const reply of replies) {
    const label = quickReplyLabels[reply] || reply
    if (label && !cleaned.includes(label)) cleaned.push(label)
  }
  return cleaned.slice(0, 2)
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function messageParts(content) {
  const text = String(content || '')
  if (!text) return []
  const parts = []
  text.split('\n').forEach((line, lineIndex) => {
    if (lineIndex > 0) parts.push({ type: 'br', text: '\n' })
    line.split(cardNamePattern).forEach((chunk) => {
      if (!chunk) return
      parts.push({
        type: cardNameTokens.includes(chunk) ? 'card' : 'text',
        text: chunk,
      })
    })
  })
  return parts
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
      makeAssistantMessage(response.reply || '답변을 만들지 못했습니다. 다시 질문해 주세요.', {
        quickReplies: response.quickReplies || [],
        messageType: response.messageType || 'general',
        confidence: response.confidence,
        aiMode: response.aiMode,
      }),
    )
  } catch (error) {
    console.warn('챗봇 API 호출 실패', error)
    messages.value.push(
      makeAssistantMessage('지금은 저장된 데이터를 기준으로만 답할게요.\n최근 소비 흐름부터 다시 확인해보면 좋아요.', {
        quickReplies: ['소비 분석 보기', '보유 카드 개선'],
        messageType: 'general',
        aiMode: 'rule_fallback',
      }),
    )
  } finally {
    isSending.value = false
    scrollToBottom()
  }
}

watch(messages, saveMessages, { deep: true })

watch(draft, (value) => {
  try {
    window.sessionStorage.setItem(chatDraftStorageKey, value)
  } catch {
    // Ignore storage failures; typing should not be blocked.
  }
})

onMounted(() => {
  saveMessages()
  scrollToBottom()
})
</script>

<style scoped>
.chat-screen {
  background: #fbfdff;
}

.chat-screen .chat-header {
  display: grid !important;
  flex-shrink: 0;
  grid-template-columns: 42px minmax(0, 1fr) 42px !important;
  align-items: center !important;
  justify-content: stretch !important;
  gap: 8px !important;
  padding: 20px 20px 18px !important;
  background: #fbfdff;
  color: #20242a;
}

.chat-header h1 {
  margin: 0;
  color: #20242a;
  font-family: "Pretendard", "Apple SD Gothic Neo", sans-serif;
  font-size: 20px;
  font-weight: 500;
  line-height: 1.25;
  letter-spacing: 0;
}

.support-button {
  display: inline-flex;
  width: 38px;
  height: 38px;
  margin-left: auto !important;
  align-items: center;
  justify-content: center;
  justify-self: end;
  border: 1px solid rgba(36, 54, 79, 0.12);
  border-radius: 14px;
  background: #fff;
  color: #24364f;
  box-shadow: 0 6px 16px rgba(36, 54, 79, 0.08);
}

.chat-body {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 16px;
}

.chat-watermark {
  position: absolute;
  left: 50%;
  top: 58%;
  width: min(220px, 58%);
  max-height: 180px;
  opacity: 0.045;
  pointer-events: none;
  transform: translate(-50%, -50%);
  user-select: none;
  z-index: 0;
}

.message-row {
  position: relative;
  z-index: 1;
  display: flex;
  width: 100%;
  align-items: flex-start;
  gap: 9px;
}

.message-row.user {
  justify-content: flex-end;
}

.assistant-avatar {
  width: 40px;
  height: 40px;
  flex: 0 0 40px;
  border: 1px solid rgba(36, 54, 79, 0.1);
  border-radius: 15px;
  background: #fff;
  box-shadow: 0 8px 18px rgba(36, 54, 79, 0.1);
  object-fit: cover;
}

.assistant-avatar.is-speaking {
  animation: avatar-talk 900ms ease-in-out infinite;
}

.message-stack {
  display: grid;
  max-width: 82%;
  gap: 5px;
}

.message-row.user .message-stack {
  justify-items: end;
}

.assistant-name {
  color: #4e5b6b;
  font-size: 11px;
  font-weight: 800;
  line-height: 1.2;
}

.message-bubble {
  position: relative;
  border: 1px solid #dbe4ee;
  border-radius: 18px;
  padding: 12px 13px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(16, 24, 40, 0.04);
}

.message-row.assistant .message-bubble::before {
  position: absolute;
  top: 13px;
  left: -6px;
  width: 11px;
  height: 11px;
  border-bottom: 1px solid #dbe4ee;
  border-left: 1px solid #dbe4ee;
  background: #fff;
  content: "";
  transform: rotate(45deg);
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
  white-space: pre-line;
  word-break: keep-all;
}

.message-card-name {
  color: #0f5fae;
  font-weight: 900;
}

.message-row.user .message-bubble p {
  color: #fff;
}

.quick-replies {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-top: 2px;
  padding-left: 3px;
}

.chat-screen .quick-replies button {
  min-height: 34px;
  border: 1px solid rgba(15, 95, 174, 0.12) !important;
  border-radius: 999px;
  padding: 8px 12px;
  background: #e8f1ff !important;
  color: #0f5fae !important;
  font-size: 11px;
  font-weight: 900;
  box-shadow: 0 5px 12px rgba(15, 95, 174, 0.08) !important;
}

.chat-screen .quick-replies button:nth-child(1) {
  border-color: rgba(15, 95, 174, 0.18) !important;
  background: linear-gradient(135deg, #e5f0ff 0%, #d8e9ff 100%) !important;
  color: #0f5fae !important;
}

.chat-screen .quick-replies button:nth-child(2) {
  border-color: rgba(0, 140, 149, 0.18) !important;
  background: linear-gradient(135deg, #e1f8f7 0%, #d8f0ff 100%) !important;
  color: #007f89 !important;
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

.chat-screen .chat-composer button {
  display: inline-flex;
  width: 44px;
  height: 44px;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: #24364f !important;
  color: #fff !important;
  box-shadow: 0 8px 18px rgba(36, 54, 79, 0.16) !important;
}

.chat-screen .chat-composer button:disabled {
  background: #dbe4ee !important;
  color: #8a9aad !important;
  box-shadow: none !important;
}

:global(.app-backdrop .phone-shell .chat-screen .chat-composer button[type="submit"]:not(:disabled)) {
  border-color: transparent !important;
  background: #24364f !important;
  color: #fff !important;
  box-shadow: 0 8px 18px rgba(36, 54, 79, 0.16) !important;
}

:global(.app-backdrop .phone-shell .chat-screen .chat-composer button[type="submit"]:not(:disabled):hover) {
  background: #1c3149 !important;
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

@keyframes avatar-talk {
  0%,
  100% {
    transform: translateY(0) scale(1);
  }
  45% {
    transform: translateY(-1px) scale(1.035);
  }
}
</style>
