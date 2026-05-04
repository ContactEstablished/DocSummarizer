<template>
  <div class="min-h-screen flex flex-col">
    <header class="border-b border-gray-800 bg-gray-900/60 backdrop-blur-sm sticky top-0 z-50">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <RouterLink to="/" class="flex items-center gap-2.5 group">
          <span class="text-2xl">📄</span>
          <span class="font-semibold text-gray-100 group-hover:text-brand-400 transition-colors">
            DocSummarizer
          </span>
        </RouterLink>

        <nav class="flex items-center gap-1">
          <RouterLink to="/" class="btn-ghost" active-class="text-brand-400 bg-gray-800">
            Library
          </RouterLink>
          <RouterLink to="/search" class="btn-ghost" active-class="text-brand-400 bg-gray-800">
            Search
          </RouterLink>
        </nav>
      </div>
    </header>

    <main class="flex-1 max-w-6xl mx-auto w-full px-4 sm:px-6 py-8">
      <RouterView />
    </main>

    <footer class="border-t border-gray-800 py-6 text-center text-sm text-gray-600">
      DocSummarizer — powered by Claude
    </footer>
  </div>
</template>
