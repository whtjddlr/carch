import { createRouter, createWebHistory } from 'vue-router'
import { ensureDevAutoLogin, initAuthSession, isAuthenticated } from '@/services/auth'
import { IS_DEMO_CHANNEL } from '@/services/api'
import { isNativeRuntime } from '@/services/secureStorage'

const protectedMeta = { requiresAuth: true, bottomNav: true }
const LandingView = () => import('@/views/LandingView.vue')
const AuthView = () => import('@/views/AuthView.vue')
const AuthCallbackView = () => import('@/views/AuthCallbackView.vue')
const DashboardView = () => import('@/views/DashboardView.vue')
const TransactionsView = () => import('@/views/TransactionsView.vue')
const TransactionCreateView = () => import('@/views/TransactionCreateView.vue')
const BudgetListView = () => import('@/views/BudgetListView.vue')
const BudgetView = () => import('@/views/BudgetView.vue')
const RecommendationView = () => import('@/views/RecommendationView.vue')
const CommunityView = () => import('@/views/CommunityView.vue')
const CommunityPostView = () => import('@/views/CommunityPostView.vue')
const CommunityEditorView = () => import('@/views/CommunityEditorView.vue')
const ChatView = () => import('@/views/ChatView.vue')
const AnalyticsView = () => import('@/views/AnalyticsView.vue')
const UtilityView = () => import('@/views/UtilityView.vue')
const PrivacyView = () => import('@/views/PrivacyView.vue')
const PlansListView = () => import('@/views/PlansListView.vue')
const PlansCreateView = () => import('@/views/PlansCreateView.vue')
const PlanDetailView = () => import('@/views/PlanDetailView.vue')
const DemoView = () => import('@/views/DemoView.vue')
const DevPanelView = () => import('@/views/DevPanelView.vue')

const routes = [
  { path: '/', name: 'Landing', component: LandingView, meta: { fullPage: true } },
  { path: '/demo', name: 'QuickStart', component: DemoView, meta: { requiresAuth: false, demoOnly: true } },
  { path: '/login', name: 'Login', component: AuthView, props: { mode: 'login' }, meta: { requiresAuth: false } },
  { path: '/signup', name: 'Signup', component: AuthView, props: { mode: 'signup' }, meta: { requiresAuth: false } },
  { path: '/login/callback', name: 'AuthCallback', component: AuthCallbackView, meta: { requiresAuth: false } },
  { path: '/privacy', name: 'Privacy', component: PrivacyView, meta: { requiresAuth: false } },
  { path: '/cards', name: 'Dashboard', component: DashboardView, meta: protectedMeta },
  { path: '/cards/:id', name: 'CardDetail', component: UtilityView, props: { type: 'card' }, meta: { requiresAuth: true } },
  { path: '/cards/apply/:id', name: 'CardApply', component: UtilityView, props: { type: 'cardApply' }, meta: { requiresAuth: true } },
  { path: '/transactions', name: 'Transactions', component: TransactionsView, meta: protectedMeta },
  { path: '/transactions/new', name: 'TransactionCreate', component: TransactionCreateView, meta: { requiresAuth: true } },
  { path: '/transactions/:id', name: 'TransactionDetail', component: UtilityView, props: { type: 'transaction' }, meta: { requiresAuth: true } },
  { path: '/budget', name: 'BudgetList', component: BudgetListView, meta: protectedMeta },
  { path: '/budget/new', redirect: '/budget' },
  { path: '/budget/current', name: 'Budget', component: BudgetView, meta: protectedMeta },
  { path: '/recommendations/new', name: 'RecommendationNew', component: RecommendationView, meta: { requiresAuth: true } },
  { path: '/recommendations/usage', name: 'RecommendationUsage', component: RecommendationView, meta: { requiresAuth: true } },
  { path: '/recommendations/:id', name: 'RecommendationDetail', component: RecommendationView, meta: { requiresAuth: true } },
  { path: '/community', name: 'Community', component: CommunityView, meta: protectedMeta },
  { path: '/community/new', name: 'CommunityNew', component: CommunityEditorView, meta: { requiresAuth: true } },
  { path: '/community/:id/edit', name: 'CommunityEdit', component: CommunityEditorView, meta: { requiresAuth: true } },
  { path: '/community/:id', name: 'CommunityPost', component: CommunityPostView, meta: { requiresAuth: true } },
  { path: '/chat', name: 'Chat', component: ChatView, meta: protectedMeta },
  { path: '/analytics', name: 'Analytics', component: AnalyticsView, meta: protectedMeta },
  { path: '/analytics/cards', name: 'CardAnalytics', component: AnalyticsView, meta: protectedMeta },
  { path: '/reports/monthly', redirect: '/analytics' },
  { path: '/notifications', name: 'Notifications', component: UtilityView, props: { type: 'notifications' }, meta: { requiresAuth: true } },
  { path: '/settings', name: 'Settings', component: UtilityView, props: { type: 'settings' }, meta: { requiresAuth: true } },
  { path: '/settings/notifications', name: 'NotificationSettings', component: UtilityView, props: { type: 'notificationSettings' }, meta: { requiresAuth: true } },
  { path: '/settings/profile', name: 'ProfileEdit', component: UtilityView, props: { type: 'profile' }, meta: { requiresAuth: true } },
  { path: '/settings/security', name: 'SecuritySettings', component: UtilityView, props: { type: 'security' }, meta: { requiresAuth: true } },
  { path: '/search', name: 'Search', component: UtilityView, props: { type: 'search' }, meta: { requiresAuth: true } },
  { path: '/plans', name: 'PurchasePlanList', component: PlansListView, meta: protectedMeta },
  { path: '/plans/new', name: 'PurchasePlanCreate', component: PlansCreateView, meta: { requiresAuth: true } },
  { path: '/plans/:id', name: 'PurchasePlanDetail', component: PlanDetailView, meta: { requiresAuth: true } },
  { path: '/dev', name: 'DevPanel', component: DevPanelView, meta: { requiresAuth: false, devOnly: true } },
  { path: '/:pathMatch(.*)*', redirect: '/cards' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  await initAuthSession()
  if (to.meta.demoOnly && !IS_DEMO_CHANNEL) return { name: 'Login', query: { next: '/cards' } }
  const allowDev = IS_DEMO_CHANNEL && !isNativeRuntime() && (import.meta.env.DEV || ['localhost', '127.0.0.1'].includes(window.location.hostname))
  if (to.meta.devOnly && !allowDev) return { name: 'Dashboard' }
  if (to.meta.requiresAuth && !isAuthenticated()) {
    const didAutoLogin = await ensureDevAutoLogin()
    if (didAutoLogin) return true
    return { name: 'Login', query: { next: to.fullPath } }
  }
  return true
})

export default router
