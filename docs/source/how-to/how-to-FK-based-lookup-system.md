# How to Upgrade to Tag-Me FK Lookup (Model Rename Resilience)

This guide walks you through upgrading an existing project to use tag-me's new FK-based lookup system, which provides resilience to Django model renames.

## Overview

### What Changed

Tag-me now uses foreign key relationships instead of string-based `model_name` lookups. This means:

- **Before:** Renaming a model would break tag lookups (orphaned records)
- **After:** Renaming a model requires only a migration; tag relationships remain intact

### Key Changes Summary

| Component | Old Behavior | New Behavior |
|-----------|--------------|--------------|
| `UserTag` lookup | `model_name` + `field_name` | `tagged_field` FK |
| `SystemTag` lookup | `model_name` + `field_name` | `tagged_field` FK |
| `TaggedFieldModel` lookup | `model_name` + `field_name` | `content` FK + `field_name` |
| `model_name` fields | Used for lookups | Cached for display only |

---

## Prerequisites

- Django 4.2 or later
- Existing tag-me installation
- Database backup (recommended)

---

## Step 1: Update Tag-Me

Update to the latest version of tag-me:

```bash
pip install --upgrade django-tag-me
```

Or if installing from source:

```bash
pip install -e /path/to/django-tag-me
```

---

## Step 2: Run Migrations

The update includes migrations that add FK fields and populate them from existing data.

```bash
python manage.py migrate tag_me
```

### What the Migration Does

1. Adds `tagged_field` FK to `UserTag` and `SystemTag` models
2. Populates the FK by matching existing `model_name` + `field_name` to `TaggedFieldModel` records
3. Updates constraints to use `content` + `field_name` instead of 5-field combinations

### Verify Migration Success

Run this in the Django shell to verify FK relationships are populated:

```python
from tag_me.models import UserTag, SystemTag, TaggedFieldModel

# Check UserTag FK population
orphaned_user_tags = UserTag.objects.filter(tagged_field__isnull=True).count()
print(f"UserTags without FK: {orphaned_user_tags}")

# Check SystemTag FK population  
orphaned_system_tags = SystemTag.objects.filter(tagged_field__isnull=True).count()
print(f"SystemTags without FK: {orphaned_system_tags}")

# If counts are > 0, see Troubleshooting section
```

---

## Step 3: Update Custom Code

If you have custom code that queries tag-me models, update it to use FK lookups.

### Querying UserTag Records

**Before (string-based lookup):**
```python
from tag_me.models import UserTag

# Old approach - fragile to model renames
user_tags = UserTag.objects.filter(
    user=request.user,
    model_name="BlogPost",
    field_name="tags",
)
```

**After (FK-based lookup):**
```python
from django.contrib.contenttypes.models import ContentType
from tag_me.models import UserTag, TaggedFieldModel

# New approach - resilient to model renames
content_type = ContentType.objects.get_for_model(BlogPost)
tagged_field = TaggedFieldModel.objects.get(
    content=content_type,
    field_name="tags",
)
user_tags = UserTag.objects.filter(
    user=request.user,
    tagged_field=tagged_field,
)
```

### Querying with Select Related

For better performance, use `select_related` to fetch the `TaggedFieldModel` in the same query:

```python
user_tags = UserTag.objects.filter(
    user=request.user,
).select_related('tagged_field', 'tagged_field__content')
```

### Using the New Properties

The models now include convenience properties for accessing current model information:

```python
from tag_me.models import UserTag

user_tag = UserTag.objects.first()

# Get current model name (lowercase, from ContentType)
print(user_tag.current_model_name)  # "blogpost"

# Get the actual model class
model_class = user_tag.current_model_class  # <class 'myapp.models.BlogPost'>

# Get proper-case model name
print(model_class.__name__)  # "BlogPost"
```

### Property Reference

| Property | Returns | Example |
|----------|---------|---------|
| `current_model_name` | Lowercase model name from ContentType | `"blogpost"` |
| `current_model_class` | The actual Django model class | `BlogPost` |

> **Note:** `current_model_name` returns lowercase because Django's `ContentType.model` field stores model names in lowercase. Use `current_model_class.__name__` for proper case.

---

## Step 4: Update Form Mixins Usage

If you use `AllFieldsTagMeModelFormMixin`, it now automatically uses FK lookups. No code changes required.

### How the Mixin Works Now

```python
# The mixin now queries like this internally:
tagged_models = TaggedFieldModel.objects.filter(tag_type="user")
user_tags = UserTag.objects.filter(user=self.user).select_related('tagged_field')

for tagged_model in tagged_models:
    user_tag = user_tags.get(tagged_field=tagged_model)  # FK lookup
    # ... creates form field
```

### Verifying Mixin Behavior

If you want to verify the FK lookup is working:

```python
from django.test.utils import CaptureQueriesContext
from django.db import connection

with CaptureQueriesContext(connection) as context:
    form = MyTagForm(user=request.user)

# Check queries use tagged_field_id, not model_name
for query in context.captured_queries:
    print(query['sql'])
    # Should see: WHERE "tag_me_usertag"."tagged_field_id" = ...
    # Should NOT see: WHERE "tag_me_usertag"."model_name" = ...
```

---

## Step 5: Update TagMeCharField Usage (If Using Choices)

If you use `TagMeCharField` with `choices`, you must now explicitly set `system_tag=True`:

**Before:**
```python
class BlogPost(models.Model):
    category = TagMeCharField(choices=CategoryChoices.choices)
```

**After:**
```python
class BlogPost(models.Model):
    category = TagMeCharField(choices=CategoryChoices.choices, system_tag=True)
```

