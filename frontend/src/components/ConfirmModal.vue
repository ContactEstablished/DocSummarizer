<script setup lang="ts">
defineProps<{
  title?: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
}>()

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
        @mousedown.self="emit('cancel')"
      >
        <Transition
          enter-active-class="transition duration-150 ease-out"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition duration-100 ease-in"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
          appear
        >
          <div class="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-sm p-6 space-y-4">
            <div>
              <h2 class="text-base font-semibold text-gray-100">
                {{ title ?? 'Are you sure?' }}
              </h2>
              <p class="mt-1.5 text-sm text-gray-400">{{ message }}</p>
            </div>

            <div class="flex justify-end gap-2 pt-1">
              <button class="btn-ghost" @click="emit('cancel')">
                {{ cancelLabel ?? 'Cancel' }}
              </button>
              <button
                class="btn-primary bg-red-700 hover:bg-red-600"
                @click="emit('confirm')"
              >
                {{ confirmLabel ?? 'Delete' }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
