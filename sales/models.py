from decimal import Decimal

from django.db import models

from customers.models import Customer
from products.models import Product


class Sale(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="sales",
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_type = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sales"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Sale #{self.pk}"


class SaleItem(models.Model):
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="sale_items",
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "sale_items"
        ordering = ["id"]

    def __str__(self):
        return f"Sale #{self.sale_id} - {self.product}"


class SaleReturn(models.Model):
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="returns",
    )
    return_date = models.DateTimeField(auto_now_add=True)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()

    class Meta:
        db_table = "sale_returns"
        ordering = ["-return_date"]

    def __str__(self):
        return f"Return #{self.pk} for sale #{self.sale_id}"


class SaleReturnItem(models.Model):
    sale_return = models.ForeignKey(
        SaleReturn,
        on_delete=models.CASCADE,
        related_name="items",
    )
    sale_item = models.ForeignKey(
        SaleItem,
        on_delete=models.CASCADE,
        related_name="return_items",
    )
    quantity = models.PositiveIntegerField()
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "sale_return_items"
        ordering = ["id"]

    def __str__(self):
        return f"Return #{self.sale_return_id} - item #{self.sale_item_id}"
