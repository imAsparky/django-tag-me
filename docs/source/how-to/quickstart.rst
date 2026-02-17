Quickstart
==========

This guide will get you up and running with django-tag-me quickly.

Installation
------------

1. Install django-tag-me:

.. code-block:: bash

    pip install django-tag-me

2. Add to ``INSTALLED_APPS`` in your ``settings.py``:

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        'tag_me',
        # ...
    ]

3. Run migrations:

.. code-block:: bash

    python manage.py migrate tag_me


Frontend Requirements
---------------------

django-tag-me requires:

* **Alpine.js 3.x** - For interactive components
* **Tailwind CSS** - For styling (uses ``tm-`` prefix to avoid conflicts)


Basic Usage
-----------

1. In your ``models.py``:

.. code-block:: python

    from django.db import models
    from tag_me.models import TagMeCharField

    class YourModel(models.Model):
        tags = TagMeCharField(blank=True)

2. In your ``forms.py``:

.. code-block:: python

    from django import forms
    from tag_me.forms import TagMeModelFormMixin
    from .models import YourModel

    class YourForm(TagMeModelFormMixin, forms.ModelForm):
        class Meta:
            model = YourModel
            fields = ['tags']

3. In your base template (``base.html``):

.. code-block:: html

    <!DOCTYPE html>
    <html>
    <head>
        {% block extra_css %}{% endblock %}
        {{ form.media.css }}
    </head>
    <body>
        {% block content %}{% endblock %}

        {% block extra_js %}{% endblock %}
        {# tag-me JS must load before Alpine.js starts #}
        {{ form.media.js }}
        <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3/dist/cdn.min.js"></script>
    </body>
    </html>

.. important::
    The tag-me JavaScript (``{{ form.media.js }}``) must load **before**
    Alpine.js. It registers the Alpine component that the widget depends on.
    If Alpine starts before the component is registered, the widget will not
    function.

4. In your page template:

.. code-block:: html

    {% extends 'base.html' %}

    {% block content %}
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">Save</button>
    </form>
    {% endblock %}


That's it! You now have a working tag selection widget.

.. tip::
    If your project doesn't use Tailwind CSS, you can add the development CDN
    to your base template's ``<head>`` for testing:

    .. code-block:: html

        <script src="https://cdn.tailwindcss.com"></script>

    This is not recommended for production. See :doc:`/how-to/installation`
    for production CSS setup.


Form Autosave Integration
-------------------------

django-tag-me's widget implements a two-way event contract that makes it
compatible with form-level autosave, dirty-tracking, and draft restoration
systems.

**Save direction:** When a user adds or removes tags, the widget dispatches a
standard ``change`` event (with ``bubbles: true``) on its hidden input. Any
form-level listener — autosave, validation, or dirty-tracking — will
automatically detect tag changes without additional configuration.

**Restore direction:** When an external system (autosave, form pre-fill, test
harness) programmatically sets the hidden input's value, it can notify the
widget by dispatching a ``form-field:external-update`` custom event on that
input. The widget will re-read the value and update its visual state to match.

.. code-block:: javascript

    // Example: restoring a saved tag value externally
    const input = document.querySelector('input[name="tags"]');
    input.value = 'python,django,alpine,';
    input.dispatchEvent(
        new CustomEvent('form-field:external-update', { bubbles: true })
    );

No configuration is needed for the save direction — it works out of the box.
The restore direction requires the external system to dispatch the custom event
after setting the value.

.. note::
    The hidden input's value uses a trailing comma as a format sentinel
    (e.g. ``python,django,``). This ensures multi-word tags like
    ``machine learning`` are parsed correctly. The trailing comma is handled
    transparently by the widget and the Django field.


Next Steps
----------

* :doc:`/how-to/installation` - Detailed installation and setup options
* :doc:`/how-to/customization` - Customize the widget appearance and behavior
* :doc:`/reference/fields` - Learn about TagMeCharField options
* :doc:`/reference/widgets` - Learn about widget configuration
