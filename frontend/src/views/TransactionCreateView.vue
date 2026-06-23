<template>
  <section class="screen">
    <header class="create-header blue-gradient">
      <AppBackButton fallback="/transactions" />
      <div>
        <p>소비내역 추가</p>
        <h1>AI 입력 보정</h1>
      </div>
    </header>

    <div class="screen-scroll scrollbar-hide create-body">
      <section class="app-card prompt-card">
        <div class="source-tabs">
          <button :class="{ active: sourceMode === 'text' }" type="button" @click="sourceMode = 'text'">
            <PencilLine :size="15" />
            문장
          </button>
          <button :class="{ active: sourceMode === 'capture' }" type="button" @click="sourceMode = 'capture'">
            <ImageIcon :size="15" />
            캡처
          </button>
        </div>

        <textarea
          v-model="rawText"
          class="form-field prompt-field"
          rows="5"
          aria-label="소비내역 원문"
          :placeholder="placeholder"
        />

        <div v-if="sourceMode === 'capture'" class="capture-box">
          <label>
            <Upload :size="18" />
            <span>{{ imageName || '이미지 선택' }}</span>
            <input type="file" accept="image/*" aria-label="결제 캡처 이미지 선택" @change="onImageChange" />
          </label>
          <img v-if="imagePreview" :src="imagePreview" alt="결제 캡처 미리보기" />
        </div>

        <div class="example-row">
          <button
            v-for="example in examples"
            :key="example"
            type="button"
            :aria-label="`예시 입력: ${example}`"
            @click="rawText = example"
          >
            {{ example }}
          </button>
        </div>

        <button class="primary-button w-100" type="button" :disabled="isParsing || !rawText.trim()" @click="handleParse">
          <Sparkles :size="16" />
          {{ isParsing ? '보정 중' : 'AI로 채우기' }}
        </button>
      </section>

      <section class="app-card result-card">
        <div class="result-head">
          <div>
            <span>확인 후 저장</span>
            <h2>{{ form.merchantName || '가맹점 미입력' }}</h2>
          </div>
          <strong :class="{ low: confidence < 0.7 }">{{ Math.round(confidence * 100) }}%</strong>
        </div>

        <label class="field-label" for="merchantName">가맹점</label>
        <input id="merchantName" v-model="form.merchantName" class="form-field" aria-label="가맹점" />

        <div class="two-col">
          <label>
            <span class="field-label">금액</span>
            <input v-model.number="form.amount" class="form-field" inputmode="numeric" aria-label="금액" />
          </label>
          <label>
            <span class="field-label">카테고리</span>
            <select v-model="form.category" class="form-field" aria-label="카테고리">
              <option v-for="category in categories" :key="category" :value="category">{{ category }}</option>
            </select>
          </label>
        </div>

        <label class="field-label" for="cardId">카드</label>
        <select id="cardId" v-model="form.cardId" class="form-field" aria-label="카드">
          <option v-for="card in cards" :key="card.id" :value="card.id">
            {{ card.issuer }} · {{ card.name }}
          </option>
        </select>

        <div class="two-col">
          <label>
            <span class="field-label">날짜</span>
            <input v-model="form.date" class="form-field" type="date" aria-label="날짜" />
          </label>
          <label>
            <span class="field-label">시간</span>
            <input v-model="form.time" class="form-field" type="time" aria-label="시간" />
          </label>
        </div>

        <label class="field-label" for="address">장소</label>
        <input id="address" v-model="form.address" class="form-field" aria-label="장소" />

        <button class="primary-button w-100" type="button" :disabled="isSaving || !canSave" @click="handleSave">
          <Check :size="16" />
          {{ isSaving ? '저장 중' : '소비내역 저장' }}
        </button>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Check, ImageIcon, PencilLine, Sparkles, Upload } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { cards as mockCards } from '@/data/mockData'
import { createTransaction, fetchOwnedCards, normalizeCard, parseTransaction } from '@/services/api'

const router = useRouter()
const sourceMode = ref('text')
const rawText = ref('오늘 스타벅스 강남역점에서 5500원 LOCA 100으로 결제했어')
const isParsing = ref(false)
const isSaving = ref(false)
const confidence = ref(0)
const imagePreview = ref('')
const imageName = ref('')
const cards = ref(mockCards)

const categories = ['카페', '쇼핑', '편의점', '뷰티', '식비', '마트', '교통', '문화', '구독', '기타']
const examples = [
  '오늘 스타벅스 강남역점에서 5500원 LOCA 100으로 결제했어',
  '신한카드 06/22 14:30 이마트 67,800원 승인',
]

const form = reactive({
  merchantName: '',
  amount: -5500,
  category: '카페',
  cardId: '10029',
  date: '2026-06-22',
  time: '14:30',
  address: '직접 입력',
  icon: '💳',
})

