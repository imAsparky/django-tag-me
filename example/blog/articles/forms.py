"""django-tag-me forms"""

from django import forms

# from tag_me.forms import TagMeModelForm
from tag_me.db.forms.mixins import TagMeModelFormMixin
from tag_me.widgets import TagMeSelectMultipleWidget

# from tag_me.forms import TagMeModelForm
from .models import Article, Author


class AuthorCreateForm(TagMeModelFormMixin, forms.ModelForm):
    """Author creation form"""

    class Meta:
        model = Author
        fields = [
            "name",
            "bio",
        ]
        labels = {
            "name": "Name",
            "bio": "Biography",
        }


class ArticleCreateForm(TagMeModelFormMixin, forms.ModelForm):
    """Article creation form"""

    class Meta:
        model = Article
        fields = [
            "tag",
            "author",
            "article",
            # "user_tag",
        ]
        labels = {
            "author": "Author",
            "article": "Article",
            "tag": "Tags", 
            # "user_tag": "User Tag",
        }
        widgets = {
        "user_tag": TagMeSelectMultipleWidget(),
        }


class ArticleListForm(forms.ModelForm):
    """Article list form"""

    class Meta:
        model = Article
        fields = [
            "tag",
            "author",
            "article",
            "user_tag",
        ]
        labels = {
            "author": "Author",
            "article": "Article",
            "tag": "Tags",
            "user_tag": "User Tag",
        }
