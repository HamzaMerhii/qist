from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Sale, SaleItem, SaleReturn, SaleReturnItem
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


@login_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale.objects.select_related("customer"), pk=pk)
    items = sale.items.select_related("product").all()
    return render(
        request,
        "sale_detail.html",
        {"sale": sale, "items": items},
    )


@login_required
def sale_items(request, pk):
    sale = get_object_or_404(Sale.objects.select_related("customer"), pk=pk)
    items = sale.items.select_related("product").all()
    return render(
        request,
        "sale_items.html",
        {"sale": sale, "items": items},
    )


@login_required
def sale_return(request, pk):
    sale = get_object_or_404(Sale.objects.select_related("customer"), pk=pk)
    items = sale.items.select_related("product").all()

    if request.method == "POST":
        reason = request.POST.get("reason", "").strip()
        selected_items = []
        refund_total = Decimal("0.00")

        for item in items:
            if request.POST.get(f"item_{item.pk}") == "on":
                quantity = int(request.POST.get(f"quantity_{item.pk}", 0) or 0)
                if quantity > 0:
                    selected_items.append((item, quantity))
                    refund_total += item.unit_price * quantity

        if not selected_items:
            return render(
                request,
                "sale_return.html",
                {"sale": sale, "items": items, "error": "Please select at least one item to return."},
            )

        sale_return = SaleReturn.objects.create(
            sale=sale,
            refund_amount=refund_total,
            reason=reason or "No reason provided",
        )

        for item, quantity in selected_items:
            SaleReturnItem.objects.create(
                sale_return=sale_return,
                sale_item=item,
                quantity=quantity,
                refund_amount=item.unit_price * quantity,
            )

        return redirect("sale_detail", pk=sale.pk)

    return render(request, "sale_return.html", {"sale": sale, "items": items})
