<script setup lang="ts">
import { onMounted } from 'vue'
import { useSummaryStore } from '@/stores/summaries'
import SummaryCard from '@/components/SummaryCard.vue'
import FileUpload from '@/components/FileUpload.vue'

const store = useSummaryStore()

onMounted(() => store.fetchPage())

async function onDelete(id: number) {
  if (confirm('Delete this summary?')) {
    await store.deleteSummary(id)
  }
}
</script>

<template>
  <div class="space-y-8">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-100">Document Library</h1>
        <p class="text-sm text-gray-500 mt-1">{{ store.total }} document{{ store.total !== 1 ? 's' : '' }} summarized</p>
      </div>
    </div>

    <FileUpload />

    <div v-if="store.loading" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="n in 6" :key="n" class="card animate-pulse h-44 bg-gray-800/50" />
    </div>

    <div v-else-if="store.error" class="text-center py-16 text-red-400">
      <p class="text-4xl mb-3">⚠️</p>
      <p>{{ store.error }}</p>
      <button class="btn-primary mt-4" @click="store.fetchPage()">Retry</button>
    </div>

    <div v-else-if="!store.items.length" class="text-center py-16 text-gray-600">
      <p class="text-5xl mb-4">📂</p>
      <p class="text-lg font-medium text-gray-500">No documents yet</p>
      <p class="text-sm mt-1">Upload a file above or drop one into the watch folder</p>
    </div>

    <div v-else class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <SummaryCard
        v-for="summary in store.items"
        :key="summary.id"
        :summary="summary"
        @delete="onDelete"
      />
    </div>

    <div v-if="store.total > store.pageSize" class="flex justify-center gap-2 pt-4">
      <button
        class="btn-ghost"
        :disabled="store.currentPage <= 1"
        @click="store.fetchPage(store.currentPage - 1)"
      >← Prev</button>
      <span class="px-4 py-2 text-sm text-gray-400">Page {{ store.currentPage }}</span>
      <button
        class="btn-ghost"
        :disabled="store.currentPage * store.pageSize >= store.total"
        @click="store.fetchPage(store.currentPage + 1)"
      >Next →</button>
    </div>
  </div>
</template>
