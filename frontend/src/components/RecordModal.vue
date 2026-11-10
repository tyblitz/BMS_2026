<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto">
    <div class="bms-card max-w-4xl w-full bg-white max-h-[90vh] flex flex-col shadow-2xl">
      <!-- Modal Header -->
      <div class="px-6 py-4 border-b border-slate-200 flex justify-between items-center bg-slate-50 rounded-t-xl">
        <div>
          <h3 class="text-lg font-bold text-slate-800">
            {{ isEdit ? 'Edit Budget Line Transaction' : 'Encode New Budget Line Transaction' }}
          </h3>
          <p class="text-xs text-slate-500">All financial metrics and balance columns recalculate automatically.</p>
        </div>
        <button @click="$emit('close')" class="text-slate-400 hover:text-slate-600 text-xl font-bold p-1">&times;</button>
      </div>

      <!-- Live Calculated Balances Banner (Rule 1 Compliance: Previewed in UI, not saved in DB) -->
      <div class="px-6 py-3 bg-blue-50/70 border-b border-blue-100 grid grid-cols-2 sm:grid-cols-5 gap-2 text-center text-xs">
        <div class="p-2 bg-white rounded-lg border border-blue-200/80 shadow-xs">
          <span class="block text-slate-400 text-[10px] uppercase font-semibold">Total Adj. Appro</span>
          <span class="font-bold text-slate-700 font-mono">{{ formatCurrency(liveBalances.total_adjusted_appro) }}</span>
        </div>
        <div class="p-2 bg-white rounded-lg border border-blue-200/80 shadow-xs">
          <span class="block text-slate-400 text-[10px] uppercase font-semibold">Total Adj. Allotment</span>
          <span class="font-bold text-blue-700 font-mono">{{ formatCurrency(liveBalances.total_adjusted_allotment) }}</span>
        </div>
        <div class="p-2 bg-white rounded-lg border border-blue-200/80 shadow-xs">
          <span class="block text-slate-400 text-[10px] uppercase font-semibold">Unobligated Balance</span>
          <span class="font-bold text-emerald-700 font-mono">{{ formatCurrency(liveBalances.unobligated) }}</span>
        </div>
        <div class="p-2 bg-white rounded-lg border border-blue-200/80 shadow-xs">
          <span class="block text-slate-400 text-[10px] uppercase font-semibold">Unpaid Balance</span>
          <span class="font-bold text-amber-700 font-mono">{{ formatCurrency(liveBalances.unpaid) }}</span>
        </div>
        <div class="p-2 bg-white rounded-lg border border-blue-200/80 shadow-xs col-span-2 sm:col-span-1">
          <span class="block text-slate-400 text-[10px] uppercase font-semibold">Unreleased Appro</span>
          <span class="font-bold text-purple-700 font-mono">{{ formatCurrency(liveBalances.unreleased) }}</span>
        </div>
      </div>

      <!-- Form Body -->
      <form @submit.prevent="handleSave" class="p-6 overflow-y-auto space-y-5 flex-1">
        <!-- Error alert -->
        <div v-if="error" class="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-xs">
          {{ error }}
        </div>

        <!-- Section 1: Organizational & Classification Scope -->
        <div>
          <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2.5">1. Organization & Scoping</h4>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">Region *</label>
              <input
                v-model="form.region"
                type="text"
                required
                :disabled="authStore.isSchool || authStore.isSDO || authStore.isRegion"
                class="w-full text-xs px-3 py-2 border rounded-lg bg-slate-50 disabled:bg-slate-100 disabled:text-slate-500"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">Division *</label>
              <input
                v-model="form.division"
                type="text"
                required
                :disabled="authStore.isSchool || authStore.isSDO"
                class="w-full text-xs px-3 py-2 border rounded-lg bg-slate-50 disabled:bg-slate-100 disabled:text-slate-500"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">Operating Unit (School/Station) *</label>
              <input
                v-model="form.operating_unit"
                type="text"
                required
                :disabled="authStore.isSchool"
                class="w-full text-xs px-3 py-2 border rounded-lg bg-slate-50 disabled:bg-slate-100 disabled:text-slate-500"
              />
            </div>
          </div>
        </div>

        <!-- Section 2: Budget Classification & UACS -->
        <div>
          <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2.5">2. Classification & UACS Codes</h4>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">Allotment Class *</label>
              <select v-model="form.allotment_class" required class="w-full text-xs px-3 py-2 border rounded-lg bg-white">
                <option value="MOOE">MOOE (Maintenance & Other Operating)</option>
                <option value="PS">PS (Personnel Services)</option>
                <option value="CO">CO (Capital Outlay)</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">Account Code (UACS Object) *</label>
              <input v-model="form.account_code" type="text" required placeholder="e.g. 5020101000" class="w-full text-xs px-3 py-2 border rounded-lg" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">UACS PAP Code</label>
              <input v-model="form.uacs_pap_code" type="text" placeholder="e.g. 310400100003000" class="w-full text-xs px-3 py-2 border rounded-lg" />
            </div>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3.5 mt-3">
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">PPA Control (Program / Project)</label>
              <input v-model="form.ppa_control" type="text" placeholder="PPA350 - Operation of Schools..." class="w-full text-xs px-3 py-2 border rounded-lg" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">Fund Source</label>
              <input v-model="form.fund_source" type="text" placeholder="e.g. 101101" class="w-full text-xs px-3 py-2 border rounded-lg" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">Date BMS (Serial / Date)</label>
              <input v-model="form.date_bms" type="text" placeholder="e.g. 46027" class="w-full text-xs px-3 py-2 border rounded-lg" />
            </div>
          </div>
        </div>

        <!-- Section 3: Financial Figures -->
        <div>
          <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2.5">3. Financial Amounts (PHP)</h4>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">Appropriations</label>
              <input v-model.number="form.appropriations" type="number" step="0.01" class="w-full text-xs px-3 py-2 border rounded-lg font-mono text-right" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">Appro Adjust</label>
              <input v-model.number="form.appro_adjust" type="number" step="0.01" class="w-full text-xs px-3 py-2 border rounded-lg font-mono text-right" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">Allotment</label>
              <input v-model.number="form.allotment" type="number" step="0.01" class="w-full text-xs px-3 py-2 border rounded-lg font-mono text-right" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">Realignment</label>
              <input v-model.number="form.realignment" type="number" step="0.01" class="w-full text-xs px-3 py-2 border rounded-lg font-mono text-right" />
            </div>
          </div>

          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3.5 mt-3">
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">Transfer From</label>
              <input v-model.number="form.transfer_from" type="number" step="0.01" class="w-full text-xs px-3 py-2 border rounded-lg font-mono text-right" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1">Transfer To</label>
              <input v-model.number="form.transfer_to" type="number" step="0.01" class="w-full text-xs px-3 py-2 border rounded-lg font-mono text-right" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1 font-semibold text-blue-900">Obligations Incurred</label>
              <input v-model.number="form.obligations_incurred" type="number" step="0.01" class="w-full text-xs px-3 py-2 border rounded-lg font-mono text-right bg-blue-50/50" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-600 mb-1 font-semibold text-emerald-900">Disbursement</label>
              <input v-model.number="form.disbursement" type="number" step="0.01" class="w-full text-xs px-3 py-2 border rounded-lg font-mono text-right bg-emerald-50/50" />
            </div>
          </div>
        </div>

        <!-- Section 4: Narrative -->
        <div>
          <label class="block text-xs font-medium text-slate-600 mb-1">Particulars / Narrative</label>
          <textarea v-model="form.particulars" rows="2" placeholder="Description of expenditure, payee, check details..." class="w-full text-xs px-3 py-2 border rounded-lg"></textarea>
        </div>

        <!-- Modal Actions -->
        <div class="pt-4 border-t border-slate-200 flex justify-end space-x-3">
          <button
            type="button"
            @click="$emit('close')"
            class="px-4 py-2 border border-slate-300 text-slate-600 rounded-lg text-xs font-medium hover:bg-slate-50 transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            :disabled="saving"
            class="px-5 py-2 bg-deped-blue hover:bg-blue-900 text-white rounded-lg text-xs font-semibold shadow-sm transition disabled:opacity-50"
          >
            {{ saving ? 'Saving...' : (isEdit ? 'Update Transaction' : 'Save Transaction') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRecordsStore } from '@/stores/records'

const props = defineProps({
  isOpen: Boolean,
  record: Object,
})

const emit = defineEmits(['close', 'saved'])

const authStore = useAuthStore()
const recordsStore = useRecordsStore()

const isEdit = computed(() => !!props.record?.id)
const saving = ref(false)
const error = ref(null)

const defaultForm = () => ({
  region: authStore.user?.region || 'National Capital Region (NCR)',
  division: authStore.user?.division || 'Division of Caloocan',
  operating_unit: authStore.user?.school_name || '',
  allotment_class: 'MOOE',
  account_code: '',
  uacs_pap_code: '',
  ppa_control: '',
  fund_source: '101101',
  date_bms: '',
  appropriations: 0,
  appro_adjust: 0,
  allotment: 0,
  realignment: 0,
  transfer_from: 0,
  transfer_to: 0,
  obligations_incurred: 0,
  disbursement: 0,
  dv_amount: 0,
  particulars: '',
  locality: 'School',
  legal_basis: 'GAA 2026',
  rc: 'SCH-IU',
  reg: 'NA',
  ccet_code: 'NA',
  ledger: 'NA',
})

const form = ref(defaultForm())

watch(
  () => props.record,
  (newVal) => {
    if (newVal) {
      form.value = { ...defaultForm(), ...newVal }
    } else {
      form.value = defaultForm()
    }
  },
  { immediate: true }
)

// Live Reactive Calculation for Preview
const liveBalances = computed(() => {
  const appro = Number(form.value.appropriations || 0)
  const approAdj = Number(form.value.appro_adjust || 0)
  const allot = Number(form.value.allotment || 0)
  const realign = Number(form.value.realignment || 0)
  const transFrom = Number(form.value.transfer_from || 0)
  const transTo = Number(form.value.transfer_to || 0)
  const obli = Number(form.value.obligations_incurred || 0)
  const disb = Number(form.value.disbursement || 0)

  const totAdjAppro = appro + approAdj
  const totAdjAllot = allot + realign + transFrom - transTo
  const unobligated = totAdjAllot - obli
  const unpaid = obli - disb
  const unreleased = totAdjAppro - totAdjAllot

  return {
    total_adjusted_appro: totAdjAppro,
    total_adjusted_allotment: totAdjAllot,
    unobligated,
    unpaid,
    unreleased,
  }
})

const formatCurrency = (val) => {
  return new Intl.NumberFormat('en-PH', { style: 'currency', currency: 'PHP' }).format(val || 0)
}

const handleSave = async () => {
  saving.value = true
  error.value = null
  try {
    if (isEdit.value) {
      await recordsStore.updateRecord(props.record.id, form.value)
    } else {
      await recordsStore.createRecord(form.value)
    }
    emit('saved')
    emit('close')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to save record.'
  } finally {
    saving.value = false
  }
}
</script>

