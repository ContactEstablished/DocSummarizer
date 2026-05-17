<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import type { Summary } from '@/api/client'

const props = defineProps<{ summary: Summary }>()
defineEmits<{ delete: [id: number]; star: [id: number] }>()

const copied = ref(false)

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

const FILE_ICONS: Record<string, string> = {
  pdf: '📕',
  docx: '📘',
  txt: '📝',
  md: '📋',
}

async function copyShortSummary(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // Clipboard API not available (non-https, etc.)
  }
}
</script>

<template>
  <article class="card flex flex-col gap-3 group">
    <div class="flex items-start justify-between gap-3">
      <div class="flex items-center gap-2 min-w-0">
        <button
          :title="summary.is_starred ? 'Unstar' : 'Star'"
          class="text-lg flex-shrink-0 transition-transform hover:scale-110"
          @click="$emit('star', summary.id)"
        >{{ summary.is_starred ? '★' : '☆' }}</button>
        <RouterLink
          :to="`/summary/${summary.id}`"
          class="font-medium text-gray-100 hover:text-brand-400 truncate transition-colors"
        >
          {{ summary.file_name }}
        </RouterLink>
      </div>
      <div class="flex items-center gap-1.5 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          :title="copied ? 'Copied!' : 'Copy summary'"
          class="text-gray-600 hover:text-gray-400 transition-colors text-sm"
          @click.prevent="copyShortSummary(summary.summary_short)"
        >
          {{ copied ? '✓' : '⎘' }}
        </button>
        <button
          class="text-gray-600 hover:text-red-400 transition-colors"
          title="Delete"
          @click="$emit('delete', summary.id)"
        >
          ✕
        </button>
      </div>
    </div>

    <p class="text-sm text-gray-400 line-clamp-2">{{ summary.summary_short }}</p>

    <div class="flex flex-wrap gap-1.5">
      <span v-for="topic in summary.key_topics" :key="topic" class="badge">{{ topic }}</span>
    </div>

    <div class="flex items-center gap-3 text-xs text-gray-600 pt-1 border-t border-gray-800">
      <span>{{ formatDate(summary.created_at) }}</span>
      <span>·</span>
      <span>{{ formatBytes(summary.original_size_bytes) }}</span>
      <span>·</span>
      <span class="uppercase">{{ summary.file_type }}</span>
    </div>
  </article>
</template>
