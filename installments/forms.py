from django import forms
from .models import InstallmentPlan


class InstallmentPlanForm(forms.ModelForm):

    class Meta:
        model = InstallmentPlan
        fields = ["total_installments", "down_payment"]