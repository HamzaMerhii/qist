from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.utils import timezone

from accounts.models import UserProfile
from customers.models import Customer
from installments.models import InstallmentPayment, InstallmentPlan
from products.models import Category, Product
from sales.models import Sale, SaleItem, SaleReturn


LOW_STOCK_THRESHOLD = 5
ZERO = Decimal("0.00")
MONEY_FIELD = DecimalField(max_digits=18, decimal_places=2)


def _local_period_bounds(day):
    current_timezone = timezone.get_current_timezone()
    day_start = timezone.make_aware(datetime.combine(day, time.min), current_timezone)
    day_end = day_start + timedelta(days=1)

    month_start_date = day.replace(day=1)
    if month_start_date.month == 12:
        next_month_date = month_start_date.replace(
            year=month_start_date.year + 1,
            month=1,
        )
    else:
        next_month_date = month_start_date.replace(month=month_start_date.month + 1)

    month_start = timezone.make_aware(
        datetime.combine(month_start_date, time.min),
        current_timezone,
    )
    next_month = timezone.make_aware(
        datetime.combine(next_month_date, time.min),
        current_timezone,
    )
    return day_start, day_end, month_start, next_month


def _sum(queryset, field_name):
    return queryset.aggregate(total=Sum(field_name))["total"] or ZERO


def _operations_context():
    today = timezone.localdate()
    day_start, day_end, month_start, next_month = _local_period_bounds(today)

    today_sales = Sale.objects.filter(created_at__gte=day_start, created_at__lt=day_end)
    month_sales = Sale.objects.filter(
        created_at__gte=month_start,
        created_at__lt=next_month,
    )
    month_returns = SaleReturn.objects.filter(
        return_date__gte=month_start,
        return_date__lt=next_month,
    )

    unpaid_payments = InstallmentPayment.objects.exclude(status="PAID")
    due_today = unpaid_payments.filter(due_date=today)
    overdue = unpaid_payments.filter(due_date__lt=today)
    upcoming = unpaid_payments.filter(
        due_date__gt=today,
        due_date__lte=today + timedelta(days=7),
    )
    paid_today = InstallmentPayment.objects.filter(status="PAID", paid_date=today)

    low_stock = Product.objects.filter(
        stock_quantity__gt=0,
        stock_quantity__lte=LOW_STOCK_THRESHOLD,
    )
    out_of_stock = Product.objects.filter(stock_quantity=0)
    active_plans = InstallmentPlan.objects.filter(status="ACTIVE")

    inventory_cost = ExpressionWrapper(
        F("cost") * F("stock_quantity"),
        output_field=MONEY_FIELD,
    )
    inventory_retail = ExpressionWrapper(
        F("price") * F("stock_quantity"),
        output_field=MONEY_FIELD,
    )
    inventory_totals = Product.objects.aggregate(
        cost_value=Sum(inventory_cost),
        retail_value=Sum(inventory_retail),
    )

    return {
        "today": today,
        "low_stock_threshold": LOW_STOCK_THRESHOLD,
        "today_sales_count": today_sales.count(),
        "today_sales_total": _sum(today_sales, "total_amount"),
        "month_sales_count": month_sales.count(),
        "month_sales_total": _sum(month_sales, "total_amount"),
        "month_refund_total": _sum(month_returns, "refund_amount"),
        "month_return_count": month_returns.count(),
        "total_customers": Customer.objects.count(),
        "new_customers_month": Customer.objects.filter(
            created_at__gte=month_start,
            created_at__lt=next_month,
        ).count(),
        "total_products": Product.objects.count(),
        "total_categories": Category.objects.count(),
        "low_stock_count": low_stock.count(),
        "out_of_stock_count": out_of_stock.count(),
        "inventory_cost_value": inventory_totals["cost_value"] or ZERO,
        "inventory_retail_value": inventory_totals["retail_value"] or ZERO,
        "active_plan_count": active_plans.count(),
        "outstanding_balance": _sum(active_plans, "remaining_balance"),
        "due_today_count": due_today.count(),
        "due_today_amount": _sum(due_today, "amount_due"),
        "overdue_count": overdue.count(),
        "overdue_amount": _sum(overdue, "amount_due"),
        "upcoming_count": upcoming.count(),
        "upcoming_amount": _sum(upcoming, "amount_due"),
        "collected_today": _sum(paid_today, "amount_due"),
        "recent_sales": Sale.objects.select_related("customer")[:8],
        "due_today_payments": due_today.select_related(
            "plan__sale__customer"
        ).order_by("due_date", "id")[:8],
        "overdue_payments": overdue.select_related(
            "plan__sale__customer"
        ).order_by("due_date", "id")[:8],
        "upcoming_payments": upcoming.select_related(
            "plan__sale__customer"
        ).order_by("due_date", "id")[:8],
        "low_stock_products": Product.objects.filter(
            stock_quantity__lte=LOW_STOCK_THRESHOLD
        ).select_related("category").order_by("stock_quantity", "name")[:8],
        "recent_returns": SaleReturn.objects.select_related(
            "sale",
            "sale__customer",
        )[:8],
        "top_products": SaleItem.objects.values(
            "product_id",
            "product__name",
        ).annotate(
            quantity_sold=Sum("quantity"),
            sales_total=Sum("total"),
        ).order_by("-quantity_sold", "product__name")[:8],
    }


def get_admin_dashboard_context():
    context = _operations_context()
    role_counts = {
        row["role"]: row["total"]
        for row in UserProfile.objects.values("role").annotate(total=Count("id"))
    }
    user_model = get_user_model()

    context.update(
        {
            "page_title": "Administrator Overview",
            "current_role": UserProfile.Role.ADMIN,
            "total_users": user_model.objects.count(),
            "active_users": user_model.objects.filter(is_active=True).count(),
            "admin_users": role_counts.get(UserProfile.Role.ADMIN, 0),
            "cashier_users": role_counts.get(UserProfile.Role.CASHIER, 0),
        }
    )
    return context


def get_cashier_dashboard_context():
    operations = _operations_context()
    cashier_keys = {
        "today",
        "low_stock_threshold",
        "today_sales_count",
        "today_sales_total",
        "collected_today",
        "due_today_count",
        "due_today_amount",
        "overdue_count",
        "overdue_amount",
        "low_stock_count",
        "out_of_stock_count",
        "recent_sales",
        "due_today_payments",
        "overdue_payments",
        "low_stock_products",
    }
    context = {key: operations[key] for key in cashier_keys}
    context.update(
        {
            "page_title": "Cashier Daily Overview",
            "current_role": UserProfile.Role.CASHIER,
            # Sales do not yet store their creator, so these figures are the
            # store-wide daily totals rather than personal cashier totals.
            "sales_scope": "store",
        }
    )
    return context
