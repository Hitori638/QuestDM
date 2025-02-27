import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  base: process.env.ELECTRON ? './' : '/',
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  // Adjust for electron build if needed
  build: {
    outDir: 'dist_electron',
    emptyOutDir: true,
  },
  // Configure server for electron-dev environment
  server: {
    port: 5173,
    strictPort: true, // Ensure server uses the specified port
  }
})