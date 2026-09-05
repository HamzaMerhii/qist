from datetime import date
from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from .models import Customer
from .forms import CustomerForm


@login_required
def customer_list(request):
    search_query = request.GET.get("search", "").strip()
    customers = Customer.objects.all()

    if search_query:
        customers = customers.filter(
            Q(full_name__icontains=search_query)
            | Q(phone__icontains=search_query)
            | Q(email__icontains=search_query)
        )

    paginator = Paginator(customers, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "customer_list.html",
        {"page_obj": page_obj, "search_query": search_query},
    )


@login_required
def customer_create(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("customers:customer_list")
    else:
        form = CustomerForm()

    return render(request, "customer_form.html", {"form": form})


@login_required
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect("customers:customer_list")
    else:
        form = CustomerForm(instance=customer)

    return render(
        request, "customer_form.html", {"form": form, "customer": customer}
    )


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    sales = customer.sales.order_by("-created_at")

    total_purchases = sales.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")

    plans = []
    for sale in sales:
        plan = getattr(sale, "installment_plan", None)
        if plan:
            plans.append(plan)

    total_paid = Decimal("0.00")
    outstanding = Decimal("0.00")
    overdue = Decimal("0.00")
    upcoming_installment = None
    next_unpaid_installment = None
    today = date.today()

    for plan in plans:
        outstanding += plan.remaining_balance
        total_paid += plan.total_amount - plan.remaining_balance
        overdue_payments = plan.payments.filter(status="PENDING", due_date__lt=today)
        overdue += overdue_payments.aggregate(total=Sum("amount_due"))["total"] or Decimal("0.00")

        candidate = plan.payments.filter(status="PENDING").order_by("due_date").first()
        if candidate and (
            next_unpaid_installment is None or candidate.due_date < next_unpaid_installment.due_date
        ):
            next_unpaid_installment = candidate
        if candidate and candidate.due_date >= today and (
            upcoming_installment is None or candidate.due_date < upcoming_installment.due_date
        ):
            upcoming_installment = candidate

    return render(
        request,
        "customer_detail.html",
        {
            "customer": customer,
            "sales": sales[:10],
            "total_purchases": total_purchases,
            "total_paid": total_paid,
            "outstanding": outstanding,
            "overdue": overdue,
            "upcoming_installment": upcoming_installment,
            "next_unpaid_installment": next_unpaid_installment,
        },
    )


@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        customer.delete()
        return redirect("customers:customer_list")

    return render(
        request, "customer_confirm_delete.html", {"customer": customer}
    )