import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  headers: { 'Content-Type': 'application/json' },
})

export interface Summary {
  id: number
  file_name: string
  file_path: string
  file_type: string
  original_size_bytes: number
  content_hash: string
  summary_short: string
  summary_long: string
  key_topics: string[]
  created_at: string
  updated_at: string
}

export interface SummaryPage {
  items: Summary[]
  total: number
  page: number
  page_size: number
}

export interface ListParams {
  page?: number
  page_size?: number
  sort?: 'created_at' | 'file_name' | 'original_size_bytes'
  order?: 'asc' | 'desc'
  file_type?: string
}

export const summaryApi = {
  list: (params: ListParams = {}) =>
    api.get<SummaryPage>('/summaries', { params: { page: 1, page_size: 20, ...params } }),

  get: (id: number) =>
    api.get<Summary>(`/summaries/${id}`),

  delete: (id: number) =>
    api.delete(`/summaries/${id}`),

  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<Summary>('/summaries/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  reSummarize: (id: number) =>
    api.patch<Summary>(`/summaries/${id}/re-summarize`),

  ask: (id: number, question: string) =>
    api.post<{ answer: string }>(`/summaries/${id}/ask`, { question }),

  search: (q: string, page = 1, pageSize = 20) =>
    api.get<SummaryPage>('/search', { params: { q, page, page_size: pageSize } }),
}
