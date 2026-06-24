<template>
  <div class="calendar-picker" :class="`mode-${mode}`">
    <button class="calendar-trigger" type="button" :aria-label="`${label} 선택`" @click="openPicker">
      <span>{{ label }}</span>
      <strong>{{ displayValue }}</strong>
      <Calendar :size="17" />
    </button>

    <div v-if="isOpen" class="calendar-scrim" @click.self="closePicker">
      <section class="calendar-sheet" role="dialog" aria-modal="true" :aria-label="`${label} 선택`">
        <div class="sheet-grip" />
        <header class="calendar-sheet-head">
          <div>
            <span>{{ isMonthMode ? '월 선택' : '날짜 선택' }}</span>
            <strong>{{ sheetTitle }}</strong>
          </div>
          <button type="button" aria-label="닫기" @click="closePicker">
            <X :size="18" />
          </button>
        </header>

        <VueDatePicker
          v-model="draftValue"
          class="calendar-inline"
          inline
          auto-apply
          :month-picker="isMonthMode"
          :formats="formats"
          :locale="ko"
          :time-config="timeConfig"
          :action-row="hiddenActionRow"
          :six-weeks="isMonthMode ? false : 'center'"
          year-first
        />

        <footer class="calendar-actions">
          <button class="quick-button" type="button" @click="selectToday">
            {{ isMonthMode ? '이번 달' : '오늘' }}
          </button>
          <button class="cancel-button" type="button" @click="closePicker">취소</button>
          <button class="apply-button" type="button" :disabled="!draftValue" @click="applyValue">적용</button>
        </footer>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { ko } from 'date-fns/locale'
import { VueDatePicker } from '@vuepic/vue-datepicker'
import '@vuepic/vue-datepicker/dist/main.css'
import { Calendar, X } from 'lucide-vue-next'

const props = defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, required: true },
  mode: {
    type: String,
    default: 'date',
    validator: (value) => ['date', 'month'].includes(value),
  },
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const draftValue = ref(null)
const isMonthMode = computed(() => props.mode === 'month')

const pickerValue = computed(() => (
  isMonthMode.value
    ? parseMonthModel(props.modelValue)
    : parseDateModel(props.modelValue)
))

const displayValue = computed(() => {
  if (!props.modelValue) return isMonthMode.value ? '월 선택' : '날짜 선택'
  if (isMonthMode.value) {
    const [year, month] = props.modelValue.split('-')
    return `${year}년 ${month}월`
  }
  const [year, month, day] = props.modelValue.split('-')
  return `${year}.${month}.${day}`
})

const sheetTitle = computed(() => {
  if (!draftValue.value) return displayValue.value
  return isMonthMode.value ? formatMonthDisplay(draftValue.value) : formatDateDisplay(draftValue.value)
})

const formats = computed(() => (
  isMonthMode.value
    ? {
        input: 'yyyy년 MM월',
        preview: 'yyyy년 MM월',
        month: 'M월',
        year: 'yyyy년',
      }
    : {
        input: 'yyyy.MM.dd',
        preview: 'yyyy.MM.dd',
        month: 'M월',
        year: 'yyyy년',
        weekDay: 'EEEEE',
      }
))

const hiddenActionRow = {
  selectBtnLabel: '적용',
  cancelBtnLabel: '취소',
  nowBtnLabel: '오늘',
  showSelect: false,
  showCancel: false,
  showNow: false,
  showPreview: false,
}

const timeConfig = { enableTimePicker: false }

watch(
  () => props.modelValue,
  () => {
    if (!isOpen.value) draftValue.value = pickerValue.value
  },
)

function openPicker() {
  draftValue.value = pickerValue.value || defaultValue()
  isOpen.value = true
}

function closePicker() {
  isOpen.value = false
}

function applyValue() {
  if (!draftValue.value) return
  emit('update:modelValue', isMonthMode.value ? formatMonthValue(draftValue.value) : formatDateValue(draftValue.value))
  closePicker()
}

