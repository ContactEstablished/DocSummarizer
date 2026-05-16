<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useSummaryStore } from '@/stores/summaries'
import SummaryCard from '@/components/SummaryCard.vue'
import FileUpload from '@/components/FileUpload.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'

const store = useSummaryStore()
const pendingDeleteId = ref<number | null>(null)

onMounted(() => store.fetchPage())

// Re-fetch when sort/filter changes (reset to page 1)
watch([() => store.sort, () => store.order, () => store.fileTypeFilter], () => {
  store.fetchPage(1)
})

function requestDelete(id: number) {
  pendingDeleteId.value = id
}

async function confirmDelete() {
  if (pendingDeleteId.value === null) return
  await store.deleteSummary(pendingDeleteId.value)
  pendingDeleteId.value = null
}
</script>

<template>
  <div class="space-y-8">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-100">Document Library</h1>
        <p class="text-sm text-gray-500 mt-1">
          {{ store.total }} document{{ store.total !== 1 ? 's' : '' }} summarized
        </p>
      </div>
    </div>

    <FileUpload />

    <!-- Sort & filter toolbar -->
    <div class="flex flex-wrap items-center gap-3 text-sm">
      <!-- File type filter -->
      <div class="flex items-center gap-1.5">
        <label class="text-gray-500 text-xs uppercase tracking-wide">Type</label>
        <select
          v-model="store.fileTypeFilter"
          class="input py-1 text-sm"
        >
          <option value="">All</option>
          <option value="pdf">PDF</option>
          <option value="docx">DOCX</option>
          <option value="txt">TXT</option>
          <option value="md">MD</option>
        </select>
      </div>

      <div class="w-px h-4 bg-gray-700" />

      <!-- Sort field -->
      <div class="flex items-center gap-1.5">
        <label class="text-gray-500 text-xs uppercase tracking-wide">Sort</label>
        <select
          v-model="store.sort"
          class="input py-1 text-sm"
        >
          <option value="created_at">Date added</option>
          <option value="file_name">Name</option>
          <option value="original_size_bytes">File size</option>
        </select>
      </div>

      <!-- Sort direction -->
      <button
        class="btn-ghost py-1 px-2 text-xs flex items-center gap-1"
        :title="store.order === 'desc' ? 'Descending — click to switch' : 'Ascending — click to switch'"
        @click="store.order = store.order === 'desc' ? 'asc' : 'desc'"
      >
        <span>{{ store.order === 'desc' ? '↓' : '↑' }}</span>
        <span>{{ store.order === 'desc' ? 'Newest first' : 'Oldest first' }}</span>
      </button>
    </div>

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
        @delete="requestDelete"
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

  <ConfirmModal
    v-if="pendingDeleteId !== null"
    message="This summary will be permanently deleted and cannot be recovered."
    @confirm="confirmDelete"
    @cancel="pendingDeleteId = null"
  />
</template>
