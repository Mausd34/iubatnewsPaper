"""articles/forms.py — article submission and comments."""

from django import forms

from .models import Article, Comment

# TinyMCE is optional at import time; fall back to a plain textarea.
try:
    from tinymce.widgets import TinyMCE
    RICH_WIDGET = TinyMCE
except ImportError:  # pragma: no cover
    RICH_WIDGET = forms.Textarea


class ArticleForm(forms.ModelForm):
    """Used for both create and update. The view decides which workflow
    action (save draft / submit / publish) the author is allowed to take."""

    class Meta:
        model = Article
        fields = (
            "title",
            "category",
            "tags",
            "excerpt",
            "content",
            "featured_image",
            "image_caption",
        )
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "w-full rounded-lg border-gray-300 "
                         "focus:border-green-700 focus:ring-green-700",
                "placeholder": "Write a clear, catchy headline…",
            }),
            "category": forms.Select(attrs={
                "class": "w-full rounded-lg border-gray-300 "
                         "focus:border-green-700 focus:ring-green-700",
            }),
            "tags": forms.CheckboxSelectMultiple(),
            "excerpt": forms.Textarea(attrs={
                "rows": 3,
                "maxlength": 300,
                "class": "w-full rounded-lg border-gray-300 "
                         "focus:border-green-700 focus:ring-green-700",
                "placeholder": "A 1–2 sentence summary shown in article "
                               "cards and search results.",
            }),
            "content": RICH_WIDGET(attrs={"cols": 80, "rows": 30}),
            "image_caption": forms.TextInput(attrs={
                "class": "w-full rounded-lg border-gray-300",
                "placeholder": "Credit / describe the photo",
            }),
        }
        help_texts = {
            "tags": "Pick all that apply — tags power search and related "
                    "articles.",
        }

    def __init__(self, *args, author=None, **kwargs):
        self.author = author
        super().__init__(*args, **kwargs)
        # Only active categories are offered.
        self.fields["category"].queryset = (
            self.fields["category"].queryset.model.objects.active()
        )


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("body",)
        widgets = {
            "body": forms.Textarea(attrs={
                "rows": 3,
                "maxlength": 1000,
                "class": "w-full rounded-lg border-gray-300 "
                         "focus:border-green-700 focus:ring-green-700",
                "placeholder": "Share your thoughts… (be respectful)",
            }),
        }
        labels = {"body": "Join the discussion"}


class RejectArticleForm(forms.Form):
    """Editor rejection form — a reason is mandatory."""

    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            "rows": 4,
            "class": "w-full rounded-lg border-gray-300",
            "placeholder": "Explain what the author should change before "
                           "resubmitting…",
        }),
        min_length=10,
    )
