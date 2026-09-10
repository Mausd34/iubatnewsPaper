"""Forms for registration, login and profile management."""

from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)
from django.contrib.auth.password_validation import validate_password

from .models import CustomUser
from .roles import CustomUserRole


class RegisterForm(UserCreationForm):
    """Public registration. New users join as readers or (pending) student
    contributors — faculty/editor/admin accounts are granted by staff."""

    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "student_id",
            "department",
            "batch",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only readers and student contributors may self-register.
        self.fields["role"].choices = [
            (CustomUserRole.READER, "Reader (read, comment & react)"),
            (CustomUserRole.STUDENT,
             "Student Contributor (submit articles for approval)"),
        ]
        self.fields["role"].initial = CustomUserRole.READER
        for name, field in self.fields.items():
            field.widget.attrs.setdefault(
                "class",
                "w-full rounded-lg border-gray-300 focus:border-green-700 "
                "focus:ring-green-700",
            )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already "
                                        "exists.")
        return email


class IUBATAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "w-full rounded-lg border-gray-300 focus:border-green-700 "
                "focus:ring-green-700",
            )


class ProfileUpdateForm(forms.ModelForm):
    """Users edit their own profile here (role is *not* exposed)."""

    class Meta:
        model = CustomUser
        fields = (
            "first_name",
            "last_name",
            "email",
            "student_id",
            "department",
            "batch",
            "phone",
            "bio",
            "profile_picture",
        )
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "profile_picture":
                field.widget.attrs.setdefault(
                    "class",
                    "w-full rounded-lg border-gray-300 focus:border-green-700 "
                    "focus:ring-green-700",
                )


class AdminUserEditForm(forms.ModelForm):
    """Staff form used in the dashboard's user-management area."""

    class Meta:
        model = CustomUser
        fields = (
            "role",
            "is_verified",
            "is_active",
            "department",
            "batch",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "w-full rounded-lg border-gray-300 focus:border-green-700 "
                "focus:ring-green-700",
            )
