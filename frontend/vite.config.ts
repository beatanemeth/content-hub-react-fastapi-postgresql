import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // The dev server forwards /api requests to FastAPI, so the browser sees one origin and the API needs no CORS
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
