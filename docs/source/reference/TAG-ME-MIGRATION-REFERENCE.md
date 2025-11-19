# Tag-Me Template Migration Reference
**For: Tailwind 4 + Semantic Tokens + Prefix Integration**

## CRITICAL RULE: CLASS ATTRIBUTES ONLY

```html
✅ CORRECT: Change class="bg-white dark:bg-gray-800"
            to     class="tm:bg-bg-base"

❌ WRONG: Modify Alpine.js directives
❌ WRONG: Change HTML structure
❌ WRONG: Touch x-data, x-show, x-init, etc.
❌ WRONG: Modify inline styles (except <style> tag scrollbars)
```

**ONE EXCEPTION:** Custom `<style>` tag content (scrollbars, swipe gestures) - use semantic OKLCH colors AND `.dark` selector.

---

## Step-by-Step Migration Process

### 1. Read styles.css First
Tag-me uses `prefix(tm)` so all utilities are prefixed:
```css
/* In styles.css */
@import "tailwindcss" prefix(tm);

@theme {
  --color-primary-base: var(--color-primary, oklch(0.61 0.20 266));
  --color-bg-base: var(--color-surface, oklch(1.00 0 0));
  /* etc... */
}
```

### 2. Map Colors to Semantic Tokens

| Tailwind Class | → | Semantic Token | Reason |
|----------------|---|----------------|--------|
| `bg-white dark:bg-gray-800` | → | `tm:bg-bg-base` | Base surface |
| `bg-gray-50 dark:bg-white/5` | → | `tm:bg-bg-raised` | Elevated surface |
| `bg-gray-100 dark:bg-gray-700` | → | `tm:bg-bg-hover` | Hover state |
| `text-gray-900 dark:text-white` | → | `tm:text-text-primary` | Primary text |
| `text-gray-600 dark:text-gray-300` | → | `tm:text-text-secondary` | Secondary text |
| `text-gray-500` | → | `tm:text-text-muted` | Tertiary text |
| `placeholder:text-gray-400` | → | `tm:placeholder:text-placeholder` | Input placeholder |
| `bg-indigo-500` | → | `tm:bg-primary-base` | Primary brand |
| `hover:bg-indigo-400` | → | `hover:tm:bg-primary-hover` | Primary hover |
| `text-white` (on colored bg) | → | `tm:text-text-on-primary` | Text on primary |
| `border-gray-300 dark:border-gray-600` | → | `tm:border-border-base` | Standard border |
| `ring-indigo-500` | → | `tm:ring-border-focus` | Focus ring |
| `bg-red-50 dark:bg-red-900/50` | → | `tm:bg-error-bg` | Error background |
| `text-red-500` | → | `tm:text-error-base` | Error color |

### 3. Handle Z-Index (Special Case)

**Problem:** Z-index tokens don't auto-generate utilities!

```css
/* In styles.css @theme - these DON'T create utilities automatically */
--z-modal: 1050;
--z-sticky: 1020;
```

**Solution:** Add utilities manually in `@layer utilities`:

```css
@layer utilities {
  .tm\:z-modal { z-index: var(--z-modal); }
  .tm\:z-sticky { z-index: var(--z-sticky); }
  /* etc... */
}
```

**In templates:** Use semantic names:
```html
class="tm:z-modal"  <!-- NOT tm:z-[1050] -->
```

### 4. Preserve Original Behavior

**IMPORTANT:** Some templates have complex x-init JavaScript for positioning/layout.

```html
<!-- DO NOT REMOVE OR MODIFY THIS -->
<div x-init=" const updatePosition = () => { ... }; ">
```

**The original dropdown container had:**
- `class="absolute z-50 mt-2 w-full ..."`
- Complex `x-init` for mobile positioning
- These MUST be preserved exactly

**When migrating:**
```html
<!-- Add tm: prefix to classes, keep x-init untouched -->
class="tm:absolute tm:z-dropdown tm:mt-2 tm:w-full ..."
x-init=" const updatePosition = () => { ... }; "  <!-- DO NOT TOUCH -->
```

---

## Dark Mode: The Prefix Trap

### The Problem
When using `prefix(tm)`, dark mode variants need manual prefix in styles.css:

```css
/* ❌ WRONG - dark mode won't work */
@layer theme {
  .dark {
    --color-bg-base: oklch(0.23 0.01 270);
  }
}

/* ✅ CORRECT - must prefix .dark selector */
@layer theme {
  .tm\:dark {
    --color-bg-base: oklch(0.23 0.01 270);
  }
}
```

### Dark Mode Variant Selector
Must match main project exactly:

```css
/* In styles.css */
@custom-variant dark (&:is(.dark *));  /* Match main project */
```

### In Templates
Dark mode classes get DOUBLE prefix automatically:

```html
<!-- You write: -->
class="tm:bg-bg-base"

<!-- Tailwind generates: -->
.tm\:bg-bg-base { background-color: var(--color-bg-base); }
.tm\:dark\:bg-bg-base { background-color: var(--color-bg-base); }
                ^      ^
          Both prefixes applied automatically!
```

