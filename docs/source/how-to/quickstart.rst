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
        <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
        {{ form.media.js }}
    </body>
    </html>

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
    If your project doesn't use Tailwind CSS, add the CDN to your base template's ``<head>``:
    
    .. code-block:: html
    
        <script src="https://cdn.tailwindcss.com"></script>


Next Steps
----------

* :doc:`/how-to/installation` - Detailed installation and setup options
* :doc:`/how-to/customization` - Customize the widget appearance and behavior
* :doc:`/reference/fields` - Learn about TagMeCharField options
* :doc:`/reference/widgets` - Learn about widget configuration
