from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from customers.models import Customer
from installments.models import Sale, InstallmentPlan, Installment, Payment


@login_required
def admin_dashboard(request):
    today = date.today()

    total_sales = Sale.objects.aggregate(total=Sum("total"))["total"] or 0
    total_collected = Payment.objects.aggregate(total=Sum("amount"))["total"] or 0
    active_plans_qs = InstallmentPlan.objects.filter(status=InstallmentPlan.Status.ACTIVE)
    active_plans = active_plans_qs.count()

    outstanding_balance = sum((p.remaining_balance for p in active_plans_qs), 0)

    overdue_qs = Installment.objects.filter(due_date__lt=today).exclude(status=Installment.Status.PAID)
    overdue_amount = sum((i.amount_remaining for i in overdue_qs), 0)

    upcoming_qs = Installment.objects.filter(
        due_date__gte=today, due_date__lte=today + timedelta(days=14)
    ).exclude(status=Installment.Status.PAID).select_related("plan__sale__customer").order_by("due_date")[:5]

    overdue_list = overdue_qs.select_related("plan__sale__customer").order_by("due_date")[:5]

    recent_payments = Payment.objects.select_related(
        "installment__plan__sale__customer"
    ).order_by("-paid_at")[:3]
    recent_sales = Sale.objects.select_related("customer").order_by("-created_at")[:3]

    # 6-month sales trend for the chart — real totals, not fabricated
    month_points = []
    cursor = today.replace(day=1)
    buckets = []
    for i in range(5, -1, -1):
        year = cursor.year
        month = cursor.month - i
        while month <= 0:
            month += 12
            year -= 1
        buckets.append((year, month))
    for (year, month) in buckets:
        total = Sale.objects.filter(created_at__year=year, created_at__month=month).aggregate(
            total=Sum("total")
        )["total"] or 0
        month_points.append({"label": date(year, month, 1).strftime("%b"), "value": float(total)})

    chart_svg_points = ""
    if month_points:
        max_val = max((p["value"] for p in month_points), default=0) or 1
        n = len(month_points)
        coords = []
        for i, p in enumerate(month_points):
            x = round((i / max(n - 1, 1)) * 600, 1)
            y = round(180 - (p["value"] / max_val) * 160, 1)
            coords.append(f"{x},{y}")
        chart_svg_points = " ".join(coords)

    context = {
        "total_customers": Customer.objects.count(),
        "recent_customers": Customer.objects.order_by("-created_at")[:5],
        "total_sales": total_sales,
        "total_collected": total_collected,
        "outstanding_balance": outstanding_balance,
        "overdue_amount": overdue_amount,
        "active_plans": active_plans,
        "upcoming_installments": upcoming_qs,
        "overdue_installments": overdue_list,
        "recent_payments": recent_payments,
        "recent_sales": recent_sales,
        "chart_points": month_points,
        "chart_svg_points": chart_svg_points,
    }
    return render(request, "admin.html", context)


@login_required
def manager_dashboard(request):
    return render(request, "manager.html")


@login_required
def sales_dashboard(request):
    return render(request, "sales.html")
