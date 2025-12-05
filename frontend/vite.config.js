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
    tailwindcss(),
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
        // Auto-register with Alpine.js after bundle loads
        outro: `
          (function() {
            if (typeof window === 'undefined') return;

            var COMPONENT_NAME = 'alpineTagMeMultiSelect';
            var registered = false;

            function registerWithAlpine() {
              if (registered) return true;

              if (typeof window.Alpine !== 'undefined' && typeof window.Alpine.data === 'function') {
                try {
                  window.Alpine.data(COMPONENT_NAME, exports.createAlpineComponent);
                  registered = true;
                  console.debug('✅ Django Tag-Me: Component registered with Alpine.js');
                  return true;
                } catch (e) {
                  console.error('❌ Django Tag-Me: Registration failed:', e);
                  return false;
                }
              }
              return false;
            }

            // Strategy 1: Alpine already loaded (try immediately)
            if (registerWithAlpine()) {
              return;
            }

            console.debug('⏳ Django Tag-Me: Waiting for Alpine.js...');

            // Strategy 2: Wait for alpine:init event
            document.addEventListener('alpine:init', function() {
              if (registerWithAlpine()) {
                console.debug('✅ Django Tag-Me: Registered via alpine:init');
              }
            });

            // Strategy 3: Wait for alpine:initialized event (fallback)
            document.addEventListener('alpine:initialized', function() {
              if (registerWithAlpine()) {
                console.debug('✅ Django Tag-Me: Registered via alpine:initialized');
              }
            });

            // Strategy 4: Polling fallback for edge cases
            var attempts = 0;
            var maxAttempts = 50;
            var pollInterval = setInterval(function() {
              attempts++;

              if (registerWithAlpine()) {
                clearInterval(pollInterval);
                return;
              }

              if (attempts >= maxAttempts) {
                clearInterval(pollInterval);
                if (typeof window.Alpine === 'undefined') {
                  console.error(
                    '❌ Django Tag-Me: Alpine.js not detected after 5 seconds.\\n' +
                    'Please ensure Alpine.js is loaded before or alongside tag-me.\\n' +
                    'See: https://django-tag-me.readthedocs.io/installation/'
                  );
                }
              }
            }, 100);
          })();
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

