// frontend/src/tag-me.js

/**
 * Django Tag-Me - Alpine.js Multi-Select Component
 * 
 * Requires Alpine.js to be loaded globally before this script.
 * Alpine.js should be available as window.Alpine.
 */

// Import styles
import './css/tag-me.css'

// Import component modules
import { CookieManager } from './js/cookie-manager.js'
import { createAlpineComponent } from './js/alpine-component.js'

// Make CookieManager available globally for backward compatibility
if (typeof window !== 'undefined') {
	window.getCookie = (name) => CookieManager.get(name)
}

// Register component with Alpine.js
if (typeof window !== 'undefined') {
	console.log('🔍 Tag-Me: Initializing...')

	const registerComponent = () => {
		if (typeof window.Alpine !== 'undefined' && window.Alpine.data) {
			window.Alpine.data('alpineTagMeMultiSelect', createAlpineComponent)
			console.log('✅ Django Tag-Me component registered with Alpine.js')
			return true
		}
		return false
	}

	// Try immediate registration (if Alpine already loaded)
	if (!registerComponent()) {
		console.log('⏳ Waiting for Alpine.js to initialize...')

		// Wait for Alpine to initialize
		document.addEventListener('alpine:init', () => {
			console.log('🎯 alpine:init event received')
			if (registerComponent()) {
				console.log('✅ Registration complete')
			} else {
				console.error('❌ Alpine.js found but registration failed')
			}
		})

		// Timeout fallback - warn if Alpine never loads
		setTimeout(() => {
			if (typeof window.Alpine === 'undefined') {
				console.error(
					'❌ Alpine.js not detected after 5 seconds.\n' +
					'Please ensure Alpine.js is loaded before tag-me.\n' +
					'See: https://django-tag-me.readthedocs.io/installation/'
				)
			}
		}, 5000)
	}
}

// Export for module usage (harmless for IIFE)
export { CookieManager, createAlpineComponent }
