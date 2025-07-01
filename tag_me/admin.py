"""django-tag-me Admin file."""

from django.contrib import admin

from tag_me.models import TaggedFieldModel, UserTag

try:
    from unfold.admin import ModelAdmin as UnfoldModelAdmin

    BaseModelAdmin = UnfoldModelAdmin
except ImportError:
    BaseModelAdmin = admin.ModelAdmin

# Register your tag_me models here.

admin.site.register(TaggedFieldModel)


class TaggedFieldModelAdmin(BaseModelAdmin): ...


admin.site.register(UserTag)


class UserTagAdmin(BaseModelAdmin): ...
