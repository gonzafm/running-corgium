import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/login': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/strava': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/auth/jwt': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/auth/register': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/users': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
