<template>
  <section class="screen">
    <header class="editor-header blue-gradient">
      <AppBackButton fallback="/community" />
      <h1>{{ isEdit ? '게시글 수정' : '새 글 작성' }}</h1>
      <button class="submit-button" type="button" :disabled="isSubmitting" @click="handleSubmit">등록</button>
    </header>

    <form class="screen-scroll scrollbar-hide editor-body" @submit.prevent="handleSubmit">
      <label class="field">
        <span>제목</span>
        <input v-model="form.title" type="text" placeholder="카드 후기나 질문 제목을 입력하세요" />
      </label>

      <label class="field">
        <span>본문</span>
        <textarea v-model="form.body" rows="9" placeholder="카드 사용 경험, 혜택 팁, 질문을 자유롭게 작성하세요" />
      </label>

      <label class="field">
        <span>태그</span>
        <input v-model="tagText" type="text" placeholder="예: 카드비교, 혜택최대화, 신한카드" />
      </label>

      <div v-if="error" class="notice-card danger">{{ error }}</div>

      <div class="tip-card">
        <strong>커뮤니티 작성 기준</strong>
        <p>카드명, 사용처, 전월 실적, 체감 혜택을 함께 적으면 다른 사용자가 비교하기 쉬워요.</p>
      </div>
    </form>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppBackButton from '@/components/AppBackButton.vue'
import { createCommunityPost, fetchCommunityPost, updateCommunityPost } from '@/services/api'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => Boolean(route.params.id))
const isSubmitting = ref(false)
const tagText = ref('')
const error = ref('')
const canEditPost = ref(true)
const form = reactive({
  title: '',
  body: '',
})

const tags = computed(() =>
  tagText.value
    .split(/[,\s#]+/)
    .map((tag) => tag.trim())
    .filter(Boolean)
    .slice(0, 5),
)

async function loadPost() {
  if (!isEdit.value) return
  try {
    const post = await fetchCommunityPost(route.params.id)
    canEditPost.value = Boolean(post.editable)
    if (!canEditPost.value) {
      error.value = '수정 권한이 없는 게시글입니다.'
      return
    }
    form.title = post.title
    form.body = post.body
    tagText.value = (post.tags || []).join(', ')
  } catch {
    error.value = '수정할 게시글을 불러오지 못했습니다.'
  }
}

async function handleSubmit() {
  error.value = ''
  if (isEdit.value && !canEditPost.value) {
    error.value = '수정 권한이 없는 게시글입니다.'
    return
  }
  if (!form.title.trim()) {
    error.value = '제목을 입력해 주세요.'
    return
  }
  if (!form.body.trim()) {
    error.value = '본문을 입력해 주세요.'
    return
  }

  isSubmitting.value = true
  try {
    const payload = {
      title: form.title.trim(),
      body: form.body.trim(),
      tags: tags.value,
    }
    const saved = isEdit.value ? await updateCommunityPost(route.params.id, payload) : await createCommunityPost(payload)
    router.push(`/community/${saved.id}`)
  } catch {
    error.value = '게시글 저장에 실패했습니다.'
  } finally {
    isSubmitting.value = false
  }
}

onMounted(loadPost)
</script>

<style scoped>
.editor-header {
  display: grid;
  grid-template-columns: 38px 1fr auto;
  align-items: center;
  gap: 10px;
  padding: 18px 20px 26px;
  color: #fff;
}

.editor-header h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 900;
}

.submit-button {
  border: 0;
  border-radius: 12px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
  font-size: 12px;
  font-weight: 900;
}

.submit-button:disabled {
  opacity: 0.6;
}

.editor-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 20px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.field span {
  color: #4a5663;
  font-size: 12px;
  font-weight: 900;
}

.field input,
.field textarea {
  width: 100%;
  border: 1px solid #dbe4ee;
  border-radius: 14px;
  padding: 13px 14px;
  background: #fff;
  color: #17202b;
  font-size: 13px;
  font-weight: 800;
  line-height: 1.6;
  outline: none;
  resize: vertical;
}

.notice-card,
.tip-card {
  border-radius: 14px;
  padding: 14px;
  background: #eef4ff;
  color: #0f5fae;
  font-size: 12px;
  font-weight: 800;
}

.notice-card.danger {
  background: #fff1f3;
  color: #d92d20;
}

.tip-card {
  background: #fbfdff;
  color: #6e6e73;
}

.tip-card strong {
  display: block;
  margin-bottom: 4px;
  color: #17202b;
}

.tip-card p {
  margin: 0;
  line-height: 1.55;
}
</style>
