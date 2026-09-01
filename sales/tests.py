from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal

from customers.models import Customer
from products.models import Product
from .models import Sale, SaleItem


class SaleModelTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            name="Test Customer",
            email="test@example.com",
            phone="1234567890",
        )
        self.product = Product.objects.create(
            name="Test Product",
            price=Decimal("100.00"),
            cost=Decimal("50.00"),
        )

    def test_sale_creation(self):
        sale = Sale.objects.create(
            customer=self.customer,
            subtotal=Decimal("100.00"),
            discount=Decimal("10.00"),
            tax=Decimal("9.00"),
            total_amount=Decimal("99.00"),
            payment_type="cash",
            status="completed",
        )
        self.assertEqual(sale.customer, self.customer)
        self.assertEqual(sale.total_amount, Decimal("99.00"))

    def test_sale_item_creation(self):
        sale = Sale.objects.create(
            customer=self.customer,
            subtotal=Decimal("100.00"),
            discount=Decimal("0.00"),
            tax=Decimal("0.00"),
            total_amount=Decimal("100.00"),
            payment_type="card",
            status="pending",
        )
        sale_item = SaleItem.objects.create(
            sale=sale,
            product=self.product,
            quantity=1,
            unit_price=Decimal("100.00"),
        )
        self.assertEqual(sale_item.sale, sale)
        self.assertEqual(sale_item.product, self.product)
