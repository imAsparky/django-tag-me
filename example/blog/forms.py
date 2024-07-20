"""blog Forms file."""

from django import forms

from tag_me.db.forms.mixins import TagMeModelFormMixin

from .models import Article


class ArticleTagsCreateForm(TagMeModelFormMixin, forms.ModelForm):
    """Article tags creation form"""

    class Meta:
        model = Article
        fields = "__all__"


class ArticleTagsUpdateForm(TagMeModelFormMixin, forms.ModelForm):
    """Article tags creation form"""

    class Meta:
        model = Article
        fields = "__all__"
