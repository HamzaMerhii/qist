from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import UserProfile
from customers.models import Customer
from installments.models import InstallmentPayment, InstallmentPlan
from products.models import Category, Product
from sales.models import Sale, SaleItem, SaleReturn


class DashboardTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.admin = user_model.objects.create_superuser(
            username="dashboard_admin",
            password="test-password",
        )
        cls.cashier = user_model.objects.create_user(
            username="dashboard_cashier",
            password="test-password",
        )
        cls.cashier.profile.role = UserProfile.Role.CASHIER
        cls.cashier.profile.save(update_fields=["role"])

        cls.customer = Customer.objects.create(
            full_name="Dashboard Customer",
            phone="70000000",
        )
        cls.category = Category.objects.create(name="Dashboard Category")
        cls.low_stock_product = Product.objects.create(
            name="Low Stock Product",
            category=cls.category,
            cost=Decimal("10.00"),
            price=Decimal("15.00"),
            stock_quantity=3,
        )
        cls.out_of_stock_product = Product.objects.create(
            name="Out of Stock Product",
            category=cls.category,
            cost=Decimal("5.00"),
            price=Decimal("8.00"),
            stock_quantity=0,
        )
        cls.sale = Sale.objects.create(
            customer=cls.customer,
            subtotal=Decimal("100.00"),
            total_amount=Decimal("100.00"),
            payment_type="CASH",
            status="COMPLETED",
        )
        SaleItem.objects.create(
            sale=cls.sale,
            product=cls.low_stock_product,
            quantity=2,
            unit_price=Decimal("15.00"),
            total=Decimal("30.00"),
        )
        SaleReturn.objects.create(
            sale=cls.sale,
            refund_amount=Decimal("10.00"),
            reason="Dashboard test return",
        )

        cls.plan = InstallmentPlan.objects.create(
            sale=cls.sale,
            total_amount=Decimal("120.00"),
            down_payment=Decimal("20.00"),
            remaining_balance=Decimal("100.00"),
            number_of_months=3,
            status="ACTIVE",
        )
        today = timezone.localdate()
        InstallmentPayment.objects.create(
            plan=cls.plan,
            installment_number=1,
            amount_due=Decimal("50.00"),
            due_date=today - timedelta(days=1),
            status="PENDING",
        )
        InstallmentPayment.objects.create(
            plan=cls.plan,
            installment_number=2,
            amount_due=Decimal("50.00"),
            due_date=today,
            status="PENDING",
        )
        InstallmentPayment.objects.create(
            plan=cls.plan,
            installment_number=3,
            amount_due=Decimal("30.00"),
            due_date=today,
            paid_date=today,
            status="PAID",
        )

    def test_anonymous_user_is_redirected_to_login(self):
        dashboard_url = reverse("admin_dashboard")

        response = self.client.get(dashboard_url)

        self.assertRedirects(
            response,
            f"{reverse('users:login')}?next={dashboard_url}",
        )

    def test_admin_can_open_dashboards(self):
        self.client.force_login(self.admin)

        for url_name in ("admin_dashboard", "sales_dashboard"):
            with self.subTest(url_name=url_name):
                self.assertEqual(self.client.get(reverse(url_name)).status_code, 200)

    def test_cashier_can_only_open_cashier_dashboard(self):
        self.client.force_login(self.cashier)

        self.assertEqual(self.client.get(reverse("admin_dashboard")).status_code, 403)
        self.assertEqual(self.client.get(reverse("sales_dashboard")).status_code, 200)

    def test_user_with_unknown_role_is_denied(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="unknown_role",
            password="test-password",
        )
        self.client.force_login(user)
        UserProfile.objects.filter(user=user).update(role="UNKNOWN")

        response = self.client.get(reverse("sales_dashboard"))

        self.assertEqual(response.status_code, 403)

    def test_admin_dashboard_contains_business_overview(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("admin_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin.html")
        self.assertEqual(response.context["today_sales_count"], 1)
        self.assertEqual(response.context["today_sales_total"], Decimal("100.00"))
        self.assertEqual(response.context["month_refund_total"], Decimal("10.00"))
        self.assertEqual(response.context["outstanding_balance"], Decimal("100.00"))
        self.assertEqual(response.context["due_today_amount"], Decimal("50.00"))
        self.assertEqual(response.context["overdue_amount"], Decimal("50.00"))
        self.assertEqual(response.context["collected_today"], Decimal("30.00"))
        self.assertEqual(response.context["low_stock_count"], 1)
        self.assertEqual(response.context["out_of_stock_count"], 1)
        self.assertEqual(response.context["inventory_cost_value"], Decimal("30.00"))
        self.assertEqual(response.context["inventory_retail_value"], Decimal("45.00"))
        self.assertEqual(response.context["admin_users"], 1)
        self.assertEqual(response.context["cashier_users"], 1)

    def test_cashier_context_excludes_management_totals(self):
        self.client.force_login(self.cashier)

        response = self.client.get(reverse("sales_dashboard"))

        self.assertTemplateUsed(response, "sales.html")
        self.assertEqual(response.context["current_role"], UserProfile.Role.CASHIER)
        self.assertEqual(response.context["sales_scope"], "store")
        self.assertNotIn("total_users", response.context)
        self.assertNotIn("inventory_cost_value", response.context)

    def test_dashboard_uses_beirut_timezone(self):
        self.assertEqual(settings.TIME_ZONE, "Asia/Beirut")

# Create your tests here.
