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

      <div class="category-tabs" role="tablist" aria-label="게시판 분류">
        <button
          v-for="cat in categories"
          :key="cat.name"
          type="button"
          class="category-tab"
          :class="{ active: activeCategory === cat.name }"
          @click="selectCategory(cat.name)"
        >
          <component :is="cat.icon" :size="14" :stroke-width="2.4" />
          <span>{{ cat.name }}</span>
        </button>
      </div>

      <section v-if="showHot" class="hot-section">
        <div class="hot-head">
          <span class="hot-flame">🔥 실시간 인기글</span>
          <small>TOP 3</small>
        </div>
        <button
          v-for="(post, i) in topPosts"
          :key="post.id"
          type="button"
          class="hot-row"
          @click="router.push(`/community/${post.id}`)"
        >
          <span class="hot-rank">{{ i + 1 }}</span>
          <span class="hot-row-title">{{ post.title }}</span>
          <span class="hot-likes"><Heart :size="12" fill="currentColor" />{{ post.likes }}</span>
        </button>
      </section>

      <div v-if="isLoading" class="notice-card">게시글을 불러오는 중입니다.</div>
      <div v-else-if="error" class="notice-card" :class="{ subtle: isFallbackData }">{{ error }}</div>

      <article
        v-for="post in displayPosts"
        :key="post.id"
        class="app-card post-card"
        @click="router.push(`/community/${post.id}`)"
      >
        <div class="post-head">
          <div class="post-author">
            <strong>
              <em class="grade-icon" :title="`${gradeOf(post.author).label} 등급`" :aria-label="`${gradeOf(post.author).label} 등급`">{{ gradeOf(post.author).emoji }}</em>
              <span class="author-name" :style="{ color: gradeOf(post.author).color }">{{ post.author }}</span>
            </strong>
            <small>{{ post.date }}</small>
          </div>
        </div>
        <h2>{{ post.title }}</h2>
        <p>{{ post.body }}</p>
        <div v-if="post.tags && post.tags.length" class="tag-row">
          <span v-for="tag in post.tags" :key="tag">#{{ tag }}</span>
        </div>
        <footer>
          <button
            type="button"
            class="like-btn"
            :class="{ liked: post.liked }"
            :aria-label="`좋아요 ${post.likes}개`"
            @click.stop="handleLike(post)"
          >
            <Heart :size="15" :fill="post.liked ? 'currentColor' : 'none'" />
            <b>{{ post.likes }}</b>
          </button>
          <span :aria-label="`댓글 ${post.comments}개`">
            <MessageCircle :size="15" />
            <b>{{ post.comments }}</b>
          </span>
          <button
            type="button"
            class="save-btn"
            :class="{ saved: isSaved(post) }"
            :aria-label="isSaved(post) ? '저장 취소' : '저장'"
            :aria-pressed="isSaved(post)"
            @click.stop="toggleSave(post)"
          >
            <Star :size="16" :fill="isSaved(post) ? 'currentColor' : 'none'" />
          </button>
        </footer>
      </article>

      <div v-if="!isLoading && !displayPosts.length" class="empty-card">
        <Users v-if="activeCategory !== '저장됨'" :size="32" />
        <Star v-else :size="32" />
        <strong v-if="activeCategory === '나의 글'">아직 작성한 글이 없어요</strong>
        <strong v-else-if="activeCategory === '저장됨'">저장한 글이 없어요</strong>
        <strong v-else>아직 게시글이 없습니다</strong>
        <p v-if="activeCategory === '저장됨'">글 우측 하단 별표를 누르면 여기 모여요.</p>
        <p v-else>첫 카드 후기를 공유해 보세요.</p>
        <RouterLink v-if="activeCategory !== '저장됨'" to="/community/new">글쓰기</RouterLink>
      </div>
    </div>

    <RouterLink class="floating-action-button" to="/community/new" aria-label="글쓰기">
      <Plus :size="20" />
    </RouterLink>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Heart, Info, MessageCircle, PenLine, Plus, Search, Star, Ticket, Users } from 'lucide-vue-next'
import AppBackButton from '@/components/AppBackButton.vue'
import { communityPosts } from '@/data/mockData'
import { fetchCommunityPosts, toggleCommunityPostLike } from '@/services/api'

const router = useRouter()
const posts = ref([])
const search = ref('')
const isLoading = ref(false)
const error = ref('')
const isFallbackData = ref(false)

// 대분류 탭 — '전체'는 없음(아무것도 선택 안 하면 전체). 같은 탭 다시 누르면 해제.
const categories = [
  { name: '이벤트', icon: Ticket },
  { name: '정보공유', icon: Info },
  { name: '나의 글', icon: PenLine },
  { name: '저장됨', icon: Star },
]
const activeCategory = ref('')
function selectCategory(name) {
  activeCategory.value = activeCategory.value === name ? '' : name
}

// 글의 태그로 콘텐츠 분류 (이벤트 / 그 외=정보공유)
function categoryOf(post) {
  const tags = post.tags || []
  if (tags.some((t) => ['발급이벤트', '발급중단', '쿠폰', '즉시할인', '공지', '프로모션', '이벤트'].includes(t))) return '이벤트'
  return '정보공유'
}

