import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import StoryView from '../views/StoryView.vue'
import MainView from '../views/MainView.vue'

const router = createRouter({
  // Use hash mode for Electron compatibility
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: MainView,
    },
    {
      path: '/about',
      name: 'about',
      // route level code-splitting
      // this generates a separate chunk (About.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('../views/AboutView.vue'),
    },
    {
      path: '/story',
      name: 'story',
      component: StoryView,
    },
  ],
})

export default router