function selectToday() {
  draftValue.value = isMonthMode.value ? parseMonthModel(currentMonthValue()) : todayDate()
}

function defaultValue() {
  return isMonthMode.value ? parseMonthModel(currentMonthValue()) : todayDate()
}

function todayDate() {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth(), now.getDate())
}

function currentMonthValue() {
  const now = new Date()
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}`
}

function parseMonthModel(value) {
  const [year, month] = String(value || '').split('-').map(Number)
  if (!year || !month) return null
  return { year, month: month - 1 }
}

function parseDateModel(value) {
  const [year, month, day] = String(value || '').split('-').map(Number)
  if (!year || !month || !day) return null
  return new Date(year, month - 1, day)
}

function formatMonthValue(value) {
  if (typeof value === 'string') return value.slice(0, 7)
  if (value instanceof Date) return `${value.getFullYear()}-${pad(value.getMonth() + 1)}`
  if (value && Number.isInteger(value.year) && Number.isInteger(value.month)) {
    return `${value.year}-${pad(value.month + 1)}`
  }
  return props.modelValue
}

function formatDateValue(value) {
  if (typeof value === 'string') return value.slice(0, 10)
  if (value instanceof Date) {
    return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}`
  }
  return props.modelValue
}

function formatMonthDisplay(value) {
  const formatted = formatMonthValue(value)
  const [year, month] = formatted.split('-')
  return `${year}년 ${month}월`
}

function formatDateDisplay(value) {
  const formatted = formatDateValue(value)
  const [year, month, day] = formatted.split('-')
  return `${year}.${month}.${day}`
}

function pad(value) {
  return String(value).padStart(2, '0')
}
</script>

<style scoped>
.calendar-picker {
  min-width: 0;
}

