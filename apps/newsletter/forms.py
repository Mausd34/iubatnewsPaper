"""newsletter/forms.py"""

from django import forms

from .models import NewsletterEmail, Subscriber


class SubscribeForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "w-full rounded-l-lg px-4 py-2 text-gray-900 "
                     "focus:outline-green-700",
            "placeholder": "you@example.com",
            "aria-label": "Email address",
        })
    )
    full_name = forms.CharField(
        max_length=120, required=False, widget=forms.HiddenInput()
    )

    def clean_email(self):
        return self.cleaned_data["email"].lower().strip()


class NewsletterComposeForm(forms.ModelForm):
    class Meta:
        model = NewsletterEmail
        fields = ("subject", "body")
        widgets = {
            "subject": forms.TextInput(attrs={
                "class": "w-full rounded-lg border-gray-300 "
                         "focus:border-green-700 focus:ring-green-700",
                "placeholder": "This week at IUBAT…",
            }),
            "body": forms.Textarea(attrs={
                "rows": 14,
                "class": "w-full rounded-lg border-gray-300 "
                         "focus:border-green-700 focus:ring-green-700",
            }),
        }
