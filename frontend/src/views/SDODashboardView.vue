<template>
  <div class="space-y-6">
    <!-- Division Profile & Welcome Banner -->
    <div class="bg-gradient-to-r from-deped-dark via-slate-800 to-deped-blue rounded-2xl p-6 text-white shadow-lg">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-800/80 text-blue-200 text-xs font-semibold uppercase tracking-wider mb-2">
            <span class="w-2 h-2 rounded-full bg-blue-400"></span>
            Schools Division Office Consolidation Hub
          </div>
          <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight">
            {{ summary?.division || authStore.user?.division || 'Division Office' }}
          </h1>
          <p class="text-sm text-blue-200 mt-1 flex items-center gap-2">
            <span>{{ summary?.region || 'National Capital Region (NCR)' }}</span>
            <span>•</span>
            <span v-if="summary?.total_schools !== undefined">
              {{ summary.total_schools }} Operating Units
            </span>
            <span>•</span>
            <span v-if="summary?.total_records !== undefined">
              {{ summary.total_records.toLocaleString() }} Consolidated Rows
            </span>
          </p>
        </div>

        <!-- Division Actions -->
        <div class="flex flex-wrap items-center gap-2.5">
          <router-link
            to="/upload"
            class="px-4 py-2.5 bg-deped-gold hover:bg-yellow-500 text-deped-dark font-bold text-sm rounded-xl shadow-md transition flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            Consolidate Files
          </router-link>

          <button
            @click="handleExport"
            :disabled="exporting"
            class="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm rounded-xl shadow-md transition flex items-center gap-2 disabled:opacity-50"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span v-if="!exporting">Export SDO Conso</span>
            <span v-else>Exporting...</span>
          </button>

          <router-link
            to="/records"
            class="px-4 py-2.5 bg-white/10 hover:bg-white/20 text-white font-medium text-sm rounded-xl transition flex items-center gap-2"
          >
            View All Division Records &rarr;
          </router-link>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-deped-blue"></div>
      <span class="ml-3 text-slate-600 font-medium">Consolidating division balances...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="p-4 bg-red-50 border-l-4 border-red-500 rounded-r-xl text-red-700 text-sm">
      {{ error }}
    </div>

    <!-- Financial Health Overview Cards -->
    <div v-else class="space-y-6">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <!-- 1. Division Adjusted Allotment -->
        <div class="bms-card p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div class="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Division Adjusted Allotment
          </div>
          <div class="text-xl font-extrabold text-slate-900 mt-2">
            ₱{{ formatMoney(summary?.total_adjusted_allotment) }}
          </div>
          <div class="text-xs text-slate-500 mt-1">
            Total for all {{ summary?.total_schools }} schools
          </div>
        </div>

        <!-- 2. Division Obligations -->
        <div class="bms-card p-4 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div class="text-xs font-semibold text-blue-700 uppercase tracking-wider">
            Total Incurred Obligations
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
            Remaining Division Allotment
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
            Payables / Pending Checks
          </div>
        </div>
      </div>

      <!-- Budget Utilization Progress Bar -->
      <div class="bms-card p-5 bg-white border border-slate-200 rounded-xl shadow-sm">
        <div class="flex justify-between items-center mb-2">
          <span class="text-sm font-bold text-slate-800">Division-wide Budget Utilization</span>
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

      <!-- School Submission & Compliance Tracker -->
      <div class="bms-card bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div class="p-4 sm:p-5 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50">
          <div>
            <h3 class="font-bold text-slate-900 text-base">School Submission & Compliance Tracker</h3>
            <p class="text-xs text-slate-500 mt-0.5">
              Consolidated breakdown across {{ summary?.total_schools || 0 }} operating units
            </p>
          </div>

          <div class="w-full sm:w-64">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Filter school..."
              class="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-deped-blue"
            />
          </div>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs text-slate-600">
            <thead class="bg-slate-100/75 text-slate-700 font-semibold uppercase tracking-wider text-[11px] border-b border-slate-200">
              <tr>
                <th class="px-4 py-3">School Operating Unit</th>
                <th class="px-4 py-3 text-center">Status</th>
                <th class="px-4 py-3 text-right">Transactions</th>
                <th class="px-4 py-3 text-right">Adjusted Allotment</th>
                <th class="px-4 py-3 text-right">Obligations</th>
                <th class="px-4 py-3 text-right">Unobligated</th>
                <th class="px-4 py-3 text-right">% Utilization</th>
                <th class="px-4 py-3 text-center">Action</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr
                v-for="school in filteredSchools"
                :key="school.school_name"
                class="hover:bg-slate-50/80 transition"
              >
                <td class="px-4 py-3 font-semibold text-slate-900">
                  {{ school.school_name }}
                </td>
                <td class="px-4 py-3 text-center">
                  <span
                    class="px-2 py-0.5 rounded-full text-[10px] font-semibold"
                    :class="school.utilization_rate >= 80 ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-blue-50 text-blue-700 border border-blue-200'"
                  >
                    {{ school.status }}
                  </span>
                </td>
                <td class="px-4 py-3 text-right font-mono">{{ school.record_count.toLocaleString() }}</td>
                <td class="px-4 py-3 text-right font-mono">₱{{ formatMoney(school.total_adjusted_allotment) }}</td>
                <td class="px-4 py-3 text-right font-mono font-medium text-blue-700">₱{{ formatMoney(school.total_obligations) }}</td>
                <td class="px-4 py-3 text-right font-mono font-bold text-emerald-700">₱{{ formatMoney(school.unobligated_balance) }}</td>
                <td class="px-4 py-3 text-right font-mono font-semibold">
                  <div class="flex items-center justify-end gap-2">
                    <span>{{ school.utilization_rate }}%</span>
                    <div class="w-12 bg-slate-100 rounded-full h-1.5 hidden md:block">
                      <div
                        class="h-1.5 rounded-full"
                        :class="school.utilization_rate >= 80 ? 'bg-emerald-500' : 'bg-deped-blue'"
                        :style="{ width: `${Math.min(school.utilization_rate, 100)}%` }"
                      ></div>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-3 text-center">
                  <router-link
                    :to="{ path: '/records', query: { operating_unit: school.school_name } }"
                    class="px-2.5 py-1 bg-slate-100 hover:bg-deped-blue hover:text-white text-slate-700 font-semibold rounded text-[11px] transition"
                  >
                    View
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

const filteredSchools = computed(() => {
  if (!summary.value?.schools_matrix) return []
  if (!searchQuery.value) return summary.value.schools_matrix
  const q = searchQuery.value.toLowerCase()
  return summary.value.schools_matrix.filter((s) => s.school_name.toLowerCase().includes(q))
})

const fetchDivisionSummary = async () => {
  loading.value = true
  error.value = null
  try {
    const res = await apiClient.get('/analytics/division-summary')
    summary.value = res.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load division summary.'
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
    link.download = `tempTable_${authStore.user?.username || 'division'}.xlsx`
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (err) {
    alert('Failed to export division records.')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  fetchDivisionSummary()
})
</script>
