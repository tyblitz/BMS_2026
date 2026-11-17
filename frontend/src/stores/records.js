import { defineStore } from 'pinia'
import apiClient from '@/api/client'

export const useRecordsStore = defineStore('records', {
  state: () => ({
    records: [],
    total: 0,
    loading: false,
    error: null,
    kpis: {
      totalAllotment: 0,
      totalObligations: 0,
      totalDisbursements: 0,
      totalUnobligated: 0,
      totalUnpaid: 0,
      totalAdjustedAppro: 0,
      unreleased: 0,
    },
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
      appropriation_type: '',
      allotment_period: '',
      ppa_code: '',
    },
  }),

  getters: {
    totalPages: (state) => Math.ceil(state.total / state.filters.limit) || 1,
    currentPage: (state) => Math.floor(state.filters.skip / state.filters.limit) + 1,
    
    // Return scope-wide KPIs fetched from database aggregation
    summaryKPIs: (state) => state.kpis,
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

        // Fetch paginated records and scope-wide KPI summary concurrently
        const summaryParams = { ...params }
        delete summaryParams.skip
        delete summaryParams.limit

        const [recordsRes, summaryRes] = await Promise.all([
          apiClient.get('/records', { params }),
          apiClient.get('/analytics/records-summary', { params: summaryParams }).catch((e) => {
            console.warn('Could not fetch records summary:', e)
            return null
          })
        ])

        this.records = recordsRes.data.items || []
        this.total = recordsRes.data.total || 0

        if (summaryRes?.data) {
          this.kpis = {
            totalAllotment: summaryRes.data.total_allotment || 0,
            totalObligations: summaryRes.data.total_obligations || 0,
            totalDisbursements: summaryRes.data.total_disbursements || 0,
            totalUnobligated: summaryRes.data.total_unobligated || 0,
            totalUnpaid: summaryRes.data.total_unpaid || 0,
            totalAdjustedAppro: summaryRes.data.total_adjusted_appro || 0,
            unreleased: summaryRes.data.unreleased || 0,
          }
        }
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
        appropriation_type: '',
        allotment_period: '',
        ppa_code: '',
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
