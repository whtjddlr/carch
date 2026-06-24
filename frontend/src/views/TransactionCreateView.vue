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
            <span>{{ imageName || '이미지 참고용 선택' }}</span>
            <input type="file" accept="image/*" aria-label="결제 캡처 이미지 선택" @change="onImageChange" />
          </label>
          <img v-if="imagePreview" :src="imagePreview" alt="결제 캡처 미리보기" />
          <p class="capture-helper">
            이미지는 참고용으로 첨부됩니다. 승인 문구를 함께 입력하면 AI로 항목을 채울 수 있어요.
          </p>
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

        <div v-if="parsedSourceText" class="source-evidence">
          <span>AI가 읽은 원문</span>
          <p>{{ parsedSourceText }}</p>
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

        <div class="payment-mode-grid">
          <label>
            <span class="field-label">결제 방식</span>
            <select v-model="form.paymentType" class="form-field" aria-label="결제 방식">
              <option value="lump_sum">일시불</option>
              <option value="installment">할부</option>
            </select>
          </label>
          <label v-if="form.paymentType === 'installment'">
            <span class="field-label">개월 수</span>
            <select v-model.number="form.installmentMonths" class="form-field" aria-label="할부 개월 수">
              <option v-for="month in installmentMonthOptions" :key="month" :value="month">{{ month }}개월</option>
            </select>
          </label>
          <label v-if="form.paymentType === 'installment'" class="installment-toggle">
            <input v-model="form.isInterestFreeInstallment" type="checkbox" />
            <span>무이자 할부</span>
          </label>
        </div>

        <div class="two-col">
          <div class="date-picker-field">
            <AppCalendarPicker v-model="form.date" label="날짜" mode="date" />
          </div>
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
import AppCalendarPicker from '@/components/AppCalendarPicker.vue'
import { cards as mockCards } from '@/data/mockData'
import { createTransaction, fetchOwnedCards, normalizeCard, parseTransaction } from '@/services/api'

const router = useRouter()
const sourceMode = ref('text')
const rawText = ref('오늘 컴포즈커피 역삼센터필드점에서 3800원 LOCA LIKIT Eat로 결제했어')
const isParsing = ref(false)
const isSaving = ref(false)
const confidence = ref(0)
const imagePreview = ref('')
const imageName = ref('')
const cards = ref(mockCards)
const parsedSourceText = ref('')

const categories = ['카페', '식비', '쇼핑', '교통', '헬스', '교육', '편의점', '뷰티', '문화', '구독', '기타']
const installmentMonthOptions = [2, 3, 4, 5, 6, 9, 10, 12]
const examples = [
  '오늘 컴포즈커피 역삼센터필드점에서 3800원 LOCA LIKIT Eat로 결제했어',
  '우리카드 06/20 23:41 무신사 스토어 86,400원 승인',
  'LOCA 100으로 카카오T 13,600원 결제',
  '카드의정석 SHOPPER로 쿠팡 240,000원 6개월 무이자 할부',
]

const form = reactive({
  merchantName: '',
  amount: -3800,
  category: '카페',
  cardId: '10106',
  paymentType: 'lump_sum',
  installmentMonths: 0,
  isInterestFreeInstallment: false,
  date: '2026-06-23',
  time: '08:42',
  address: '서울 강남구 테헤란로 231',
  icon: '☕',
})

const placeholder = computed(() => (
  sourceMode.value === 'capture'
    ? '[우리카드] 06/20 23:41 무신사 스토어 86,400원 승인'
    : '오늘 컴포즈커피 역삼센터필드점에서 3800원 LOCA LIKIT Eat로 결제했어'
))

const canSave = computed(() => form.merchantName.trim() && Number(form.amount) !== 0 && form.cardId && form.date && form.time)

const applyParsed = (parsed) => {
  form.merchantName = parsed.merchantName || parsed.merchant || form.merchantName
  form.amount = parsed.amount || parsed.amt || form.amount
  form.category = parsed.category || parsed.cat || form.category
  form.cardId = parsed.cardId || form.cardId
  form.paymentType = parsed.paymentType || parsed.payment_type || form.paymentType
  form.installmentMonths = Number(parsed.installmentMonths ?? parsed.installment_months ?? form.installmentMonths) || 0
  form.isInterestFreeInstallment = Boolean(parsed.isInterestFreeInstallment ?? parsed.is_interest_free_installment ?? form.isInterestFreeInstallment)
  if (form.paymentType === 'installment' && form.installmentMonths < 2) {
    form.installmentMonths = 2
  }
  form.date = parsed.date || String(parsed.approvedAt || '').slice(0, 10) || form.date
  form.time = parsed.time || String(parsed.approvedAt || '').slice(11, 16) || form.time
  form.address = parsed.address || parsed.addr || form.address
  form.icon = parsed.icon || form.icon
  confidence.value = parsed.confidence || 0.8
}

const handleParse = async () => {
  isParsing.value = true
  try {
    parsedSourceText.value = rawText.value.trim()
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
      paymentType: form.paymentType,
      installmentMonths: form.paymentType === 'installment' ? form.installmentMonths : 0,
      isInterestFreeInstallment: form.paymentType === 'installment' && form.isInterestFreeInstallment,
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

.date-picker-field {
  min-width: 0;
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

.capture-helper {
  grid-column: 1 / -1;
  margin: -2px 0 0;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.45;
}

.example-row {
  display: grid;
  gap: 8px;
  margin: 12px 0;
  padding-bottom: 0;
}

.example-row button {
  min-height: 44px;
  overflow: visible;
  border: 1px solid rgba(15, 95, 174, 0.1);
  border-radius: 13px;
  padding: 10px 12px;
  background: #fbfdff;
  color: #4a5663;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.45;
  text-align: left;
  white-space: normal;
  word-break: keep-all;
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

.source-evidence {
  display: grid;
  gap: 7px;
  margin: -2px 0 14px;
  border: 1px solid rgba(15, 95, 174, 0.12);
  border-radius: 14px;
  padding: 12px;
  background: rgba(232, 241, 251, 0.58);
}

.source-evidence span {
  color: #0f5fae;
  font-size: 11px;
  font-weight: 950;
}

.source-evidence p {
  margin: 0;
  color: #17202b;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.5;
  word-break: keep-all;
  overflow-wrap: anywhere;
}

.two-col {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.payment-mode-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  align-items: end;
}

.installment-toggle {
  grid-column: 1 / -1;
  display: flex;
  min-height: 44px;
  align-items: center;
  gap: 9px;
  border: 1px solid rgba(15, 95, 174, 0.14);
  border-radius: 13px;
  padding: 0 12px;
  background: #f8fbff;
  color: #17202b;
  font-size: 13px;
  font-weight: 850;
}

.installment-toggle input {
  width: 17px;
  height: 17px;
  accent-color: #0f5fae;
}

.field-label {
  margin-top: 12px;
}

.result-card .primary-button {
  margin-top: 14px;
}
</style>
