// Django Tag-Me Library - Combined JavaScript
// original code by https://github.com/alexpechkarev/alpinejs-multiselect/
// Optimized cookie handling with caching. Fix for issue-266
const CookieManager = {
	cache: new Map(),
	lastParsed: 0,
	parse() {
		const now = Date.now();
		// Re-parse only if cache is older than 1 second
		if (now - this.lastParsed > 1000) {
			this.cache.clear();
			if (document.cookie && document.cookie !== '') {
				document.cookie.split(';').forEach(cookie => {
					const trimmed = cookie.trim();
					const equalIndex = trimmed.indexOf('=');
					if (equalIndex > 0) {
						const name = trimmed.substring(0, equalIndex);
						const value = trimmed.substring(equalIndex + 1);
						this.cache.set(name, decodeURIComponent(value));
					}
				});
			}
			this.lastParsed = now;
		}
	},
	get(name) {
		this.parse();
		return this.cache.get(name) || null;
	}
};
// Backward compatibility - keep original function signature
function getCookie(name) {
	return CookieManager.get(name);
}

function base64Encode(obj) {
	return btoa(JSON.stringify(obj));
}
document.addEventListener("alpine:init", () => {
	function createOptionElementFromTag(selectElement, tag) {
		// Add tags directly to alpineTagMeMultiSelect
		// instead of creating <option> elements first
		let addTag = String(tag).trim()
		const option = document.createElement('option');
		option.setAttribute('data-search', addTag);
		option.setAttribute('value', addTag);
		option.innerText = addTag;
		selectElement.appendChild(option);
	}
	Alpine.data("alpineTagMeMultiSelect", (obj) => ({
		addTagURL: obj.addTagURL,
		elementId: obj.elementId,
		permittedToAddTags: obj.permittedToAddTags,
		allowMultipleSelect: obj.allowMultipleSelect,
		selected: obj.selected,
		canAddNewTag: false,
		autoSelectNewTags: obj.autoSelectNewTags,
		newTagsArray: [],
		isCreatingTag: false, // Track loading state for tag creation
		tagCreationError: null, // Store error messages
		options: [],
		selectedElms: [],
		show: false,
		menuShow: false,
		search: '',
		selectElement: null, // Cached DOM element
		allOptions: [], // Cache of all available options
		// Optimized data structures for O(1) lookups
		optionsByValue: new Map(), // Map of value -> option object for O(1) lookups
		selectedIndexMap: new Map(), // Map of value -> selectedElms array index for O(1) lookups
		focusedIndex: -1, // Track which option is currently focused for keyboard navigation
		// CSS configuration object (future: will come from Vite build)
		styles: obj.styles || {
			// Mobile touch targets
			mobileOption: 'min-h-[48px] p-3 active:bg-indigo-100 active:scale-95 transition-transform duration-75',
			mobileButton: 'min-w-[44px] min-h-[44px] p-2 active:bg-indigo-200 active:scale-95',
			// Desktop-first classes (existing behavior preserved)
			desktopOption: 'hover:bg-slate-100',
			desktopButton: 'hover:text-indigo-900 hover:bg-indigo-100',
			// Responsive combination
			responsiveOption: 'hover:bg-slate-100 min-h-[48px] p-3 active:bg-indigo-100 active:scale-95 md:min-h-auto md:p-2',
		},
		// Method to get combined classes
		getOptionClasses() {
			return this.styles.responsiveOption;
		},
		getButtonClasses() {
			return this.styles.mobileButton + ' ' + this.styles.desktopButton;
		},
		// COMPUTED PROPERTY: Optimized displayed selected elements
		get displayedSelectedElms() {
			return this.selectedElms.filter(opt => opt.text).slice(0, this.displayNumberSelected || 10);
		},
		// Rebuild options cache after tag creation
		rebuildOptionsCache() {
			// Clear existing caches
			this.allOptions = [];
			this.options = [];
			this.optionsByValue.clear();
			// Rebuild from updated select element
			const options = this.selectElement.options;
			for (let i = 0; i < options.length; i++) {
				const option = {
					value: options[i].value,
					text: options[i].innerText,
					search: options[i].dataset.search,
					selected: Object.values(this.selected).includes(options[i].value)
				};
				this.allOptions.push(option);
				this.options.push(option);
				this.optionsByValue.set(option.value, option);
			}
			// Re-run current search if there is one
			if (this.search) {
				this.performSearch(this.search);
			}
		},
		// KEYBOARD NAVIGATION METHODS
		// Navigate down to next option
		navigateDown() {
			if (this.options.length === 0) return;
			this.focusedIndex = Math.min(this.focusedIndex + 1, this.options.length - 1);
			//console.log(`[TagMe] Keyboard navigation: focused index ${this.focusedIndex}`);
		},
		// Navigate up to previous option  
		navigateUp() {
			if (this.options.length === 0) return;
			this.focusedIndex = Math.max(this.focusedIndex - 1, 0);
			//console.log(`[TagMe] Keyboard navigation: focused index ${this.focusedIndex}`);
		},
		// Select the currently focused option
		selectFocused() {
			if (this.focusedIndex >= 0 && this.focusedIndex < this.options.length) {
				// Create a mock event object since select() expects one
				const mockEvent = { target: null };
				this.select(this.focusedIndex, mockEvent);
				//console.log(`[TagMe] Keyboard selection: selected option at index ${this.focusedIndex}`);
			}
		},
		// Check if an option is currently focused
		isFocused(index) {
			return this.focusedIndex === index;
		},
		// Reset focus when dropdown opens/closes
		resetFocus() {
			this.focusedIndex = -1;
		},
		open() {
			this.show = true;
			this.resetFocus(); // Reset keyboard focus when opening
		},
		close() {
			this.show = false;
			this.resetFocus(); // Reset keyboard focus when closing
		},
		toggle() {
			this.show = !this.show
		},
		menuOpen() {
			this.menuShow = true
		},
		menuClose(target = 'default') {
			this.menuShow = false;
			// TODO: Focus management - currently commented out due to interference from other app components
			// Issue: Focus successfully sets to search input but immediately gets reset to <body>
			// This may be caused by: CSS focus styles, other JS libraries, or Alpine.js interactions
			// Debug: check for global focus handlers, CSS that might affect focus, other Alpine components
			switch (target) {
				case 'search':
					// GOAL: Return focus to search input after escape key
					// Currently: Focus goes to menu button instead (default Alpine/browser behavior)
					// For now: Use default behavior to avoid focus fighting
					break;
				case 'toggle':
					// FUTURE: Focus the menu toggle button when closing via other means
					break;
				case 'default':
				default:
					// No focus management, let browser handle naturally
					break;
			}
			/* COMMENTED OUT - Focus management attempts
			setTimeout(() => {
				const searchId = `search-${this.elementId.replace('id_', '')}`;
				const searchInput = document.getElementById(searchId);
				if (searchInput && target === 'search') {
					searchInput.focus();
					// Issue: focus sets successfully but gets immediately overridden
				}
			}, 100);
			*/
		},
		menuToggle() {
			this.menuShow = !this.menuShow
		},
		logOptions() {
			//console.log("Current Options Container:", this.options);
		},
		// Debounced search function (debouncing handled by Alpine.js in template)
		performSearch(searchTerm) {
			//console.log(`[TagMe] Filtering options for ${this.elementId}, search term: "${searchTerm}"`);
			// Perform the actual filtering on cached options
			if (searchTerm === '') {
				// If search is empty, show all options
				this.options = [...this.allOptions];
			} else {
				const reg = new RegExp(searchTerm, 'gi');
				this.options = this.allOptions.filter((option) => {
					return option.search.match(reg);
				});
			}
			this.canAddNewTag = this.options.length === 0;
			this.resetFocus(); // Reset focus when search results change
		},
		// Optimized method to update selection maps
		updateSelectionMaps() {
			this.selectedIndexMap.clear();
			this.selectedElms.forEach((option, index) => {
				this.selectedIndexMap.set(option.value, index);
			});
		},
		// Initializing component
		init() {
			// LOG: DOM Query for initial setup (ONLY TIME WE QUERY DOM)
			//console.log(`[TagMe] Initial setup for ${this.elementId} - CACHING ELEMENT`);
			// Cache the select element - this is the ONLY DOM query we'll make
			this.selectElement = document.getElementById(this.elementId);
			const options = this.selectElement.options;
			// Build and cache all options once with optimized data structures
			for (let i = 0; i < options.length; i++) {
				const option = {
					value: options[i].value,
					text: options[i].innerText,
					search: options[i].dataset.search,
					selected: Object.values(this.selected).includes(options[i].value)
				};
				this.allOptions.push(option);
				this.options.push(option);
				// Build value lookup map
				this.optionsByValue.set(option.value, option);
				if (option.selected) {
					this.selectedElms.push(option)
				}
			}
			// Initialize selection index map
			this.updateSelectionMaps();

			// Direct search watcher - debouncing handled by Alpine.js in template
			this.$watch("search", (searchTerm => {
				//console.log(`[TagMe] Search term changed for ${this.elementId}: "${searchTerm}"`);
				this.performSearch(searchTerm);
			}));
		},
		createNewTag() {
			this.isCreatingTag = true; // Start loading state
			this.tagCreationError = null; // Clear any previous errors
			this.canAddNewTag = false; // Remove 'add' button when new tag has been submitted
			// LOG: Using cached element instead of DOM query
			//console.log(`[TagMe] Using CACHED element for new tag creation in ${this.elementId}`);
			// Use cached element instead of DOM query
			const selectElement = this.selectElement;
			this.newTagsArray.length = 0;
			this.newTagsArray = this.search.split(',').map(tag => String(tag).trim());
			fetch(this.addTagURL, {
				method: 'POST',
				body: new URLSearchParams([
					['encoded_tag', base64Encode(this.search)],
					['csrfmiddlewaretoken', getCookie('csrftoken')],
				]),
			})
				.then(r => {
					if (r.status === 200) {
						return r.json();
					} else {
						// Handle HTTP errors
						throw new Error(`HTTP ${r.status}: ${r.statusText}`);
					}
				})
				.then(data => {
					//console.log('Tag creation successful:', data);
					if (data.is_error) {
						throw new Error(data.error_message || 'Unknown server error occurred');
					} else {
						// Success - update the select element
						selectElement.innerHTML = ''; // Remove all options in select element
						data.tags.forEach(tag => {
							// Repopulate select element with options from tags
							createOptionElementFromTag(selectElement, tag);
						});
						this.clearSearch(); // Clear search input
						// Rebuild options cache from updated select element
						this.rebuildOptionsCache();
					}
				})
				.catch(error => {
					console.error('Tag creation failed:', error);
					this.tagCreationError = error.message || 'Failed to create tag. Please try again.';
					this.canAddNewTag = true; // Re-enable the add button on error
				})
				.finally(() => {
					this.isCreatingTag = false; // End loading state
				});
		},
		// clear search field
		clearSearch() {
			this.search = '';
			this.tagCreationError = null; // Clear any error messages when searching
		},
		// deselect selected options
		deselectTag() {
			//console.log(`[TagMe] Deselecting all tags for ${this.elementId}`);
			setTimeout(() => {
				this.selected = []
				this.selectedElms = []
				this.selectedIndexMap.clear();
				// Update all options selection status efficiently
				this.allOptions.forEach((option) => {
					option.selected = false;
				});
				// Update current filtered options too
				this.options.forEach((option) => {
					option.selected = false;
				});
			}, 100)
		},
		// OPTIMIZED select given option - O(1) instead of O(n²)
		select(index, event) {
			//console.log(`[TagMe] Select/deselect operation for ${this.elementId} using O(1) lookup`);
			if (!this.allowMultipleSelect && this.selected.length === 1) {
				alert("You've reached the maximum number of selections!");
				return;
			}
			const option = this.options[index];
			if (!option.selected) {
				// Selecting the option
				option.selected = true;
				option.element = event.target;
				this.selected.push(option.value);
				this.selectedElms.push(option);
				// Update the corresponding option in allOptions using O(1) lookup
				const allOption = this.optionsByValue.get(option.value);
				if (allOption) {
					allOption.selected = true;
				}
				// Update selection index map
				this.selectedIndexMap.set(option.value, this.selectedElms.length - 1);
			} else {
				// Deselecting the option
				option.selected = false;
				// Remove from selected array using O(1) lookup
				const selectedIndex = this.selected.indexOf(option.value);
				if (selectedIndex > -1) {
					this.selected.splice(selectedIndex, 1);
				}
				// Remove from selectedElms using optimized lookup
				const elmIndex = this.selectedIndexMap.get(option.value);
				if (elmIndex !== undefined) {
					setTimeout(() => {
						this.selectedElms.splice(elmIndex, 1);
						this.updateSelectionMaps(); // Rebuild index map after removal
					}, 100);
				}
				// Update the corresponding option in allOptions using O(1) lookup
				const allOption = this.optionsByValue.get(option.value);
				if (allOption) {
					allOption.selected = false;
				}
			}
		},
		// OPTIMIZED remove from selected option - O(1) instead of O(n²)
		remove(index, option) {
			//console.log(`[TagMe] Remove operation for ${this.elementId} using O(1) lookup`);
			// Remove from selectedElms array directly using index
			this.selectedElms.splice(index, 1);
			// Remove from selected values using O(1) indexOf
			const selectedIndex = this.selected.indexOf(option.value);
			if (selectedIndex > -1) {
				this.selected.splice(selectedIndex, 1);
			}
			// Update option selection status using O(1) Map lookup
			const allOption = this.optionsByValue.get(option.value);
			if (allOption) {
				allOption.selected = false;
			}
			// Update any filtered options that match this value
			this.options.forEach((opt) => {
				if (opt.value === option.value) {
					opt.selected = false;
				}
			});
			// Rebuild selection index map efficiently
			this.updateSelectionMaps();
		},
		// filter out selected elements
		selectedElements() {
			return this.options.filter(op => op.selected === true)
		},
		// get selected values
		selectedValues() {
			return this.options.filter(op => op.selected === true).map(el => el.value)
		}
	}));
});
