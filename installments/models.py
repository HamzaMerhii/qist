from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models

from customers.models import Customer

FREQUENCY_DAYS = {
    "weekly": 7,
    "biweekly": 14,
    "monthly": 30,
    "quarterly": 90,
}


class Sale(models.Model):
    """A sale/contract a customer is buying — the thing an installment plan gets configured for."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        OPEN = "open", "Open"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="sales")
    description = models.CharField(max_length=255, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sales"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Sale #{self.pk} — {self.customer.full_name}"

    @property
    def invoice_number(self):
        return f"SL-{self.pk:04d}" if self.pk else "SL-PENDING"


class SaleItem(models.Model):
    """A product/service line on a Sale, built during the 'Items' wizard step."""

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "products.Product", on_delete=models.SET_NULL, null=True, blank=True, related_name="sale_items"
    )
    description = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return self.description

    @property
    def line_total(self):
        gross = self.quantity * self.unit_price
        return (gross - (gross * self.discount_pct / 100)).quantize(Decimal("0.01"))

    @property
    def has_plan(self):
        return hasattr(self, "plan")


class InstallmentPlan(models.Model):
    """The generated payment schedule for a Sale. (Installment Configuration page)"""

    class Frequency(models.TextChoices):
        WEEKLY = "weekly", "Weekly"
        BIWEEKLY = "biweekly", "Bi-Weekly"
        MONTHLY = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    sale = models.OneToOneField(Sale, on_delete=models.CASCADE, related_name="plan")
    down_payment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    frequency = models.CharField(max_length=10, choices=Frequency.choices, default=Frequency.MONTHLY)
    number_of_installments = models.PositiveIntegerField(default=1)
    first_due_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "installment_plans"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Plan for {self.sale}"

    @property
    def total_financed(self):
        return self.sale.total - self.down_payment

    @property
    def total_paid(self):
        return self.installments.aggregate(total=models.Sum("payments__amount"))["total"] or Decimal("0")

    @property
    def remaining_balance(self):
        return self.total_financed - self.total_paid

    @property
    def collection_progress_pct(self):
        if self.total_financed <= 0:
            return 0
        return round((self.total_paid / self.total_financed) * 100, 1)

    @property
    def next_unpaid_installment(self):
        return self.installments.exclude(status=Installment.Status.PAID).order_by("due_date").first()

    def generate_installments(self):
        """Split total_financed into equal installments on the configured frequency.
        The last installment absorbs any rounding remainder.
        """
        from datetime import timedelta

        count = self.number_of_installments
        step = timedelta(days=FREQUENCY_DAYS.get(self.frequency, 30))
        base_amount = (self.total_financed / count).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        rows = []
        running_total = Decimal("0")
        for i in range(1, count + 1):
            due_date = self.first_due_date + step * (i - 1)
            if i == count:
                amount = self.total_financed - running_total
            else:
                amount = base_amount
                running_total += amount
            rows.append({"sequence": i, "due_date": due_date, "amount": amount})
        return rows

    def save_installments(self):
        self.installments.all().delete()
        Installment.objects.bulk_create([
            Installment(plan=self, sequence=row["sequence"], due_date=row["due_date"], amount=row["amount"])
            for row in self.generate_installments()
        ])


class Installment(models.Model):
    """A single due payment within a plan. (Plan Details schedule table)"""

    class Status(models.TextChoices):
        UPCOMING = "upcoming", "Upcoming"
        DUE = "due", "Due"
        OVERDUE = "overdue", "Overdue"
        PARTIALLY_PAID = "partially_paid", "Partially paid"
        PAID = "paid", "Paid"

    plan = models.ForeignKey(InstallmentPlan, on_delete=models.CASCADE, related_name="installments")
    sequence = models.PositiveIntegerField()
    due_date = models.DateField()
    original_due_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    late_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPCOMING)
    is_rescheduled = models.BooleanField(default=False)
    reschedule_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "installments"
        ordering = ["due_date"]
        unique_together = ("plan", "sequence")

    def __str__(self):
        return f"Installment {self.sequence} of {self.plan}"

    @property
    def amount_paid(self):
        return self.payments.aggregate(total=models.Sum("amount"))["total"] or Decimal("0")

    @property
    def amount_remaining(self):
        return (self.amount + self.late_fee) - self.amount_paid

    def refresh_status(self):
        from django.utils import timezone

        if self.amount_remaining <= 0:
            self.status = self.Status.PAID
        elif self.amount_paid > 0:
            self.status = self.Status.PARTIALLY_PAID
        elif self.due_date < timezone.localdate():
            self.status = self.Status.OVERDUE
        elif self.due_date == timezone.localdate():
            self.status = self.Status.DUE
        else:
            self.status = self.Status.UPCOMING
        self.save(update_fields=["status"])


class Payment(models.Model):
    """A recorded payment against an installment. (Record Payment page)"""

    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"
        CREDIT_CARD = "credit_card", "Credit Card"
        CHEQUE = "cheque", "Cheque"

    installment = models.ForeignKey(Installment, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.CASH)
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments_recorded"
    )
    paid_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payments"
        ordering = ["-paid_at"]

    def __str__(self):
        return f"Payment of {self.amount} for {self.installment}"

    @property
    def receipt_number(self):
        return f"RCPT-{self.pk:05d}" if self.pk else "RCPT-PENDING"
