from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Customer
from .forms import CustomerForm
from installments.models import InstallmentPlan, Installment


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
        {
            "page_obj": page_obj,
            "search_query": search_query,
        },
    )


@login_required
def customer_create(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("customer_list")
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
            return redirect("customer_list")
    else:
        form = CustomerForm(instance=customer)
    return render(request, "customer_form.html", {"form": form})


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    sales = customer.sales.select_related("plan").order_by("-created_at")
    total_purchases = sales.aggregate(total=Sum("total"))["total"] or 0

    plans = InstallmentPlan.objects.filter(sale__customer=customer)
    total_paid = sum((p.total_paid for p in plans), 0)
    outstanding = sum((p.remaining_balance for p in plans), 0)

    today = timezone.localdate()
    overdue_qs = Installment.objects.filter(
        plan__sale__customer=customer, due_date__lt=today
    ).exclude(status=Installment.Status.PAID)
    overdue = sum((i.amount_remaining for i in overdue_qs), 0)

    next_unpaid = (
        Installment.objects.filter(plan__sale__customer=customer)
        .exclude(status=Installment.Status.PAID)
        .order_by("due_date")
        .first()
    )

    upcoming = (
        Installment.objects.filter(plan__sale__customer=customer, due_date__gte=today)
        .exclude(status=Installment.Status.PAID)
        .order_by("due_date")
        .first()
    )

    return render(request, "customer_detail.html", {
        "customer": customer,
        "sales": sales[:5],
        "total_purchases": total_purchases,
        "total_paid": total_paid,
        "outstanding": outstanding,
        "overdue": overdue,
        "next_unpaid_installment": next_unpaid,
        "upcoming_installment": upcoming,
    })


@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        customer.delete()
        return redirect("customer_list")
    return render(request, "customer_confirm_delete.html", {"customer": customer})
