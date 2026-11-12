<template>
  <div class="space-y-6">
    <!-- Top Action & Title Bar -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-extrabold text-slate-900 tracking-tight">Budget & Financial Records</h1>
        <p class="text-xs text-slate-500 mt-0.5">
          Viewing records under <span class="font-semibold text-deped-blue">{{ authStore.userScopeDescription }}</span>
        </p>
      </div>

      <div class="flex items-center space-x-2.5">
        <button
          @click="openCreateModal"
          class="inline-flex items-center px-3.5 py-2 bg-deped-blue hover:bg-blue-900 text-white text-xs font-semibold rounded-lg shadow-sm transition"
        >
          <span class="mr-1.5 text-base leading-none">+</span> Encode Line
        </button>

        <router-link
          to="/upload"
          class="inline-flex items-center px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-sm transition"
        >
          <svg class="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          Upload Excel
        </router-link>

        <button
          @click="recordsStore.exportConsolidatedExcel"
          class="inline-flex items-center px-3.5 py-2 bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold rounded-lg shadow-sm transition"
        >
          <svg class="w-3.5 h-3.5 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Export Conso (.xlsx)
        </button>
      </div>
    </div>

    <!-- KPI Summary Cards -->
    <div class="grid grid-cols-2 sm:grid-cols-5 gap-3.5">
      <div class="bms-card p-4 bg-gradient-to-br from-white to-slate-50">
        <span class="block text-slate-400 text-[11px] uppercase font-bold tracking-wider mb-1">Total Allotment</span>
        <span class="text-lg sm:text-xl font-extrabold text-blue-900 font-mono">
          {{ formatCurrency(recordsStore.summaryKPIs.totalAllotment) }}
        </span>
      </div>

      <div class="bms-card p-4 bg-gradient-to-br from-white to-slate-50">
        <span class="block text-slate-400 text-[11px] uppercase font-bold tracking-wider mb-1">Obligations Incurred</span>
        <span class="text-lg sm:text-xl font-extrabold text-slate-800 font-mono">
          {{ formatCurrency(recordsStore.summaryKPIs.totalObligations) }}
        </span>
      </div>

      <div class="bms-card p-4 bg-gradient-to-br from-white to-slate-50">
        <span class="block text-slate-400 text-[11px] uppercase font-bold tracking-wider mb-1">Disbursements</span>
        <span class="text-lg sm:text-xl font-extrabold text-slate-800 font-mono">
          {{ formatCurrency(recordsStore.summaryKPIs.totalDisbursements) }}
        </span>
      </div>

      <div class="bms-card p-4 bg-gradient-to-br from-emerald-50/50 to-white border-emerald-100">
        <span class="block text-emerald-600 text-[11px] uppercase font-bold tracking-wider mb-1">Unobligated Balance</span>
        <span class="text-lg sm:text-xl font-extrabold text-emerald-700 font-mono">
          {{ formatCurrency(recordsStore.summaryKPIs.totalUnobligated) }}
        </span>
      </div>

      <div class="bms-card p-4 bg-gradient-to-br from-amber-50/50 to-white border-amber-100 col-span-2 sm:col-span-1">
        <span class="block text-amber-600 text-[11px] uppercase font-bold tracking-wider mb-1">Unpaid Obligations</span>
        <span class="text-lg sm:text-xl font-extrabold text-amber-700 font-mono">
          {{ formatCurrency(recordsStore.summaryKPIs.totalUnpaid) }}
        </span>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="bms-card p-4 bg-white">
      <div class="grid grid-cols-1 sm:grid-cols-6 gap-3">
        <!-- Search text -->
        <div :class="divisions.length > 1 ? 'sm:col-span-1' : 'sm:col-span-2'">
          <input
            v-model="recordsStore.filters.search"
            @input="handleFilterChange"
            type="text"
            placeholder="Search particulars, PPA, account code, station..."
            class="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:ring-1 focus:ring-deped-blue focus:outline-none"
          />
        </div>

        <!-- Division Filter Dropdown (Region & Admin) -->
        <div v-if="divisions.length > 1">
          <select
            v-model="recordsStore.filters.division"
            @change="handleDivisionChange"
            class="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg bg-white focus:ring-1 focus:ring-deped-blue focus:outline-none"
          >
            <option value="">All Divisions</option>
            <option
              v-for="div in divisions"
              :key="div"
              :value="div"
            >
              {{ div }}
            </option>
          </select>
        </div>

        <!-- Operating Unit / School Dropdown -->
        <div v-if="operatingUnits.length > 1">
          <select
            v-model="recordsStore.filters.operating_unit"
            @change="handleFilterChange"
            class="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg bg-white focus:ring-1 focus:ring-deped-blue focus:outline-none"
          >
            <option value="">All Schools & Stations</option>
            <option
              v-for="ou in operatingUnits"
              :key="ou"
              :value="ou"
            >
              {{ isSdoProper(ou) ? '🏛️ ' + ou + ' (SDO Proper)' : '🏫 ' + ou }}
            </option>
          </select>
        </div>

        <!-- Allotment Class Filter -->
        <div>
          <select
            v-model="recordsStore.filters.allotment_class"
            @change="handleFilterChange"
            class="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg bg-white focus:ring-1 focus:ring-deped-blue focus:outline-none"
          >
            <option value="">All Allotment Classes</option>
            <option value="MOOE">MOOE</option>
            <option value="PS">PS</option>
            <option value="CO">CO</option>
          </select>
        </div>

        <!-- Fund Source Filter -->
        <div>
          <input
            v-model="recordsStore.filters.fund_source"
            @input="handleFilterChange"
            type="text"
            placeholder="Filter Fund Source..."
            class="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:ring-1 focus:ring-deped-blue focus:outline-none"
          />
        </div>

        <!-- Reset Button -->
        <div class="flex items-center space-x-2">
          <button
            @click="handleResetFilters"
            class="w-full text-xs py-2 px-3 border border-slate-200 hover:bg-slate-50 text-slate-600 rounded-lg font-medium transition"
          >
            Reset Filters
          </button>
        </div>
      </div>
    </div>

    <!-- Data Table Container -->
    <div class="bms-card overflow-hidden bg-white">
      <!-- Loading indicator -->
      <div v-if="recordsStore.loading" class="p-8 text-center text-slate-500 text-xs">
        <svg class="animate-spin h-6 w-6 text-deped-blue mx-auto mb-2" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
        </svg>
        Loading budget records...
      </div>

      <!-- Empty state -->
      <div v-else-if="recordsStore.records.length === 0" class="p-12 text-center text-slate-400 text-xs">
        <p class="text-sm font-semibold text-slate-600 mb-1">No budget records found</p>
        <p>No transaction rows match your active filters or authorized organizational scope.</p>
      </div>

      <!-- Table -->
      <div v-else class="overflow-x-auto">
        <table class="w-full text-left text-xs border-collapse">
          <thead>
            <tr class="bg-slate-50/80 text-slate-500 uppercase tracking-wider text-[10px] font-bold border-b border-slate-200">
              <th class="py-3 px-3.5">Operating Unit (Station)</th>
              <th class="py-3 px-3.5">PPA / Account Code</th>
              <th class="py-3 px-2.5 text-center">Class</th>
              <th class="py-3 px-3 text-right">Adj. Allotment</th>
              <th class="py-3 px-3 text-right">Obligations</th>
              <th class="py-3 px-3 text-right">Disbursements</th>
              <th class="py-3 px-3 text-right font-semibold text-emerald-800">Unobligated</th>
              <th class="py-3 px-3 text-right font-semibold text-amber-800">Unpaid</th>
              <th class="py-3 px-3 text-center">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr
              v-for="rec in recordsStore.records"
              :key="rec.id"
              class="hover:bg-blue-50/40 transition-colors group"
            >
              <!-- Operating Unit (School or SDO Proper) -->
              <td class="py-2.5 px-3.5 font-medium max-w-[200px] truncate" :title="rec.operating_unit">
                <span
                  v-if="isSdoProper(rec.operating_unit, rec.division)"
                  class="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200"
                >
                  🏛️ SDO Proper Office
                </span>
                <span v-else class="inline-flex items-center gap-1 font-semibold text-slate-900">
                  <span class="text-xs">🏫</span> {{ rec.operating_unit }}
                </span>
              </td>

              <!-- PPA & Account Code -->
              <td class="py-2.5 px-3.5 max-w-[220px]">
                <div class="truncate font-semibold text-slate-700" :title="rec.ppa_control">
                  {{ rec.ppa_control || 'N/A' }}
                </div>
                <div class="text-[10px] text-slate-400 font-mono">
                  UACS: {{ rec.account_code || '-' }}
                </div>
              </td>

              <!-- Class Badge -->
              <td class="py-2.5 px-2.5 text-center">
                <span
                  class="inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider"
                  :class="{
                    'bg-blue-100 text-blue-700': rec.allotment_class === 'MOOE',
                    'bg-purple-100 text-purple-700': rec.allotment_class === 'PS',
                    'bg-amber-100 text-amber-700': rec.allotment_class === 'CO',
                  }"
                >
                  {{ rec.allotment_class || '-' }}
                </span>
              </td>

              <!-- Total Adjusted Allotment -->
              <td class="py-2.5 px-3 text-right font-mono font-medium text-slate-700">
                {{ formatCurrency(rec.total_adjusted_allotment || rec.allotment) }}
              </td>

              <!-- Obligations Incurred -->
              <td class="py-2.5 px-3 text-right font-mono text-slate-700">
                {{ formatCurrency(rec.obligations_incurred) }}
              </td>

              <!-- Disbursements -->
              <td class="py-2.5 px-3 text-right font-mono text-slate-700">
                {{ formatCurrency(rec.disbursement) }}
              </td>

              <!-- Dynamic Unobligated Balance -->
              <td class="py-2.5 px-3 text-right font-mono font-bold text-emerald-700">
                {{ formatCurrency(rec.unobligated) }}
              </td>

              <!-- Dynamic Unpaid Balance -->
              <td class="py-2.5 px-3 text-right font-mono font-bold text-amber-700">
                {{ formatCurrency(rec.unpaid) }}
              </td>

              <!-- Actions (Edit & Soft-Delete) -->
              <td class="py-2.5 px-3 text-center">
                <div class="inline-flex items-center space-x-1">
                  <button
                    @click="openEditModal(rec)"
                    class="p-1 text-slate-400 hover:text-blue-600 transition"
                    title="Edit Record"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>

                  <button
                    @click="confirmSoftDelete(rec)"
                    class="p-1 text-slate-400 hover:text-red-600 transition"
                    title="Soft Delete"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination Footer -->
      <div class="p-3.5 bg-slate-50 border-t border-slate-200 flex flex-col sm:flex-row justify-between items-center text-xs text-slate-500 gap-3">
        <div>
          Showing <span class="font-bold text-slate-700">{{ recordsStore.records.length }}</span> of
          <span class="font-bold text-slate-700">{{ recordsStore.total }}</span> records
        </div>

        <div class="flex items-center space-x-2">
          <button
            :disabled="recordsStore.currentPage <= 1"
            @click="recordsStore.setPage(recordsStore.currentPage - 1)"
            class="px-2.5 py-1 bg-white border border-slate-300 rounded hover:bg-slate-100 disabled:opacity-40"
          >
            Previous
          </button>
          <span>Page {{ recordsStore.currentPage }} of {{ recordsStore.totalPages }}</span>
          <button
            :disabled="recordsStore.currentPage >= recordsStore.totalPages"
            @click="recordsStore.setPage(recordsStore.currentPage + 1)"
            class="px-2.5 py-1 bg-white border border-slate-300 rounded hover:bg-slate-100 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
    </div>

    <!-- Record Create/Edit Modal -->
    <RecordModal
      :isOpen="isModalOpen"
      :record="selectedRecord"
      @close="isModalOpen = false"
      @saved="handleRecordSaved"
    />

    <!-- Soft Delete Confirmation Dialog -->
    <div v-if="deleteCandidate" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
      <div class="bms-card max-w-sm w-full p-5 bg-white shadow-xl">
        <h4 class="text-sm font-bold text-slate-800 mb-2">Confirm Soft Deletion</h4>
        <p class="text-xs text-slate-500 mb-4">
          Are you sure you want to soft-delete this transaction line? The row will be archived and retained for audit compliance.
        </p>
        <div class="flex justify-end space-x-2 text-xs">
          <button @click="deleteCandidate = null" class="px-3 py-1.5 border border-slate-300 rounded-lg text-slate-600 hover:bg-slate-50">
            Cancel
          </button>
          <button @click="executeSoftDelete" class="px-3 py-1.5 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700">
            Soft Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useRecordsStore } from '@/stores/records'
