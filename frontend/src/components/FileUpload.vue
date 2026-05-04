<script setup lang="ts">
import { ref } from 'vue'
import { useSummaryStore } from '@/stores/summaries'

const store = useSummaryStore()
const dragging = ref(false)
const uploading = ref(false)
const uploadError = ref<string | null>(null)

const ACCEPTED = '.pdf,.docx,.txt,.md'

async function handleFiles(files: FileList | null) {
  if (!files?.length) return
  uploading.value = true
  uploadError.value = null
  try {
    await store.uploadFile(files[0])
  } catch (e: unknown) {
    uploadError.value = e instanceof Error ? e.message : 'Upload failed'
  } finally {
    uploading.value = false
  }
}

function onDrop(e: DragEvent) {
  dragging.value = false
  handleFiles(e.dataTransfer?.files ?? null)
}
</script>

<template>
  <div
    class="border-2 border-dashed rounded-xl p-8 text-center transition-colors duration-200 cursor-pointer"
    :class="dragging ? 'border-brand-500 bg-brand-900/10' : 'border-gray-700 hover:border-gray-600'"
    @dragover.prevent="dragging = true"
    @dragleave="dragging = false"
    @drop.prevent="onDrop"
    @click="($refs.fileInput as HTMLInputElement).click()"
  >
    <input
      ref="fileInput"
      type="file"
      :accept="ACCEPTED"
      class="hidden"
      @change="handleFiles(($event.target as HTMLInputElement).files)"
    />

    <p v-if="uploading" class="text-brand-400 text-sm animate-pulse">Uploading &amp; summarizing…</p>
    <template v-else>
      <p class="text-3xl mb-2">📤</p>
      <p class="text-sm text-gray-400">Drop a file here or click to browse</p>
      <p class="text-xs text-gray-600 mt-1">PDF, DOCX, TXT, MD</p>
    </template>

    <p v-if="uploadError" class="text-red-400 text-xs mt-2">{{ uploadError }}</p>
  </div>
</template>
