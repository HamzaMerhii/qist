from django import forms
from .models import InstallmentPlan


class InstallmentPlanForm(forms.ModelForm):
    class Meta:
        model = InstallmentPlan
        fields = ["number_of_months", "down_payment"]
        labels = {
            "number_of_months": "Duration (Months)",
            "down_payment": "Down Payment ($)",
        }
        widgets = {
            "number_of_months": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "value": 1}
            ),
            "down_payment": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "step": "0.01", "value": 0}
            ),
        }