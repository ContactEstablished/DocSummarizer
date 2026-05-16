<script setup lang="ts">
import { ref } from 'vue'
import { useSummaryStore } from '@/stores/summaries'

const store = useSummaryStore()
const dragging = ref(false)
const uploading = ref(false)
const toast = ref<{ message: string; type: 'success' | 'error' } | null>(null)

const ACCEPTED = '.pdf,.docx,.txt,.md'

let toastTimer: ReturnType<typeof setTimeout> | null = null

function showToast(message: string, type: 'success' | 'error') {
  if (toastTimer) clearTimeout(toastTimer)
  toast.value = { message, type }
  toastTimer = setTimeout(() => { toast.value = null }, 5000)
}

async function handleFiles(files: FileList | null) {
  if (!files?.length) return
  const fileArray = Array.from(files)
  uploading.value = true

  let succeeded = 0
  let failed = 0
  const errors: string[] = []

  for (const file of fileArray) {
    try {
      await store.uploadFile(file)
      succeeded++
    } catch (e: unknown) {
      failed++
      errors.push(`${file.name}: ${e instanceof Error ? e.message : 'Upload failed'}`)
    }
  }

  uploading.value = false

  if (fileArray.length === 1) {
    if (succeeded === 1) {
      showToast(`"${fileArray[0].name}" summarized successfully.`, 'success')
    } else {
      showToast(errors[0] ?? 'Upload failed — please try again.', 'error')
    }
  } else {
    if (failed === 0) {
      showToast(`All ${succeeded} files summarized successfully.`, 'success')
    } else if (succeeded === 0) {
      showToast(`All ${failed} files failed. ${errors[0]}`, 'error')
    } else {
      showToast(`${succeeded} succeeded, ${failed} failed. ${errors[0]}`, 'error')
    }
  }
}

function onDrop(e: DragEvent) {
  dragging.value = false
  handleFiles(e.dataTransfer?.files ?? null)
}
</script>

<template>
  <div class="space-y-3">
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
        multiple
        class="hidden"
        @change="handleFiles(($event.target as HTMLInputElement).files)"
      />

      <p v-if="uploading" class="text-brand-400 text-sm animate-pulse">
        Uploading &amp; summarizing…
      </p>
      <template v-else>
        <p class="text-3xl mb-2">📤</p>
        <p class="text-sm text-gray-400">Drop files here or click to browse</p>
        <p class="text-xs text-gray-600 mt-1">PDF, DOCX, TXT, MD · Multiple files supported</p>
      </template>
    </div>

    <!-- Toast notification -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 translate-y-1"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-1"
    >
      <div
        v-if="toast"
        class="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium"
        :class="toast.type === 'success'
          ? 'bg-emerald-900/40 border border-emerald-700/50 text-emerald-300'
          : 'bg-red-900/40 border border-red-700/50 text-red-300'"
      >
        <span>{{ toast.type === 'success' ? '✓' : '✕' }}</span>
        <span>{{ toast.message }}</span>
      </div>
    </Transition>
  </div>
</template>
