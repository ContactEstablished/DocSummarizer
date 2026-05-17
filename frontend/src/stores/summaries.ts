import { defineStore } from 'pinia'
import { ref } from 'vue'
import { summaryApi, type ListParams, type Summary, type TopicCount, type TemplateInfo } from '@/api/client'

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
  const topicFilter = ref<string>('')
  const starredOnly = ref(false)

  // Topics
  const topics = ref<TopicCount[]>([])

  // Prompt templates
  const templates = ref<TemplateInfo[]>([])
  const selectedTemplate = ref<string>(localStorage.getItem('ds_prompt_template') || 'default')

  function setTemplate(key: string) {
    selectedTemplate.value = key
    localStorage.setItem('ds_prompt_template', key)
  }

  async function fetchTemplates() {
    try {
      const { data } = await summaryApi.templates()
      templates.value = data
    } catch {
      // Non-critical — templates list just won't be populated
    }
  }

  async function fetchTopics() {
    try {
      const { data } = await summaryApi.topics()
      topics.value = data
    } catch {
      // Non-critical
    }
  }

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
      if (topicFilter.value) params.topic = topicFilter.value
      if (starredOnly.value) params.starred_only = true
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
    const template = selectedTemplate.value !== 'default' ? selectedTemplate.value : undefined
    const { data } = await summaryApi.upload(file, template)
    if (!items.value.find((s) => s.id === data.id)) {
      items.value.unshift(data)
      total.value += 1
    }
    return data
  }

  async function reSummarize(id: number, promptTemplate?: string): Promise<Summary> {
    const { data } = await summaryApi.reSummarize(id, promptTemplate)
    const idx = items.value.findIndex((s) => s.id === id)
    if (idx !== -1) items.value[idx] = data
    return data
  }

  async function toggleStar(id: number): Promise<Summary> {
    const { data } = await summaryApi.toggleStar(id)
    const idx = items.value.findIndex((s) => s.id === id)
    if (idx !== -1) items.value[idx] = data
    return data
  }

  return {
    items, total, currentPage, pageSize, loading, error,
    sort, order, fileTypeFilter, topicFilter, starredOnly,
    topics, templates, selectedTemplate,
    setTemplate, fetchTemplates, fetchTopics,
    fetchPage, deleteSummary, uploadFile, reSummarize, toggleStar,
  }
})
