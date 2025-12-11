# How to Use the Tag-Me Widget in Standalone Forms

This guide shows how to use the `TagMeSelectMultipleWidget` in forms that are not backed by a model with `TagMeCharField`.

## When to Use Standalone Mode

Use standalone mode when:

- Your form doesn't have a model
- Your tag choices come from an external source (API, service, computed)
- You want the tag-me UI without the database-backed tag management

## Standalone Mode Behaviour

When you provide `choices` explicitly, the widget operates in **standalone mode** with these automatic settings:

| Setting | Standalone Behaviour | Reason |
|---------|---------------------|--------|
| `permitted_to_add_tags` | **Forced False** | No backend to save new tags |
| `add_tag_url` | **Ignored** | No endpoint exists |
| `mgmt_url` | **Ignored** | No tag management available |
| `help_url` | **Allowed** | Documentation link still useful |

This ensures the widget behaves safely as a selection-only control.

## Basic Usage: Static Choices

For choices that are the same for all users:

```python
from django import forms
from tag_me.forms.fields import TagMeCharField
from tag_me.widgets import TagMeSelectMultipleWidget


class CategoryForm(forms.Form):
    categories = TagMeCharField(
        required=False,
        widget=TagMeSelectMultipleWidget(
            choices=['Technology', 'Science', 'Arts', 'Sports'],
            multiple=True,
            # permitted_to_add_tags is automatically False in standalone mode
        )
    )
```

## Dynamic Choices Per User

When choices vary per user or request, instantiate the widget in the form's `__init__` method:

```python
from django import forms
from tag_me.forms.fields import TagMeCharField
from tag_me.widgets import TagMeSelectMultipleWidget


def get_tags_for_user(user):
    """Your logic to fetch available tags for this user."""
    # Example: from a service, API, or computed
    return ['Tag A', 'Tag B', 'Tag C']


class ProjectForm(forms.Form):
    tags = TagMeCharField(required=False)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tags'].widget = TagMeSelectMultipleWidget(
            choices=get_tags_for_user(user),
            multiple=True,
            help_url='/docs/tags/',  # Help URL is still allowed
        )
```

In your view:

```python
def project_view(request):
    form = ProjectForm(user=request.user)
    return render(request, 'project_form.html', {'form': form})
```

> **Important:** Always instantiate the widget in `__init__` when choices are dynamic.
> Defining the widget at class level causes all form instances to share the same
> widget instance with the same choices.

## Single Selection

To allow only one selection (like a dropdown):

```python
class PriorityForm(forms.Form):
    priority = TagMeCharField(
        widget=TagMeSelectMultipleWidget(
            choices=['Low', 'Medium', 'High', 'Critical'],
            multiple=False,  # Single selection only
        )
    )
```

## Widget Parameters

| Parameter | Type | Default | Standalone |Description |
|-----------|------|---------|------------|------------|
| `choices` | list, str, or callable | None | Required | Available tag options |
| `multiple` | bool | True | ✓ | Allow multiple selections |
| `permitted_to_add_tags` | bool | True | **Forced False** | Allow creating new tags |
| `auto_select_new_tags` | bool | True | ✓ | Auto-select newly created tags |
| `display_number_selected` | int | 2 | ✓ | Max pills shown before "+N more" |
| `add_tag_url` | str | "" | **Ignored** | URL endpoint for creating new tags |
| `help_url` | str | "" | ✓ | URL for help documentation |
| `mgmt_url` | str | "" | **Ignored** | URL for tag management |
| `template` | str | "tag_me/tag_me_select.html" | ✓ | Custom template path |

## Why Use TagMeCharField (Not CharField)

Always pair the widget with `TagMeCharField` from `tag_me.forms.fields`:

```python
from tag_me.forms.fields import TagMeCharField  # Use this

# NOT: from django import forms; forms.CharField
```

`TagMeCharField` processes submitted data through `FieldTagListFormatter` which:

- Sanitizes input (removes dangerous characters)
- Sorts tags alphabetically
- Removes duplicates
- Ensures consistent CSV format with trailing comma

## Handling Form Submission

```python
def project_view(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST, user=request.user)
        if form.is_valid():
            # form.cleaned_data['tags'] is a sanitized CSV string
            # e.g., "Tag A,Tag C," (sorted, trailing comma)
            tags = form.cleaned_data['tags']
            process_tags(tags)
    else:
        form = ProjectForm(user=request.user)

    return render(request, 'project_form.html', {'form': form})
```

## Pre-selecting Values (Edit Scenario)

To pre-select tags when editing:

```python
def edit_view(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    if request.method == 'POST':
        form = ProjectForm(request.POST, user=request.user)
        # ... handle submission
    else:
        form = ProjectForm(
            user=request.user,
            initial={'tags': item.tags}  # Pre-select existing tags
        )

    return render(request, 'edit_form.html', {'form': form})
```

## Validating Against Allowed Choices

The widget does not validate that submitted values are in the allowed choices.
Add validation in your form's `clean_` method if needed:

```python
class ProjectForm(forms.Form):
    tags = TagMeCharField(required=False)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.allowed_tags = get_tags_for_user(user)
        self.fields['tags'].widget = TagMeSelectMultipleWidget(
            choices=self.allowed_tags,
        )

    def clean_tags(self):
        value = self.cleaned_data.get('tags', '')
        if not value:
            return value

        # Parse submitted tags
        submitted = {t.strip() for t in value.rstrip(',').split(',') if t.strip()}
        allowed = set(self.allowed_tags)

        invalid = submitted - allowed
        if invalid:
            raise forms.ValidationError(f"Invalid tags: {', '.join(invalid)}")

        return value
```

## Behaviour: Selected Value Not in Choices

If a previously selected tag is no longer in the available choices:

- The tag will still display as a selected pill
- The user can remove it
- The user cannot re-add it (not in choices list)

This allows users to see and remove outdated selections.

## Template Requirements

Ensure your template loads the tag-me assets:

```html
{% load tag_me_assets %}

<head>
    <!-- Your other CSS -->
    <link rel="stylesheet" href="{% tag_me_css %}">
</head>

<body>
    <!-- Your form -->
    {{ form.as_p }}

    <!-- Alpine.js must load first -->
    <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <!-- Then tag-me JS -->
    <script defer src="{% tag_me_js %}"></script>
</body>
```

Or use the combined tag:

```html
{% load tag_me_assets %}

<!-- Outputs both CSS link and JS script -->
{% tag_me_assets %}
```
