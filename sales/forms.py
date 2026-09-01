from django import forms
from .models import Sale


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = [
            "customer",
            "subtotal",
            "discount",
            "tax",
            "total_amount",
            "payment_type",
            "status",
        ]
