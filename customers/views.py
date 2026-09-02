from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q,Sum
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
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        customer.delete()
        return redirect("customers:customer_list")

    return render(
        request, "customer_confirm_delete.html", {"customer": customer}
    )

@login_required
def customer_detail(request, customer_id):
    """Detailed profile page showing customer sales, installment plans, and total balance."""
    customer = get_object_or_404(Customer, pk=customer_id)
    
    # Fetch all sales and installment plans for this customer
    sales = customer.sales.select_related("installment_plan").order_by("-created_at")
    
    # Calculate lifetime figures
    total_spent = sales.aggregate(Sum("total_amount"))["total_amount__sum"] or 0
    
    # Calculate total remaining balance across all active plans
    active_plans = [s.installment_plan for s in sales if hasattr(s, "installment_plan")]
    
    total_remaining = 0
    for plan in active_plans:
        paid_installments = plan.payments.filter(status="PAID").aggregate(
            Sum("amount_due")
        )["amount_due__sum"] or 0
        
        plan_paid = (plan.down_payment or 0) + paid_installments
        balance = plan.total_amount - plan_paid
        total_remaining += max(balance, 0)

    context = {
        "customer": customer,
        "sales": sales,
        "total_spent": total_spent,
        "total_remaining": total_remaining,
    }
    return render(request, "customer_detail.html", context)