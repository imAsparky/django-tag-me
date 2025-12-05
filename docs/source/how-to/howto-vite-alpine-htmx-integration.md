# How to integrate django-tag-me with Vite, Alpine.js, and HTMX

This guide explains how to configure django-tag-me to work correctly in projects that use Vite as a build tool, Alpine.js for reactivity, and HTMX for dynamic content loading.

## Prerequisites

- Django project with django-tag-me installed
- Vite configured as your frontend build tool
- Alpine.js loaded via Vite (as an ES module)
- HTMX for partial page updates (e.g., slideovers, modals)

## The problem

When using django-tag-me in a modern frontend stack, you may encounter errors like:

```
Alpine Expression Error: alpineTagMeMultiSelect is not defined
```

This happens because:

1. **Script execution order**: Vite bundles Alpine.js as an ES module (`type="module"`), which defers execution. Tag-me's IIFE bundle may execute before Alpine is available.

2. **Dynamic content**: HTMX swaps content into the DOM after the initial page load. Alpine.js doesn't automatically initialize components in dynamically added content.

3. **Component registration timing**: The tag-me component must be registered with Alpine *before* `Alpine.start()` processes `x-data` attributes.

## Solution overview

The solution involves three changes:

1. Register the tag-me component on the `alpine:init` event
2. Defer `Alpine.start()` until after the DOM is ready
3. Re-initialize Alpine on HTMX content swaps

## Step 1: Load tag-me assets correctly

In your base template, load tag-me assets after your main Vite bundle:

```html
{% load vite_tags %}
{% load tag_me_assets %}

<head>
    <!-- Your Vite bundle (contains Alpine.js) -->
    {% vite_asset 'main' %}
    
    <!-- Tag-me assets (must load AFTER Alpine) -->
    {% tag_me_assets %}
    
    <!-- Register tag-me component with Alpine -->
    <script>
        document.addEventListener('alpine:init', function() {
            if (window.DjangoTagMe && window.Alpine) {
                Alpine.data('alpineTagMeMultiSelect', DjangoTagMe.createAlpineComponent);
                console.log('✅ Tag-Me component registered with Alpine');
            }
        });
    </script>
    
    <!-- Other assets -->
    {% vite_asset 'other-bundle' %}
</head>
```

The inline script listens for Alpine's `alpine:init` event, which fires just before Alpine processes the DOM. This ensures the tag-me component is registered at the right time.

## Step 2: Defer Alpine.start()

Modify your Alpine.js initialization to defer `Alpine.start()` until the DOM is ready. This gives all scripts (including those with `defer`) time to register their `alpine:init` listeners.

```javascript
// frontend/src/lib/alpine.js
import Alpine from 'alpinejs'

// ... your plugins, components, stores ...

// Make Alpine available globally
window.Alpine = Alpine

// Defer Alpine.start() to allow component registration
function startAlpine() {
    Alpine.start()
    console.debug('✅ Alpine.js initialized')
}

if (document.readyState === 'complete') {
    // Page fully loaded - yield to other scripts first
    setTimeout(startAlpine, 0)
} else {
    // Still loading - wait for DOMContentLoaded
    document.addEventListener('DOMContentLoaded', startAlpine)
}

export default Alpine
```

### Why this matters

ES modules execute when `document.readyState` is `'interactive'`, not `'loading'`. Without deferring `Alpine.start()`:

1. Your Alpine module executes and calls `Alpine.start()` immediately
2. Alpine processes all `x-data` attributes
3. Tag-me's script executes *after* and registers its component too late

By deferring to `DOMContentLoaded`, you ensure:

1. Your Alpine module executes, registers the `DOMContentLoaded` listener
2. Tag-me's script executes, registers the `alpine:init` listener
3. `DOMContentLoaded` fires
4. `Alpine.start()` runs, dispatches `alpine:init`
5. Tag-me's listener fires, registers the component
6. Alpine processes `x-data` attributes (component now available)

## Step 3: Initialize Alpine on HTMX swaps

