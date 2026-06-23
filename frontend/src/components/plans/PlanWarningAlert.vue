<template>
  <div class="plan-alert" :class="tone">
    <component :is="tone === 'danger' ? AlertTriangle : Info" :size="16" />
    <div>
      <strong v-if="title">{{ title }}</strong>
      <p>{{ message }}</p>
    </div>
  </div>
</template>

<script setup>
import { AlertTriangle, Info } from 'lucide-vue-next'

defineProps({
  title: { type: String, default: '' },
  message: { type: String, required: true },
  tone: { type: String, default: 'info' },
})
</script>

<style scoped>
.plan-alert {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  border-radius: 16px;
  padding: 14px;
}

.plan-alert strong {
  display: block;
  margin-bottom: 2px;
  font-size: 12px;
  font-weight: 900;
}

.plan-alert p {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.45;
}

.info {
  background: #e8f1ff;
  color: #0f5fae;
}

.warning {
  background: #fffaeb;
  color: #b54708;
}

.danger {
  background: #fef3f2;
  color: #b42318;
}
</style>
