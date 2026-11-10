<template>
  <div class="max-w-6xl mx-auto space-y-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-extrabold text-slate-900 tracking-tight">User & Role Management</h1>
        <p class="text-xs text-slate-500 mt-0.5">
          Provision accounts and enforce organizational data boundaries for School, SDO, and Regional tiers.
        </p>
      </div>

      <button
        @click="openCreateModal"
        class="inline-flex items-center px-4 py-2 bg-deped-blue hover:bg-blue-900 text-white text-xs font-semibold rounded-lg shadow-sm transition"
      >
        <span class="mr-1.5 text-base leading-none">+</span> Provision New User
      </button>
    </div>

    <!-- Users Table Card -->
    <div class="bms-card bg-white overflow-hidden">
      <!-- Loading indicator -->
      <div v-if="loading" class="p-8 text-center text-xs text-slate-500">
        Loading user accounts...
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead>
            <tr class="bg-slate-50 text-slate-500 uppercase text-[10px] font-bold border-b border-slate-200">
              <th class="py-3 px-4">Username / Email</th>
              <th class="py-3 px-3 text-center">Assigned Role</th>
              <th class="py-3 px-4">Data Scope (School / Division / Region)</th>
              <th class="py-3 px-3 text-center">Status</th>
              <th class="py-3 px-3 text-center">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="u in users" :key="u.id" class="hover:bg-blue-50/30 transition">
              <!-- Username -->
              <td class="py-3 px-4">
                <span class="font-bold text-slate-800 block">{{ u.username }}</span>
                <span class="text-[10px] text-slate-400">{{ u.email || 'No email registered' }}</span>
              </td>

              <!-- Role Badge -->
              <td class="py-3 px-3 text-center">
                <span
                  class="px-2.5 py-1 rounded-full text-[10px] font-extrabold uppercase tracking-wider"
                  :class="{
                    'bg-emerald-100 text-emerald-800': u.role === 'school',
                    'bg-blue-100 text-blue-800': u.role === 'sdo',
                    'bg-purple-100 text-purple-800': u.role === 'region',
                    'bg-amber-100 text-amber-800': u.role === 'admin'
                  }"
                >
                  {{ u.role }}
                </span>
              </td>

              <!-- Data Scope -->
              <td class="py-3 px-4 text-xs">
                <div v-if="u.role === 'school'" class="text-slate-700">
                  <span class="font-semibold text-slate-900">{{ u.school_name || 'Unassigned School' }}</span>
                  <span class="text-[10px] text-slate-400 block">{{ u.division }} &bull; {{ u.region }}</span>
                </div>
                <div v-else-if="u.role === 'sdo'" class="text-slate-700">
                  <span class="font-semibold text-slate-900">{{ u.division || 'Unassigned Division' }}</span>
                  <span class="text-[10px] text-slate-400 block">{{ u.region }}</span>
                </div>
                <div v-else-if="u.role === 'region'" class="text-slate-700">
                  <span class="font-semibold text-slate-900">{{ u.region || 'Unassigned Region' }}</span>
                </div>
                <div v-else class="text-slate-400 italic">
                  Full System Scope (All Offices)
                </div>
              </td>

              <!-- Status -->
              <td class="py-3 px-3 text-center">
                <span
                  class="px-2 py-0.5 rounded text-[10px] font-bold"
                  :class="u.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-600'"
                >
                  {{ u.is_active ? 'Active' : 'Inactive' }}
                </span>
              </td>

              <!-- Actions -->
              <td class="py-3 px-3 text-center">
                <div class="inline-flex items-center space-x-2">
                  <button @click="openEditModal(u)" class="text-slate-400 hover:text-blue-600 p-1" title="Edit User">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    v-if="u.username !== 'admin'"
                    @click="deleteUser(u)"
                    class="text-slate-400 hover:text-red-600 p-1"
                    title="Soft Delete User"
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
    </div>

    <!-- User Modal (Create / Edit) -->
    <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
      <div class="bms-card max-w-lg w-full p-6 bg-white shadow-2xl">
        <div class="flex justify-between items-center pb-3 border-b border-slate-100 mb-4">
          <h3 class="text-base font-bold text-slate-800">{{ isEdit ? 'Edit User Account' : 'Provision User Account' }}</h3>
          <button @click="isModalOpen = false" class="text-slate-400 hover:text-slate-600 text-lg font-bold">&times;</button>
        </div>

        <form @submit.prevent="saveUser" class="space-y-4 text-xs">
          <div>
            <label class="block font-semibold text-slate-700 mb-1">Username *</label>
            <input v-model="form.username" type="text" required :disabled="isEdit" class="w-full px-3 py-2 border rounded-lg bg-slate-50 disabled:bg-slate-100" />
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">Email</label>
            <input v-model="form.email" type="email" class="w-full px-3 py-2 border rounded-lg" />
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">
              {{ isEdit ? 'Change Password (leave blank to keep current)' : 'Password *' }}
            </label>
            <input v-model="form.password" type="password" :required="!isEdit" class="w-full px-3 py-2 border rounded-lg" />
          </div>

          <div>
            <label class="block font-semibold text-slate-700 mb-1">Role *</label>
            <select v-model="form.role" required class="w-full px-3 py-2 border rounded-lg bg-white">
              <option value="school">School (Encoder / Station Level)</option>
              <option value="sdo">SDO (Division Consolidator)</option>
              <option value="region">Regional Office (Region Consolidator)</option>
              <option value="admin">System Administrator</option>
            </select>
          </div>

          <!-- Dynamic Scoping inputs -->
          <div v-if="form.role === 'school'" class="space-y-3 pt-2 border-t border-slate-100">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">School Name (Operating Unit) *</label>
              <input v-model="form.school_name" type="text" required placeholder="e.g. Amparo High School" class="w-full px-3 py-2 border rounded-lg" />
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block font-semibold text-slate-700 mb-1">Division *</label>
                <input v-model="form.division" type="text" required placeholder="Division of Caloocan" class="w-full px-3 py-2 border rounded-lg" />
              </div>
              <div>
                <label class="block font-semibold text-slate-700 mb-1">Region *</label>
                <input v-model="form.region" type="text" required placeholder="NCR" class="w-full px-3 py-2 border rounded-lg" />
              </div>
            </div>
          </div>

          <div v-else-if="form.role === 'sdo'" class="space-y-3 pt-2 border-t border-slate-100">
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block font-semibold text-slate-700 mb-1">Division *</label>
                <input v-model="form.division" type="text" required placeholder="Division of Caloocan" class="w-full px-3 py-2 border rounded-lg" />
              </div>
              <div>
                <label class="block font-semibold text-slate-700 mb-1">Region *</label>
                <input v-model="form.region" type="text" required placeholder="NCR" class="w-full px-3 py-2 border rounded-lg" />
              </div>
            </div>
          </div>

          <div v-else-if="form.role === 'region'" class="pt-2 border-t border-slate-100">
            <div>
              <label class="block font-semibold text-slate-700 mb-1">Region *</label>
              <input v-model="form.region" type="text" required placeholder="National Capital Region (NCR)" class="w-full px-3 py-2 border rounded-lg" />
            </div>
          </div>

          <div class="pt-4 border-t border-slate-100 flex justify-end space-x-2">
            <button type="button" @click="isModalOpen = false" class="px-4 py-2 border rounded-lg text-slate-600 hover:bg-slate-50">
              Cancel
            </button>
            <button type="submit" class="px-5 py-2 bg-deped-blue hover:bg-blue-900 text-white rounded-lg font-semibold shadow-sm">
              Save Account
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

