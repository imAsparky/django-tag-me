// frontend/src/js/alpine-component.js

import { CookieManager, base64Encode } from './cookie-manager.js'

/**
 * Creates the Alpine.js component for Tag-Me
 * @param {Object} obj - Configuration object
 * @returns {Object} Alpine component
 */
export function createAlpineComponent(obj) {
	return {
		// Configuration
		addTagURL: obj.addTagURL,
		elementId: obj.elementId,
		permittedToAddTags: obj.permittedToAddTags,
		allowMultipleSelect: obj.allowMultipleSelect,
		selected: obj.selected,
		autoSelectNewTags: obj.autoSelectNewTags,
		displayNumberSelected: obj.displayNumberSelected || 2,

		// State
		canAddNewTag: false,
		isCreatingTag: false,
		tagCreationError: null,
		options: [],
		selectedElms: [],
		show: false,
		menuShow: false,
		search: '',
		selectElement: null,
		allOptions: [],
		optionsByValue: new Map(),
		selectedIndexMap: new Map(),
		focusedIndex: -1,

		// Computed
		get displayedSelectedElms() {
			return this.selectedElms
				.filter(opt => opt.text)
				.slice(0, this.displayNumberSelected)
		},

		// Initialization
		init() {
			// Cache the select element
			this.selectElement = document.getElementById(this.elementId)
			const options = this.selectElement.options

			// Build options cache
			for (let i = 0; i < options.length; i++) {
				const option = {
					value: options[i].value,
					text: options[i].innerText,
					search: options[i].dataset.search,
					selected: Object.values(this.selected).includes(options[i].value)
				}
				this.allOptions.push(option)
				this.options.push(option)
				this.optionsByValue.set(option.value, option)

				if (option.selected) {
					this.selectedElms.push(option)
				}
			}

			this.updateSelectionMaps()

			// Watch search changes
			this.$watch('search', (searchTerm) => {
				this.performSearch(searchTerm)
			})
		},

		// UI Methods
		open() {
			this.show = true
			this.resetFocus()
		},

		close() {
			this.show = false
			this.menuShow = false
			this.resetFocus()
		},

		toggle() {
			this.show = !this.show
		},

		menuOpen() {
			this.menuShow = true
		},

		menuClose() {
			this.menuShow = false
		},

		menuToggle() {
			this.menuShow = !this.menuShow
		},

		// Search Methods
		performSearch(searchTerm) {
			if (searchTerm === '') {
				this.options = [...this.allOptions]
			} else {
				const reg = new RegExp(searchTerm, 'gi')
				this.options = this.allOptions.filter((option) => {
					return option.search.match(reg)
				})
			}
			this.canAddNewTag = this.options.length === 0
			this.resetFocus()
		},

		clearSearch() {
			this.search = ''
			this.tagCreationError = null
		},

		// Selection Methods
		select(index, event) {
			if (!this.allowMultipleSelect && this.selected.length === 1) {
				alert("You've reached the maximum number of selections!")
				return
			}

			const option = this.options[index]
			if (!option.selected) {
				option.selected = true
				option.element = event.target
				this.selected.push(option.value)
				this.selectedElms.push(option)

				const allOption = this.optionsByValue.get(option.value)
				if (allOption) {
					allOption.selected = true
				}

				this.selectedIndexMap.set(option.value, this.selectedElms.length - 1)
			} else {
				option.selected = false

				const selectedIndex = this.selected.indexOf(option.value)
				if (selectedIndex > -1) {
					this.selected.splice(selectedIndex, 1)
				}

				const elmIndex = this.selectedIndexMap.get(option.value)
				if (elmIndex !== undefined) {
					setTimeout(() => {
						this.selectedElms.splice(elmIndex, 1)
						this.updateSelectionMaps()
					}, 100)
				}

				const allOption = this.optionsByValue.get(option.value)
				if (allOption) {
					allOption.selected = false
				}
			}
		},

		remove(index, option) {
			this.selectedElms.splice(index, 1)

			const selectedIndex = this.selected.indexOf(option.value)
			if (selectedIndex > -1) {
				this.selected.splice(selectedIndex, 1)
			}

			const allOption = this.optionsByValue.get(option.value)
			if (allOption) {
				allOption.selected = false
			}

			this.options.forEach((opt) => {
				if (opt.value === option.value) {
					opt.selected = false
				}
			})

			this.updateSelectionMaps()
		},

		deselectTag() {
			setTimeout(() => {
				this.selected = []
				this.selectedElms = []
				this.selectedIndexMap.clear()

				this.allOptions.forEach((option) => {
					option.selected = false
				})

				this.options.forEach((option) => {
					option.selected = false
				})
			}, 100)
		},

		// Keyboard Navigation
		navigateDown() {
			if (this.options.length === 0) return
			this.focusedIndex = Math.min(this.focusedIndex + 1, this.options.length - 1)
		},

		navigateUp() {
			if (this.options.length === 0) return
			this.focusedIndex = Math.max(this.focusedIndex - 1, 0)
		},

		selectFocused() {
			if (this.focusedIndex >= 0 && this.focusedIndex < this.options.length) {
				const mockEvent = { target: null }
				this.select(this.focusedIndex, mockEvent)
			}
		},

		isFocused(index) {
			return this.focusedIndex === index
		},

		resetFocus() {
			this.focusedIndex = -1
		},

		// Tag Creation
		async createNewTag() {
			this.isCreatingTag = true
			this.tagCreationError = null
			this.canAddNewTag = false

			const selectElement = this.selectElement

			try {
				const response = await fetch(this.addTagURL, {
					method: 'POST',
					body: new URLSearchParams([
						['encoded_tag', base64Encode(this.search)],
						['csrfmiddlewaretoken', CookieManager.get('csrftoken')],
					]),
				})

				if (response.status === 200) {
					const data = await response.json()

					if (data.is_error) {
						throw new Error(data.error_message || 'Unknown server error occurred')
					}

					selectElement.innerHTML = ''
					data.tags.forEach(tag => {
						this.createOptionElementFromTag(selectElement, tag)
					})

					this.clearSearch()
					this.rebuildOptionsCache()
				} else {
					throw new Error(`HTTP ${response.status}: ${response.statusText}`)
				}
			} catch (error) {
				console.error('Tag creation failed:', error)
				this.tagCreationError = error.message || 'Failed to create tag. Please try again.'
				this.canAddNewTag = true
			} finally {
				this.isCreatingTag = false
			}
		},

		createOptionElementFromTag(selectElement, tag) {
			const addTag = String(tag).trim()
			const option = document.createElement('option')
			option.setAttribute('data-search', addTag)
			option.setAttribute('value', addTag)
			option.innerText = addTag
			selectElement.appendChild(option)
		},

		// Utilities
		updateSelectionMaps() {
			this.selectedIndexMap.clear()
			this.selectedElms.forEach((option, index) => {
				this.selectedIndexMap.set(option.value, index)
			})
		},

		rebuildOptionsCache() {
			this.allOptions = []
			this.options = []
			this.optionsByValue.clear()

			const options = this.selectElement.options
			for (let i = 0; i < options.length; i++) {
				const option = {
					value: options[i].value,
					text: options[i].innerText,
					search: options[i].dataset.search,
					selected: Object.values(this.selected).includes(options[i].value)
				}
				this.allOptions.push(option)
				this.options.push(option)
				this.optionsByValue.set(option.value, option)
			}

			if (this.search) {
				this.performSearch(this.search)
			}
		},

		selectedElements() {
			return this.options.filter(op => op.selected === true)
		},

		selectedValues() {
			return this.options.filter(op => op.selected === true).map(el => el.value)
		}
	}
}
