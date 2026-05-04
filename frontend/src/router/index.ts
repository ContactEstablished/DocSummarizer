import { createRouter, createWebHistory } from 'vue-router'
import SummaryList from '@/views/SummaryList.vue'
import SummaryDetail from '@/views/SummaryDetail.vue'
import Search from '@/views/Search.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: SummaryList },
    { path: '/summary/:id', component: SummaryDetail, props: true },
    { path: '/search', component: Search },
  ],
})
