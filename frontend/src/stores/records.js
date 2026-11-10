import { defineStore } from 'pinia'
import apiClient from '@/api/client'

export const useRecordsStore = defineStore('records', {
  state: () => ({
    records: [],
    total: 0,
    loading: false,
    error: null,
    filters: {
      skip: 0,
      limit: 25,
      search: '',
      allotment_class: '',
      fund_source: '',
      account_code: '',
      operating_unit: '',
      division: '',
      region: '',
    },
  }),

  getters: {
    totalPages: (state) => Math.ceil(state.total / state.filters.limit) || 1,
    currentPage: (state) => Math.floor(state.filters.skip / state.filters.limit) + 1,
    
    // Aggregated financial metrics for the current view
    summaryKPIs: (state) => {
      let totalAllotment = 0
      let totalObligations = 0
      let totalDisbursements = 0
      let totalUnobligated = 0
      let totalUnpaid = 0

      for (const r of state.records) {
        totalAllotment += parseFloat(r.total_adjusted_allotment || r.allotment || 0)
        totalObligations += parseFloat(r.obligations_incurred || 0)
        totalDisbursements += parseFloat(r.disbursement || 0)
        totalUnobligated += parseFloat(r.unobligated || 0)
        totalUnpaid += parseFloat(r.unpaid || 0)
      }

      return {
        totalAllotment,
        totalObligations,
        totalDisbursements,
        totalUnobligated,
        totalUnpaid,
      }
    },
  },

  actions: {
    async fetchRecords() {
      this.loading = true
      this.error = null
      try {
        const params = { ...this.filters }
        // Clean empty filter fields
        Object.keys(params).forEach((key) => {
          if (params[key] === '' || params[key] === null) {
            delete params[key]
          }
        })

        const response = await apiClient.get('/records', { params })
        this.records = response.data.items || []
        this.total = response.data.total || 0
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to fetch records.'
      } finally {
        this.loading = false
      }
    },

    setPage(page) {
      this.filters.skip = (page - 1) * this.filters.limit
      this.fetchRecords()
    },

    setLimit(newLimit) {
      this.filters.limit = newLimit
      this.filters.skip = 0
      this.fetchRecords()
    },

    resetFilters() {
      this.filters = {
        skip: 0,
        limit: 25,
        search: '',
        allotment_class: '',
        fund_source: '',
        account_code: '',
        operating_unit: '',
        division: '',
        region: '',
      }
      this.fetchRecords()
    },

    async createRecord(payload) {
      const response = await apiClient.post('/records', payload)
      await this.fetchRecords()
      return response.data
    },

    async updateRecord(id, payload) {
      const response = await apiClient.put(`/records/${id}`, payload)
      await this.fetchRecords()
      return response.data
    },

    async deleteRecord(id) {
      await apiClient.delete(`/records/${id}`)
      await this.fetchRecords()
    },

    async exportConsolidatedExcel() {
      const params = { ...this.filters }
      delete params.skip
      delete params.limit
      delete params.search

      const response = await apiClient.get('/export/excel', {
        params,
        responseType: 'blob',
      })

      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      })
      const link = document.createElement('a')
      link.href = window.URL.createObjectURL(blob)
      link.download = `CONSO_tempTable_${new Date().toISOString().slice(0, 10)}.xlsx`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    },
  },
})

