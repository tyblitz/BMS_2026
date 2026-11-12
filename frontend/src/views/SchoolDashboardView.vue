<template>
  <div class="space-y-6">
    <!-- School Profile & Welcome Banner -->
    <div class="bg-gradient-to-r from-deped-blue via-blue-900 to-deped-dark rounded-2xl p-6 text-white shadow-lg">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-800/80 text-blue-200 text-xs font-semibold uppercase tracking-wider mb-2">
            <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
            School Operating Unit
          </div>
          <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight">
            {{ summary?.school_name || authStore.user?.school_name || 'School Workspace' }}
          </h1>
          <p class="text-sm text-blue-200 mt-1 flex items-center gap-2">
            <span>{{ summary?.division || authStore.user?.division || 'Schools Division Office' }}</span>
            <span>•</span>
            <span>{{ summary?.region || authStore.user?.region || 'National Capital Region (NCR)' }}</span>
            <span v-if="summary?.total_records !== undefined" class="bg-blue-800 px-2 py-0.5 rounded text-xs">
              {{ summary.total_records.toLocaleString() }} line items
            </span>
          </p>
        </div>

        <!-- Direct Actions -->
        <div class="flex flex-wrap items-center gap-2.5">
          <router-link
            to="/upload"
            class="px-4 py-2.5 bg-deped-gold hover:bg-yellow-500 text-deped-dark font-bold text-sm rounded-xl shadow-md transition flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            Upload tempTable
          </router-link>

          <button
            @click="handleExport"
            :disabled="exporting"
            class="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm rounded-xl shadow-md transition flex items-center gap-2 disabled:opacity-50"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span v-if="!exporting">Export Excel</span>
            <span v-else>Exporting...</span>
          </button>

          <router-link
            to="/records"
            class="px-4 py-2.5 bg-white/10 hover:bg-white/20 text-white font-medium text-sm rounded-xl transition flex items-center gap-2"
          >
            View All Records &rarr;
          </router-link>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-deped-blue"></div>
      <span class="ml-3 text-slate-600 font-medium">Calculating school balances...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="p-4 bg-red-50 border-l-4 border-red-500 rounded-r-xl text-red-700 text-sm">
      {{ error }}
    </div>

    <!-- Financial Health Overview Cards -->
    <div v-else class="space-y-6">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <!-- 1. Total Adjusted Allotment -->
        <div class="bms-card p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div class="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Total Adjusted Allotment
          </div>
          <div class="text-xl font-extrabold text-slate-900 mt-2">
            ₱{{ formatMoney(summary?.total_adjusted_allotment) }}
          </div>
          <div class="text-xs text-slate-500 mt-1">
            Allotment + Transfers & Realignments
          </div>
        </div>

        <!-- 2. Obligations Incurred -->
        <div class="bms-card p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div class="text-xs font-semibold text-blue-700 uppercase tracking-wider">
            Obligations Incurred
          </div>
          <div class="text-xl font-extrabold text-blue-700 mt-2">
            ₱{{ formatMoney(summary?.total_obligations) }}
          </div>
          <div class="text-xs text-blue-600 mt-1 font-medium">
            {{ summary?.utilization_rate }}% Utilization Rate
          </div>
        </div>

        <!-- 3. Disbursements -->
        <div class="bms-card p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div class="text-xs font-semibold text-indigo-700 uppercase tracking-wider">
            Disbursements
          </div>
          <div class="text-xl font-extrabold text-indigo-700 mt-2">
            ₱{{ formatMoney(summary?.total_disbursements) }}
          </div>
          <div class="text-xs text-indigo-600 mt-1 font-medium">
            {{ summary?.disbursement_rate }}% Disbursed
          </div>
        </div>

        <!-- 4. Unobligated Balance -->
        <div class="bms-card p-4 bg-white border border-slate-200 rounded-xl shadow-sm" :class="summary?.unobligated_balance < 0 ? 'bg-red-50/50 border-red-200' : ''">
          <div class="text-xs font-semibold uppercase tracking-wider" :class="summary?.unobligated_balance < 0 ? 'text-red-700' : 'text-emerald-700'">
            Unobligated Balance
          </div>
          <div class="text-xl font-extrabold mt-2" :class="summary?.unobligated_balance < 0 ? 'text-red-700' : 'text-emerald-700'">
            ₱{{ formatMoney(summary?.unobligated_balance) }}
          </div>
          <div class="text-xs text-slate-500 mt-1">
            Remaining Allotment to Obligate
          </div>
        </div>

        <!-- 5. Unpaid Balance -->
        <div class="bms-card p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div class="text-xs font-semibold text-amber-700 uppercase tracking-wider">
            Unpaid Obligations
          </div>
          <div class="text-xl font-extrabold text-amber-700 mt-2">
            ₱{{ formatMoney(summary?.unpaid_balance) }}
          </div>
          <div class="text-xs text-slate-500 mt-1">
            Obligations - Disbursements
          </div>
        </div>
      </div>

      <!-- Budget Utilization Progress Bar -->
      <div class="bms-card p-5 bg-white border border-slate-200 rounded-xl shadow-sm">
        <div class="flex justify-between items-center mb-2">
          <span class="text-sm font-bold text-slate-800">Overall Budget Utilization</span>
          <span class="text-sm font-bold text-deped-blue">{{ summary?.utilization_rate }}%</span>
        </div>
        <div class="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
          <div
            class="h-3 rounded-full transition-all duration-500"
            :class="summary?.utilization_rate > 90 ? 'bg-emerald-500' : summary?.utilization_rate > 50 ? 'bg-deped-blue' : 'bg-amber-500'"
            :style="{ width: `${Math.min(summary?.utilization_rate || 0, 100)}%` }"
          ></div>
        </div>
        <div class="flex justify-between text-xs text-slate-400 mt-2">
          <span>0%</span>
          <span>Target: 100% Obligated</span>
          <span>100%</span>
        </div>
      </div>

      <!-- Recent School Transactions -->
      <div class="bms-card bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div class="p-4 sm:p-5 border-b border-slate-200 flex justify-between items-center bg-slate-50">
          <div>
            <h3 class="font-bold text-slate-900 text-base">Recent School Line Items</h3>
            <p class="text-xs text-slate-500 mt-0.5">Latest encoded and imported budget entries</p>
          </div>
          <router-link
            to="/records"
            class="text-xs font-bold text-deped-blue hover:text-blue-900 inline-flex items-center gap-1"
          >
            Open Full Table &rarr;
          </router-link>
        </div>

        <div v-if="!summary?.recent_records || summary.recent_records.length === 0" class="p-8 text-center text-slate-400 text-sm">
          No records found for this school operating unit. Click "Upload tempTable" to import.
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-left text-xs text-slate-600">
            <thead class="bg-slate-100/75 text-slate-700 font-semibold uppercase tracking-wider text-[11px] border-b border-slate-200">
              <tr>
                <th class="px-4 py-3">Date</th>
                <th class="px-4 py-3">P.A.P / Particulars</th>
                <th class="px-4 py-3">Account Code</th>
                <th class="px-4 py-3 text-right">Allotment</th>
                <th class="px-4 py-3 text-right">Obligations</th>
                <th class="px-4 py-3 text-right">Disbursement</th>
                <th class="px-4 py-3 text-right text-emerald-700">Unobligated</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="row in summary.recent_records" :key="row.id" class="hover:bg-slate-50/80 transition">
                <td class="px-4 py-3 font-mono">{{ row.date_bms || '-' }}</td>
                <td class="px-4 py-3">
                  <div class="font-medium text-slate-900 max-w-xs truncate" :title="row.particulars">
                    {{ row.particulars || 'No description' }}
                  </div>
                  <div class="text-[10px] text-slate-400 font-mono">{{ row.uacs_pap_code }}</div>
                </td>
                <td class="px-4 py-3 font-mono font-medium">{{ row.account_code || '-' }}</td>
                <td class="px-4 py-3 text-right font-mono">₱{{ formatMoney(row.allotment) }}</td>
                <td class="px-4 py-3 text-right font-mono font-medium text-blue-700">₱{{ formatMoney(row.obligations_incurred) }}</td>
                <td class="px-4 py-3 text-right font-mono font-medium text-indigo-700">₱{{ formatMoney(row.disbursement) }}</td>
                <td class="px-4 py-3 text-right font-mono font-bold text-emerald-700">₱{{ formatMoney(row.unobligated) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/api/client'

const authStore = useAuthStore()

const summary = ref(null)
const loading = ref(true)
const error = ref(null)
const exporting = ref(false)

const formatMoney = (val) => {
  if (val === null || val === undefined) return '0.00'
  return Number(val).toLocaleString('en-PH', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

const fetchSchoolSummary = async () => {
  loading.value = true
  error.value = null
  try {
    const res = await apiClient.get('/analytics/school-summary')
    summary.value = res.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load school summary.'
  } finally {
    loading.value = false
  }
}

const handleExport = async () => {
  exporting.value = true
  try {
    const response = await apiClient.get('/export', {
      responseType: 'blob',
    })
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `tempTable_${authStore.user?.username || 'school'}.xlsx`
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (err) {
    alert('Failed to export school records.')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  fetchSchoolSummary()
})
</script>
