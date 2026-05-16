import { defineStore } from 'pinia'
import { ref } from 'vue'
import { summaryApi, type ListParams, type Summary, type SummaryPage } from '@/api/client'

export const useSummaryStore = defineStore('summaries', () => {
  const items = ref<Summary[]>([])
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Sort & filter state
  const sort = ref<ListParams['sort']>('created_at')
  const order = ref<ListParams['order']>('desc')
  const fileTypeFilter = ref<string>('')

  async function fetchPage(page = 1) {
    loading.value = true
    error.value = null
    try {
      const params: ListParams = {
        page,
        page_size: pageSize.value,
        sort: sort.value,
        order: order.value,
      }
      if (fileTypeFilter.value) params.file_type = fileTypeFilter.value
      const { data } = await summaryApi.list(params)
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
    // Only prepend if not a duplicate (deduplicated items may already be in the list)
    if (!items.value.find((s) => s.id === data.id)) {
      items.value.unshift(data)
      total.value += 1
    }
    return data
  }

  async function reSummarize(id: number): Promise<Summary> {
    const { data } = await summaryApi.reSummarize(id)
    const idx = items.value.findIndex((s) => s.id === id)
    if (idx !== -1) items.value[idx] = data
    return data
  }

  return {
    items, total, currentPage, pageSize, loading, error,
    sort, order, fileTypeFilter,
    fetchPage, deleteSummary, uploadFile, reSummarize,
  }
})
