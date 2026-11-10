<template>
  <div class="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-slate-900 via-deped-dark to-deped-blue">
    <div class="max-w-md w-full bms-card p-8 bg-white/95 backdrop-blur shadow-2xl border-slate-100">
      <!-- Header -->
      <div class="text-center mb-8">
        <div class="w-16 h-16 bg-deped-blue text-deped-gold rounded-2xl flex items-center justify-center text-2xl font-bold mx-auto mb-4 shadow-lg ring-4 ring-blue-100">
          BMS
        </div>
        <h2 class="text-2xl font-extrabold text-slate-900 tracking-tight">DepEd Budget Monitoring</h2>
        <p class="text-sm text-slate-500 mt-1">Hierarchical Consolidation & Management Portal</p>
      </div>

      <!-- Error Alert -->
      <div v-if="authStore.error" class="mb-5 p-3.5 bg-red-50 border-l-4 border-red-500 text-red-700 text-sm rounded-r-lg">
        {{ authStore.error }}
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="space-y-5">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">Username</label>
          <input
            v-model="username"
            type="text"
            required
            placeholder="e.g. admin or school_amparo"
            class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-deped-blue focus:bg-white text-sm transition"
          />
        </div>

        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1.5">Password</label>
          <input
            v-model="password"
            type="password"
            required
            placeholder="••••••••"
            class="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-deped-blue focus:bg-white text-sm transition"
          />
        </div>

        <button
          type="submit"
          :disabled="authStore.loading"
          class="w-full py-3 bg-deped-blue hover:bg-blue-900 text-white font-semibold rounded-lg shadow-md hover:shadow-lg transition-all duration-200 flex items-center justify-center text-sm disabled:opacity-50"
        >
          <span v-if="!authStore.loading">Sign In</span>
          <span v-else class="flex items-center space-x-2">
            <svg class="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            <span>Authenticating...</span>
          </span>
        </button>
      </form>

      <!-- Roles hint -->
      <div class="mt-8 pt-5 border-t border-slate-100 text-xs text-slate-400 text-center">
        Default administrative credentials: <span class="font-mono text-slate-600 font-medium">admin</span> / <span class="font-mono text-slate-600 font-medium">Admin123!</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const username = ref('admin')
const password = ref('Admin123!')

const handleSubmit = async () => {
  const success = await authStore.login(username.value, password.value)
  if (success) {
    router.push('/records')
  }
}
</script>