This makes the distinction between system tags (predefined choices) and user tags (user-created) explicit.

---

## Step 6: Handle Model Renames (The Main Benefit)

With the FK-based system, renaming models is now safe. Here's the process:

### Renaming a Model

1. **Rename the model class:**
   ```python
   # Before
   class BlogPost(models.Model):
       tags = TagMeCharField()
   
   # After
   class Article(models.Model):
       tags = TagMeCharField()
   ```

2. **Create the migration:**
   ```bash
   python manage.py makemigrations
   ```

3. **Apply the migration:**
   ```bash
   python manage.py migrate
   ```

### What Happens Automatically

- `ContentType` updates to point to the new model name
- `TaggedFieldModel.content` FK still points to the correct ContentType
- `UserTag.tagged_field` FK still points to the correct TaggedFieldModel
- **All tag relationships remain intact**

### The `model_name` Fields

After a rename, the cached `model_name` fields will be stale:

```python
tagged_field = TaggedFieldModel.objects.first()
print(tagged_field.model_name)  # "BlogPost" (stale)
print(tagged_field.current_model_name)  # "article" (correct)
```

The stale `model_name` doesn't affect functionality because lookups use FKs. The field is refreshed automatically on the next migration when `SystemTagRegistry.populate_registered_fields()` runs.

---

## Troubleshooting

### Orphaned Records After Migration

If you have `UserTag` or `SystemTag` records without FK relationships:

```python
from django.contrib.contenttypes.models import ContentType
from tag_me.models import UserTag, TaggedFieldModel

# Find orphaned records
orphaned = UserTag.objects.filter(tagged_field__isnull=True)

for user_tag in orphaned:
    # Try to find the TaggedFieldModel by model_name
    try:
        # Get ContentType by model name
        ct = ContentType.objects.get(model=user_tag.model_name.lower())
        tagged_field = TaggedFieldModel.objects.get(
            content=ct,
            field_name=user_tag.field_name,
        )
        user_tag.tagged_field = tagged_field
        user_tag.save()
        print(f"Fixed: {user_tag}")
    except (ContentType.DoesNotExist, TaggedFieldModel.DoesNotExist):
        print(f"Cannot fix: {user_tag} - model or field no longer exists")
```

### Migration Conflicts

If you encounter migration conflicts:

```bash
# Check migration status
python manage.py showmigrations tag_me

# If needed, fake a migration (use with caution)
python manage.py migrate tag_me --fake
```

### Test Failures After Upgrade

Common issues and fixes:

| Error | Cause | Fix |
|-------|-------|-----|
| `KeyError: 'tagged_field'` | Test creating UserTag without FK | Add `tagged_field=` to test setup |
| `AssertionError: lowercase != ProperCase` | `current_model_name` returns lowercase | Use `current_model_class.__name__` for proper case |
| `IntegrityError: NOT NULL constraint` | `tagged_field` FK is required | Ensure TaggedFieldModel exists before creating UserTag |

### Verifying FK Integrity

Run this to check overall FK integrity:

```python
from tag_me.models import UserTag, SystemTag, TaggedFieldModel

def check_fk_integrity():
    issues = []
    
    # Check UserTag -> TaggedFieldModel
    for ut in UserTag.objects.select_related('tagged_field'):
        if ut.tagged_field is None:
            issues.append(f"UserTag {ut.id} has no tagged_field FK")
        elif ut.field_name != ut.tagged_field.field_name:
            issues.append(f"UserTag {ut.id} field_name mismatch")
    
    # Check SystemTag -> TaggedFieldModel
    for st in SystemTag.objects.select_related('tagged_field'):
        if st.tagged_field is None:
            issues.append(f"SystemTag {st.id} has no tagged_field FK")
    
    # Check TaggedFieldModel -> ContentType
    for tfm in TaggedFieldModel.objects.select_related('content'):
        if tfm.content is None:
            issues.append(f"TaggedFieldModel {tfm.id} has no content FK")
        elif tfm.content.model_class() is None:
            issues.append(f"TaggedFieldModel {tfm.id} points to deleted model")
    
    return issues

issues = check_fk_integrity()
if issues:
    print("Issues found:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("All FK relationships are valid")
```

---

## Quick Reference

### New Lookup Pattern

```python
from django.contrib.contenttypes.models import ContentType
from tag_me.models import TaggedFieldModel, UserTag

# 1. Get ContentType for your model
content_type = ContentType.objects.get_for_model(MyModel)

# 2. Get TaggedFieldModel by content + field_name
tagged_field = TaggedFieldModel.objects.get(
    content=content_type,
    field_name="my_field",
)

# 3. Query UserTag/SystemTag by tagged_field FK
user_tags = UserTag.objects.filter(tagged_field=tagged_field)
```

### New Model Properties

```python
# On TaggedFieldModel, UserTag, SystemTag:
obj.current_model_name   # Lowercase name from ContentType
obj.current_model_class  # Actual model class
```

### TagMeCharField with Choices

```python
# System tags (predefined choices) - requires system_tag=True
tags = TagMeCharField(choices=MyChoices.choices, system_tag=True)

# User tags (user-created) - no choices
tags = TagMeCharField()
```

---

## Summary

1. **Update tag-me** to the latest version
2. **Run migrations** to add FK fields
3. **Update custom queries** to use FK lookups instead of `model_name`
4. **Add `system_tag=True`** if using `choices` with TagMeCharField
5. **Enjoy model rename resilience** - rename models freely without breaking tags

For questions or issues, please open an issue on the tag-me repository.
