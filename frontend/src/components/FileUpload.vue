<script setup lang="ts">
import { ref } from 'vue'
import { useSummaryStore } from '@/stores/summaries'

const store = useSummaryStore()
const dragging = ref(false)
const uploading = ref(false)
const uploadProgress = ref({ current: 0, total: 0 })
const toast = ref<{ message: string; type: 'success' | 'error' } | null>(null)

const ACCEPTED = '.pdf,.docx,.txt,.md'
const ACCEPTED_EXTENSIONS = new Set(['pdf', 'docx', 'txt', 'md'])

let toastTimer: ReturnType<typeof setTimeout> | null = null

function showToast(message: string, type: 'success' | 'error') {
  if (toastTimer) clearTimeout(toastTimer)
  toast.value = { message, type }
  toastTimer = setTimeout(() => { toast.value = null }, 5000)
}

function getExtension(name: string): string {
  return name.split('.').pop()?.toLowerCase() ?? ''
}

function isAcceptedFile(file: File): boolean {
  return ACCEPTED_EXTENSIONS.has(getExtension(file.name))
}

// ── Recursive folder reading via DataTransfer entries ───────────────────

function readEntryAsFile(entry: FileSystemFileEntry): Promise<File> {
  return new Promise((resolve, reject) => entry.file(resolve, reject))
}

function readDirectoryEntries(reader: FileSystemDirectoryReader): Promise<FileSystemEntry[]> {
  return new Promise((resolve, reject) => reader.readEntries(resolve, reject))
}

async function collectFilesFromEntry(entry: FileSystemEntry): Promise<File[]> {
  if (entry.isFile) {
    const file = await readEntryAsFile(entry as FileSystemFileEntry)
    return isAcceptedFile(file) ? [file] : []
  }
  if (entry.isDirectory) {
    const reader = (entry as FileSystemDirectoryEntry).createReader()
    const files: File[] = []
    // readEntries may return partial batches — loop until empty
    let batch: FileSystemEntry[]
    do {
      batch = await readDirectoryEntries(reader)
      for (const child of batch) {
        files.push(...await collectFilesFromEntry(child))
      }
    } while (batch.length > 0)
    return files
  }
  return []
}

async function collectFilesFromDataTransfer(dataTransfer: DataTransfer): Promise<File[]> {
  const items = Array.from(dataTransfer.items)
  const entries = items
    .map(item => item.webkitGetAsEntry?.())
    .filter((e): e is FileSystemEntry => e !== null && e !== undefined)

  // If we got entries (folder-capable browsers), use recursive traversal
  if (entries.length > 0) {
    const allFiles: File[] = []
    for (const entry of entries) {
      allFiles.push(...await collectFilesFromEntry(entry))
    }
    return allFiles
  }

  // Fallback: plain file list (no folder support in this browser)
  return Array.from(dataTransfer.files).filter(isAcceptedFile)
}

// ── Upload orchestration ────────────────────────────────────────────────

async function processFiles(files: File[]) {
  if (!files.length) return
  uploading.value = true
  uploadProgress.value = { current: 0, total: files.length }

  let succeeded = 0
  let failed = 0
  const errors: string[] = []

  for (const file of files) {
    uploadProgress.value.current++
    try {
      await store.uploadFile(file)
      succeeded++
    } catch (e: unknown) {
      failed++
      errors.push(`${file.name}: ${e instanceof Error ? e.message : 'Upload failed'}`)
    }
  }

  uploading.value = false

  if (files.length === 1) {
    if (succeeded === 1) {
      showToast(`"${files[0].name}" summarized successfully.`, 'success')
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

function handleFiles(files: FileList | null) {
  if (!files?.length) return
  processFiles(Array.from(files).filter(isAcceptedFile))
}

async function onDrop(e: DragEvent) {
  dragging.value = false
  if (!e.dataTransfer) return
  const files = await collectFilesFromDataTransfer(e.dataTransfer)
  processFiles(files)
}
</script>

<template>
  <div class="space-y-3">
    <div
      class="border-2 border-dashed rounded-xl p-8 text-center transition-colors duration-200"
      :class="dragging ? 'border-brand-500 bg-brand-900/10' : 'border-gray-700 hover:border-gray-600'"
      @dragover.prevent="dragging = true"
      @dragleave="dragging = false"
      @drop.prevent="onDrop"
    >
      <input
        ref="fileInput"
        type="file"
        :accept="ACCEPTED"
        multiple
        class="hidden"
        @change="handleFiles(($event.target as HTMLInputElement).files)"
      />
      <!-- Separate hidden input for folder selection (webkitdirectory) -->
      <input
        ref="folderInput"
        type="file"
        webkitdirectory
        class="hidden"
        @change="handleFiles(($event.target as HTMLInputElement).files)"
      />

      <div v-if="uploading" class="space-y-2">
        <p class="text-brand-400 text-sm animate-pulse">
          Summarizing {{ uploadProgress.current }} of {{ uploadProgress.total }}…
        </p>
        <div class="w-48 mx-auto h-1.5 bg-gray-800 rounded-full overflow-hidden">
          <div
            class="h-full bg-brand-500 rounded-full transition-all duration-300"
            :style="{ width: `${(uploadProgress.current / uploadProgress.total) * 100}%` }"
          />
        </div>
      </div>
      <template v-else>
        <p class="text-3xl mb-2">📤</p>
        <p class="text-sm text-gray-400">Drop files or folders here</p>
        <div class="flex items-center justify-center gap-3 mt-3">
          <button
            type="button"
            class="btn-ghost text-xs"
            @click.stop="($refs.fileInput as HTMLInputElement).click()"
          >Browse files</button>
          <span class="text-gray-700 text-xs">or</span>
          <button
            type="button"
            class="btn-ghost text-xs"
            @click.stop="($refs.folderInput as HTMLInputElement).click()"
          >Browse folder</button>
        </div>
        <p class="text-xs text-gray-600 mt-2">PDF, DOCX, TXT, MD · Folders scanned recursively</p>
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
