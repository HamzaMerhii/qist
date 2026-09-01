# Generated manually to add the sales data model.

import decimal

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("customers", "0001_initial"),
        ("products", "0004_product_cost_alter_product_price"),
    ]

    operations = [
        migrations.CreateModel(
            name="Sale",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "subtotal",
                    models.DecimalField(
                        decimal_places=2,
                        default=decimal.Decimal("0.00"),
                        max_digits=12,
                    ),
                ),
                (
                    "discount",
                    models.DecimalField(
                        decimal_places=2,
                        default=decimal.Decimal("0.00"),
                        max_digits=12,
                    ),
                ),
                (
                    "tax",
                    models.DecimalField(
                        decimal_places=2,
                        default=decimal.Decimal("0.00"),
                        max_digits=12,
                    ),
                ),
                (
                    "total_amount",
                    models.DecimalField(decimal_places=2, max_digits=12),
                ),
                ("payment_type", models.CharField(max_length=20)),
                ("status", models.CharField(max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="sales",
                        to="customers.customer",
                    ),
                ),
            ],
            options={
                "db_table": "sales",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="SaleItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("quantity", models.PositiveIntegerField()),
                (
                    "unit_price",
                    models.DecimalField(decimal_places=2, max_digits=12),
                ),
                (
                    "discount",
                    models.DecimalField(
                        decimal_places=2,
                        default=decimal.Decimal("0.00"),
                        max_digits=12,
                    ),
                ),
                (
                    "tax",
                    models.DecimalField(
                        decimal_places=2,
                        default=decimal.Decimal("0.00"),
                        max_digits=12,
                    ),
                ),
                ("total", models.DecimalField(decimal_places=2, max_digits=12)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="sale_items",
                        to="products.product",
                    ),
                ),
                (
                    "sale",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="sales.sale",
                    ),
                ),
            ],
            options={
                "db_table": "sale_items",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="SaleReturn",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("return_date", models.DateTimeField(auto_now_add=True)),
                (
                    "refund_amount",
                    models.DecimalField(decimal_places=2, max_digits=12),
                ),
                ("reason", models.TextField()),
                (
                    "sale",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="returns",
                        to="sales.sale",
                    ),
                ),
            ],
            options={
                "db_table": "sale_returns",
                "ordering": ["-return_date"],
            },
        ),
        migrations.CreateModel(
            name="SaleReturnItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("quantity", models.PositiveIntegerField()),
                (
                    "refund_amount",
                    models.DecimalField(decimal_places=2, max_digits=12),
                ),
                (
                    "sale_item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="return_items",
                        to="sales.saleitem",
                    ),
                ),
                (
                    "sale_return",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="sales.salereturn",
                    ),
                ),
            ],
            options={
                "db_table": "sale_return_items",
                "ordering": ["id"],
            },
        ),
    ]
