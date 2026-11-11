import { defineStore } from 'pinia'
import apiClient from '@/api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('bms_token') || null,
    user: JSON.parse(localStorage.getItem('bms_user') || 'null'),
    loading: false,
    error: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    userRole: (state) => state.user?.role || '',
    userScopeDescription: (state) => {
      if (!state.user) return ''
      if (state.user.role === 'school') return `School: ${state.user.school_name || 'N/A'}`
      if (state.user.role === 'sdo') return `SDO Division: ${state.user.division || 'N/A'}`
      if (state.user.role === 'region') return `Regional Office: ${state.user.region || 'N/A'}`
      if (state.user.role === 'admin') return 'System Administrator (Full Access)'
      return state.user.role
    },
    isAdmin: (state) => state.user?.role === 'admin',
    isSchool: (state) => state.user?.role === 'school',
    isSDO: (state) => state.user?.role === 'sdo',
    isRegion: (state) => state.user?.role === 'region',
  },

  actions: {
    async login(username, password) {
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.post('/auth/login', {
          username: String(username).trim(),
          password: String(password).trim(),
        })

        this.token = response.data.access_token
        this.user = response.data.user

        localStorage.setItem('bms_token', this.token)
        localStorage.setItem('bms_user', JSON.stringify(this.user))
        return true
      } catch (err) {
        const detail = err.response?.data?.detail
        if (Array.isArray(detail)) {
          this.error = detail.map((d) => d.msg || JSON.stringify(d)).join(', ')
        } else if (typeof detail === 'string') {
          this.error = detail
        } else {
          this.error = 'Login failed. Please check credentials.'
        }
        return false
      } finally {
        this.loading = false
      }
    },

    async fetchProfile() {
      if (!this.token) return
      try {
        const response = await apiClient.get('/auth/me')
        this.user = response.data
        localStorage.setItem('bms_user', JSON.stringify(this.user))
      } catch (err) {
        this.logout()
      }
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('bms_token')
      localStorage.removeItem('bms_user')
    },
  },
})

