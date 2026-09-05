from django.db import models
from sales.models import Sale


class InstallmentPlan(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    sale = models.OneToOneField(
        Sale, on_delete=models.CASCADE, related_name="installment_plan"
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    down_payment = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2)
    number_of_months = models.IntegerField(default=1)
    start_date = models.DateField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="ACTIVE"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Plan for Sale #{self.sale_id}"


class InstallmentPayment(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("OVERDUE", "Overdue"),
    ]

    plan = models.ForeignKey(
        InstallmentPlan, on_delete=models.CASCADE, related_name="payments"
    )
    installment_number = models.IntegerField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="PENDING"
    )

    def __str__(self):
        return f"Payment #{self.installment_number} for Plan #{self.plan_id}"