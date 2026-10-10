import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/signals': 'http://127.0.0.1:8000',
      '/analyze': 'http://127.0.0.1:8000',
      '/portfolio': 'http://127.0.0.1:8000',
      '/shock-table': 'http://127.0.0.1:8000',
      '/stress': 'http://127.0.0.1:8000',
      '/replay': 'http://127.0.0.1:8000',
      '/calibration': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
      '/presets': 'http://127.0.0.1:8000',
      '/themes': 'http://127.0.0.1:8000',
      '/scenarios': 'http://127.0.0.1:8000',
    },
  },
})
