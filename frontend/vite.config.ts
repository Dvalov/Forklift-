import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'url'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/warehouse': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/converter': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
    },
  },
})
