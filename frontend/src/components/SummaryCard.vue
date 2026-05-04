<script setup lang="ts">
import { RouterLink } from 'vue-router'
import type { Summary } from '@/api/client'

defineProps<{ summary: Summary }>()
defineEmits<{ delete: [id: number] }>()

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
</script>

<template>
  <article class="card flex flex-col gap-3 group">
    <div class="flex items-start justify-between gap-3">
      <div class="flex items-center gap-2 min-w-0">
        <span class="text-xl flex-shrink-0">{{ FILE_ICONS[summary.file_type] ?? '📄' }}</span>
        <RouterLink
          :to="`/summary/${summary.id}`"
          class="font-medium text-gray-100 hover:text-brand-400 truncate transition-colors"
        >
          {{ summary.file_name }}
        </RouterLink>
      </div>
      <button
        class="flex-shrink-0 text-gray-600 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
        title="Delete"
        @click="$emit('delete', summary.id)"
      >
        ✕
      </button>
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
