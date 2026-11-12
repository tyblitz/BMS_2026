<template>
  <div class="space-y-6">
    <!-- Regional Executive Banner -->
    <div class="bg-gradient-to-r from-blue-950 via-deped-blue to-indigo-900 rounded-2xl p-6 text-white shadow-lg">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-800/80 text-blue-200 text-xs font-semibold uppercase tracking-wider mb-2">
            <span class="w-2 h-2 rounded-full bg-deped-gold"></span>
            Regional Executive Dashboard
          </div>
          <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight">
            DepEd National Capital Region (NCR)
          </h1>
          <p class="text-sm text-blue-200 mt-1 flex flex-wrap items-center gap-2">
            <span>Executive Regional Office Portal</span>
            <span>•</span>
            <span v-if="summary?.total_divisions !== undefined">{{ summary.total_divisions }} Schools Division Offices</span>
            <span>•</span>
            <span v-if="summary?.total_schools !== undefined">{{ summary.total_schools }} Operating Units</span>
            <span>•</span>
            <span v-if="summary?.total_records !== undefined">{{ summary.total_records.toLocaleString() }} Regional Rows</span>
          </p>
        </div>

        <!-- Regional Actions -->
        <div class="flex flex-wrap items-center gap-2.5">
          <router-link
            to="/upload"
            class="px-4 py-2.5 bg-deped-gold hover:bg-yellow-500 text-deped-dark font-bold text-sm rounded-xl shadow-md transition flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            Import Division Files
          </router-link>

          <button
            @click="handleExport"
            :disabled="exporting"
            class="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm rounded-xl shadow-md transition flex items-center gap-2 disabled:opacity-50"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span v-if="!exporting">Master Conso Export</span>
            <span v-else>Streaming Export...</span>
          </button>

          <router-link
            to="/records"
            class="px-4 py-2.5 bg-white/10 hover:bg-white/20 text-white font-medium text-sm rounded-xl transition flex items-center gap-2"
          >
            All Regional Records &rarr;
          </router-link>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-deped-blue"></div>
      <span class="ml-3 text-slate-600 font-medium">Aggregating 16 SDO metrics across NCR...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="p-4 bg-red-50 border-l-4 border-red-500 rounded-r-xl text-red-700 text-sm">
      {{ error }}
    </div>

    <!-- Financial Health Overview Cards -->
    <div v-else class="space-y-6">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <!-- 1. Regional Adjusted Allotment -->
        <div class="bms-card p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div class="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Total NCR Allotment
          </div>
          <div class="text-xl font-extrabold text-slate-900 mt-2">
            ₱{{ formatMoney(summary?.total_adjusted_allotment) }}
          </div>
          <div class="text-xs text-slate-500 mt-1">
            Grand Total for 16 Divisions
          </div>
        </div>

        <!-- 2. Regional Obligations -->
        <div class="bms-card p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div class="text-xs font-semibold text-blue-700 uppercase tracking-wider">
            NCR Incurred Obligations
          </div>
          <div class="text-xl font-extrabold text-blue-700 mt-2">
            ₱{{ formatMoney(summary?.total_obligations) }}
          </div>
          <div class="text-xs text-blue-600 mt-1 font-medium">
            {{ summary?.utilization_rate }}% Regional Utilization
          </div>
        </div>

        <!-- 3. Regional Disbursements -->
        <div class="bms-card p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div class="text-xs font-semibold text-indigo-700 uppercase tracking-wider">
            Total Disbursements
          </div>
          <div class="text-xl font-extrabold text-indigo-700 mt-2">
            ₱{{ formatMoney(summary?.total_disbursements) }}
          </div>
          <div class="text-xs text-indigo-600 mt-1 font-medium">
            {{ summary?.disbursement_rate }}% Disbursed
          </div>
        </div>

        <!-- 4. Unobligated Balance -->
        <div class="bms-card p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div class="text-xs font-semibold text-emerald-700 uppercase tracking-wider">
            Unobligated Balance
          </div>
          <div class="text-xl font-extrabold text-emerald-700 mt-2">
            ₱{{ formatMoney(summary?.unobligated_balance) }}
          </div>
          <div class="text-xs text-slate-500 mt-1">
            Remaining Allotment in Region
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
            Accounts Payable in NCR
          </div>
        </div>
      </div>

      <!-- Regional Budget Utilization Progress Bar -->
      <div class="bms-card p-5 bg-white border border-slate-200 rounded-xl shadow-sm">
        <div class="flex justify-between items-center mb-2">
          <span class="text-sm font-bold text-slate-800">Regional Budget Utilization Performance</span>
          <span class="text-sm font-bold text-deped-blue">{{ summary?.utilization_rate }}%</span>
        </div>
        <div class="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
          <div
            class="h-3 rounded-full transition-all duration-500"
            :class="summary?.utilization_rate > 90 ? 'bg-emerald-500' : summary?.utilization_rate > 50 ? 'bg-deped-blue' : 'bg-amber-500'"
            :style="{ width: `${Math.min(summary?.utilization_rate || 0, 100)}%` }"
          ></div>
        </div>
      </div>

      <!-- 16-Division Comparative Matrix & Leaderboard -->
      <div class="bms-card bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div class="p-4 sm:p-5 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50">
          <div>
            <h3 class="font-bold text-slate-900 text-base">16 Schools Division Offices — Performance Leaderboard</h3>
            <p class="text-xs text-slate-500 mt-0.5">
              Ranked by Budget Utilization Rate across all SDOs in the National Capital Region
            </p>
          </div>

          <div class="w-full sm:w-64">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search division..."
              class="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-deped-blue"
            />
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs text-slate-600">
            <thead class="bg-slate-100/75 text-slate-700 font-semibold uppercase tracking-wider text-[11px] border-b border-slate-200">
              <tr>
                <th class="px-4 py-3 text-center">Rank</th>
                <th class="px-4 py-3">Division Office</th>
                <th class="px-4 py-3 text-center">Schools</th>
                <th class="px-4 py-3 text-right">Transactions</th>
                <th class="px-4 py-3 text-right">Adjusted Allotment</th>
                <th class="px-4 py-3 text-right">Obligations</th>
                <th class="px-4 py-3 text-right">Unobligated</th>
                <th class="px-4 py-3 text-right">% Utilization</th>
                <th class="px-4 py-3 text-center">Drilldown</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr
                v-for="(div, index) in filteredDivisions"
                :key="div.division"
                class="hover:bg-slate-50/80 transition"
              >
                <td class="px-4 py-3 text-center font-bold text-slate-400">
                  <span
                    class="w-6 h-6 inline-flex items-center justify-center rounded-full text-xs font-extrabold"
                    :class="index === 0 ? 'bg-amber-100 text-amber-800 ring-2 ring-amber-300' : index === 1 ? 'bg-slate-200 text-slate-700' : index === 2 ? 'bg-orange-100 text-orange-800' : 'text-slate-500'"
                  >
                    {{ index + 1 }}
                  </span>
                </td>
                <td class="px-4 py-3 font-bold text-slate-900">
                  {{ div.division }}
                </td>
                <td class="px-4 py-3 text-center font-medium">{{ div.schools_count }}</td>
                <td class="px-4 py-3 text-right font-mono">{{ div.record_count.toLocaleString() }}</td>
                <td class="px-4 py-3 text-right font-mono">₱{{ formatMoney(div.total_adjusted_allotment) }}</td>
                <td class="px-4 py-3 text-right font-mono font-medium text-blue-700">₱{{ formatMoney(div.total_obligations) }}</td>
                <td class="px-4 py-3 text-right font-mono font-bold text-emerald-700">₱{{ formatMoney(div.unobligated_balance) }}</td>
                <td class="px-4 py-3 text-right font-mono font-bold">
                  <div class="flex items-center justify-end gap-2">
                    <span :class="div.utilization_rate >= 80 ? 'text-emerald-700' : 'text-slate-800'">
                      {{ div.utilization_rate }}%
                    </span>
                    <div class="w-12 bg-slate-100 rounded-full h-1.5 hidden md:block">
                      <div
                        class="h-1.5 rounded-full"
                        :class="div.utilization_rate >= 80 ? 'bg-emerald-500' : 'bg-deped-blue'"
                        :style="{ width: `${Math.min(div.utilization_rate, 100)}%` }"
                      ></div>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-3 text-center">
                  <router-link
                    :to="{ path: '/records', query: { division: div.division } }"
                    class="px-2.5 py-1 bg-slate-100 hover:bg-deped-blue hover:text-white text-slate-700 font-semibold rounded text-[11px] transition"
                  >
                    Inspect
                  </router-link>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/api/client'

const authStore = useAuthStore()

const summary = ref(null)
const loading = ref(true)
const error = ref(null)
const exporting = ref(false)
const searchQuery = ref('')

const formatMoney = (val) => {
  if (val === null || val === undefined) return '0.00'
  return Number(val).toLocaleString('en-PH', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

const filteredDivisions = computed(() => {
  if (!summary.value?.divisions_matrix) return []
  if (!searchQuery.value) return summary.value.divisions_matrix
  const q = searchQuery.value.toLowerCase()
  return summary.value.divisions_matrix.filter((d) => d.division.toLowerCase().includes(q))
})

const fetchRegionSummary = async () => {
  loading.value = true
  error.value = null
  try {
    const res = await apiClient.get('/analytics/region-summary')
    summary.value = res.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load regional summary.'
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
    link.download = 'tempTable_Regional_NCR_Conso.xlsx'
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (err) {
    alert('Failed to export regional consolidation.')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  fetchRegionSummary()
})
</script>
