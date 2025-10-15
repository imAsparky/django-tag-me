// frontend/tailwind.config.js
module.exports = {
	prefix: 'tm-',
	content: [
		'./src/**/*.{js,jsx,ts,tsx,css}',
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
}
