from decimal import Decimal
from django.db import models
from sales.models import Sale


class InstallmentPlan(models.Model):
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="installment_plans",
    )
    total_installments = models.PositiveIntegerField()
    down_payment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=50, default="ACTIVE")  # ACTIVE, COMPLETED, CANCELLED
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "installment_plans"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Plan #{self.id} (Sale #{self.sale_id})"


class Installment(models.Model):
    plan = models.ForeignKey(
        InstallmentPlan,
        on_delete=models.CASCADE,
        related_name="installments",
    )
    sequence_number = models.PositiveIntegerField()
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=50, default="PENDING")  # PENDING, PAID, OVERDUE
    late_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    original_due_date = models.DateField()

    class Meta:
        db_table = "installments"
        ordering = ["sequence_number"]

    def __str__(self):
        return f"Installment #{self.sequence_number} for Plan #{self.plan_id}"