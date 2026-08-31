import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// The site owner hosts sub-projects at paths on a personal domain, so the base
// path has to be settable at build time rather than assumed to be the root.
export default defineConfig({
  base: process.env.VITE_BASE ?? '/',
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: process.env.VITE_API ?? 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
