# tag_me/docs/asset_loading.md (or in your Sphinx docs)

"""
Asset Loading Guide
===================

Tag-Me uses Vite for building assets with cache-busting hashes. There are multiple
ways to include the tag-me assets in your templates.

Option 1: Automatic (Recommended)
----------------------------------

The widget automatically includes its assets via Django's Media class:

.. code-block:: python

    # In your form
    class MyForm(TagMeModelFormMixin, forms.ModelForm):
        class Meta:
            model = MyModel
            fields = ['tags']
            widgets = {
                'tags': TagMeSelectMultipleWidget(),
            }

.. code-block:: html

    <!-- In your template -->
    {{ form.media }}  <!-- Automatically includes tag-me CSS and JS -->
    {{ form }}

Option 2: Manual Template Tags
-------------------------------

For more control, use the template tags:

.. code-block:: html

    {% load tag_me_assets %}
    
    <!DOCTYPE html>
    <html>
    <head>
        <!-- Alpine.js (required, load before tag-me) -->
        <script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/focus@3.x.x/dist/cdn.min.js"></script>
        <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
        
        <!-- Tag-Me assets -->
        <link rel="stylesheet" href="{% tag_me_css %}">
    </head>
    <body>
        <!-- Your content -->
        
        <script src="{% tag_me_js %}"></script>
    </body>
    </html>

Option 3: Combined Tag
-----------------------

Use the combined tag for quick inclusion:

.. code-block:: html

    {% load tag_me_assets %}
    
    <head>
        <!-- Alpine.js first -->
        <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
        
        <!-- Tag-Me assets (both CSS and JS) -->
        {% tag_me_assets %}
    </head>

Option 4: Manual Static References
-----------------------------------

If you need direct control:

.. code-block:: python

    from tag_me.assets import get_tag_me_js, get_tag_me_css
    from django.templatetags.static import static
    
    css_url = static(get_tag_me_css())
    js_url = static(get_tag_me_js())

Asset Manifest
--------------

Tag-Me uses Vite's manifest.json for cache-busting. The manifest is located at:

    tag_me/static/tag_me/dist/.vite/manifest.json

The asset loading functions automatically read this manifest to get the correct
hashed filenames. If the manifest is not found (e.g., in development), the
functions fall back to unhashed filenames.

Development vs Production
-------------------------

Development:
    npm run watch  # Rebuilds on file changes
    # Assets are unhashed for easier debugging

Production:
    npm run prod   # Creates optimized, hashed assets
    # Assets include cache-busting hashes

Troubleshooting
---------------

**Assets Not Loading:**

1. Check that you've run the build:
   
   .. code-block:: bash
   
       cd tag_me/frontend
       npm install
       npm run prod

2. Check that collectstatic has been run (for production):
   
   .. code-block:: bash
   
       python manage.py collectstatic

3. Check the manifest exists:
   
   .. code-block:: bash
   
       ls tag_me/static/tag_me/dist/.vite/manifest.json

**Wrong Asset Versions:**

Clear your browser cache or use hard refresh (Ctrl+Shift+R or Cmd+Shift+R).

**Alpine Not Found Error:**

Make sure Alpine.js is loaded before tag-me scripts:

.. code-block:: html

    <!-- Alpine BEFORE tag-me -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script src="{% tag_me_js %}"></script>
"""
