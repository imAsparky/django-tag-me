// frontend/src/js/alpine-component.js
/**
* Alpine.js Tag Selector Component
*
* - Set-based state management
* - Order array for drag-to-reorder functionality
* - No reliance on DOM <select> element state
* - Reactive computed properties (Alpine caches these)
* - Keyboard navigation
* - Desktop inline actions, mobile menu
* - Drag-to-reorder selected tags
* - Two-way form autosave integration via event contract
*
* @param {Object} config - Configuration object from Django template
* @returns {Object} Alpine component instance
*/
export function createAlpineComponent(config) {
  return {
    // ============================================
    // STATE - Simple Sets + Order Array
    // ============================================
    /**
    * Available tags users can select from (the tag library)
    * @type {Set<string>}
    */
    availableTags: new Set((config.choices || []).filter(tag => tag && tag.trim())),
    /**
    * Currently selected tags (unordered for fast lookups)
    * @type {Set<string>}
    */
    selectedTags: new Set((config.selected || []).filter(tag => tag && tag.trim())),
    /**
    * Order of selected tags (for display and form submission)
    * @type {string[]}
    */
    tagOrder: (config.selected || []).filter(tag => tag && tag.trim()),
    // ============================================
    // UI STATE
    // ============================================
    /** Search input value */
    search: '',
    /** Dropdown visibility */
    show: false,
    /** Menu (Add/Clear/Remove) visibility */
    menuShow: false,
    /** Bottom sheet visibility (mobile add tag) */
    bottomSheetShow: false,
    /** Tag creation in progress */
    isCreatingTag: false,
    /** Tag creation error message */
    tagCreationError: null,
    /** Currently focused tag name (for keyboard nav) */
    focusedTag: null,
    /** Current screen width (for responsive logic) */
    screenWidth: window.innerWidth,
    /** ARIA announcement for screen readers */
    ariaAnnouncement: '',
    /** Swipe gesture state */
    swipeState: {
      startX: null,
      startY: null,
      currentX: null,
      deltaX: 0,
      isActive: false,
      element: null,
      animationFrame: null
    },
    // ============================================
    // INTERNAL FLAGS
    // ============================================
    /**
    * Guard flag to suppress change event dispatch during external restore.
    * Prevents write-back loop when form-field:external-update triggers
    * a state update that causes formValue to change.
    * @type {boolean}
    * @private
    */
    _suppressChangeEvent: false,
    // ============================================
    // CONFIGURATION (from Django)
    // ============================================
    /** URL to add new tags to the library */
    addTagURL: config.addTagURL || '',
    /** Whether user can add new tags (false for system tags) */
    permittedToAddTags: config.permittedToAddTags !== false,
    /** Allow multiple tag selection */
    allowMultiple: config.allowMultiple !== false,
    /** Auto-select newly created tags */
    autoSelectNewTags: config.autoSelectNewTags !== false,
    /** Max number of selected tags to display */
    maxDisplay: config.displayNumberSelected || 2,
    /** Help URL (if provided by developer) */
    helpUrl: config.helpUrl || '',
    /** Management URL (if provided by developer) */
    mgmtUrl: config.mgmtUrl || '',
    // ============================================
    // LIFECYCLE
    // ============================================
    /**
    * Initialize component
    *
    * Sets up:
    * - Responsive screen width tracking
    * - Save side: watches formValue and dispatches 'change' on hidden input
    * - Restore side: listens for 'form-field:external-update' on hidden input
    */
    init() {
      // Update screen width on resize
      window.addEventListener('resize', () => {
        this.screenWidth = window.innerWidth;
      });

      // ------------------------------------------
      // SAVE SIDE: Dispatch 'change' event when formValue changes
      // ------------------------------------------
      // Uses $watch on the computed formValue so every code path that
      // mutates selectedTags or tagOrder (toggleTag, removeTag,
      // deselectAll, createNewTag) is covered by a single integration
      // point. The _suppressChangeEvent guard prevents firing during
      // external restore (form-field:external-update).
      this.$watch('formValue', () => {
        if (this._suppressChangeEvent) return;
        this.$refs.hiddenInput.dispatchEvent(
          new Event('change', { bubbles: true })
        );
      });

      // ------------------------------------------
      // RESTORE SIDE: Listen for external value updates
      // ------------------------------------------
      // External systems (autosave, form-filler, test harness) set the
      // hidden input's .value and then dispatch this custom event.
      // We re-read the value, parse it, and replace our internal state.
      // Alpine's reactivity then updates the visual chips automatically.
      this.$refs.hiddenInput.addEventListener('form-field:external-update', () => {
        const newValue = this.$refs.hiddenInput.value;
        const tags = this.parseTagValue(newValue);

        // Suppress change event — the value hasn't actually changed,
        // we're just syncing visual state to match the hidden input.
        this._suppressChangeEvent = true;

        // Replace selection state
        this.selectedTags = new Set(tags);
        this.tagOrder = [...tags];

        // Add unknown tags to availableTags so they appear in the
        // dropdown with a checkmark, consistent with normal selection.
        // Server-side validation remains the authority on validity.
        tags.forEach(tag => {
          if (!this.availableTags.has(tag)) {
            this.availableTags.add(tag);
          }
        });

        this._suppressChangeEvent = false;
      });
    },
    // ============================================
    // COMPUTED PROPERTIES (Alpine caches these)
    // ============================================
    /**
    * Check if screen is desktop size
    * Uses 768px breakpoint (md:)
    * @returns {boolean}
    */
    get isDesktop() {
      return this.screenWidth >= 768;
    },
    /**
    * Check if screen is mobile size
    * Uses 768px breakpoint (md:)
    * @returns {boolean}
    */
    get isMobile() {
      return this.screenWidth < 768;
    },
    /**
    * Check if device has virtual keyboard (touch device)
    * Used to determine auto-focus behavior
    * @returns {boolean}
    */
    get hasVirtualKeyboard() {
      return ('ontouchstart' in window) ||
        (navigator.maxTouchPoints > 0) ||
        (navigator.msMaxTouchPoints > 0);
    },
    /**
    * Should we auto-focus search when dropdown opens?
    * Auto-focus on devices with physical keyboards only
    * @returns {boolean}
    */
    get shouldAutoFocus() {
      return !this.hasVirtualKeyboard;
    },
    /**
    * Filtered tags based on search input
    * @returns {string[]} Sorted array of matching tags
    */
    get filteredTags() {
      if (!this.search) {
        return Array.from(this.availableTags).sort();
      }
      const searchLower = this.search.toLowerCase();
      return Array.from(this.availableTags)
        .filter(tag => tag.toLowerCase().includes(searchLower))
        .sort((a, b) => {
          // Prioritize tags that start with search term
          const aStarts = a.toLowerCase().startsWith(searchLower);
          const bStarts = b.toLowerCase().startsWith(searchLower);
          if (aStarts && !bStarts) return -1;
          if (!aStarts && bStarts) return 1;
          return a.localeCompare(b);
        });
    },
    /**
    * Selected tags as ordered array (uses tagOrder)
    * @returns {string[]}
    */
    get selectedArray() {
      // Filter tagOrder to only include tags still in selectedTags
      return this.tagOrder.filter(tag => this.selectedTags.has(tag));
    },
    /**
    * Selected tags to display (limited by maxDisplay)
    * @returns {string[]}
    */
    get displayedSelected() {
      return this.selectedArray.slice(0, this.maxDisplay);
    },
    /**
    * Number of selected tags not displayed
    * @returns {number}
    */
    get overflowCount() {
      return Math.max(0, this.selectedArray.length - this.maxDisplay);
    },
    /**
    * Form value (comma-separated string for Django, preserves order)
    *
    * Includes a trailing comma when tags are selected. This acts as a
    * format sentinel that guarantees parse_tags (Python side) always
    * uses comma-delimited mode, which is critical for multi-word tags.
    * Without the trailing comma, a single multi-word tag like
    * "machine learning" would be split into two tags by the space-
    * delimited parser.
    *
    * The Python _parse_value() already does rstrip(","), so the
    * trailing comma is transparently handled on the server side.
    *
    * @returns {string} e.g. "python,django," or "" (empty when no selection)
    */
    get formValue() {
      const tags = this.selectedArray;
      return tags.length > 0 ? tags.join(',') + ',' : '';
    },
    /**
    * Whether user can add a new tag
    * @returns {boolean}
    */
    get canAddTag() {
      const trimmedSearch = this.search.trim();
      return this.permittedToAddTags &&
        trimmedSearch.length > 0 &&
        this.filteredTags.length === 0 &&
        !this.availableTags.has(trimmedSearch);
    },
    /**
    * Whether menu has static links (Help/Management)
    * @returns {boolean}
    */
    get hasLinks() {
      return !!(this.helpUrl || this.mgmtUrl);
    },
    /**
    * Badge state for menu button
    * @returns {Object} { type: 'none'|'add'|'actions', count: number, show: boolean }
    */
    get menuBadge() {
      if (this.canAddTag) {
        return {
          type: 'add',
          show: true,
          count: 0,
          cssClass: 'tm-badge-dot'
        };
      }
      // Priority 2: Multiple actions available (mobile only - count badge)
      if (this.isMobile) {
        let actionCount = 0;
        if (this.search.length > 0) actionCount++;
        if (this.selectedTags.size > 0) actionCount++;
        if (actionCount > 0) {
          return {
            type: 'actions',
            show: true,
            count: actionCount,
            cssClass: 'tm-badge-count tm-badge-info'
          };
        }
      }
      // No badge
      return {
        type: 'none',
        show: false,
        count: 0,
        cssClass: ''
      };
    },
    /**
    * CSS class for menu button (contextual styling)
    * @returns {string}
    */
    get menuButtonClass() {
      if (this.canAddTag) return 'tm-menu-btn-primary';
      if (this.selectedTags.size > 0) return 'tm-menu-btn-info';
      return '';
    },
    /**
    * Whether to show quick actions (desktop only)
    * @returns {boolean}
    */
    get showQuickActions() {
      return this.isDesktop && (this.search.length > 0 || this.selectedTags.size > 0);
    },
    /**
    * Whether to show inline Add option in search results (desktop only)
    * @returns {boolean}
    */
    get showInlineAdd() {
      return this.isDesktop && this.canAddTag;
    },
    // ============================================
    // TAG SELECTION OPERATIONS
    // ============================================
    /**
    * Toggle tag selection state
    * @param {string} tagName - Tag to toggle
    */
    toggleTag(tagName) {
      if (this.selectedTags.has(tagName)) {
        // Remove from Set
        this.selectedTags.delete(tagName);
        // Remove from order array
        this.tagOrder = this.tagOrder.filter(t => t !== tagName);
        // ARIA announcement
        this.ariaAnnouncement = `Removed tag: ${tagName}`;
      } else {
        // Check single-select limit
        if (!this.allowMultiple && this.selectedTags.size >= 1) {
          alert("You've reached the maximum number of selections!");
          return;
        }
        // Add to Set
        this.selectedTags.add(tagName);
        // Add to end of order array
        this.tagOrder.push(tagName);
        // ARIA announcement
        this.ariaAnnouncement = `Added tag: ${tagName}`;
      }
    },
    /**
    * Remove a specific tag from selection
    * @param {string} tagName - Tag to remove
    */
    removeTag(tagName) {
      this.selectedTags.delete(tagName);
      this.tagOrder = this.tagOrder.filter(t => t !== tagName);
      // ARIA announcement
      this.ariaAnnouncement = `Removed tag: ${tagName}`;
    },
    /**
    * Clear all selected tags
    */
    deselectAll() {
      const count = this.selectedTags.size;
      this.selectedTags.clear();
      this.tagOrder = [];
      // ARIA announcement
      this.ariaAnnouncement = `Removed all ${count} tags`;
    },
    /**
    * Check if a tag is selected
    * @param {string} tagName - Tag to check
    * @returns {boolean}
    */
    isSelected(tagName) {
      return this.selectedTags.has(tagName);
    },

    // ============================================
    // TAG CREATION (Updates tag library)
    // ============================================
    /**
    * Create new tag and add to library
    * Makes POST request to backend to persist tag
    * Backend handles UserTag.tags update and save
    */
    async createNewTag() {
      const newTagName = this.search.trim();
      // Guard clauses
      if (!newTagName) return;
      if (!this.permittedToAddTags) {
        console.warn('Tag creation not permitted (system tags are readonly)');
        return;
      }
      this.isCreatingTag = true;
      this.tagCreationError = null;
      try {
        const response = await fetch(this.addTagURL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: new URLSearchParams([
            ['encoded_tag', this.base64Encode(newTagName)],
            ['csrfmiddlewaretoken', this.getCsrfToken()],
          ]),
        });
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        if (data.is_error) {
          throw new Error(data.error_message || 'Unknown server error');
        }
        // Backend saved tag to UserTag.tags (tag library updated)
        // Just add to our local available tags
        const addedTag = data.tag || newTagName;
        if (!this.availableTags.has(addedTag)) {
          this.availableTags.add(addedTag);
        }
        // Auto-select if configured
        if (this.autoSelectNewTags) {
          this.selectedTags.add(addedTag);
          this.tagOrder.push(addedTag);
          // ARIA announcement
          this.ariaAnnouncement = `Created and selected tag: ${addedTag}`;
        } else {
          // ARIA announcement
          this.ariaAnnouncement = `Created tag: ${addedTag}`;
        }
        // Clear search and close menu/sheet
        this.search = '';
        this.tagCreationError = null;
        this.menuShow = false;
        this.bottomSheetShow = false;
        console.debug(`✅ Tag "${addedTag}" added to library and ${this.autoSelectNewTags ? 'selected' : 'available'}`);
      } catch (error) {
        console.error('Tag creation failed:', error);
        this.tagCreationError = error.message || 'Failed to create tag. Please try again.';
      } finally {
        this.isCreatingTag = false;
      }
    },
    // ============================================
    // SEARCH & UI OPERATIONS
    // ============================================
    /**
    * Clear search input and errors
    */
    clearSearch() {
      this.search = '';
      this.tagCreationError = null;
      this.focusedTag = null;
    },
    /**
    * Open dropdown
    */
    open() {
      this.show = true;
      this.focusedTag = null;
    },
    /**
    * Close dropdown
    */
    close() {
      this.show = false;
      this.menuShow = false;
      this.bottomSheetShow = false;
      this.focusedTag = null;
    },
    /**
    * Toggle dropdown visibility
    */
    toggle() {
      this.show = !this.show;
      if (!this.show) {
        this.menuShow = false;
        this.bottomSheetShow = false;
        this.focusedTag = null;
      }
    },
    /**
    * Open menu (Add/Clear/Remove buttons)
    */
    menuOpen() {
      this.menuShow = true;
    },
    /**
    * Close menu
    */
    menuClose() {
      this.menuShow = false;
    },
    /**
    * Toggle menu visibility
    */
    menuToggle() {
      this.menuShow = !this.menuShow;
    },
    // ============================================
    // MOBILE BOTTOM SHEET
    // ============================================
    /**
    * Open bottom sheet for adding tag (mobile only)
    */
    openBottomSheet() {
      this.bottomSheetShow = true;
      this.tagCreationError = null;
      // Close the mobile menu if it's open
      this.menuShow = false;
    },
    /**
    * Close bottom sheet
    */
    closeBottomSheet() {
      this.bottomSheetShow = false;
      this.tagCreationError = null;
    },
    // ============================================
    // KEYBOARD NAVIGATION (FIXED)
    // ============================================
    /**
    * Navigate down in filtered tag list
    * FIXED: Added scroll-into-view for focused element
    */
    navigateDown() {
      const tags = this.filteredTags;
      if (tags.length === 0) return;

      const currentIndex = tags.indexOf(this.focusedTag);
      const nextIndex = currentIndex < 0 ? 0 : Math.min(currentIndex + 1, tags.length - 1);
      this.focusedTag = tags[nextIndex];

      // Scroll focused element into view
      this.$nextTick(() => {
        const focusedElement = document.getElementById(`tag-option-${this.focusedTag}`);
        if (focusedElement) {
          focusedElement.scrollIntoView({
            behavior: 'smooth',
            block: 'nearest',
            inline: 'nearest'
          });
        }
      });

      // ARIA announcement
      this.ariaAnnouncement = `Focused: ${this.focusedTag}`;
    },
    /**
    * Navigate up in filtered tag list
    * FIXED: Added scroll-into-view for focused element
    */
    navigateUp() {
      const tags = this.filteredTags;
      if (tags.length === 0) return;

      const currentIndex = tags.indexOf(this.focusedTag);
      const prevIndex = currentIndex < 0 ? 0 : Math.max(currentIndex - 1, 0);
      this.focusedTag = tags[prevIndex];

      // Scroll focused element into view
      this.$nextTick(() => {
        const focusedElement = document.getElementById(`tag-option-${this.focusedTag}`);
        if (focusedElement) {
          focusedElement.scrollIntoView({
            behavior: 'smooth',
            block: 'nearest',
            inline: 'nearest'
          });
        }
      });

      // ARIA announcement
      this.ariaAnnouncement = `Focused: ${this.focusedTag}`;
    },
    /**
    * Select the currently focused tag
    * FIXED: Auto-focus first tag if none focused yet
    */
    selectFocused() {
      // If no tag is focused yet, focus the first one
      if (!this.focusedTag && this.filteredTags.length > 0) {
        this.focusedTag = this.filteredTags[0];
      }

      // Now select it if it exists in the filtered list
      if (this.focusedTag && this.filteredTags.includes(this.focusedTag)) {
        this.toggleTag(this.focusedTag);
      }
    },
    /**
    * Check if a tag is currently focused (for styling)
    * @param {string} tagName - Tag to check
    * @returns {boolean}
    */
    isFocused(tagName) {
      return this.focusedTag === tagName;
    },
    /**
    * Reset focus state
    */
    resetFocus() {
      this.focusedTag = null;
    },
    // ============================================
    // SWIPE GESTURES (Mobile Touch Interactions)
    // ============================================
    /**
    * Handle touch start - begin tracking swipe
    * @param {TouchEvent} event - Touch event
    * @param {HTMLElement} element - The list item being swiped
    */
    handleSwipeStart(event, element) {
      console.debug('🟢 SWIPE START', { isMobile: this.isMobile, hasElement: !!element });
      if (!this.isMobile) return;

      const touch = event.touches[0];
      this.swipeState.startX = touch.clientX;
      this.swipeState.startY = touch.clientY;
      this.swipeState.currentX = touch.clientX;
      this.swipeState.deltaX = 0;
      this.swipeState.isActive = false;
      this.swipeState.element = element;

      // Disable transition during swipe for immediate feedback
      element.style.transition = 'none';
    },
    /**
    * Handle touch move - update visual feedback
    * @param {TouchEvent} event - Touch event
    */
    handleSwipeMove(event) {
      console.debug('🔵 SWIPE MOVE', { isMobile: this.isMobile, hasStart: !!this.swipeState.startX });
      if (!this.isMobile || !this.swipeState.startX || !this.swipeState.element) return;

      const touch = event.touches[0];
      this.swipeState.currentX = touch.clientX;

      const deltaX = this.swipeState.currentX - this.swipeState.startX;
      const deltaY = touch.clientY - this.swipeState.startY;

      // Only activate swipe if horizontal movement exceeds vertical
      // This prevents interfering with vertical scrolling
      if (!this.swipeState.isActive && Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 10) {
        this.swipeState.isActive = true;
        // Prevent scrolling once we've determined this is a horizontal swipe
        event.preventDefault();
      }

      if (this.swipeState.isActive) {
        event.preventDefault();
        this.swipeState.deltaX = deltaX;

        // Update visual feedback using RAF for smooth performance
        if (this.swipeState.animationFrame) {
          cancelAnimationFrame(this.swipeState.animationFrame);
        }

        this.swipeState.animationFrame = requestAnimationFrame(() => {
          if (this.swipeState.element) {
            const element = this.swipeState.element;
            const threshold = element.offsetWidth * 0.5;

            // Cap the translation at threshold distance for better feel
            const cappedDelta = Math.max(-threshold, Math.min(threshold, this.swipeState.deltaX));

            // Apply transform
            element.style.transform = `translateX(${cappedDelta}px)`;

            // Add visual hint classes based on direction and state
            if (Math.abs(cappedDelta) > threshold * 0.3) {
              element.classList.add('swipe-active');
            } else {
              element.classList.remove('swipe-active');
            }
          }
        });
      }
    },
    /**
     * Handle touch end - complete or cancel swipe with success animation
     * OPTION 2: Animates to edge before snapping back
     * @param {TouchEvent} event - Touch event
     * @param {string} tagName - Name of the tag being swiped
     */
    handleSwipeEnd(event, tagName) {
      if (!this.isMobile || !this.swipeState.element) {
        this.resetSwipe();
        return;
      }

      const element = this.swipeState.element;
      const threshold = element.offsetWidth * 0.5;
      const deltaX = this.swipeState.deltaX;

      // Check if swipe exceeded threshold (either direction)
      if (this.swipeState.isActive && Math.abs(deltaX) >= threshold) {
        // SUCCESS ANIMATION SEQUENCE

        // 1. Animate to edge (show success)
        const direction = deltaX > 0 ? 1 : -1;
        const targetX = element.offsetWidth * 0.7 * direction; // 70% of width

        // Enable smooth transition
        element.style.transition = 'transform 0.15s cubic-bezier(0.4, 0, 0.2, 1)';
        element.style.transform = `translateX(${targetX}px)`;

        // 2. Toggle tag state after brief moment (while sliding)
        setTimeout(() => {
          this.toggleTag(tagName);
        }, 75); // Mid-animation toggle

        // 3. Snap back with new state
        setTimeout(() => {
          if (this.swipeState.element === element) {
            // Re-enable standard transition
            element.style.transition = 'transform 0.2s ease-out';
            element.style.transform = '';
            element.classList.remove('swipe-active');

            // Clean up after snap-back completes
            setTimeout(() => {
              this.resetSwipe();
            }, 200);
          }
        }, 150); // Start snap-back

      } else {
        // BELOW THRESHOLD - Just snap back
        element.style.transition = 'transform 0.2s ease-out';
        element.style.transform = '';
        element.classList.remove('swipe-active');

        setTimeout(() => {
          this.resetSwipe();
        }, 200);
      }
    },

    /**
    * Reset swipe state and clean up visual feedback
    */
    resetSwipe() {
      if (this.swipeState.animationFrame) {
        cancelAnimationFrame(this.swipeState.animationFrame);
      }

      if (this.swipeState.element) {
        this.swipeState.element.style.transform = '';
        this.swipeState.element.style.transition = '';
        this.swipeState.element.classList.remove('swipe-active');
      }

      this.swipeState.startX = null;
      this.swipeState.startY = null;
      this.swipeState.currentX = null;
      this.swipeState.deltaX = 0;
      this.swipeState.isActive = false;
      this.swipeState.element = null;
      this.swipeState.animationFrame = null;
    },
    // ============================================
    // UTILITIES
    // ============================================
    /**
    * Get CSRF token from cookies
    * @returns {string|null}
    */
    getCsrfToken() {
      const cookies = document.cookie.split(';');
      for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
          return decodeURIComponent(value);
        }
      }
      return null;
    },
    /**
    * Base64 encode a value
    * @param {string} str - String to encode
    * @returns {string}
    */
    base64Encode(str) {
      return btoa(JSON.stringify(str));
    },
    /**
    * Parse a tag value string into an array of tag names.
    *
    * Handles the comma-separated format produced by formValue,
    * including trailing commas (format sentinel), leading/trailing
    * whitespace around tags, and empty segments.
    *
    * Backwards-compatible with values stored before the trailing
    * comma convention was adopted.
    *
    * @param {string} value - Raw value from hidden input (e.g. "python,django," or "python,django")
    * @returns {string[]} Array of trimmed, non-empty tag names
    */
    parseTagValue(value) {
      if (!value || typeof value !== 'string') return [];
      return value.split(',')
        .map(t => t.trim())
        .filter(t => t.length > 0);
    }
  }
}
