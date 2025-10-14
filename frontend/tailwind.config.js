// frontend/tailwind.config.js
module.exports = {
	prefix: 'tm-',
	content: [
		'./src/**/*.{js,jsx,ts,tsx,css}',  // ← Added .css here
		'../tag_me/templates/**/*.html',
	],
	theme: {
		extend: {
			colors: {
				'tag-primary': '#4f46e5',
				'tag-primary-dark': '#4338ca',
				'tag-primary-light': '#eef2ff',
				'tag-secondary': '#6366f1',
				'tag-accent': '#818cf8',
			},
			borderRadius: {
				'tag': '9999px',
			},
			spacing: {
				'tag': '0.375rem',
			}
		},
	},
	plugins: [],
	// Can remove safelist now that we have @layer components
	safelist: [
		'tm-bg-indigo-50',
		'tm-bg-indigo-100',
		'tm-text-indigo-800',
		'tm-text-indigo-900',
		'tm-border-indigo-200',
		'tm-border-indigo-300',
	]
}
