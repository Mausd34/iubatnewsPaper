"""core/forms.py — contact form."""

from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={
            "class": "w-full rounded-lg border-gray-300 focus:border-green-700 "
                     "focus:ring-green-700",
        }),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "w-full rounded-lg border-gray-300 focus:border-green-700 "
                     "focus:ring-green-700",
        }),
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            "class": "w-full rounded-lg border-gray-300 focus:border-green-700 "
                     "focus:ring-green-700",
        }),
    )
    message = forms.CharField(
        min_length=10,
        widget=forms.Textarea(attrs={
            "rows": 6,
            "class": "w-full rounded-lg border-gray-300 focus:border-green-700 "
                     "focus:ring-green-700",
        }),
    )