When HTMX loads content containing tag-me widgets (e.g., into a slideover), Alpine needs to initialize those new elements. Add `Alpine.initTree()` to your HTMX event handlers:

```javascript
// frontend/src/integrations/htmx-handlers.js

htmx.on('htmx:afterSwap', (e) => {
    // Initialize Alpine components in swapped content
    if (window.Alpine) {
        Alpine.initTree(e.detail.target)
        console.debug('[HTMX] Alpine.initTree() called on:', e.detail.target.id || 'target')
    }
    
    // Your other afterSwap logic (show modals, slideovers, etc.)
    switch (e.detail.target.id) {
        case 'slide':
            Alpine.store('displaySlide').showSlide()
            break
        case 'modal':
            Alpine.store('displayModal').showModal()
            break
    }
})
```

`Alpine.initTree(element)` tells Alpine to scan the given element and its descendants for `x-data` attributes and initialize any components found.

## Step 4: Clean up template hacks

If you previously used workarounds like `{{ form.media }}` in base templates or `<head>{{ form.media }}</head>` in partials, remove them:

```html
<!-- REMOVE these - they don't work correctly -->
{{ form.media }}
<head>{{ form.media }}</head>
```

These approaches fail because:

- `{{ form.media }}` requires a `form` variable in the template context (often missing)
- `<head>` tags inside `<body>` are invalid HTML and ignored by browsers
- HTMX doesn't execute `<script>` tags in swapped content by default

## Troubleshooting

### Component still not defined

Check the browser console for these messages in order:

1. `⏳ Django Tag-Me: Waiting for Alpine.js...` - Tag-me loaded, waiting for Alpine
2. `✅ Tag-Me component registered with Alpine` - Registration successful
3. `✅ Alpine.js initialized` - Alpine started

If you see the error before these messages, the registration script isn't running or is running too late.

### Widget works on page load but not in slideover

Ensure `Alpine.initTree()` is called in your `htmx:afterSwap` handler. Check that it's being called on the correct target element.

### Debug checklist

Run these in the browser console:

```javascript
// Is Alpine loaded?
console.log('Alpine:', window.Alpine)

// Is tag-me loaded?
console.log('DjangoTagMe:', window.DjangoTagMe)

// Is the component registered?
// (This creates a test instance - if it works, registration succeeded)
const test = Alpine.data('alpineTagMeMultiSelect')
console.log('Component factory:', test)
```

## Complete example

### base.html

```html
{% load vite_tags %}
{% load tag_me_assets %}

<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}{% endblock %}</title>
    
    {% vite_hmr %}
    {% vite_asset 'main' %}
    
    {% tag_me_assets %}
    <script>
        document.addEventListener('alpine:init', function() {
            if (window.DjangoTagMe && window.Alpine) {
                Alpine.data('alpineTagMeMultiSelect', DjangoTagMe.createAlpineComponent);
            }
        });
    </script>
    
    {% block extra_head %}{% endblock %}
</head>
<body>
    {% block content %}{% endblock %}
    
    {% include '_partials/slideover.html' %}
</body>
</html>
```

### alpine.js

```javascript
import Alpine from 'alpinejs'

window.Alpine = Alpine

// Your components, stores, plugins...

function startAlpine() {
    Alpine.start()
}

if (document.readyState === 'complete') {
    setTimeout(startAlpine, 0)
} else {
    document.addEventListener('DOMContentLoaded', startAlpine)
}

export default Alpine
```

### htmx-handlers.js

```javascript
htmx.on('htmx:afterSwap', (e) => {
    if (window.Alpine) {
        Alpine.initTree(e.detail.target)
    }
})
```

## Summary

| Problem | Solution |
|---------|----------|
| Tag-me component not defined | Register on `alpine:init` event in base template |
| Alpine starts before registration | Defer `Alpine.start()` to `DOMContentLoaded` |
| Widget doesn't work in HTMX content | Call `Alpine.initTree()` on `htmx:afterSwap` |
| `{{ form.media }}` doesn't work | Use `{% tag_me_assets %}` template tag instead |
