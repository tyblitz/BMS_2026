<template>
  <div class="space-y-6">
    <!-- Admin Control Center Banner -->
    <div class="bg-gradient-to-r from-slate-900 via-deped-dark to-slate-800 rounded-2xl p-6 text-white shadow-lg">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-900/60 text-red-200 text-xs font-semibold uppercase tracking-wider mb-2">
            <span class="w-2 h-2 rounded-full bg-red-400"></span>
            System Administration
          </div>
          <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Admin Operations Control Center
          </h1>
          <p class="text-sm text-slate-300 mt-1 flex flex-wrap items-center gap-2">
            <span>System Telemetry & Governance</span>
            <span>•</span>
            <span v-if="telemetry?.users?.total !== undefined">{{ telemetry.users.total }} Provisioned Accounts</span>
            <span>•</span>
            <span v-if="telemetry?.database?.active_records !== undefined">{{ telemetry.database.active_records.toLocaleString() }} Active Database Rows</span>
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-2.5">
          <router-link
            to="/users"
            class="px-4 py-2.5 bg-deped-gold hover:bg-yellow-500 text-deped-dark font-bold text-sm rounded-xl shadow-md transition flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            Manage Accounts ({{ telemetry?.users?.total || 212 }})
          </router-link>

          <router-link
            to="/settings"
            class="px-4 py-2.5 bg-white/10 hover:bg-white/20 text-white font-medium text-sm rounded-xl transition flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Database Settings
          </router-link>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-deped-blue"></div>
      <span class="ml-3 text-slate-600 font-medium">Gathering system telemetry...</span>
    </div>

    <!-- Telemetry Cards -->
    <div v-else class="space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Card 1: Active Database Engine -->
        <div class="bms-card p-6 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div class="flex items-center justify-between mb-4">
            <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Database Engine</span>
            <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
              {{ telemetry?.database?.status }}
            </span>
          </div>
          <div class="text-2xl font-extrabold text-slate-900">
            {{ telemetry?.database?.engine }}
          </div>
          <div class="text-xs text-slate-500 font-mono mt-1 truncate" :title="telemetry?.database?.url_display">
            {{ telemetry?.database?.url_display }}
          </div>

          <div class="mt-4 pt-4 border-t border-slate-100 flex justify-between text-xs text-slate-600">
            <div>
              <span class="text-slate-400 block">Active Rows</span>
              <span class="font-bold text-slate-900 font-mono">{{ telemetry?.database?.active_records?.toLocaleString() }}</span>
            </div>
            <div>
              <span class="text-slate-400 block">Soft-Deleted</span>
              <span class="font-bold text-slate-500 font-mono">{{ telemetry?.database?.deleted_records?.toLocaleString() }}</span>
            </div>
            <router-link to="/settings" class="self-end text-deped-blue hover:text-blue-900 font-bold">
              Switch &rarr;
            </router-link>
          </div>
        </div>

        <!-- Card 2: User Accounts Provisioned -->
        <div class="bms-card p-6 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div class="flex items-center justify-between mb-4">
            <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">User Directory</span>
            <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
              {{ telemetry?.users?.active }} Active
            </span>
          </div>
          <div class="text-2xl font-extrabold text-slate-900">
            {{ telemetry?.users?.total }} Total Accounts
          </div>
          <div class="text-xs text-slate-500 mt-1">
            Regional Office, SDOs, and School Encoders
          </div>

          <div class="mt-4 pt-4 border-t border-slate-100 grid grid-cols-4 gap-2 text-center text-xs">
            <div class="p-1.5 bg-slate-50 rounded">
              <span class="text-slate-400 block text-[10px]">Admin</span>
              <span class="font-bold text-slate-800">{{ telemetry?.users?.admin }}</span>
            </div>
            <div class="p-1.5 bg-slate-50 rounded">
              <span class="text-slate-400 block text-[10px]">Regional</span>
              <span class="font-bold text-slate-800">{{ telemetry?.users?.region }}</span>
            </div>
            <div class="p-1.5 bg-slate-50 rounded">
              <span class="text-slate-400 block text-[10px]">SDOs</span>
              <span class="font-bold text-slate-800">{{ telemetry?.users?.sdo }}</span>
            </div>
            <div class="p-1.5 bg-slate-50 rounded">
              <span class="text-slate-400 block text-[10px]">Schools</span>
              <span class="font-bold text-slate-800">{{ telemetry?.users?.school }}</span>
            </div>
          </div>
        </div>

        <!-- Card 3: Global Financial Scope -->
        <div class="bms-card p-6 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div class="flex items-center justify-between mb-4">
            <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">NCR Financial Scope</span>
            <span class="text-xs font-bold text-blue-700">{{ telemetry?.financial?.utilization_rate }}% Utilized</span>
          </div>
          <div class="text-2xl font-extrabold text-slate-900">
            ₱{{ formatMoney(telemetry?.financial?.total_adjusted_allotment) }}
          </div>
          <div class="text-xs text-slate-500 mt-1">
            Across {{ telemetry?.operational?.divisions_count }} Divisions & {{ telemetry?.operational?.schools_count }} Schools
          </div>

          <div class="mt-4 pt-4 border-t border-slate-100 flex justify-between text-xs text-slate-600">
            <div>
              <span class="text-slate-400 block">Obligated</span>
              <span class="font-bold text-blue-700 font-mono">₱{{ formatMoney(telemetry?.financial?.total_obligations) }}</span>
            </div>
            <div>
              <span class="text-slate-400 block">Unobligated</span>
              <span class="font-bold text-emerald-700 font-mono">₱{{ formatMoney(telemetry?.financial?.unobligated_balance) }}</span>
            </div>
            <router-link to="/records" class="self-end text-deped-blue hover:text-blue-900 font-bold">
              Global Table &rarr;
            </router-link>
          </div>
        </div>
      </div>

      <!-- Quick Shortcuts Grid -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <router-link
          to="/users"
          class="bms-card p-4 bg-white border border-slate-200 hover:border-deped-blue rounded-xl shadow-sm hover:shadow transition flex items-center gap-3"
        >
          <div class="w-10 h-10 rounded-lg bg-blue-50 text-deped-blue flex items-center justify-center font-bold">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          </div>
          <div>
            <div class="font-bold text-slate-900 text-sm">User Management</div>
            <div class="text-xs text-slate-500">Create, edit, reset passwords</div>
          </div>
        </router-link>

        <router-link
          to="/settings"
          class="bms-card p-4 bg-white border border-slate-200 hover:border-emerald-600 rounded-xl shadow-sm hover:shadow transition flex items-center gap-3"
        >
          <div class="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2 1.5 3 3.5 3h9c2 0 3.5-1 3.5-3V7c0-2-1.5-3-3.5-3h-9C5.5 4 4 5 4 7z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h4" />
            </svg>
          </div>
          <div>
            <div class="font-bold text-slate-900 text-sm">Database Settings</div>
            <div class="text-xs text-slate-500">Hot-swap SQLite / MySQL</div>
          </div>
        </router-link>

        <router-link
          to="/upload"
          class="bms-card p-4 bg-white border border-slate-200 hover:border-amber-600 rounded-xl shadow-sm hover:shadow transition flex items-center gap-3"
        >
          <div class="w-10 h-10 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center font-bold">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
          </div>
          <div>
            <div class="font-bold text-slate-900 text-sm">Bulk Ingestion</div>
            <div class="text-xs text-slate-500">Streaming Excel upload</div>
          </div>
        </router-link>

        <router-link
          to="/records"
          class="bms-card p-4 bg-white border border-slate-200 hover:border-purple-600 rounded-xl shadow-sm hover:shadow transition flex items-center gap-3"
        >
          <div class="w-10 h-10 rounded-lg bg-purple-50 text-purple-700 flex items-center justify-center font-bold">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <div class="font-bold text-slate-900 text-sm">Global Data Table</div>
            <div class="text-xs text-slate-500">View all 208k+ line items</div>
          </div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/api/client'

const authStore = useAuthStore()

const telemetry = ref(null)
const loading = ref(true)

const formatMoney = (val) => {
  if (val === null || val === undefined) return '0.00'
  return Number(val).toLocaleString('en-PH', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

const fetchAdminSummary = async () => {
  loading.value = true
  try {
    const res = await apiClient.get('/analytics/admin-summary')
    telemetry.value = res.data
  } catch (err) {
    console.error('Failed to load admin summary', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchAdminSummary()
})
</script>
