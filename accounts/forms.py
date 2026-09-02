from django import forms
from django.contrib.auth.models import User
from .models import UserProfile


class UserCreationWithRoleForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=UserProfile.Role.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            raise forms.ValidationError("Email address is required.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            user.profile.role = self.cleaned_data["role"]
            user.profile.save()
        return user


class UserUpdateForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=UserProfile.Role.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "is_active"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            raise forms.ValidationError("Email address is required.")
        # Exclude current user from unique email check on edit
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email