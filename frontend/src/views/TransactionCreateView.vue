<template>
  <section class="screen">
    <header class="create-header blue-gradient">
      <AppBackButton fallback="/transactions" />
      <div>
        <h1>결제내역 추가</h1>
      </div>
    </header>

    <div class="screen-scroll scrollbar-hide create-body">
      <div class="tx-input">
        <textarea
          v-model="rawText"
          class="form-field prompt-field"
          rows="4"
          aria-label="소비내역 원문"
          placeholder="예: 오늘 컴포즈커피에서 3,800원 LOCA LIKIT Eat로 결제했어"
        />
        <div class="input-actions">
          <label class="img-upload">
            <ImageIcon :size="16" />
            <span>{{ imageName || '이미지 업로드' }}</span>
            <input type="file" accept="image/*" aria-label="결제 캡처 업로드" @change="onImageChange" />
          </label>
          <button class="primary-button" type="button" :disabled="isParsing || !rawText.trim()" @click="handleParse">
            <Sparkles :size="16" />
            {{ isParsing ? '채우는 중' : 'AI로 채우기' }}
          </button>
        </div>
      </div>

      <div class="tx-form">
        <label class="field">
          <span class="field-label"><Store :size="14" /> 가맹점</span>
          <input v-model="form.merchantName" class="form-field" aria-label="가맹점" />
        </label>

        <div class="two-col">
          <label class="field">
            <span class="field-label"><Coins :size="14" /> 금액</span>
            <input v-model.number="form.amount" class="form-field" inputmode="numeric" aria-label="금액" />
          </label>
          <label class="field">
            <span class="field-label"><Tag :size="14" /> 카테고리</span>
            <select v-model="form.category" class="form-field" aria-label="카테고리">
              <option v-for="category in categories" :key="category" :value="category">{{ category }}</option>
            </select>
          </label>
        </div>

        <label class="field">
          <span class="field-label"><CreditCard :size="14" /> 카드</span>
          <select v-model="form.cardId" class="form-field" aria-label="카드">
            <option v-for="card in cards" :key="card.id" :value="card.id">{{ card.issuer }} · {{ card.name }}</option>
          </select>
        </label>

        <div class="field">
          <span class="field-label"><Wallet :size="14" /> 결제 방식</span>
          <div class="pay-seg" role="radiogroup" aria-label="결제 방식">
            <button type="button" :class="{ active: form.paymentType === 'lump_sum' }" @click="setPaymentMode('lump_sum')">일시불</button>
            <button type="button" :class="{ active: form.paymentType === 'installment' }" @click="setPaymentMode('installment')">할부</button>
          </div>
          <div v-if="form.paymentType === 'installment'" class="install-extra">
            <select v-model.number="form.installmentMonths" class="form-field" aria-label="할부 개월 수">
              <option v-for="month in installmentMonthOptions" :key="month" :value="month">{{ month }}개월</option>
            </select>
            <label class="free-toggle" :class="{ on: form.isInterestFreeInstallment }">
              <input type="checkbox" v-model="form.isInterestFreeInstallment" />
              무이자
            </label>
          </div>
        </div>

        <div class="two-col">
          <div class="field">
            <span class="field-label"><CalendarDays :size="14" /> 날짜</span>
            <AppCalendarPicker v-model="form.date" label="" mode="date" />
          </div>
          <label class="field">
            <span class="field-label"><Clock :size="14" /> 시간</span>
            <input v-model="form.time" class="form-field" type="time" aria-label="시간" />
          </label>
        </div>

        <div class="preview-block">
          <span class="preview-label">이렇게 추가돼요</span>
          <div class="tx-preview">
            <span class="prev-emoji">{{ form.icon || '🧾' }}</span>
            <div class="prev-info">
              <strong>{{ form.merchantName || '가맹점' }}</strong>
              <small>{{ form.category }} · {{ paymentLabel }} · {{ form.time || '시간' }}</small>
            </div>
            <span class="prev-card">
              <img
                v-if="previewCardImage"
                :src="previewCardImage"
                :alt="previewCard?.name"
                :class="previewOri"
                @load="onPreviewThumb"
              />
            </span>
            <b>{{ Math.abs(Number(form.amount) || 0).toLocaleString() }}원</b>
          </div>
        </div>

        <button class="primary-button w-100" type="button" :disabled="isSaving || !canSave" @click="handleSave">
          <Check :size="16" />
          {{ isSaving ? '저장 중' : '소비내역 저장' }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { CalendarDays, Check, Clock, Coins, CreditCard, ImageIcon, Sparkles, Store, Tag, Wallet } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import AppCalendarPicker from '@/components/AppCalendarPicker.vue'
import { cards as mockCards } from '@/data/mockData'
import { createTransaction, fetchOwnedCards, normalizeCard, parseTransaction } from '@/services/api'

const router = useRouter()
const rawText = ref('오늘 컴포즈커피 역삼센터필드점에서 3800원 LOCA LIKIT Eat로 결제했어')
const isParsing = ref(false)
const isSaving = ref(false)
const cards = ref(mockCards)
const imageName = ref('')
const previewOri = ref('')

const categories = ['카페', '식비', '쇼핑', '교통', '헬스', '교육', '편의점', '뷰티', '문화', '구독', '기타']
const installmentMonthOptions = [2, 3, 4, 5, 6, 9, 10, 12]

const form = reactive({
  merchantName: '',
  amount: 3800,
  category: '카페',
  cardId: '10106',
  paymentType: 'lump_sum',
  installmentMonths: 0,
  isInterestFreeInstallment: false,
  date: '2026-06-23',
  time: '08:42',
  address: '',
  icon: '☕',
})

const canSave = computed(() => form.merchantName.trim() && Number(form.amount) !== 0 && form.cardId && form.date && form.time)

// 결제내역 목록에 추가될 모습 미리보기
const paymentLabel = computed(() => {
  if (form.paymentType !== 'installment') return '일시불'
  const months = form.installmentMonths || 0
  return form.isInterestFreeInstallment ? `무이자 ${months}개월` : `할부 ${months}개월`
})
const previewCard = computed(() => cards.value.find((card) => String(card.id) === String(form.cardId)) || null)
const previewCardImage = computed(() => previewCard.value?.imageUrl || '')
function onPreviewThumb(event) {
  const img = event.target
  previewOri.value = img.naturalWidth > img.naturalHeight ? 'is-landscape' : 'is-portrait'
}

function onImageChange(event) {
  const file = event.target.files?.[0]
  if (file) imageName.value = file.name
}

function setPaymentMode(mode) {
  if (mode === 'lump_sum') {
    form.paymentType = 'lump_sum'
    form.installmentMonths = 0
    form.isInterestFreeInstallment = false
    return
  }
  form.paymentType = 'installment'
  if (form.installmentMonths < 2) form.installmentMonths = 2
}

const applyParsed = (parsed) => {
  form.merchantName = parsed.merchantName || parsed.merchant || form.merchantName
  form.amount = Math.abs(parsed.amount || parsed.amt || form.amount)
  form.category = parsed.category || parsed.cat || form.category
  form.cardId = parsed.cardId || form.cardId
  form.paymentType = parsed.paymentType || parsed.payment_type || form.paymentType
  form.installmentMonths = Number(parsed.installmentMonths ?? parsed.installment_months ?? form.installmentMonths) || 0
  form.isInterestFreeInstallment = Boolean(parsed.isInterestFreeInstallment ?? parsed.is_interest_free_installment ?? form.isInterestFreeInstallment)
  if (form.isInterestFreeInstallment) form.paymentType = 'installment'
  if (form.paymentType === 'installment' && form.installmentMonths < 2) form.installmentMonths = 2
  form.date = parsed.date || String(parsed.approvedAt || '').slice(0, 10) || form.date
  form.time = parsed.time || String(parsed.approvedAt || '').slice(11, 16) || form.time
  form.address = parsed.address || parsed.addr || form.address
  form.icon = parsed.icon || form.icon
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
      amount: -Math.abs(Number(form.amount) || 0),
      approvedAt: `${form.date}T${form.time}:00+09:00`,
      paymentType: form.paymentType,
      installmentMonths: form.paymentType === 'installment' ? form.installmentMonths : 0,
      isInterestFreeInstallment: form.paymentType === 'installment' && form.isInterestFreeInstallment,
      icon: form.icon,
      address: form.address,
    })
    router.replace('/transactions')
  } catch (error) {
    console.warn('거래내역 저장 API를 불러오지 못했습니다.', error)
  } finally {
    isSaving.value = false
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
  padding: 16px 20px;
  color: #fff;
}