const placeholder = computed(() => (
  sourceMode.value === 'capture'
    ? '[신한카드] 06/22 14:30 이마트 67,800원 승인'
    : '오늘 스타벅스 강남역점에서 5500원 LOCA 100으로 결제했어'
))

const canSave = computed(() => form.merchantName.trim() && Number(form.amount) !== 0 && form.cardId && form.date && form.time)

const applyParsed = (parsed) => {
  form.merchantName = parsed.merchantName || parsed.merchant || form.merchantName
  form.amount = parsed.amount || parsed.amt || form.amount
  form.category = parsed.category || parsed.cat || form.category
  form.cardId = parsed.cardId || form.cardId
  form.date = parsed.date || String(parsed.approvedAt || '').slice(0, 10) || form.date
  form.time = parsed.time || String(parsed.approvedAt || '').slice(11, 16) || form.time
  form.address = parsed.address || parsed.addr || form.address
  form.icon = parsed.icon || form.icon
  confidence.value = parsed.confidence || 0.8
}

const handleParse = async () => {
  isParsing.value = true
  try {
    const parsed = await parseTransaction(rawText.value)
    applyParsed(parsed)
  } catch (error) {
    console.warn('거래내역 보정 API를 불러오지 못했습니다.', error)
  } finally {
    isParsing.value = false
  }
}

const handleSave = async () => {
  isSaving.value = true
  try {
    await createTransaction({
      cardId: form.cardId,
      merchantName: form.merchantName,
      category: form.category,
      amount: form.amount,
      approvedAt: `${form.date}T${form.time}:00+09:00`,
      icon: form.icon,
      address: form.address,
    })
    router.push('/transactions')
  } catch (error) {
    console.warn('거래내역 저장 API를 불러오지 못했습니다.', error)
  } finally {
    isSaving.value = false
  }
}

const onImageChange = (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  imageName.value = file.name
  imagePreview.value = URL.createObjectURL(file)
  if (!rawText.value.trim()) {
    rawText.value = '[카드앱] 06/22 14:30 이마트 67,800원 승인'
  }
}

onMounted(async () => {
  try {
    const apiCards = await fetchOwnedCards()
    cards.value = apiCards.map((card, index) => normalizeCard(card, index))
  } catch (error) {
    console.warn('카드 API를 불러오지 못해 mock 카드 목록을 사용합니다.', error)
  }
  await handleParse()
})
</script>

<style scoped>
.create-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 24px 20px;
  color: #fff;
}

.create-header p {
  margin: 0 0 4px;
  color: rgba(255, 255, 255, 0.68);
  font-size: 12px;
  font-weight: 700;
}

.create-header h1 {
  margin: 0;
  font-size: 23px;
  font-weight: 900;
}

.create-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 20px;
}

.prompt-card,
.result-card {
  padding: 16px;
}

.source-tabs {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-bottom: 12px;
}

.source-tabs button {
  display: inline-flex;
  min-height: 44px;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border-radius: 12px;
  padding: 10px;
  background: #e7edf4;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 900;
}

.source-tabs button.active {
  background: #e8f1ff;
  color: #0f5fae;
}

.prompt-field {
  min-height: 118px;
  resize: vertical;
  line-height: 1.55;
}

.capture-box {
  display: grid;
  grid-template-columns: 1fr 92px;
  gap: 10px;
  margin-top: 10px;
}

.capture-box label {
  display: flex;
  min-height: 72px;
  min-width: 0;
  align-items: center;
  gap: 8px;
  border: 1px dashed #bfdbfe;
  border-radius: 14px;
  padding: 12px;
  background: #e8f1ff;
  color: #0f5fae;
  font-size: 12px;
  font-weight: 900;
}

.capture-box input {
  display: none;
}

.capture-box img {
  width: 92px;
  height: 72px;
  object-fit: cover;
  border-radius: 12px;
  border: 1px solid #dbe4ee;
}

.example-row {
  display: flex;
  gap: 7px;
  overflow-x: auto;
  margin: 12px 0;
  padding-bottom: 2px;
  scrollbar-width: none;
}

.example-row::-webkit-scrollbar {
  display: none;
}

.example-row button {
  flex: 0 0 auto;
  max-width: 230px;
  min-height: 40px;
  overflow: hidden;
  border-radius: 999px;
  padding: 7px 10px;
  background: #fbfdff;
  color: #4a5663;
  font-size: 11px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.result-head span {
  color: #0f5fae;
  font-size: 11px;
  font-weight: 900;
}

.result-head h2 {
  margin: 4px 0 0;
  color: #17202b;
  font-size: 18px;
  font-weight: 900;
}

.result-head strong {
  border-radius: 999px;
  padding: 5px 9px;
  background: #ecfdf5;
  color: #008c95;
  font-size: 12px;
  font-weight: 900;
}

.result-head strong.low {
  background: #f7f1e6;
  color: #ea580c;
}

.two-col {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.field-label {
  margin-top: 12px;
}

.result-card .primary-button {
  margin-top: 14px;
}
</style>