import RecordModal from '@/components/RecordModal.vue'
import apiClient from '@/api/client'

const authStore = useAuthStore()
const recordsStore = useRecordsStore()
const route = useRoute()
const router = useRouter()

const isModalOpen = ref(false)
const selectedRecord = ref(null)
const deleteCandidate = ref(null)
const divisions = ref([])
const operatingUnits = ref([])

const isSdoProper = (ou, div) => {
  if (!ou) return false
  if (div && ou === div) return true
  return ou.toLowerCase().startsWith('division of')
}

const loadDivisions = async () => {
  try {
    const res = await apiClient.get('/records/divisions')
    divisions.value = res.data || []
  } catch (err) {
    console.error('Failed to load divisions', err)
  }
}

const loadOperatingUnits = async () => {
  try {
    const params = {}
    if (recordsStore.filters.division) {
      params.division = recordsStore.filters.division
    }
    const res = await apiClient.get('/records/operating-units', { params })
    operatingUnits.value = res.data || []
  } catch (err) {
    console.error('Failed to load operating units', err)
  }
}

const syncRouteFilters = () => {
  // CRITICAL: Always reset all filters to clean state first.
  // This guarantees that clicking "Inspect", "View", or switching between dashboards
  // never leaves stale school or division filters from a previous view.
  recordsStore.filters.skip = 0
  recordsStore.filters.limit = 25
  recordsStore.filters.search = route.query.search ? String(route.query.search) : ''
  recordsStore.filters.allotment_class = route.query.allotment_class ? String(route.query.allotment_class) : ''
  recordsStore.filters.fund_source = route.query.fund_source ? String(route.query.fund_source) : ''
  recordsStore.filters.account_code = route.query.account_code ? String(route.query.account_code) : ''
  recordsStore.filters.operating_unit = route.query.operating_unit ? String(route.query.operating_unit) : ''
  recordsStore.filters.division = route.query.division ? String(route.query.division) : ''
  recordsStore.filters.region = route.query.region ? String(route.query.region) : ''
}