const users = ref([])
const loading = ref(false)
const isModalOpen = ref(false)
const isEdit = ref(false)
const selectedUser = ref(null)

const defaultForm = () => ({
  username: '',
  email: '',
  password: '',
  role: 'school',
  school_name: '',
  division: '',
  region: 'National Capital Region (NCR)',
  is_active: true,
})

const form = ref(defaultForm())

const fetchUsers = async () => {
  loading.value = true
  try {
    const res = await apiClient.get('/users')
    users.value = res.data.items || []
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  isEdit.value = false
  selectedUser.value = null
  form.value = defaultForm()
  isModalOpen.value = true
}

const openEditModal = (u) => {
  isEdit.value = true
  selectedUser.value = u
  form.value = { ...u, password: '' }
  isModalOpen.value = true
}

const saveUser = async () => {
  try {
    if (isEdit.value) {
      await apiClient.put(`/users/${selectedUser.value.id}`, form.value)
    } else {
      await apiClient.post('/users', form.value)
    }
    isModalOpen.value = false
    await fetchUsers()
  } catch (err) {
    alert(err.response?.data?.detail || 'Failed to save user.')
  }
}

const deleteUser = async (u) => {
  if (confirm(`Are you sure you want to soft-delete user account '${u.username}'?`)) {
    try {
      await apiClient.delete(`/users/${u.id}`)
      await fetchUsers()
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete user.')
    }
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

