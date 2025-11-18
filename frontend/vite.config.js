// frontend/vite.config.js
import { defineConfig } from 'vite'
import path from 'path'
import { fileURLToPath } from 'url'
import tailwindcss from '@tailwindcss/vite'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const isProduction = process.env.NODE_ENV === 'production'

export default defineConfig({
  plugins: [
    tailwindcss(),  // ← NEW
  ],
  build: {
    lib: {
      entry: path.resolve(__dirname, 'src/tag-me.js'),
      name: 'DjangoTagMe',
      fileName: 'tag-me',
      formats: ['iife']
    },
    outDir: path.resolve(__dirname, '../tag_me/static/tag_me/dist'),
    emptyOutDir: true,
    target: 'es2022',
    rollupOptions: {
      external: [],
      onwarn(warning, warn) {
        if (warning.code === 'MODULE_LEVEL_DIRECTIVE') {
          return
        }
        warn(warning)
      },
      output: {
        globals: {},
        entryFileNames: 'js/[name].[hash].js',
        assetFileNames: (assetInfo) => {
          if (assetInfo.names && assetInfo.names.some(name => name.endsWith('.css'))) {
            return 'css/[name].[hash][extname]'
          }
          return '[name].[hash][extname]'
        },
        outro: `
          // Django Tag-Me initialization check
          if (typeof window !== 'undefined') {
            if (typeof window.Alpine === 'undefined') {
              console.error(
                '❌ Django Tag-Me requires Alpine.js. ' +
                'Please include Alpine.js before tag-me scripts. ' +
                'See: https://django-tag-me.readthedocs.io/installation/'
              );
            } else {
              console.log('✅ Django Tag-Me loaded successfully');
            }
          }
        `
      }
    },
    sourcemap: !isProduction,
    minify: isProduction ? 'terser' : false,
    terserOptions: isProduction ? {
      compress: {
        passes: 2,
        drop_console: true,
        drop_debugger: true
      }
    } : undefined,
    manifest: 'manifest.json'
  },
  css: {
    devSourcemap: !isProduction,
  },
  server: {
    port: 5175
  },
  esbuild: {
    target: 'es2022',
    drop: isProduction ? ['console', 'debugger'] : []
  },
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development')
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
