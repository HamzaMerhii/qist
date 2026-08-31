from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    cost = models.DecimalField(
            max_digits=10, 
            decimal_places=2,
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.00
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "products"
        ordering = ["name"]
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return f"{self.name} ({self.id})"

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0