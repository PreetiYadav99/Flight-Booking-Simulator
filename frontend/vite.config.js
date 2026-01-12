import { defineConfig } from 'vite'

export default defineConfig({
  base: './',
  build: {
    // increase warning threshold to avoid noisy warnings for slightly-large chunks
    chunkSizeWarningLimit: 800,
    rollupOptions: {
      output: {
        // basic manual chunking to separate vendor and large libs
        manualChunks: {
          vendor: ['react', 'react-dom'],
          helpers: ['html2canvas', 'jspdf']
        }
      }
    }
  }
})
