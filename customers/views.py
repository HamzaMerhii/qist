from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
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