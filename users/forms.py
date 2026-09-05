from django import forms
from django.contrib.auth.models import User

from .models import UserProfile


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    role = forms.ChoiceField(choices=UserProfile.Role.choices, initial=UserProfile.Role.CASHIER)

    class Meta:
        model = User
        fields = ["username", "email", "password", "role"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            user.profile.role = self.cleaned_data["role"]
            user.profile.save()
        return user


class UserRoleForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["role"]
