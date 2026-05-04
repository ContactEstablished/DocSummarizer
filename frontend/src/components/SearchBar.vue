<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const query = ref('')

function submit() {
  if (query.value.trim()) {
    router.push({ path: '/search', query: { q: query.value.trim() } })
  }
}
</script>

<template>
  <form class="flex gap-2" @submit.prevent="submit">
    <input
      v-model="query"
      type="search"
      placeholder="Search summaries…"
      class="input flex-1"
    />
    <button type="submit" class="btn-primary">Search</button>
  </form>
</template>
