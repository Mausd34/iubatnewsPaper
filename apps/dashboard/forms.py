"""dashboard/forms.py"""

from django import forms

from apps.articles.models import Category


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "description", "icon", "order", "is_active")
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full rounded-lg border-gray-300 "
                         "focus:border-green-700 focus:ring-green-700",
            }),
            "description": forms.Textarea(attrs={
                "rows": 3,
                "class": "w-full rounded-lg border-gray-300",
            }),
            "icon": forms.TextInput(attrs={
                "class": "w-24 rounded-lg border-gray-300 text-center",
            }),
            "order": forms.NumberInput(attrs={
                "class": "w-24 rounded-lg border-gray-300",
            }),
        }
