<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { summaryApi, type Summary } from '@/api/client'
import { useSummaryStore } from '@/stores/summaries'

const props = defineProps<{ id: string }>()
const router = useRouter()
const store = useSummaryStore()

const summary = ref<Summary | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    const { data } = await summaryApi.get(Number(props.id))
    summary.value = data
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load summary'
  } finally {
    loading.value = false
  }
})

async function onDelete() {
  if (!summary.value) return
  if (confirm('Delete this summary?')) {
    await store.deleteSummary(summary.value.id)
    router.push('/')
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString()
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
</script>

<template>
  <div>
    <button class="btn-ghost mb-6" @click="router.back()">← Back</button>

    <div v-if="loading" class="space-y-4 animate-pulse">
      <div class="h-8 bg-gray-800 rounded w-1/2" />
      <div class="h-4 bg-gray-800 rounded w-full" />
      <div class="h-4 bg-gray-800 rounded w-3/4" />
    </div>

    <div v-else-if="error" class="text-center py-16 text-red-400">
      <p>{{ error }}</p>
    </div>

    <article v-else-if="summary" class="space-y-6 max-w-3xl">
      <div class="flex items-start justify-between gap-4">
        <h1 class="text-2xl font-bold text-gray-100 break-all">{{ summary.file_name }}</h1>
        <button class="btn-ghost text-red-500 hover:text-red-400 flex-shrink-0" @click="onDelete">
          Delete
        </button>
      </div>

      <div class="flex flex-wrap gap-2 text-xs text-gray-500">
        <span>{{ summary.file_type.toUpperCase() }}</span>
        <span>·</span>
        <span>{{ formatBytes(summary.original_size_bytes) }}</span>
        <span>·</span>
        <span>Added {{ formatDate(summary.created_at) }}</span>
      </div>

      <div class="flex flex-wrap gap-1.5">
        <span v-for="topic in summary.key_topics" :key="topic" class="badge">{{ topic }}</span>
      </div>

      <section>
        <h2 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">Short Summary</h2>
        <p class="text-gray-300 leading-relaxed">{{ summary.summary_short }}</p>
      </section>

      <section>
        <h2 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">Full Summary</h2>
        <div class="prose prose-invert prose-sm max-w-none text-gray-300 leading-relaxed">
          {{ summary.summary_long }}
        </div>
      </section>

      <section class="border-t border-gray-800 pt-4">
        <h2 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">File Details</h2>
        <dl class="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
          <dt class="text-gray-500">Path</dt>
          <dd class="text-gray-300 font-mono text-xs break-all">{{ summary.file_path }}</dd>
          <dt class="text-gray-500">Hash (SHA-256)</dt>
          <dd class="text-gray-300 font-mono text-xs break-all">{{ summary.content_hash }}</dd>
          <dt class="text-gray-500">Last updated</dt>
          <dd class="text-gray-300">{{ formatDate(summary.updated_at) }}</dd>
        </dl>
      </section>
    </article>
  </div>
</template>
