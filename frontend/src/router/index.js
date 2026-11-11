import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoginView from '@/views/LoginView.vue'
import RecordsView from '@/views/RecordsView.vue'
import UploadView from '@/views/UploadView.vue'
import SettingsView from '@/views/SettingsView.vue'
import UsersView from '@/views/UsersView.vue'
import SchoolDashboardView from '@/views/SchoolDashboardView.vue'
import SDODashboardView from '@/views/SDODashboardView.vue'
import RegionDashboardView from '@/views/RegionDashboardView.vue'
import AdminDashboardView from '@/views/AdminDashboardView.vue'

export function getHomeRouteForRole(role) {
  switch (role) {
    case 'school':
      return '/school/dashboard'
    case 'sdo':
      return '/sdo/dashboard'
    case 'region':
      return '/region/dashboard'
    case 'admin':
      return '/admin/dashboard'
    default:
      return '/records'
  }
}

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { public: true },
  },
  {
    path: '/',
    redirect: () => {
      const authStore = useAuthStore()
      if (authStore.isAuthenticated) {
        return getHomeRouteForRole(authStore.userRole)
      }
      return '/login'
    },
  },
  {
    path: '/school/dashboard',
    name: 'SchoolDashboard',
    component: SchoolDashboardView,
    meta: { roles: ['school', 'admin'] },
  },
  {
    path: '/sdo/dashboard',
    name: 'SDODashboard',
    component: SDODashboardView,
    meta: { roles: ['sdo', 'admin'] },
  },
  {
    path: '/region/dashboard',
    name: 'RegionDashboard',
    component: RegionDashboardView,
    meta: { roles: ['region', 'admin'] },
  },
  {
    path: '/admin/dashboard',
    name: 'AdminDashboard',
    component: AdminDashboardView,
    meta: { roles: ['admin'] },
  },
  {
    path: '/records',
    name: 'Records',
    component: RecordsView,
    meta: { roles: ['school', 'sdo', 'region', 'admin'] },
  },
  {
    path: '/upload',
    name: 'Upload',
    component: UploadView,
    meta: { roles: ['school', 'sdo', 'region', 'admin'] },
  },
  {
    path: '/users',
    name: 'Users',
    component: UsersView,
    meta: { roles: ['admin'] },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: SettingsView,
    meta: { roles: ['admin'] },
  },
  // Catch-all route to fallback to home
  {
    path: '/:pathMatch(.*)*',
    redirect: () => {
      const authStore = useAuthStore()
      if (authStore.isAuthenticated) {
        return getHomeRouteForRole(authStore.userRole)
      }
      return '/login'
    },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (!to.meta.public && !authStore.isAuthenticated) {
    return next({ name: 'Login' })
  }

  if (to.name === 'Login' && authStore.isAuthenticated) {
    const homeRoute = getHomeRouteForRole(authStore.userRole)
    return next(homeRoute)
  }

  if (to.meta.roles && Array.isArray(to.meta.roles)) {
    if (!to.meta.roles.includes(authStore.userRole)) {
      // Access denied -> redirect to their designated home route
      const homeRoute = getHomeRouteForRole(authStore.userRole)
      return next(homeRoute)
    }
  }

  next()
})

export default router
