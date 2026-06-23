<template>
  <section class="screen">
    <header class="detail-header blue-gradient">
      <AppBackButton fallback="/community" />
      <div class="header-actions">
        <button class="ghost-button" type="button" @click="router.push(`/community/${route.params.id}/edit`)">
          <Pencil :size="15" />
          수정
        </button>
        <button class="ghost-button danger" type="button" @click="handleDelete">
          <Trash2 :size="15" />
          삭제
        </button>
      </div>
    </header>

    <div class="screen-scroll scrollbar-hide page-padding">
      <div v-if="isLoading" class="notice-card">게시글을 불러오는 중입니다.</div>
      <div v-else-if="error" class="notice-card" :class="{ danger: !isFallbackData, subtle: isFallbackData }">
        {{ error }}
      </div>

      <article v-if="post" class="app-card post-detail">
        <div class="post-head">
          <span>{{ post.avatar }}</span>
          <div>
            <strong>{{ post.author }}</strong>
            <small>{{ post.date }}</small>
          </div>
        </div>
        <h1>{{ post.title }}</h1>
        <p>{{ post.body }}</p>
        <div class="tag-row">
          <span v-for="tag in post.tags" :key="tag">#{{ tag }}</span>
        </div>
        <footer>
          <button
            type="button"
            :class="{ liked: post.liked }"
            :aria-label="`좋아요 ${post.likes}개`"
            @click="handleLike"
          >
            <Heart :size="17" :fill="post.liked ? 'currentColor' : 'none'" />
          </button>
          <span :aria-label="`댓글 ${comments.length}개`">
            <MessageCircle :size="17" />
          </span>
        </footer>
      </article>

      <article v-if="post" class="app-card comment-card">
        <h2>댓글 {{ comments.length }}개</h2>
        <form class="comment-form" @submit.prevent="handleCommentSubmit">
          <input v-model="commentBody" type="text" aria-label="댓글 입력" placeholder="댓글을 입력하세요" />
          <button class="primary-icon" type="submit" :disabled="!commentBody.trim()" aria-label="댓글 등록">
            <Send :size="16" />
          </button>
        </form>
        <ul class="comment-list">
          <li v-for="comment in comments" :key="comment.id">
            <span>{{ comment.avatar }}</span>
            <div>
              <strong>{{ comment.author }}</strong>
              <small>{{ comment.date }}</small>
              <p>{{ comment.body || comment.text }}</p>
            </div>
            <button type="button" aria-label="댓글 삭제" @click="handleCommentDelete(comment.id)">
              <Trash2 :size="14" />
            </button>
          </li>
        </ul>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Heart, MessageCircle, Pencil, Send, Trash2 } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { communityPosts } from '@/data/mockData'
import {
  createCommunityComment,
  deleteCommunityComment,
  deleteCommunityPost,
  fetchCommunityPost,
  toggleCommunityPostLike,
} from '@/services/api'

const route = useRoute()
const router = useRouter()
const post = ref(null)
const commentBody = ref('')
const isLoading = ref(false)
const error = ref('')
const isFallbackData = ref(false)
const comments = computed(() => post.value?.commentItems || [])

async function loadPost() {
  isLoading.value = true
  error.value = ''
  isFallbackData.value = false
  try {
    post.value = await fetchCommunityPost(route.params.id)
  } catch {
    const fallbackPost = communityPosts.find((item) => String(item.id) === String(route.params.id))
    if (fallbackPost) {
      post.value = {
        ...fallbackPost,
        commentItems: [
          { id: `${fallbackPost.id}-comment-1`, author: '남주현', avatar: '남', date: '방금 전', body: '예시 데이터에서도 댓글 흐름을 확인할 수 있어요.' },
        ],
      }
      isFallbackData.value = true
      error.value = '백엔드 연결 전이라 예시 게시글로 보여드려요.'
    } else {
      error.value = '게시글을 찾을 수 없습니다.'
    }
  } finally {
    isLoading.value = false
  }
}

async function handleLike() {
  if (!post.value) return
  const original = { ...post.value }
  post.value.liked = !post.value.liked
  post.value.likes += post.value.liked ? 1 : -1
  try {
    post.value = await toggleCommunityPostLike(post.value.id)
  } catch {
    if (!isFallbackData.value) post.value = original
  }
}

