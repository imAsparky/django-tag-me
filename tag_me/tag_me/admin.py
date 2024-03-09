"""django-tag-me Admin file."""

from django.contrib import admin

from tag_me.models import TaggedFieldModel, UserTag

# Register your tag_me models here.

admin.site.register(TaggedFieldModel)
admin.site.register(UserTag)
