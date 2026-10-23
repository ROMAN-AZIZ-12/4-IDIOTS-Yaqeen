import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const frontendPort = Number(process.env.PORT || process.env.FRONTEND_PORT || 5173)
const backendPort = Number(process.env.BACKEND_PORT || 8000)

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: frontendPort,
    strictPort: true,
    proxy: {
      '/api': {
        target: `http://127.0.0.1:${backendPort}`,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})