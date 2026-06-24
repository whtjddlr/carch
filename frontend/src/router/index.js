import { createRouter, createWebHistory } from 'vue-router'
import LandingView from '@/views/LandingView.vue'
import AuthView from '@/views/AuthView.vue'
import AuthCallbackView from '@/views/AuthCallbackView.vue'
import DashboardView from '@/views/DashboardView.vue'
import TransactionsView from '@/views/TransactionsView.vue'
import TransactionCreateView from '@/views/TransactionCreateView.vue'
import BudgetListView from '@/views/BudgetListView.vue'
import BudgetView from '@/views/BudgetView.vue'
import RecommendationView from '@/views/RecommendationView.vue'
import CommunityView from '@/views/CommunityView.vue'
import CommunityPostView from '@/views/CommunityPostView.vue'
import CommunityEditorView from '@/views/CommunityEditorView.vue'
import ChatView from '@/views/ChatView.vue'
import AnalyticsView from '@/views/AnalyticsView.vue'
import UtilityView from '@/views/UtilityView.vue'
import PlansListView from '@/views/PlansListView.vue'
import PlansCreateView from '@/views/PlansCreateView.vue'
import PlanDetailView from '@/views/PlanDetailView.vue'
import DevPanelView from '@/views/DevPanelView.vue'
import { ensureDevAutoLogin, isAuthenticated } from '@/services/auth'

const protectedMeta = { requiresAuth: true, bottomNav: true }

const routes = [
  { path: '/', name: 'Landing', component: LandingView, meta: { fullPage: true } },
  { path: '/login', name: 'Login', component: AuthView, props: { mode: 'login' }, meta: { requiresAuth: false } },
  { path: '/signup', name: 'Signup', component: AuthView, props: { mode: 'signup' }, meta: { requiresAuth: false } },
  { path: '/login/callback', name: 'AuthCallback', component: AuthCallbackView, meta: { requiresAuth: false } },
  { path: '/cards', name: 'Dashboard', component: DashboardView, meta: protectedMeta },
  { path: '/cards/:id', name: 'CardDetail', component: UtilityView, props: { type: 'card' }, meta: { requiresAuth: true } },
  { path: '/cards/apply/:id', name: 'CardApply', component: UtilityView, props: { type: 'cardApply' }, meta: { requiresAuth: true } },
  { path: '/transactions', name: 'Transactions', component: TransactionsView, meta: protectedMeta },
  { path: '/transactions/new', name: 'TransactionCreate', component: TransactionCreateView, meta: { requiresAuth: true } },
  { path: '/transactions/:id', name: 'TransactionDetail', component: UtilityView, props: { type: 'transaction' }, meta: { requiresAuth: true } },
  { path: '/budget', name: 'BudgetList', component: BudgetListView, meta: protectedMeta },
  { path: '/budget/new', name: 'BudgetNew', component: UtilityView, props: { type: 'budgetNew' }, meta: { requiresAuth: true } },
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
  { path: '/reports/monthly', name: 'MonthlyReport', component: UtilityView, props: { type: 'report' }, meta: { requiresAuth: true } },
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
  if (to.meta.devOnly && !import.meta.env.DEV) return { name: 'Dashboard' }
  if (to.meta.requiresAuth && !isAuthenticated()) {
    const didAutoLogin = await ensureDevAutoLogin()
    if (didAutoLogin) return true
    return { name: 'Login', query: { next: to.fullPath } }
  }
  return true
})

export default router
