<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-extrabold text-slate-900 tracking-tight">Upload & Consolidate tempTable Files</h1>
      <p class="text-xs text-slate-500 mt-0.5">
        Upload single school files or multi-file batches. The system validates headers, deduplicates rows via SHA-256 signatures, and scopes data to
        <span class="font-semibold text-deped-blue">{{ authStore.userScopeDescription }}</span>.
      </p>
    </div>

    <!-- Dropzone Area -->
    <div
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
      class="bms-card p-8 border-2 border-dashed text-center transition-all duration-200 cursor-pointer"
      :class="isDragging ? 'border-deped-blue bg-blue-50/50 ring-4 ring-blue-50' : 'border-slate-300 hover:border-slate-400 bg-white'"
      @click="$refs.fileInput.click()"
    >
      <input
        ref="fileInput"
        type="file"
        multiple
        accept=".xlsx,.xlsm"
        class="hidden"
        @change="handleFileSelect"
      />

      <div class="w-14 h-14 bg-blue-50 text-deped-blue rounded-full flex items-center justify-center mx-auto mb-3 shadow-inner">
        <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
      </div>
      <h3 class="text-sm font-bold text-slate-700 mb-1">Drag and drop tempTable files here, or click to browse</h3>
      <p class="text-xs text-slate-400">Accepts Microsoft Excel workbooks (.xlsx, .xlsm) with the 'Combine Sheet' template</p>
    </div>

    <!-- Selected Files Queue -->
    <div v-if="files.length > 0" class="bms-card p-5 bg-white space-y-4">
      <div class="flex justify-between items-center pb-3 border-b border-slate-100">
        <h4 class="text-xs font-bold uppercase tracking-wider text-slate-600">
          Selected Files for Consolidation ({{ files.length }})
        </h4>
        <button @click="files = []" class="text-xs text-red-500 hover:text-red-700 font-medium">Clear All</button>
      </div>

      <div class="divide-y divide-slate-100 max-h-56 overflow-y-auto">
        <div v-for="(f, idx) in files" :key="idx" class="py-2 flex justify-between items-center text-xs">
          <div class="flex items-center space-x-2 truncate">
            <span class="font-medium text-slate-700 truncate max-w-md">{{ f.name }}</span>
            <span class="text-slate-400 text-[10px]">({{ formatFileSize(f.size) }})</span>
          </div>
          <button @click="removeFile(idx)" class="text-slate-400 hover:text-red-500 font-bold px-2">&times;</button>
        </div>
      </div>

      <!-- Action Button -->
      <div class="pt-2 flex justify-end">
        <button
          @click="startUpload"
          :disabled="uploading"
          class="px-5 py-2.5 bg-deped-blue hover:bg-blue-900 text-white text-xs font-semibold rounded-lg shadow-sm transition disabled:opacity-50 flex items-center space-x-2"
        >
          <span v-if="!uploading">Consolidate & Upload Files</span>
          <span v-else class="flex items-center space-x-2">
            <svg class="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            <span>Ingesting & Deduplicating...</span>
          </span>
        </button>
      </div>
    </div>

    <!-- Upload Summary Results Banner -->
    <div v-if="uploadResult" class="bms-card p-6 bg-white space-y-5">
      <div class="flex items-center space-x-2 text-emerald-700">
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
        </svg>
        <h4 class="text-sm font-bold text-slate-800">Consolidation Ingestion Complete</h4>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center text-xs">
        <div class="p-3 bg-slate-50 rounded-lg border border-slate-200">
          <span class="block text-slate-400 text-[10px] uppercase font-bold">Total Rows Read</span>
          <span class="text-base font-extrabold text-slate-800 font-mono">{{ uploadResult.overall_summary.total_rows_read }}</span>
        </div>
        <div class="p-3 bg-emerald-50 rounded-lg border border-emerald-200">
          <span class="block text-emerald-600 text-[10px] uppercase font-bold">New Rows Inserted</span>
          <span class="text-base font-extrabold text-emerald-700 font-mono">{{ uploadResult.overall_summary.total_inserted }}</span>
        </div>
        <div class="p-3 bg-amber-50 rounded-lg border border-amber-200">
          <span class="block text-amber-600 text-[10px] uppercase font-bold">Duplicates Skipped</span>
          <span class="text-base font-extrabold text-amber-700 font-mono">{{ uploadResult.overall_summary.total_duplicates_skipped }}</span>
        </div>
        <div class="p-3 bg-rose-50 rounded-lg border border-rose-200">
          <span class="block text-rose-600 text-[10px] uppercase font-bold">Out of Scope Skipped</span>
          <span class="text-base font-extrabold text-rose-700 font-mono">{{ uploadResult.overall_summary.total_skipped_out_of_scope }}</span>
        </div>
      </div>

      <!-- File Details Table -->
      <div>
        <h5 class="text-xs font-bold text-slate-600 mb-2">File Breakdown</h5>
        <div class="overflow-x-auto border border-slate-100 rounded-lg">
          <table class="w-full text-left text-xs">
            <thead class="bg-slate-50 text-slate-500 uppercase text-[10px]">
              <tr>
                <th class="py-2 px-3">File Name</th>
                <th class="py-2 px-3 text-right">Rows</th>
                <th class="py-2 px-3 text-right text-emerald-700">Inserted</th>
                <th class="py-2 px-3 text-right text-amber-700">Duplicates</th>
                <th class="py-2 px-3 text-center">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="(item, idx) in uploadResult.file_details" :key="idx">
                <td class="py-2 px-3 font-medium text-slate-700">{{ item.filename }}</td>
                <td class="py-2 px-3 text-right font-mono">{{ item.total_rows || 0 }}</td>
                <td class="py-2 px-3 text-right font-mono font-semibold text-emerald-700">{{ item.inserted || 0 }}</td>
                <td class="py-2 px-3 text-right font-mono font-semibold text-amber-700">{{ item.duplicates_skipped || 0 }}</td>
                <td class="py-2 px-3 text-center">
                  <span
                    class="px-2 py-0.5 rounded text-[10px] font-bold uppercase"
                    :class="item.status === 'success' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'"
                  >
                    {{ item.status }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="pt-2 flex justify-end">
        <router-link
          to="/records"
          class="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold rounded-lg shadow-sm transition"
        >
          View Updated Records Table &rarr;
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/api/client'

const authStore = useAuthStore()

const files = ref([])
const isDragging = ref(false)
const uploading = ref(false)
const uploadResult = ref(null)

const handleDrop = (e) => {
  isDragging.value = false
  if (e.dataTransfer.files) {
    addFiles(e.dataTransfer.files)
  }
}

const handleFileSelect = (e) => {
  if (e.target.files) {
    addFiles(e.target.files)
  }
}

const addFiles = (selectedFiles) => {
  for (const f of selectedFiles) {
    if (f.name.toLowerCase().endsWith('.xlsx') || f.name.toLowerCase().endsWith('.xlsm')) {
      files.value.push(f)
    }
  }
}

const removeFile = (idx) => {
  files.value.splice(idx, 1)
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const startUpload = async () => {
  if (files.value.length === 0) return
  uploading.value = true
  uploadResult.value = null

  try {
    const formData = new FormData()
    for (const f of files.value) {
      formData.append('files', f)
    }

    const response = await apiClient.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    uploadResult.value = response.data
    files.value = []
  } catch (err) {
    alert(err.response?.data?.detail || 'Upload failed.')
  } finally {
    uploading.value = false
  }
}
</script>
