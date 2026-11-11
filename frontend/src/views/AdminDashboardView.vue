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
          <p class="text-sm text-slate-300 mt-1 flex items-center gap-2">
            <span>Full System Access</span>
            <span>•</span>
            <span>User Provisioning • Dynamic Database Switcher • Global Audit</span>
          </p>
        </div>

        <div class="flex items-center gap-3">
          <router-link
            to="/users"
            class="px-4 py-2.5 bg-deped-gold hover:bg-yellow-500 text-deped-dark font-bold text-sm rounded-xl shadow-md transition flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            Manage 212 Accounts
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

    <!-- Quick Navigation Matrix -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div class="bms-card p-6 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition">
        <div class="w-10 h-10 rounded-lg bg-blue-50 text-deped-blue flex items-center justify-center font-bold mb-4">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
        </div>
        <h3 class="font-bold text-slate-900 text-lg">User Directory</h3>
        <p class="text-slate-600 text-sm mt-2">
          Manage 212 accounts: Regional Office, 16 SDOs, and 194 School Encoders.
        </p>
        <router-link to="/users" class="inline-flex items-center text-deped-blue hover:text-blue-800 font-semibold text-sm mt-4">
          Open User Management &rarr;
        </router-link>
      </div>

      <div class="bms-card p-6 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition">
        <div class="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold mb-4">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2 1.5 3 3.5 3h9c2 0 3.5-1 3.5-3V7c0-2-1.5-3-3.5-3h-9C5.5 4 4 5 4 7z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h4" />
          </svg>
        </div>
        <h3 class="font-bold text-slate-900 text-lg">Database Switcher</h3>
        <p class="text-slate-600 text-sm mt-2">
          Hot-swap the active database between local SQLite, MySQL/MariaDB, and Postgres.
        </p>
        <router-link to="/settings" class="inline-flex items-center text-emerald-700 hover:text-emerald-800 font-semibold text-sm mt-4">
          Database Settings &rarr;
        </router-link>
      </div>

      <div class="bms-card p-6 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition">
        <div class="w-10 h-10 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center font-bold mb-4">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 class="font-bold text-slate-900 text-lg">All Records</h3>
        <p class="text-slate-600 text-sm mt-2">
          Global access to all 208k+ transaction rows across the entire NCR region.
        </p>
        <router-link to="/records" class="inline-flex items-center text-amber-700 hover:text-amber-800 font-semibold text-sm mt-4">
          Open Global Table &rarr;
        </router-link>
      </div>

      <div class="bms-card p-6 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition">
        <div class="w-10 h-10 rounded-lg bg-purple-50 text-purple-700 flex items-center justify-center font-bold mb-4">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
        </div>
        <h3 class="font-bold text-slate-900 text-lg">System Ingestion</h3>
        <p class="text-slate-600 text-sm mt-2">
          Batch upload or verify benchmark files with deterministic SHA-256 deduplication.
        </p>
        <router-link to="/upload" class="inline-flex items-center text-purple-700 hover:text-purple-800 font-semibold text-sm mt-4">
          Open Ingestion &rarr;
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
</script>