async function handleCommentSubmit() {
  const body = commentBody.value.trim()
  if (!body || !post.value) return
  let created
  try {
    created = await createCommunityComment(post.value.id, { body })
  } catch {
    if (!isFallbackData.value) return
    created = {
      id: `local-${Date.now()}`,
      author: '남주현',
      avatar: '남',
      date: '방금 전',
      body,
    }
  }
  post.value.commentItems = [...comments.value, created]
  post.value.comments = comments.value.length
  commentBody.value = ''
}

async function handleCommentDelete(commentId) {
  if (!post.value) return
  try {
    await deleteCommunityComment(commentId)
  } catch {
    if (!isFallbackData.value) return
  }
  post.value.commentItems = comments.value.filter((comment) => comment.id !== commentId)
  post.value.comments = comments.value.length
}

async function handleDelete() {
  if (!post.value) return
  await deleteCommunityPost(post.value.id)
  router.push('/community')
}

onMounted(loadPost)
</script>

<style scoped>
.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px 30px;
  color: #fff;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.ghost-button {
  display: inline-flex;
  min-height: 40px;
  align-items: center;
  gap: 5px;
  border: 0;
  border-radius: 12px;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
  font-size: 12px;
  font-weight: 900;
}

.ghost-button.danger {
  background: rgba(255, 255, 255, 0.12);
}

.page-padding {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 20px 28px;
}

.notice-card {
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

.notice-card.subtle {
  background: rgba(232, 241, 251, 0.72);
  color: #4a5663;
}

.post-detail,
.comment-card {
  padding: 16px;
}

.post-head {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 14px;
}

.post-head > span,
.comment-list > li > span {
  display: flex;
  width: 34px;
  height: 34px;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  border-radius: 999px;
  background: #e8f1ff;
  color: #0f5fae;
  font-weight: 900;
}

.post-head strong,
.comment-list strong {
  display: block;
  color: #17202b;
  font-size: 13px;
  font-weight: 900;
}

.post-head small,
.comment-list small {
  color: #6e6e73;
  font-size: 11px;
  font-weight: 700;
}

h1 {
  margin: 0 0 12px;
  color: #17202b;
  font-size: 20px;
  font-weight: 900;
  line-height: 1.35;
}

.post-detail p {
  margin: 0 0 14px;
  color: #4a5663;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.7;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 14px;
}

.tag-row span {
  border-radius: 999px;
  padding: 5px 8px;
  background: #e7edf4;
  color: #4a5663;
  font-size: 10px;
  font-weight: 900;
}

footer {
  display: flex;
  gap: 8px;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 800;
}

footer button,
footer span {
  display: inline-flex;
  width: 40px;
  height: 40px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  border: 0;
  padding: 0;
  background: #fbfdff;
  color: inherit;
  font: inherit;
}

footer button {
  cursor: pointer;
}

footer button.liked {
  color: #d92d20;
  background: #fff1f3;
}

h2 {
  margin: 0 0 12px;
  color: #17202b;
  font-size: 15px;
  font-weight: 900;
}

.comment-form {
  display: grid;
  grid-template-columns: 1fr 44px;
  gap: 8px;
  margin-bottom: 14px;
}

.comment-form input {
  min-width: 0;
  min-height: 44px;
  border: 1px solid #dbe4ee;
  border-radius: 12px;
  padding: 11px 12px;
  color: #17202b;
  font-size: 13px;
  font-weight: 800;
  outline: none;
}

.primary-icon {
  display: flex;
  width: 44px;
  height: 44px;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 12px;
  background: #0f5fae;
  color: #fff;
}

.primary-icon:disabled {
  background: #dbe4ee;
  color: #8a9aad;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 0;
  margin: 0;
  list-style: none;
}

.comment-list li {
  display: grid;
  grid-template-columns: 34px 1fr 40px;
  gap: 9px;
}

.comment-list p {
  margin: 4px 0 0;
  color: #4a5663;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.55;
}

.comment-list button {
  align-self: start;
  width: 40px;
  height: 40px;
  border: 0;
  padding: 0;
  background: transparent;
  color: #8a9aad;
}
</style>
