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

The quickest way to verify is with the management command:

```bash
python manage.py tag_me check
```

This runs five integrity checks covering orphaned records, stale names, NULL FKs,
field name mismatches, and stale ContentTypes. If everything is clean, you'll see
all checks passing.

For a detailed breakdown including per-field tag counts:

```bash
python manage.py tag_me check --verbose
```

Alternatively, you can verify in the Django shell:

```python
from tag_me.models import UserTag, SystemTag

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

With the FK-based system, renaming models is now safe. Tag-me automatically detects
and repairs orphaned records during migration.

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
   When Django asks "Did you rename the BlogPost model to Article?", answer **yes**.

3. **Apply the migration:**
   ```bash
   python manage.py migrate
   ```

That's it. No additional steps required.

### What Happens Automatically

During `migrate`, tag-me's `post_migrate` handler:

1. Clears Django's `ContentType` cache (prevents stale lookups)
2. Registers fields via `update_or_create` using `content` FK + `field_name`
3. Detects any orphaned `TaggedFieldModel` records (where the old ContentType
   no longer maps to a model class)
4. Matches orphans to their replacements using field signature analysis
5. Migrates `UserTag` and `SystemTag` FK relationships to the replacement
6. Cleans up the orphan and stale ContentType

All tag relationships remain intact. No data is lost.

### When Django Uses DeleteModel + CreateModel

Sometimes Django generates `DeleteModel` + `CreateModel` instead of `RenameModel`
(e.g., if you rename the model and change fields in the same migration). This creates
a new ContentType rather than updating the existing one.

Tag-me handles this automatically via the orphan merger. It uses two strategies to
find the correct merge target:

- **Unique match** — only one candidate with the same app, field name, and tag type
- **Field signature matching** — compares the full set of tagged field names to
  disambiguate when multiple candidates exist

For a detailed walkthrough:

```bash
python manage.py tag_me help rename-workflow
```

### The `model_name` Fields

After a rename, the cached `model_name` fields are refreshed automatically when
`populate_registered_fields()` runs during migration:

```python
tagged_field = TaggedFieldModel.objects.first()
print(tagged_field.model_name)        # "Article" (updated automatically)
print(tagged_field.current_model_name) # "article" (from ContentType)
```

If you need to verify the update happened:

```bash
python manage.py tag_me check
```

The check command reports any stale `model_name` values that don't match their
ContentType.

---

## Troubleshooting

### Quick Health Check

The fastest way to diagnose any tag-me issue:

```bash
python manage.py tag_me check
```

This runs five integrity checks and reports the exact command to fix each issue found.
For detailed output:

```bash
python manage.py tag_me check --verbose
```

### Orphaned Records After Migration

If `tag_me check` reports orphaned `TaggedFieldModel` records:

```bash
# Preview what the merger will do
python manage.py tag_me fix-orphans --dry-run --verbose

# Apply the fix
python manage.py tag_me fix-orphans

# Verify
python manage.py tag_me check
```

The orphan merger matches orphaned records to their replacements using field
signatures. If it can't find a match (reported as "unresolved"), you can fix
manually in the Django shell:

```python
from django.contrib.contenttypes.models import ContentType
from tag_me.models import UserTag, TaggedFieldModel

# Find the orphan and the correct target
orphan = TaggedFieldModel.objects.get(id=<ORPHAN_ID>)
content_type = ContentType.objects.get_for_model(NewModelClass)
target = TaggedFieldModel.objects.get(content=content_type, field_name=orphan.field_name)

# Migrate FK relationships
UserTag.objects.filter(tagged_field=orphan).update(tagged_field=target)
SystemTag.objects.filter(tagged_field=orphan).update(tagged_field=target)

# Clean up
stale_ct = orphan.content
orphan.delete()
if stale_ct.model_class() is None:
    stale_ct.delete()
```

### Stale ContentType Cache

If you see unexpected behavior after manual database operations or a database
restore:

```bash
python manage.py tag_me clear-cache
python manage.py tag_me populate
python manage.py tag_me check
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

### Built-in Troubleshooting Guide

For common problems with shell-ready fix commands:

```bash
python manage.py tag_me help troubleshooting
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

### Management Command

```bash
python manage.py tag_me populate              # create/update all tags
python manage.py tag_me populate --user 42    # specific user
python manage.py tag_me check                 # data integrity audit
python manage.py tag_me check --verbose       # detailed breakdown
python manage.py tag_me fix-orphans --dry-run # preview orphan repair
python manage.py tag_me fix-orphans           # apply orphan repair
python manage.py tag_me clear-cache           # clear ContentType cache
python manage.py tag_me help                  # built-in documentation
```

---

## Summary

1. **Update tag-me** to the latest version
2. **Run migrations** to add FK fields
3. **Update custom queries** to use FK lookups instead of `model_name`
4. **Add `system_tag=True`** if using `choices` with TagMeCharField
5. **Enjoy model rename resilience** — rename models freely without breaking tags
6. **Use `tag_me check`** any time you want to verify data integrity

For detailed CLI documentation, see [How to Use the Tag-me CLI](how-to-management-command.rst).

For questions or issues, please open an issue on the tag-me repository.
