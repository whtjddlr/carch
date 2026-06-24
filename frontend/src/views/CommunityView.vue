<template>
  <section class="screen">
    <header class="simple-header blue-gradient">
      <AppBackButton fallback="/cards" />
      <div>
        <h1>커뮤니티</h1>
      </div>
    </header>

    <div class="screen-scroll scrollbar-hide page-padding">
      <label class="search-box">
        <Search :size="16" />
        <input
          v-model="search"
          type="search"
          aria-label="커뮤니티 검색"
          placeholder="카드명, 혜택, 작성자 검색"
          @keyup.enter="loadPosts"
        />
      </label>

      <section class="community-guide app-card">
        <div>
          <span>오늘의 카드 이야기</span>
          <strong>혜택 비교와 실사용 후기를 모아봤어요</strong>
        </div>
        <div class="guide-topics" aria-label="추천 주제">
          <button type="button" @click="search = '카드비교'; loadPosts()">카드비교</button>
          <button type="button" @click="search = '혜택최대화'; loadPosts()">혜택최대화</button>
          <button type="button" @click="search = '마트'; loadPosts()">마트</button>
        </div>
      </section>

      <div v-if="isLoading" class="notice-card">게시글을 불러오는 중입니다.</div>
      <div v-else-if="error" class="notice-card" :class="{ subtle: isFallbackData }">{{ error }}</div>

      <article
        v-for="post in posts"
        :key="post.id"
        class="app-card post-card"
        @click="router.push(`/community/${post.id}`)"
      >
        <div class="post-head">
          <span>{{ post.avatar }}</span>
          <div>
            <strong>{{ post.author }}</strong>
            <small>{{ post.date }}</small>
          </div>
        </div>
        <h2>{{ post.title }}</h2>
        <p>{{ post.body }}</p>
        <div class="tag-row">
          <span v-for="tag in post.tags" :key="tag">#{{ tag }}</span>
        </div>
        <footer>
          <button
            type="button"
            :class="{ liked: post.liked }"
            :aria-label="`좋아요 ${post.likes}개`"
            @click.stop="handleLike(post)"
          >
            <Heart :size="16" :fill="post.liked ? 'currentColor' : 'none'" />
          </button>
          <span :aria-label="`댓글 ${post.comments}개`">
            <MessageCircle :size="16" />
          </span>
        </footer>
      </article>

      <div v-if="!isLoading && !posts.length" class="empty-card">
        <Users :size="32" />
        <strong>아직 게시글이 없습니다</strong>
        <p>첫 카드 후기를 공유해 보세요.</p>
        <RouterLink to="/community/new">글쓰기</RouterLink>
      </div>
    </div>

    <RouterLink class="floating-action-button" to="/community/new" aria-label="글쓰기">
      <Plus :size="20" />
    </RouterLink>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Heart, MessageCircle, Plus, Search, Users } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { communityPosts } from '@/data/mockData'
import { fetchCommunityPosts, toggleCommunityPostLike } from '@/services/api'

const router = useRouter()
const posts = ref([])
const search = ref('')
const isLoading = ref(false)
const error = ref('')
const isFallbackData = ref(false)

async function loadPosts() {
  isLoading.value = true
  error.value = ''
  isFallbackData.value = false
  try {
    posts.value = await fetchCommunityPosts(search.value ? { search: search.value } : {})
  } catch {
    const term = search.value.trim().toLowerCase()
    posts.value = communityPosts.filter((post) => (
      !term || `${post.title} ${post.body} ${post.author} ${post.tags.join(' ')}`.toLowerCase().includes(term)
    ))
    isFallbackData.value = true
    error.value = '저장된 게시글을 표시합니다.'
  } finally {
    isLoading.value = false
  }
}

async function handleLike(post) {
  const original = { ...post }
  post.liked = !post.liked
  post.likes += post.liked ? 1 : -1
  try {
    const updated = await toggleCommunityPostLike(post.id)
    Object.assign(post, updated)
  } catch {
    if (!isFallbackData.value) Object.assign(post, original)
  }
}

