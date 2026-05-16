<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { summaryApi, type Summary } from '@/api/client'
import { useSummaryStore } from '@/stores/summaries'
import ConfirmModal from '@/components/ConfirmModal.vue'

const props = defineProps<{ id: string }>()
const router = useRouter()
const store = useSummaryStore()

const summary = ref<Summary | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const showDeleteModal = ref(false)

// Re-summarize state
const reSummarizing = ref(false)
const reSummarizeError = ref<string | null>(null)

// Copy state
const copiedField = ref<string | null>(null)

// Q&A state
const question = ref('')
const answer = ref<string | null>(null)
const askLoading = ref(false)
const askError = ref<string | null>(null)

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

async function confirmDelete() {
  if (!summary.value) return
  await store.deleteSummary(summary.value.id)
  router.push('/')
}

async function reSummarize() {
  if (!summary.value) return
  reSummarizing.value = true
  reSummarizeError.value = null
  try {
    const updated = await store.reSummarize(summary.value.id)
    summary.value = updated
  } catch (e: unknown) {
    reSummarizeError.value = e instanceof Error ? e.message : 'Re-summarization failed'
  } finally {
    reSummarizing.value = false
  }
}

async function copyText(text: string, field: string) {
  try {
    await navigator.clipboard.writeText(text)
    copiedField.value = field
    setTimeout(() => { copiedField.value = null }, 2000)
  } catch {
    // Clipboard API not available
  }
}

function exportMarkdown() {
  if (!summary.value) return
  const s = summary.value
  const lines = [
    `# ${s.file_name}`,
    '',
    `**Type:** ${s.file_type.toUpperCase()}  `,
    `**Size:** ${formatBytes(s.original_size_bytes)}  `,
    `**Added:** ${formatDate(s.created_at)}`,
    '',
    `**Topics:** ${s.key_topics.join(', ')}`,
    '',
    '## Short Summary',
    '',
    s.summary_short,
    '',
    '## Full Summary',
    '',
    s.summary_long,
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${s.file_name.replace(/\.[^.]+$/, '')}-summary.md`
  a.click()
  URL.revokeObjectURL(url)
}

async function submitQuestion() {
  if (!summary.value || !question.value.trim()) return
  askLoading.value = true
  askError.value = null
  answer.value = null
  try {
    const { data } = await summaryApi.ask(summary.value.id, question.value.trim())
    answer.value = data.answer
  } catch (e: unknown) {
    askError.value = e instanceof Error ? e.message : 'Failed to get an answer'
  } finally {
    askLoading.value = false
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
      <!-- Header -->
      <div class="flex items-start justify-between gap-4">
        <h1 class="text-2xl font-bold text-gray-100 break-all">{{ summary.file_name }}</h1>
        <div class="flex items-center gap-2 flex-shrink-0">
          <button
            class="btn-ghost text-xs"
            title="Export as Markdown"
            @click="exportMarkdown"
          >⬇ Export</button>
          <button
            class="btn-ghost text-red-500 hover:text-red-400 text-xs"
            @click="showDeleteModal = true"
          >Delete</button>
        </div>
      </div>

      <!-- Metadata -->
      <div class="flex flex-wrap gap-2 text-xs text-gray-500">
        <span>{{ summary.file_type.toUpperCase() }}</span>
        <span>·</span>
        <span>{{ formatBytes(summary.original_size_bytes) }}</span>
        <span>·</span>
        <span>Added {{ formatDate(summary.created_at) }}</span>
      </div>

      <!-- Topics -->
      <div class="flex flex-wrap gap-1.5">
        <span v-for="topic in summary.key_topics" :key="topic" class="badge">{{ topic }}</span>
      </div>

      <!-- Short Summary -->
      <section>
        <div class="flex items-center justify-between mb-2">
          <h2 class="text-sm font-semibold text-gray-400 uppercase tracking-wide">Short Summary</h2>
          <button
            class="text-xs text-gray-600 hover:text-gray-400 transition-colors"
            @click="copyText(summary.summary_short, 'short')"
          >{{ copiedField === 'short' ? '✓ Copied' : '⎘ Copy' }}</button>
        </div>
        <p class="text-gray-300 leading-relaxed">{{ summary.summary_short }}</p>
      </section>

      <!-- Full Summary -->
      <section>
        <div class="flex items-center justify-between mb-2">
          <h2 class="text-sm font-semibold text-gray-400 uppercase tracking-wide">Full Summary</h2>
          <button
            class="text-xs text-gray-600 hover:text-gray-400 transition-colors"
            @click="copyText(summary.summary_long, 'long')"
          >{{ copiedField === 'long' ? '✓ Copied' : '⎘ Copy' }}</button>
        </div>
        <div class="text-gray-300 leading-relaxed whitespace-pre-wrap">{{ summary.summary_long }}</div>
      </section>

      <!-- Re-summarize -->
      <section class="border-t border-gray-800 pt-4">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-sm font-semibold text-gray-400 uppercase tracking-wide">Re-summarize</h2>
            <p class="text-xs text-gray-600 mt-0.5">Run Claude again on the same document text to get a fresh summary.</p>
          </div>
          <button
            class="btn-ghost text-xs flex-shrink-0"
            :disabled="reSummarizing"
            @click="reSummarize"
          >
            <span v-if="reSummarizing" class="animate-pulse">Running…</span>
            <span v-else>↻ Re-summarize</span>
          </button>
        </div>
        <p v-if="reSummarizeError" class="mt-2 text-xs text-red-400">{{ reSummarizeError }}</p>
      </section>

      <!-- Ask a Question -->
      <section class="border-t border-gray-800 pt-4 space-y-3">
        <h2 class="text-sm font-semibold text-gray-400 uppercase tracking-wide">Ask a Question</h2>
        <p class="text-xs text-gray-600">Ask Claude anything about this document based on its summary.</p>
        <form class="flex gap-2" @submit.prevent="submitQuestion">
          <input
            v-model="question"
            type="text"
            class="input flex-1 text-sm"
            placeholder="e.g. What are the key recommendations?"
            :disabled="askLoading"
          />
          <button
            type="submit"
            class="btn-primary text-sm flex-shrink-0"
            :disabled="askLoading || !question.trim()"
          >
            <span v-if="askLoading" class="animate-pulse">Thinking…</span>
            <span v-else>Ask</span>
          </button>
        </form>
        <div v-if="askError" class="text-xs text-red-400">{{ askError }}</div>
        <Transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="opacity-0 translate-y-1"
          enter-to-class="opacity-100 translate-y-0"
        >
          <div
            v-if="answer"
            class="bg-gray-800/60 border border-gray-700/50 rounded-lg p-4 text-sm text-gray-300 leading-relaxed whitespace-pre-wrap"
          >{{ answer }}</div>
        </Transition>
      </section>

      <!-- File Details -->
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

  <ConfirmModal
    v-if="showDeleteModal"
    :title="`Delete &quot;${summary?.file_name}&quot;?`"
    message="This summary will be permanently deleted and cannot be recovered."
    @confirm="confirmDelete"
    @cancel="showDeleteModal = false"
  />
</template>
