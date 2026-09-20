import { defineConfig } from 'vite';

export default defineConfig({
  root: '.',
  server: {
    port: 5173,
    open: false,
    proxy: {
      // Proxy API calls to the FastAPI backend
      '/api': {
        target: 'http://127.0.0.1:1414',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:1414',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
});
