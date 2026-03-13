import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    host: true, // Expose to local network
    port: 5174,
  },
  define: {
    'process.env.VITE_API_BASE_URL': JSON.stringify('http://localhost:8000/api')
  }
})
