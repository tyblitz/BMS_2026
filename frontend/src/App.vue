<template>
  <div class="min-h-screen flex flex-col bg-slate-50">
    <!-- Top Navigation Bar (Shown when authenticated) -->
    <header v-if="authStore.isAuthenticated" class="bg-deped-blue text-white shadow-md sticky top-0 z-30">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center h-16">
        <!-- Brand / Logo -->
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-lg bg-deped-gold flex items-center justify-center font-bold text-deped-dark shadow-sm">
            BMS
          </div>
          <div>
            <span class="font-bold text-lg tracking-tight block">Budget Monitoring System</span>
            <span class="text-xs text-blue-200 block">DepEd Financial Consolidation Portal</span>
          </div>
        </div>

        <!-- Navigation Links -->
        <nav class="hidden md:flex items-center space-x-1">
          <router-link
            to="/records"
            class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="$route.path === '/records' ? 'bg-deped-dark text-white' : 'text-blue-100 hover:bg-blue-800'"
          >
            Budget Records
          </router-link>
          <router-link
            to="/upload"
            class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="$route.path === '/upload' ? 'bg-deped-dark text-white' : 'text-blue-100 hover:bg-blue-800'"
          >
            Upload & Consolidate
          </router-link>
          <router-link
            v-if="authStore.isAdmin"
            to="/settings"
            class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="$route.path === '/settings' ? 'bg-deped-dark text-white' : 'text-blue-100 hover:bg-blue-800'"
          >
            Database Settings
          </router-link>
        </nav>

        <!-- User Scope & Profile Badge -->
        <div class="flex items-center space-x-4">
          <div class="hidden sm:flex flex-col text-right">
            <span class="text-sm font-semibold leading-tight">{{ authStore.user?.username }}</span>
            <span class="text-xs text-blue-200 max-w-[200px] truncate" :title="authStore.userScopeDescription">
              {{ authStore.userScopeDescription }}
            </span>
          </div>
          <button
            @click="handleLogout"
            class="text-xs bg-red-600/90 hover:bg-red-700 text-white font-medium px-3 py-1.5 rounded-lg transition-colors shadow-sm"
          >
            Sign Out
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content View -->
    <main class="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
      <router-view />
    </main>

    <!-- Footer -->
    <footer v-if="authStore.isAuthenticated" class="bg-white border-t border-slate-200 py-3 text-center text-xs text-slate-500">
      Department of Education &bull; Budget Monitoring System (BMS 2026) &bull; Standalone & Conso Web Platform
    </footer>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>