.calendar-trigger {
  display: grid;
  width: 100%;
  min-height: 58px;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 6px 10px;
  border: 1px solid #dbe4ee;
  border-radius: 15px;
  padding: 10px 12px;
  background:
    linear-gradient(180deg, #ffffff 0%, #f8fbfe 100%);
  color: #17202b;
  text-align: left;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.calendar-trigger span {
  color: #6f7d8c;
  font-size: 10px;
  font-weight: 800;
}

.calendar-trigger strong {
  min-width: 0;
  color: #17202b;
  font-size: 13px;
  font-weight: 900;
}

.calendar-trigger svg {
  grid-row: 1 / span 2;
  grid-column: 2;
  color: #2c638f;
}

.calendar-scrim {
  position: fixed;
  inset: 0;
  z-index: 90;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 0 14px 14px;
  background: rgba(23, 32, 43, 0.28);
  backdrop-filter: blur(5px);
  animation: calendar-fade 140ms ease both;
}

.calendar-sheet {
  width: min(100%, 360px);
  max-height: min(78dvh, 560px);
  overflow-y: auto;
  border: 1px solid rgba(219, 228, 238, 0.92);
  border-radius: 24px;
  padding: 8px 14px 12px;
  background:
    radial-gradient(circle at 12% 0%, rgba(15, 95, 174, 0.07), transparent 34%),
    linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
  box-shadow: 0 22px 56px rgba(36, 54, 79, 0.2);
  animation: calendar-up 180ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
}

.sheet-grip {
  width: 40px;
  height: 4px;
  margin: 2px auto 12px;
  border-radius: 999px;
  background: #dbe4ee;
}

.calendar-sheet-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.calendar-sheet-head span {
  color: #6f7d8c;
  font-size: 10.5px;
  font-weight: 900;
}

.calendar-sheet-head strong {
  display: block;
  margin-top: 2px;
  color: #17202b;
  font-size: 18px;
  font-weight: 900;
  letter-spacing: 0;
}

.calendar-sheet-head button {
  display: inline-flex;
  width: 34px;
  height: 34px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(138, 154, 173, 0.14);
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
  color: #486782;
  box-shadow: 0 6px 14px rgba(36, 54, 79, 0.08);
}

.calendar-inline :deep(.dp--main),
.calendar-inline :deep(.dp--menu),
.calendar-inline :deep(.dp--instance-calendar) {
  width: 100%;
  min-width: 0;
  font-family: var(--carch-font-sans);
}

.calendar-inline :deep(.dp--menu) {
  border: 0;
  background: transparent;
  box-shadow: none;
}

.calendar-inline :deep(.dp--menu-inner) {
  padding: 0;
  background: transparent;
}

.calendar-inline :deep(.dp--month-year-row) {
  height: 38px;
  margin: 4px 0 8px;
  color: #17202b;
}

.calendar-inline :deep(.dp--inner-nav) {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #f1f6fb;
  color: #2c638f;
}

.calendar-inline :deep(.dp--month-year-select-base) {
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
}

.calendar-inline :deep(.dp--calendar-header) {
  color: #8a9aad;
  font-size: 11px;
  font-weight: 900;
}

.calendar-inline :deep(.dp--calendar-header-cell) {
  border-bottom: 0;
  padding: 4px 0 6px;
}

.calendar-inline :deep(.dp--calendar-row) {
  margin: 3px 0;
}

.calendar-inline :deep(.dp--cell-inner) {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  color: #17202b;
  font-size: 13px;
  font-weight: 900;
}

.calendar-inline :deep(.dp--date-hoverable:hover),
.calendar-inline :deep(.dp--month-year-select-base:hover),
.calendar-inline :deep(.dp--inner-nav:hover) {
  background: #eef5fb;
  color: #0f5fae;
}

.calendar-inline :deep(.dp--today) {
  border-color: rgba(15, 95, 174, 0.3);
}

.calendar-inline :deep(.dp--active) {
  background: #24364f;
  color: #fff;
  box-shadow: 0 8px 16px rgba(36, 54, 79, 0.16);
}

.calendar-inline :deep(.dp--cell-offset) {
  color: #b7c3cf;
}

.calendar-inline :deep(.dp--selection-grid-header) {
  color: #17202b;
  font-size: 16px;
  font-weight: 900;
}

.calendar-inline :deep(.dp--overlay-container) {
  height: auto;
  overflow: visible;
}

.calendar-inline :deep(.dp--overlay-row) {
  gap: 6px;
  margin: 0 0 6px;
}

.calendar-inline :deep(.dp--overlay-col) {
  width: calc((100% - 12px) / 3);
  padding: 0;
}

.calendar-inline :deep(.dp--overlay-cell),
.calendar-inline :deep(.dp--overlay-cell-active) {
  min-height: 42px;
  border-radius: 14px;
  padding: 11px 0;
  background: #f6f9fc;
  color: #17202b;
  font-size: 13px;
  font-weight: 900;
}

.calendar-inline :deep(.dp--overlay-cell:hover) {
  background: #eef5fb;
  color: #0f5fae;
}

.calendar-inline :deep(.dp--overlay-cell-active) {
  background: #24364f;
  color: #fff;
  box-shadow: 0 8px 16px rgba(36, 54, 79, 0.16);
}

.calendar-actions {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 8px;
  margin-top: 12px;
  border-top: 1px solid rgba(36, 54, 79, 0.08);
  padding-top: 10px;
}

.calendar-actions button {
  min-height: 38px;
  border-radius: 999px;
  padding: 0 14px;
  font-size: 12px;
  font-weight: 900;
}

.quick-button {
  justify-self: start;
  background: #edf4fb;
  color: #2c638f;
}

.cancel-button {
  background: transparent;
  color: #6f7d8c;
}

.apply-button {
  background: #24364f;
  color: #fff;
  box-shadow: 0 10px 20px rgba(36, 54, 79, 0.16);
}

.apply-button:disabled {
  opacity: 0.45;
}

@keyframes calendar-fade {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes calendar-up {
  from {
    opacity: 0;
    transform: translateY(14px) scale(0.98);
  }

  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>
