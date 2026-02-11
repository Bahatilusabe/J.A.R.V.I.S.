import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import compression from 'vite-plugin-compression'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    compression({
      algorithm: 'brotli',
      ext: '.br',
    }),
    compression({
      algorithm: 'gzip',
      ext: '.gz',
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@services': path.resolve(__dirname, './src/services'),
      '@store': path.resolve(__dirname, './src/store'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@types': path.resolve(__dirname, './src/types'),
      '@assets': path.resolve(__dirname, './src/assets'),
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
        // Note: do NOT proxy top-level SPA routes like '/deception' to the backend.
        // The SPA defines a client-side route at /deception; proxying that path
        // caused Vite to forward the request to the backend (which returned 404).
        // Keep only API and websocket proxies here.
        // WebSocket proxy intentionally removed: backend currently does not expose
        // the WebSocket endpoints expected by the UI (e.g. /ws/self_healing).
        // If you later add a real WebSocket server on the backend, re-add the
        // proxy entry with ws: true and target pointing to that server.
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: process.env.VITE_SOURCEMAP === 'true',
    // Use esbuild for minification (faster and included by default). Avoid requiring terser as an extra dep.
    minify: 'esbuild',
    // When using esbuild, specify drop: 'console' via terserOptions isn't applicable; use esbuild options if needed.
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['d3', 'three', 'cytoscape'],
          'state': ['@reduxjs/toolkit', 'react-redux', '@tanstack/react-query'],
          // 'eventsource' is a Node server-side package and should not be bundled for the browser.
          // The browser provides a native EventSource implementation; keep socket.io-client only.
          'realtime': ['socket.io-client'],
        },
      },
    },
  },
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
  },
})
