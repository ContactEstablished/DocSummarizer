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

export const summaryApi = {
  list: (page = 1, pageSize = 20) =>
    api.get<SummaryPage>('/summaries', { params: { page, page_size: pageSize } }),

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

  search: (q: string, page = 1, pageSize = 20) =>
    api.get<SummaryPage>('/search', { params: { q, page, page_size: pageSize } }),
}