---

## Custom <style> Tag Migration

For inline `<style>` tags (scrollbars, animations):

```css
/* ❌ BEFORE */
.menu-scrollable::-webkit-scrollbar-track {
  background-color: #e5e7eb;  /* hex color */
}

@media (prefers-color-scheme: dark) {
  .menu-scrollable::-webkit-scrollbar-track {
    background-color: #1f2937;
  }
}

/* ✅ AFTER */
.menu-scrollable::-webkit-scrollbar-track {
  background-color: oklch(0.91 0.00 286); /* semantic OKLCH */
}

.dark .menu-scrollable::-webkit-scrollbar-track {
  background-color: oklch(0.36 0.01 259); /* .dark class, not media query */
}
```

**Key changes:**
1. Hex → OKLCH semantic colors
2. `@media (prefers-color-scheme: dark)` → `.dark` selector
3. Match token values from styles.css

---

## Complete Token Reference

### Surface Elevation (3 levels)
```
bg-base     → Base surfaces (white/dark gray)
bg-raised   → Elevated (cards, inputs)
bg-hover    → Hover states, interactive elements
```

### Text Hierarchy (4 levels + special)
```
text-primary      → Headings, main content
text-secondary    → Labels, secondary info
text-muted        → Tertiary, helper text
text-placeholder  → Input placeholders
text-on-primary   → Text ON colored backgrounds (MD3 contrast pairing)
```

### Interactive Colors
```
primary-base      → Brand color
primary-hover     → Hover state
primary-bg        → Light tint background
border-base       → Standard borders
border-focus      → Focus rings
```

### State Colors
```
error-base, error-bg, error-border, error-text
success-base, success-bg, success-border, success-text
```

### Z-Index Scale
```
z-dropdown: 1000
z-sticky: 1020
z-modal-backdrop: 1040
z-modal: 1050
```

---

## Migration Checklist (Per Template)

1. ✅ **Read original template** - understand what's there
2. ✅ **ONLY modify `class="..."`** - nothing else
3. ✅ **Add `tm:` prefix** to every Tailwind class
4. ✅ **Map colors** to semantic tokens (see table above)
5. ✅ **Keep x-init, x-data, Alpine directives** exactly as-is
6. ✅ **Document mapping decisions** in template footer comment
7. ✅ **Note any gaps** (missing tokens, edge cases)
8. ✅ **Test one template** before moving to next

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Modifying Alpine.js
```html
❌ DON'T: Change x-show="show" to x-show="isOpen"
❌ DON'T: Modify x-init positioning logic
❌ DON'T: Touch x-data configuration
```

### ❌ Mistake 2: Removing Important Classes
```html
❌ DON'T: Remove x-cloak (prevents flash)
❌ DON'T: Remove transition classes
❌ DON'T: Remove arbitrary values if they're critical (like min-h-[44px] for touch targets)
```

### ❌ Mistake 3: Inconsistent Token Usage
```html
❌ WRONG: Mix old and new
class="tm:bg-bg-base text-gray-900"
         ^              ^
      Migrated      Not migrated

✅ CORRECT: All classes migrated
class="tm:bg-bg-base tm:text-text-primary"
```

### ❌ Mistake 4: Forgetting Hover/Focus Prefixes
```html
❌ WRONG: hover:bg-primary-base
✅ CORRECT: hover:tm:bg-primary-base
```

---

## Key Insights from Migration

### 1. Z-Index Requires Manual Utilities
Unlike colors, z-index tokens don't auto-generate. Must add to `@layer utilities`.

### 2. Dark Mode Needs Explicit Prefix in Layers
The `prefix(tm)` affects `@layer theme` selectors - must write `.tm\:dark`.

### 3. Original Template Complexity Must Be Preserved
Mobile positioning JavaScript in x-init is critical - don't touch it.

### 4. MD3 "On-Color" Pattern
`text-on-primary` is for text ON primary-colored backgrounds (contrast pairing).

### 5. Three-Level Elevation is Sufficient
- bg-base (page/container)
- bg-raised (cards/inputs)  
- bg-hover (interactive states)

More levels create confusion without benefit.

---

## Testing Strategy

1. **Replace ONE template** at a time
2. **Rebuild CSS**: `npm run build`
3. **Test in browser**:
   - Light mode works?
   - Dark mode toggles?
   - Interactive states work?
   - Z-index stacking correct?
4. **Fix issues** before moving to next template
5. **Document learnings** for next template

---

## Quick Reference: Original → Migrated

```html
<!-- ORIGINAL -->
<div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-white/10">
  <button class="text-indigo-500 hover:bg-gray-100">Click</button>
</div>

<!-- MIGRATED -->
<div class="tm:bg-bg-base tm:border tm:border-border-base">
  <button class="tm:text-primary-base hover:tm:bg-bg-hover">Click</button>
</div>
```

**Remember:** Only the `class=""` attribute changed. Everything else identical.