onMounted(loadPosts)
</script>

<style scoped>
.simple-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 24px 20px;
  color: #fff;
}

.simple-header h1 {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 900;
}

.simple-header p {
  margin: 0;
  color: rgba(255, 255, 255, 0.72);
  font-size: 12px;
  font-weight: 700;
}

.page-padding {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px 20px 116px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #dbe4ee;
  border-radius: 14px;
  padding: 0 12px;
  background: #fff;
  color: #6e6e73;
}

.search-box input {
  width: 100%;
  min-width: 0;
  min-height: 44px;
  border: 0;
  padding: 12px 0;
  background: transparent;
  color: #17202b;
  font-size: 13px;
  font-weight: 800;
  outline: none;
}

.notice-card,
.empty-card {
  border-radius: 14px;
  padding: 14px;
  background: #e8f1ff;
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

.post-card {
  padding: 15px;
  cursor: pointer;
}

.community-guide {
  display: grid;
  gap: 12px;
  padding: 15px;
  background:
    radial-gradient(circle at 100% 0%, rgba(0, 140, 149, 0.12), transparent 44%),
    #fff !important;
  border: 1px solid rgba(36, 54, 79, 0.08) !important;
  border-radius: 18px !important;
  box-shadow: 0 12px 24px rgba(36, 54, 79, 0.055) !important;
}

.community-guide span {
  color: #0f5fae;
  font-size: 11px;
  font-weight: 900;
}

.community-guide strong {
  display: block;
  margin-top: 4px;
  color: #17202b;
  font-size: 15px;
  font-weight: 950;
  line-height: 1.35;
}

.guide-topics {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.guide-topics button {
  min-height: 34px;
  border-radius: 999px;
  padding: 0 11px;
  background: rgba(15, 95, 174, 0.08);
  color: #0f5fae;
  font-size: 11px;
  font-weight: 900;
}

.post-head {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 12px;
}

.post-head > span {
  display: flex;
  width: 34px;
  height: 34px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: rgba(232, 241, 255, 0.64);
  color: #0f5fae;
  font-weight: 900;
}

.post-head strong,
h2 {
  display: block;
  margin: 0;
  color: #17202b;
  font-size: 14px;
  font-weight: 900;
}

.post-head small,
.post-card p,
footer {
  color: #6e6e73;
  font-size: 12px;
  font-weight: 700;
}

h2 {
  margin-bottom: 7px;
  font-size: 15px;
  line-height: 1.35;
}

.post-card p {
  display: -webkit-box;
  overflow: hidden;
  margin: 0 0 12px;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.tag-row span {
  border-radius: 999px;
  padding: 4px 8px;
  background: #e7edf4;
  color: #4a5663;
  font-size: 10px;
  font-weight: 900;
}

footer {
  display: flex;
  gap: 8px;
}

footer button,
footer span {
  display: inline-flex;
  width: 40px;
  height: 40px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  border: 1px solid rgba(23, 32, 43, 0.07);
  padding: 0;
  background: rgba(251, 253, 255, 0.38);
  color: inherit;
  font: inherit;
}

footer button {
  cursor: pointer;
}

footer button.liked {
  color: #d92d20;
  border-color: rgba(217, 45, 32, 0.13);
  background: rgba(255, 241, 243, 0.72);
}

.empty-card {
  display: flex;
  min-height: 180px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  background: #fff;
  color: #6e6e73;
  text-align: center;
}

.empty-card strong {
  color: #17202b;
  font-size: 15px;
  font-weight: 900;
}

.empty-card p {
  margin: 0;
}

.empty-card a {
  display: inline-flex;
  min-height: 36px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  margin-top: 8px;
  padding: 0 14px;
  background: #24364f;
  color: #fff;
  font-size: 12px;
  font-weight: 900;
  text-decoration: none;
}

.floating-action-button {
  bottom: 86px;
}
</style>
