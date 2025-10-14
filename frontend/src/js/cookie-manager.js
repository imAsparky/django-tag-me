// frontend/src/js/cookie-manager.js

/**
 * Optimized cookie handling with caching
 * Fix for issue-266
 */
export const CookieManager = {
	cache: new Map(),
	lastParsed: 0,

	parse() {
		const now = Date.now()
		// Re-parse only if cache is older than 1 second
		if (now - this.lastParsed > 1000) {
			this.cache.clear()
			if (document.cookie && document.cookie !== '') {
				document.cookie.split(';').forEach(cookie => {
					const trimmed = cookie.trim()
					const equalIndex = trimmed.indexOf('=')
					if (equalIndex > 0) {
						const name = trimmed.substring(0, equalIndex)
						const value = trimmed.substring(equalIndex + 1)
						this.cache.set(name, decodeURIComponent(value))
					}
				})
			}
			this.lastParsed = now
		}
	},

	get(name) {
		this.parse()
		return this.cache.get(name) || null
	}
}

/**
 * Base64 encoding utility
 * @param {Object} obj - Object to encode
 * @returns {string} Base64 encoded string
 */
export function base64Encode(obj) {
	return btoa(JSON.stringify(obj))
}
