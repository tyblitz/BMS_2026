<template>
  <div class="space-y-6">
    <!-- Division Profile & Welcome Banner -->
    <div class="bg-gradient-to-r from-deped-dark via-slate-800 to-deped-blue rounded-2xl p-6 text-white shadow-lg">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-800/80 text-blue-200 text-xs font-semibold uppercase tracking-wider mb-2">
            <span class="w-2 h-2 rounded-full bg-blue-400"></span>
            Schools Division Office Workspace
          </div>
          <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight">
            {{ authStore.user?.division || 'Schools Division Office' }}
          </h1>
          <p class="text-sm text-blue-200 mt-1 flex items-center gap-2">
            <span>Division Consolidator Portal</span>
            <span>•</span>
            <span>{{ authStore.user?.region || 'National Capital Region (NCR)' }}</span>
          </p>
        </div>

        <div class="flex items-center gap-3">
          <router-link
            to="/upload"
            class="px-4 py-2.5 bg-deped-gold hover:bg-yellow-500 text-deped-dark font-bold text-sm rounded-xl shadow-md transition flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            Consolidate School Files
          </router-link>
          <router-link
            to="/records"
            class="px-4 py-2.5 bg-white/10 hover:bg-white/20 text-white font-medium text-sm rounded-xl transition flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            View Division Records
          </router-link>
        </div>
      </div>
    </div>

    <!-- Quick Workflow Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="bms-card p-6 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition">
        <div class="w-10 h-10 rounded-lg bg-blue-50 text-deped-blue flex items-center justify-center font-bold mb-4">
          1
        </div>
        <h3 class="font-bold text-slate-900 text-lg">Division Records</h3>
        <p class="text-slate-600 text-sm mt-2">
          Monitor all budget line items across all schools under {{ authStore.user?.division || 'your division' }}.
        </p>
        <router-link to="/records" class="inline-flex items-center text-deped-blue hover:text-blue-800 font-semibold text-sm mt-4">
          Browse Division Table &rarr;
        </router-link>
      </div>

      <div class="bms-card p-6 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition">
        <div class="w-10 h-10 rounded-lg bg-purple-50 text-purple-700 flex items-center justify-center font-bold mb-4">
          2
        </div>
        <h3 class="font-bold text-slate-900 text-lg">Batch Consolidation</h3>
        <p class="text-slate-600 text-sm mt-2">
          Drag and drop multiple school tempTable files to bulk-ingest and deduplicate division data.
        </p>
        <router-link to="/upload" class="inline-flex items-center text-purple-700 hover:text-purple-800 font-semibold text-sm mt-4">
          Upload Multi-Files &rarr;
        </router-link>
      </div>

      <div class="bms-card p-6 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition">
        <div class="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold mb-4">
          3
        </div>
        <h3 class="font-bold text-slate-900 text-lg">Export SDO Conso</h3>
        <p class="text-slate-600 text-sm mt-2">
          Export the consolidated 33-column Excel file ready for submission to the Regional Office.
        </p>
        <router-link to="/records" class="inline-flex items-center text-emerald-700 hover:text-emerald-800 font-semibold text-sm mt-4">
          Export Division Sheet &rarr;
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
</script>
