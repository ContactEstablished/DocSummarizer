import { defineStore } from 'pinia'
import { ref } from 'vue'
import { summaryApi, type Summary, type SummaryPage } from '@/api/client'

export const useSummaryStore = defineStore('summaries', () => {
  const items = ref<Summary[]>([])
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchPage(page = 1) {
    loading.value = true
    error.value = null
    try {
      const { data } = await summaryApi.list(page, pageSize.value)
      items.value = data.items
      total.value = data.total
      currentPage.value = data.page
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to load summaries'
    } finally {
      loading.value = false
    }
  }

  async function deleteSummary(id: number) {
    await summaryApi.delete(id)
    items.value = items.value.filter((s) => s.id !== id)
    total.value = Math.max(0, total.value - 1)
  }

  async function uploadFile(file: File): Promise<Summary> {
    const { data } = await summaryApi.upload(file)
    items.value.unshift(data)
    total.value += 1
    return data
  }

  return { items, total, currentPage, pageSize, loading, error, fetchPage, deleteSummary, uploadFile }
})