const handleDivisionChange = async () => {
  // When division changes, reset school filter because the school belongs to previous division
  recordsStore.filters.operating_unit = ''
  recordsStore.filters.skip = 0
  await loadOperatingUnits()
  await recordsStore.fetchRecords()
}

const handleResetFilters = async () => {
  recordsStore.resetFilters()
  // Clean URL query
  await router.replace({ path: '/records' })
  await loadOperatingUnits()
}

let debounceTimer = null
const handleFilterChange = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    recordsStore.filters.skip = 0
    recordsStore.fetchRecords()
  }, 300)
}

const openCreateModal = () => {
  selectedRecord.value = null
  isModalOpen.value = true
}

const openEditModal = (rec) => {
  selectedRecord.value = rec
  isModalOpen.value = true
}

const handleRecordSaved = () => {
  recordsStore.fetchRecords()
}

const confirmSoftDelete = (rec) => {
  deleteCandidate.value = rec
}

const executeSoftDelete = async () => {
  if (deleteCandidate.value) {
    await recordsStore.deleteRecord(deleteCandidate.value.id)
    deleteCandidate.value = null
  }
}

const formatCurrency = (val) => {
  return new Intl.NumberFormat('en-PH', { style: 'currency', currency: 'PHP' }).format(val || 0)
}

watch(
  () => route.query,
  async () => {
    syncRouteFilters()
    await loadOperatingUnits()
    recordsStore.fetchRecords()
  }
)

onMounted(async () => {
  syncRouteFilters()
  await Promise.all([
    loadDivisions(),
    loadOperatingUnits(),
  ])
  recordsStore.fetchRecords()
})
</script>