.create-header h1 {
  margin: 0;
  font-size: 21px;
  font-weight: 900;
}

.create-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 12px 20px 16px;
}

/* 입력 영역 — 박스 없이 입력창 + 버튼만 */
.tx-input {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.prompt-field {
  min-height: 74px;
  resize: vertical;
  line-height: 1.5;
}

.input-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.input-actions .primary-button {
  min-height: 44px;
}

.img-upload {
  display: inline-flex;
  min-height: 44px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  overflow: hidden;
  border: 1px solid #dbe4ee;
  border-radius: 999px;
  padding: 0 14px;
  background: #fff;
  color: #4a5663;
  font-size: 13px;
  font-weight: 800;
}

.img-upload svg {
  flex: 0 0 auto;
  color: #0f5fae;
}

.img-upload span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.img-upload input {
  display: none;
}

.preview-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 2px;
}

.preview-label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: #6e7885;
  font-size: 12px;
  font-weight: 800;
}

.tx-preview {
  display: flex;
  align-items: center;
  gap: 11px;
  border-radius: 16px;
  padding: 13px 14px;
  background: #f4f7fb;
}

.prev-emoji {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 11px;
  background: #fff;
  font-size: 19px;
  box-shadow: 0 2px 7px rgba(36, 54, 79, 0.08);
}

