from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from django.shortcuts import render

from sales.models import Sale, SaleReturn
from installments.models import InstallmentPlan, InstallmentPayment


@login_required
def admin_dashboard(request):
    today = date.today()

    total_sales = Sale.objects.aggregate(total=Sum("total_amount"))["total"] or 0

    total_collected = InstallmentPayment.objects.filter(
        status="PAID"
    ).aggregate(total=Sum("amount_due"))["total"] or 0

    outstanding_balance = InstallmentPlan.objects.filter(
        status="ACTIVE"
    ).aggregate(total=Sum("remaining_balance"))["total"] or 0

    overdue_qs = InstallmentPayment.objects.filter(
        status="PENDING", due_date__lt=today
    )
    overdue_amount = overdue_qs.aggregate(total=Sum("amount_due"))["total"] or 0

    active_plans = InstallmentPlan.objects.filter(status="ACTIVE").count()

    # Monthly sales totals for the chart (last 7 months)
    since = today.replace(day=1) - timedelta(days=210)
    monthly = (
        Sale.objects.filter(created_at__date__gte=since)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Sum("total_amount"))
        .order_by("month")
    )
    chart_labels = [m["month"].strftime("%b") for m in monthly]
    chart_values = [float(m["total"] or 0) for m in monthly]

    upcoming_payments = InstallmentPayment.objects.filter(
        status="PENDING", due_date__gte=today
    ).select_related("plan__sale__customer").order_by("due_date")[:5]

    overdue_payments = overdue_qs.select_related(
        "plan__sale__customer"
    ).order_by("due_date")[:5]

    recent_sales = Sale.objects.select_related("customer").order_by("-created_at")[:5]

    return render(request, "admin.html", {
        "total_sales": total_sales,
        "total_collected": total_collected,
        "outstanding_balance": outstanding_balance,
        "overdue_amount": overdue_amount,
        "active_plans": active_plans,
        "chart_labels": chart_labels,
        "chart_values": chart_values,
        "upcoming_payments": upcoming_payments,
        "overdue_payments": overdue_payments,
        "recent_sales": recent_sales,
    })


@login_required
def sales_dashboard(request):
    today = date.today()
    week_end = today + timedelta(days=7)

    todays_sales = Sale.objects.filter(created_at__date=today)
    sales_today_total = todays_sales.aggregate(total=Sum("total_amount"))["total"] or 0
    sales_today_count = todays_sales.count()

    collected_today = InstallmentPayment.objects.filter(
        status="PAID", paid_date=today
    ).aggregate(total=Sum("amount_due"))["total"] or 0

    due_this_week = InstallmentPayment.objects.filter(
        status="PENDING", due_date__gte=today, due_date__lte=week_end
    ).aggregate(total=Sum("amount_due"))["total"] or 0

    overdue_count = InstallmentPayment.objects.filter(
        status="PENDING", due_date__lt=today
    ).count()

    recent_sales = Sale.objects.select_related("customer").order_by("-created_at")[:6]

    upcoming_payments = InstallmentPayment.objects.filter(
        status="PENDING", due_date__gte=today
    ).select_related("plan__sale__customer").order_by("due_date")[:6]

    return render(request, "sales.html", {
        "sales_today_total": sales_today_total,
        "sales_today_count": sales_today_count,
        "collected_today": collected_today,
        "due_this_week": due_this_week,
        "overdue_count": overdue_count,
        "recent_sales": recent_sales,
        "upcoming_payments": upcoming_payments,
    })