// 저장(북마크) — 로컬 저장
const SAVED_KEY = 'carch.community.saved.v1'
function readSaved() {
  try {
    const v = JSON.parse(window.localStorage.getItem(SAVED_KEY) || '[]')
    return Array.isArray(v) ? v.map(String) : []
  } catch {
    return []
  }
}
const savedIds = ref(readSaved())
function isSaved(post) {
  return savedIds.value.includes(String(post.id))
}
function toggleSave(post) {
  const id = String(post.id)
  const next = new Set(savedIds.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  savedIds.value = [...next]
  try {
    window.localStorage.setItem(SAVED_KEY, JSON.stringify(savedIds.value))
  } catch {
    // 저장 실패 시 이번 세션 메모리만 유지
  }
}

const displayPosts = computed(() => {
  const list = posts.value
  if (activeCategory.value === '나의 글') return list.filter((post) => post.editable)
  if (activeCategory.value === '저장됨') return list.filter((post) => isSaved(post))
  if (activeCategory.value === '이벤트' || activeCategory.value === '정보공유') {
    return list.filter((post) => categoryOf(post) === activeCategory.value)
  }
  return list
})

// 실시간 인기글 TOP3 (좋아요순) — 전체(미선택) + 검색 안 할 때만
const topPosts = computed(() => [...posts.value].sort((a, b) => (b.likes || 0) - (a.likes || 0)).slice(0, 3))
const showHot = computed(() => !activeCategory.value && !search.value && !isLoading.value && topPosts.value.length >= 3)

// 까치 성장 등급제 — 작성자 누적 좋아요로 등급 산정 (알 → 까치)
const GRADES = [
  { min: 250, label: '까치', emoji: '🐦‍⬛', color: '#24364f' },
  { min: 140, label: '어린 까치', emoji: '🐦', color: '#0f5fae' },
  { min: 70, label: '아기새', emoji: '🐤', color: '#c2410c' },
  { min: 30, label: '병아리', emoji: '🐣', color: '#b8860b' },
  { min: 0, label: '알', emoji: '🥚', color: '#7b8794' },
]
const authorLikes = computed(() => {
  const map = {}
  posts.value.forEach((post) => {
    map[post.author] = (map[post.author] || 0) + (post.likes || 0)
  })
  return map
})
function gradeOf(author) {
  const total = authorLikes.value[author] || 0
  return GRADES.find((g) => total >= g.min) || GRADES[GRADES.length - 1]
}

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
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  padding: 22px 20px;
  color: #fff;
}

.simple-header h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 900;
  line-height: 1.2;
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

.category-tabs {
  display: flex;
  flex: 0 0 auto;
  gap: 7px;
  overflow-x: auto;
  padding-bottom: 2px;
  scrollbar-width: none;
}

.category-tabs::-webkit-scrollbar {
  display: none;
}

.category-tab {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 5px;
  min-height: 34px;
  border-radius: 999px;
  padding: 0 13px;
  background: #eef2f7;
  color: #6e7885;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  transition: background 140ms ease, color 140ms ease;
}

.category-tab svg {
  opacity: 0.85;
}

.category-tab.active {
  background: #24364f;
  color: #fff;
}

.hot-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
  border: 1px solid rgba(217, 45, 32, 0.16);
  border-radius: 16px;
  padding: 13px 14px;
  background:
    radial-gradient(circle at 100% 0%, rgba(255, 99, 71, 0.12), transparent 52%),
    #fff;
  box-shadow: 0 10px 24px rgba(217, 45, 32, 0.07);
}

.hot-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 4px;
}

.hot-flame {
  color: #d92d20;
  font-size: 13px;
  font-weight: 950;
}

.hot-head small {
  color: #f0857a;
  font-size: 11px;
  font-weight: 900;
}

.hot-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 7px 2px;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.hot-row + .hot-row {
  border-top: 1px solid rgba(217, 45, 32, 0.08);
}

.hot-rank {
  flex: 0 0 auto;
  display: inline-flex;
  width: 20px;
  height: 20px;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  background: #d92d20;
  color: #fff;
  font-size: 11px;
  font-weight: 950;
  line-height: 1;
  padding-bottom: 1px;
}

.hot-row-title {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  color: #17202b;
  font-size: 13px;
  font-weight: 800;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.hot-likes {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  color: #d92d20;
  font-size: 12px;
  font-weight: 900;
}

.post-head {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.post-head .post-author strong {
  display: flex;
  align-items: center;
  gap: 6px;
}

.grade-icon {
  flex: 0 0 auto;
  font-size: 18px;
  font-style: normal;
  line-height: 1;
}

.author-name {
  font-size: 14px;
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
  min-height: 34px;
  align-items: center;
  justify-content: center;
  gap: 5px;
  border-radius: 999px;
  border: 1px solid rgba(23, 32, 43, 0.07);
  padding: 0 12px;
  background: rgba(251, 253, 255, 0.38);
  color: #6e6e73;
  font: inherit;
  /* 좋아요/저장은 누르면 즉시 색이 바뀌도록 색 전환 애니메이션 제거 */
  transition: none;
}

footer button svg,
footer span svg {
  transition: none;
}

footer b {
  font-size: 12px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

footer button {
  cursor: pointer;
}

/* 좋아요 = 항상 빨강(빈 하트도 빨강), 누르면 채워짐. 전역 button !important 를 이겨야 해서 svg까지 직접 지정 */
footer button.like-btn,
footer button.like-btn svg {
  color: #d92d20 !important;
  stroke: #d92d20 !important;
}

footer button.like-btn.liked {
  border-color: rgba(217, 45, 32, 0.18);
  background: rgba(255, 241, 243, 0.72);
}

/* 저장 = 항상 노랑(빈 별도 노랑), 누르면 채워짐 */
footer button.save-btn {
  margin-left: auto;
  padding: 0 11px;
}

footer button.save-btn,
footer button.save-btn svg {
  color: #e0a700 !important;
  stroke: #e0a700 !important;
}

footer .save-btn.saved {
  border-color: rgba(234, 179, 8, 0.34);
  background: rgba(254, 243, 199, 0.7);
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
