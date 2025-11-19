// frontend/src/tag-me.js
/**
* Django Tag-Me - Alpine.js Multi-Select Component
*
* Requires Alpine.js to be loaded globally before this script.
* Alpine.js should be available as window.Alpine.
*/
// Import styles
import './css/styles.css'
// Import component
import { createAlpineComponent } from './js/alpine-component.js'
// Register component with Alpine.js
if (typeof window !== 'undefined') {
  console.debug('🔍 Tag-Me: Initializing...')
  // DEBUG: Check what we imported
  console.debug('📦 createAlpineComponent imported:', typeof createAlpineComponent)
  // DEBUG: Create test instance to verify it has new methods
  try {
    const testConfig = {
      choices: [],
      selected: [],
      addTagURL: '',
      permittedToAddTags: true,
      allowMultiple: true,
      autoSelectNewTags: true,
      displayNumberSelected: 2,
      helpUrl: '',
      mgmtUrl: ''
    }
    console.debug('🧪 Creating test instance...')
    const testInstance = createAlpineComponent(testConfig)
    console.debug('🧪 Test instance created successfully')
    console.debug('🧪 Has toggle?', typeof testInstance.toggle)
    console.debug('🧪 Has menuBadge?', 'menuBadge' in testInstance)
    console.debug('🧪 Has menuButtonClass?', 'menuButtonClass' in testInstance)
    console.debug('🧪 Has showInlineAdd?', 'showInlineAdd' in testInstance)
    // Try to access menuBadge
    try {
      const badge = testInstance.menuBadge
      console.debug('🧪 menuBadge returns:', badge)
    } catch (e) {
      console.error('🧪 Error accessing menuBadge:', e)
    }
  } catch (e) {
    console.error('❌ Failed to create test instance:', e)
  }
  const registerComponent = () => {
    if (typeof window.Alpine !== 'undefined' && window.Alpine.data) {
      console.debug('📝 Registering component with Alpine...')
      window.Alpine.data('alpineTagMeMultiSelect', createAlpineComponent)
      console.debug('✅ Django Tag-Me component registered with Alpine.js')
      return true
    }
    return false
  }
  // Try immediate registration (if Alpine already loaded)
  if (!registerComponent()) {
    console.debug('⏳ Waiting for Alpine.js to initialize...')
    // Wait for Alpine to initialize
    document.addEventListener('alpine:init', () => {
      console.debug('🎯 alpine:init event received')
      if (registerComponent()) {
        console.debug('✅ Registration complete')
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
  console.debug('✅ Tag-Me initialization complete')
}
// Export for module usage
export { createAlpineComponent }
