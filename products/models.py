from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=255)
   
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
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