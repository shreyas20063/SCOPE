import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  define: {
    // Fix for plotly.js dependencies that check for Node.js globals
    global: 'globalThis',
  },
  resolve: {
    alias: {
      // Empty shims for Node.js built-ins used by plotly dependencies
      'buffer/': 'buffer',
    },
  },
  server: {
    port: 3001,
    open: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    // Enable minification for production
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,  // Remove console.log in production
        drop_debugger: true,
      },
    },
    // Code splitting configuration
    rollupOptions: {
      output: {
        // Manual chunk splitting for better caching
        manualChunks: {
          // Vendor chunks - rarely change, cache well
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-plotly': ['plotly.js', 'react-plotly.js'],
          'vendor-three': ['three'],
          'vendor-axios': ['axios'],
        },
      },
    },
    // Target modern browsers for smaller bundles
    target: 'es2020',
    // Generate source maps for debugging (can disable for smaller builds)
    sourcemap: false,
    // Chunk size warning threshold (in KB)
    chunkSizeWarningLimit: 1000,
  },
  // Optimize dependencies
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'axios'],
    // Exclude large libraries from pre-bundling (loaded on demand)
    exclude: ['three'],
  },
})
