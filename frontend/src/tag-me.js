// frontend/src/tag-me.js
/**
 * Django Tag-Me - Alpine.js Multi-Select Component
 *
 * This file exports the Alpine component factory.
 * Registration with Alpine.js is handled automatically by the Vite build
 * (see outro in vite.config.js).
 *
 * The component is registered as 'alpineTagMeMultiSelect' and can be used:
 * <div x-data="alpineTagMeMultiSelect({ choices: [...], selected: [...], ... })">
 */

// Import styles (will be extracted to CSS file by Vite)
import './css/styles.css'

// Import component factory
import { createAlpineComponent } from './js/alpine-component.js'

// Export for library usage
// The IIFE build exposes this as window.DjangoTagMe.createAlpineComponent
export { createAlpineComponent }