.prev-info {
  flex: 1 1 auto;
  min-width: 0;
}

.prev-info strong {
  display: block;
  overflow: hidden;
  color: #17202b;
  font-size: 13.5px;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.prev-info small {
  display: block;
  margin-top: 2px;
  color: #6e7885;
  font-size: 11.5px;
  font-weight: 700;
}

.prev-card {
  position: relative;
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 40px;
  height: 26px;
  overflow: hidden;
  border-radius: 5px;
  background: #e8edf2;
}

.prev-card img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.prev-card img.is-portrait {
  inset: auto;
  top: 50%;
  left: 50%;
  width: 26px;
  height: 40px;
  max-width: none;
  transform: translate(-50%, -50%) rotate(-90deg);
}

.tx-preview b {
  flex: 0 0 auto;
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
  font-variant-numeric: tabular-nums;
}

/* 결과 폼 — 박스/구분선 없이 한 흐름으로 정렬 */
.tx-form {
  display: flex;
  flex-direction: column;
  gap: 11px;
}

.field {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: #4a5663;
  font-size: 12.5px;
  font-weight: 800;
}

.field-label :deep(svg),
.field-label svg {
  color: #0f5fae;
}

.two-col {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  align-items: start;
}

/* 날짜·시간 컨트롤 높이 통일 */
.two-col .form-field,
.two-col :deep(.calendar-trigger) {
  height: 46px;
  min-height: 46px;
}

.pay-seg {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.app-backdrop .phone-shell .pay-seg button {
  min-height: 44px;
  border: 1px solid #dbe4ee !important;
  border-radius: 13px;
  background: #fff !important;
  color: #526071 !important;
  font-size: 13.5px;
  font-weight: 800;
}

.app-backdrop .phone-shell .pay-seg button.active {
  border-color: transparent !important;
  background: #24364f !important;
  color: #fff !important;
}

.install-extra {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 12px;
  margin-top: 2px;
}

.free-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #6e7885;
  font-size: 13px;
  font-weight: 800;
  white-space: nowrap;
}

.free-toggle.on {
  color: #0f5fae;
}

.free-toggle input {
  width: 17px;
  height: 17px;
  accent-color: #0f5fae;
}

.tx-form .primary-button {
  margin-top: 4px;
}
</style>
