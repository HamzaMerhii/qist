from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.shortcuts import render

from customers.models import Customer
from installments.models import Sale, InstallmentPlan, Installment, Payment


def _date_range_from_request(request, default_days=30):
    today = date.today()
    start_str = request.GET.get("start")
    end_str = request.GET.get("end")
    try:
        start = date.fromisoformat(start_str) if start_str else today - timedelta(days=default_days)
    except ValueError:
        start = today - timedelta(days=default_days)
    try:
        end = date.fromisoformat(end_str) if end_str else today
    except ValueError:
        end = today
    return start, end


@login_required
def reports_home(request):
    return render(request, "reports_home.html")


@login_required
def sales_report(request):
    start, end = _date_range_from_request(request)
    sales = Sale.objects.filter(
        created_at__date__gte=start, created_at__date__lte=end
    ).select_related("customer").order_by("-created_at")

    totals = sales.aggregate(
        count=Count("id"), subtotal=Sum("subtotal"), discount=Sum("discount"),
        tax=Sum("tax"), total=Sum("total"),
    )

    by_status = sales.values("status").annotate(count=Count("id"), total=Sum("total")).order_by("status")

    return render(request, "sales_report.html", {
        "start": start, "end": end, "sales": sales, "totals": totals, "by_status": by_status,
    })


@login_required
def installment_report(request):
    start, end = _date_range_from_request(request, default_days=60)
    status_filter = request.GET.get("status", "")

    installments = Installment.objects.filter(
        due_date__gte=start, due_date__lte=end
    ).select_related("plan__sale__customer").order_by("due_date")

    if status_filter:
        installments = installments.filter(status=status_filter)

    totals = installments.aggregate(count=Count("id"), amount=Sum("amount"), late_fee=Sum("late_fee"))
    by_status = installments.values("status").annotate(count=Count("id"), amount=Sum("amount")).order_by("status")

    return render(request, "installment_report.html", {
        "start": start, "end": end, "installments": installments, "totals": totals,
        "by_status": by_status, "status_filter": status_filter,
        "status_choices": Installment.Status.choices,
    })


@login_required
def outstanding_report(request):
    plans = InstallmentPlan.objects.filter(
        status=InstallmentPlan.Status.ACTIVE
    ).select_related("sale__customer")

    rows = []
    for plan in plans:
        remaining = plan.remaining_balance
        if remaining > 0:
            rows.append({
                "customer": plan.sale.customer,
                "plan": plan,
                "total_financed": plan.total_financed,
                "total_paid": plan.total_paid,
                "remaining": remaining,
            })
    rows.sort(key=lambda r: r["remaining"], reverse=True)

    grand_total = sum((r["remaining"] for r in rows), 0)

    return render(request, "outstanding_report.html", {"rows": rows, "grand_total": grand_total})


@login_required
def collection_report(request):
    start, end = _date_range_from_request(request)
    payments = Payment.objects.filter(
        paid_at__date__gte=start, paid_at__date__lte=end
    ).select_related("installment__plan__sale__customer").order_by("-paid_at")

    totals = payments.aggregate(count=Count("id"), total=Sum("amount"))
    by_method = payments.values("method").annotate(count=Count("id"), total=Sum("amount")).order_by("-total")

    return render(request, "collection_report.html", {
        "start": start, "end": end, "payments": payments, "totals": totals, "by_method": by_method,
    })
