from django import forms
from .models import Sale, InstallmentPlan, Installment, Payment

INPUT = (
    "w-full bg-white border border-slate-300 rounded-lg py-2 px-3 text-sm text-slate-900 "
    "placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 "
    "focus:border-indigo-500 transition-all"
)


class AddItemForm(forms.Form):
    product_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    description = forms.CharField(max_length=255, widget=forms.TextInput(attrs={"class": INPUT, "placeholder": "Item name"}))
    sku = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={"class": INPUT}))
    unit_price = forms.DecimalField(min_value=0, decimal_places=2, widget=forms.NumberInput(attrs={"class": INPUT, "step": "0.01"}))
    quantity = forms.IntegerField(min_value=1, initial=1, widget=forms.NumberInput(attrs={"class": INPUT}))


class SummaryForm(forms.Form):
    discount = forms.DecimalField(min_value=0, decimal_places=2, required=False, initial=0, widget=forms.NumberInput(attrs={"class": INPUT, "step": "0.01"}))
    tax = forms.DecimalField(min_value=0, decimal_places=2, required=False, initial=0, widget=forms.NumberInput(attrs={"class": INPUT, "step": "0.01"}))




class PlanConfigForm(forms.Form):
    down_payment = forms.DecimalField(min_value=0, decimal_places=2, widget=forms.NumberInput(attrs={"class": INPUT}))
    frequency = forms.ChoiceField(choices=InstallmentPlan.Frequency.choices, widget=forms.Select(attrs={"class": INPUT}))
    number_of_installments = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={"class": INPUT}))
    first_due_date = forms.DateField(widget=forms.DateInput(attrs={"class": INPUT, "type": "date"}))

    def __init__(self, *args, sale=None, **kwargs):
        self.sale = sale
        super().__init__(*args, **kwargs)

    def clean_down_payment(self):
        down_payment = self.cleaned_data["down_payment"]
        if self.sale and down_payment > self.sale.total:
            raise forms.ValidationError("Down payment can't exceed the sale total.")
        return down_payment


class RescheduleForm(forms.ModelForm):
    class Meta:
        model = Installment
        fields = ["due_date", "reschedule_reason"]
        widgets = {
            "due_date": forms.DateInput(attrs={"class": INPUT, "type": "date"}),
            "reschedule_reason": forms.TextInput(attrs={"class": INPUT, "placeholder": "Reason (optional)"}),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount", "method", "reference", "notes"]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": INPUT, "step": "0.01"}),
            "method": forms.Select(attrs={"class": INPUT}),
            "reference": forms.TextInput(attrs={"class": INPUT}),
            "notes": forms.Textarea(attrs={"class": INPUT, "rows": 3}),
        }
