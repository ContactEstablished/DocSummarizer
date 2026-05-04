<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { summaryApi, type Summary } from '@/api/client'
import SummaryCard from '@/components/SummaryCard.vue'
import { useSummaryStore } from '@/stores/summaries'

const route = useRoute()
const router = useRouter()
const store = useSummaryStore()

const query = ref((route.query.q as string) ?? '')
const results = ref<Summary[]>([])
const total = ref(0)
const loading = ref(false)
const error = ref<string | null>(null)
const searched = ref(false)

async function doSearch(q: string) {
  if (!q.trim()) return
  loading.value = true
  error.value = null
  searched.value = true
  try {
    const { data } = await summaryApi.search(q)
    results.value = data.items
    total.value = data.total
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Search failed'
  } finally {
    loading.value = false
  }
}

function submit() {
  if (query.value.trim()) {
    router.push({ path: '/search', query: { q: query.value.trim() } })
  }
}

watch(() => route.query.q, (q) => {
  query.value = (q as string) ?? ''
  doSearch(query.value)
})

onMounted(() => {
  if (query.value) doSearch(query.value)
})
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-gray-100">Search</h1>

    <form class="flex gap-2" @submit.prevent="submit">
      <input v-model="query" type="search" placeholder="Search summaries, topics, filenames…" class="input flex-1" />
      <button type="submit" class="btn-primary" :disabled="loading">
        {{ loading ? 'Searching…' : 'Search' }}
      </button>
    </form>

    <p v-if="searched && !loading" class="text-sm text-gray-500">
      {{ total }} result{{ total !== 1 ? 's' : '' }} for <span class="text-gray-300">"{{ route.query.q }}"</span>
    </p>

    <div v-if="error" class="text-red-400 text-sm">{{ error }}</div>

    <div v-if="loading" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="n in 3" :key="n" class="card animate-pulse h-44 bg-gray-800/50" />
    </div>

    <div v-else-if="searched && !results.length" class="text-center py-12 text-gray-600">
      <p class="text-4xl mb-3">🔍</p>
      <p>No results found</p>
    </div>

    <div v-else class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <SummaryCard
        v-for="summary in results"
        :key="summary.id"
        :summary="summary"
        @delete="store.deleteSummary(summary.id).then(() => results = results.filter(r => r.id !== summary.id))"
      />
    </div>
  </div>
</template>
