<template>
  <div class="max-w-3xl mx-auto space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-extrabold text-slate-900 tracking-tight">Database & Infrastructure Settings</h1>
      <p class="text-xs text-slate-500 mt-0.5">
        Manage database connectivity. The system supports decentralized local storage (SQLite/MySQL) and can hot-swap to remote servers without service restarts.
      </p>
    </div>

    <!-- Active Database Status Card -->
    <div class="bms-card p-6 bg-white space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-bold text-slate-800">Current Database Engine</h3>
        <span
          class="px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider"
          :class="dbInfo.mode === 'local_sqlite' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'"
        >
          {{ dbInfo.mode === 'local_sqlite' ? 'Decentralized (Local)' : 'External Database Server' }}
        </span>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
        <div class="p-3 bg-slate-50 rounded-lg border border-slate-200">
          <span class="block text-slate-400 text-[10px] uppercase font-bold">SQL Dialect</span>
          <span class="text-sm font-bold text-slate-700 uppercase font-mono">{{ dbInfo.dialect || 'sqlite' }}</span>
        </div>
        <div class="p-3 bg-slate-50 rounded-lg border border-slate-200">
          <span class="block text-slate-400 text-[10px] uppercase font-bold">Active Connection Target</span>
          <span class="text-xs font-medium text-slate-700 font-mono truncate block" :title="dbInfo.active_database_url">
            {{ dbInfo.active_database_url || 'sqlite:///./bms_local.db' }}
          </span>
        </div>
      </div>
    </div>

    <!-- Dynamic Switcher Form Card -->
    <div class="bms-card p-6 bg-white space-y-5">
      <div>
        <h3 class="text-sm font-bold text-slate-800 mb-1">Switch Database Target</h3>
        <p class="text-xs text-slate-400">
          Configure a new target connection. The system tests the connection before switching and automatically applies all schema tables and indexes.
        </p>
      </div>

      <!-- Presets Selector -->
      <div>
        <label class="block text-xs font-semibold uppercase text-slate-600 mb-1.5">Connection Presets</label>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <button
            type="button"
            @click="setPreset('sqlite')"
            class="p-2.5 border rounded-lg text-left text-xs transition"
            :class="selectedPreset === 'sqlite' ? 'border-deped-blue bg-blue-50/50 text-deped-blue font-semibold' : 'border-slate-200 hover:bg-slate-50 text-slate-600'"
          >
            <span class="block font-bold">Local SQLite</span>
            <span class="text-[10px] text-slate-400">Standalone file (0 config)</span>
          </button>

          <button
            type="button"
            @click="setPreset('xampp')"
            class="p-2.5 border rounded-lg text-left text-xs transition"
            :class="selectedPreset === 'xampp' ? 'border-deped-blue bg-blue-50/50 text-deped-blue font-semibold' : 'border-slate-200 hover:bg-slate-50 text-slate-600'"
          >
            <span class="block font-bold">XAMPP MySQL</span>
            <span class="text-[10px] text-slate-400">localhost:3306 (MariaDB)</span>
          </button>

          <button
            type="button"
            @click="setPreset('remote')"
            class="p-2.5 border rounded-lg text-left text-xs transition"
            :class="selectedPreset === 'remote' ? 'border-deped-blue bg-blue-50/50 text-deped-blue font-semibold' : 'border-slate-200 hover:bg-slate-50 text-slate-600'"
          >
            <span class="block font-bold">Remote Server</span>
            <span class="text-[10px] text-slate-400">MySQL / PostgreSQL</span>
          </button>
        </div>
      </div>

      <!-- Connection URL Input -->
      <div>
        <label class="block text-xs font-semibold uppercase text-slate-600 mb-1.5">Database Connection URL</label>
        <input
          v-model="candidateUrl"
          type="text"
          placeholder="e.g. mysql+pymysql://root:@localhost:3306/bms_db"
          class="w-full text-xs font-mono px-3.5 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-deped-blue focus:outline-none"
        />
      </div>

      <!-- Test & Switch Feedback Banner -->
      <div v-if="actionFeedback" class="p-3 rounded-lg text-xs" :class="actionFeedback.success ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-red-50 text-red-800 border border-red-200'">
        {{ actionFeedback.message }}
      </div>

      <!-- Action Buttons -->
      <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
        <button
          type="button"
          @click="testConnection"
          :disabled="testing"
          class="px-4 py-2 border border-slate-300 text-slate-700 hover:bg-slate-50 rounded-lg text-xs font-semibold transition disabled:opacity-50"
        >
          {{ testing ? 'Testing...' : 'Test Connection' }}
        </button>

        <button
          type="button"
          @click="switchConnection"
          :disabled="switching || !candidateUrl"
          class="px-5 py-2 bg-deped-blue hover:bg-blue-900 text-white rounded-lg text-xs font-semibold shadow-sm transition disabled:opacity-50"
        >
          {{ switching ? 'Applying...' : 'Apply & Switch Database' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

const dbInfo = ref({})
const candidateUrl = ref('')
const selectedPreset = ref('sqlite')
const testing = ref(false)
const switching = ref(false)
const actionFeedback = ref(null)

const setPreset = (type) => {
  selectedPreset.value = type
  if (type === 'sqlite') {
    candidateUrl.value = 'sqlite:///./data/bms_local.db'
  } else if (type === 'xampp') {
    candidateUrl.value = 'mysql+pymysql://root:@localhost:3306/bms_db?charset=utf8mb4'
  } else if (type === 'remote') {
    candidateUrl.value = 'postgresql+psycopg2://user:password@remote-db.deped.gov.ph:5432/bms_db'
  }
}

const fetchDbInfo = async () => {
  try {
    const res = await apiClient.get('/settings/db')
    dbInfo.value = res.data
    if (!candidateUrl.value) {
      candidateUrl.value = res.data.active_database_url
    }
  } catch (err) {
    console.error(err)
  }
}

const testConnection = async () => {
  testing.value = true
  actionFeedback.value = null
  try {
    const res = await apiClient.post('/settings/db/test', { database_url: candidateUrl.value })
    actionFeedback.value = res.data
  } catch (err) {
    actionFeedback.value = { success: false, message: err.response?.data?.detail || 'Connection test failed.' }
  } finally {
    testing.value = false
  }
}

const switchConnection = async () => {
  switching.value = true
  actionFeedback.value = null
  try {
    const res = await apiClient.post('/settings/db/switch', { database_url: candidateUrl.value })
    actionFeedback.value = res.data
    await fetchDbInfo()
  } catch (err) {
    actionFeedback.value = { success: false, message: err.response?.data?.detail || 'Database switch failed.' }
  } finally {
    switching.value = false
  }
}

onMounted(() => {
  fetchDbInfo()
})
</script>

