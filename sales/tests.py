from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal

from customers.models import Customer
from products.models import Product
from .models import Sale, SaleItem


class SaleModelTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            full_name="Test Customer",
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
            total=Decimal("100.00"),
        )
        self.assertEqual(sale_item.sale, sale)
        self.assertEqual(sale_item.product, self.product)


class SaleViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="secret123")
        self.customer = Customer.objects.create(
            full_name="View Customer",
            email="view@example.com",
            phone="9876543210",
        )
        self.product = Product.objects.create(
            name="View Product",
            price=Decimal("150.00"),
            cost=Decimal("85.00"),
        )
        self.sale = Sale.objects.create(
            customer=self.customer,
            subtotal=Decimal("150.00"),
            discount=Decimal("0.00"),
            tax=Decimal("0.00"),
            total_amount=Decimal("150.00"),
            payment_type="cash",
            status="completed",
        )
        self.sale_item = SaleItem.objects.create(
            sale=self.sale,
            product=self.product,
            quantity=2,
            unit_price=Decimal("75.00"),
            total=Decimal("150.00"),
        )

    def test_sale_detail_view(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("sales:sale_detail", args=[self.sale.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "View Customer")

    def test_sale_items_view(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("sales:sale_items", args=[self.sale.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "View Product")

    def test_sale_return_view(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("sales:sale_return", args=[self.sale.pk]),
            {
                "reason": "Damaged item",
                f"quantity_{self.sale_item.pk}": "1",
                f"item_{self.sale_item.pk}": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.sale.returns.exists())
