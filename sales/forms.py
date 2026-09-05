from django import forms
from django.forms import inlineformset_factory
from .models import Sale, SaleItem
from products.models import Product  # Adjust import path if needed


class SaleForm(forms.ModelForm):
    PAYMENT_TYPE_CHOICES = [
        ("FULL", "Full Payment"),
        ("INSTALLMENT", "Installment Plan"),
    ]

    payment_type = forms.ChoiceField(choices=PAYMENT_TYPE_CHOICES)

    class Meta:
        model = Sale
        fields = ["customer", "payment_type", "discount", "tax"]


class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ["product", "quantity", "discount", "tax"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(stock_quantity__gt=0)
        self.fields["discount"].required = False
        self.fields["tax"].required = False


SaleItemFormSet = inlineformset_factory(
    Sale,
    SaleItem,
    form=SaleItemForm,
    extra=3,
    can_delete=True,
)