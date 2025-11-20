import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  build: {
    lib: {
      entry: resolve(__dirname, 'src/widget/main.js'),
      name: 'CustomerServiceWidget',
      fileName: 'chat-widget',
      formats: ['iife'],
    },
    outDir: 'dist/widget',
    emptyOutDir: false,
    rollupOptions: {
      output: {
        globals: {
          vue: 'Vue',
        },
      },
    },
  },
})


