from django import forms
from .models import Customer

INPUT_CLASSES = (
    "w-full px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm "
    "text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 "
    "focus:ring-2 focus:ring-indigo-500/30 outline-none transition-all"
)


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["full_name", "phone", "email", "address"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "phone": forms.TextInput(attrs={"class": INPUT_CLASSES}),
            "email": forms.EmailInput(attrs={"class": INPUT_CLASSES}),
            "address": forms.Textarea(attrs={"class": INPUT_CLASSES, "rows": 3}),
        }

