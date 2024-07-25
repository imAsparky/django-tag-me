"""blog Forms file."""

from django import forms

from tag_me.db.forms.mixins import TagMeModelFormMixin

from .models import Article


class ArticleCreateForm(TagMeModelFormMixin, forms.ModelForm):
    """Article tags creation form"""

    class Meta:
        model = Article
        fields = "__all__"
        exclude = ["tag", "user_tag2"]


class ArticleUpdateForm(TagMeModelFormMixin, forms.ModelForm):
    """Article tags creation form"""

    class Meta:
        model = Article
        fields = "__all__"
