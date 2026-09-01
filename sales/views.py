from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Sale
from .forms import SaleForm
from django.db.models import Q
from django.core.paginator import Paginator

@login_required
def sale_list(request):
    search_query = request.GET.get("search", "").strip()
    sales = Sale.objects.all()
    if search_query:
        sales = sales.filter(
            Q(customer__name__icontains=search_query)
        )
    paginator = Paginator(sales, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        "sales_list.html",
        {
            "page_obj": page_obj,
            "search_query": search_query,
        },
    )


@login_required
def sale_create(request):
    if request.method == "POST":
        form = SaleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("sale_list")
    else:
        form = SaleForm()
    return render(request, "sale_form.html", {"form": form})


@login_required
def sale_update(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == "POST":
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            return redirect("sale_list")
    else:
        form = SaleForm(instance=sale)
    return render(request, "sale_form.html", {"form": form})


@login_required
def sale_delete(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == "POST":
        sale.delete()
        return redirect("sale_list")
    return render(request, "sale_confirm_delete.html", {"sale": sale})
