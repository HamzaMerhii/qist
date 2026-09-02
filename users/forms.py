from django import forms
from django.contrib.auth.models import User

from .models import UserProfile

INPUT = (
    "w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm "
    "text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 "
    "focus:ring-2 focus:ring-indigo-500/30 outline-none transition-all"
)


class UserCreateForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": INPUT}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={"class": INPUT}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": INPUT}))
    role = forms.ChoiceField(choices=UserProfile.Role.choices, widget=forms.Select(attrs={"class": INPUT}))

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data.get("email", ""),
            password=self.cleaned_data["password"],
        )
        user.profile.role = self.cleaned_data["role"]
        user.profile.save()
        return user


class UserRoleForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["role"]
        widgets = {"role": forms.Select(attrs={"class": INPUT})}
