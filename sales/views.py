from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.db import transaction
from django.contrib import messages

from .models import Sale, SaleItem, SaleReturn, SaleReturnItem
from .forms import SaleForm, SaleItemFormSet
from django.db.models import F
from products.models import Product

@login_required
def sale_list(request):
    search_query = request.GET.get("search", "").strip()
    sales = Sale.objects.select_related("customer").all()

    if search_query:
        sales = sales.filter(
            Q(customer__full_name__icontains=search_query)
            | Q(pk__icontains=search_query)
        )

    paginator = Paginator(sales, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "sale_list.html",
        {
            "page_obj": page_obj,
            "search_query": search_query,
        },
    )


@login_required
@transaction.atomic
def sale_create(request):
    if request.method == "POST":
        form = SaleForm(request.POST)
        formset = SaleItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            sale = form.save(commit=False)
            
            subtotal = Decimal("0.00")
            sale.subtotal = Decimal("0.00")
            sale.total_amount = Decimal("0.00")
            sale.status = "COMPLETED"
            sale.save()

            items = formset.save(commit=False)
            valid_items = [item for item in items if item.product_id and item.quantity]

            if not valid_items:
                messages.error(request, "Please select at least one product with a valid quantity.")
                transaction.set_rollback(True)
                return render(request, "sale_form.html", {"form": form, "formset": formset})

            for item in valid_items:
                # 1. Lock and fetch fresh product state directly from DB
                product = Product.objects.select_for_update().get(pk=item.product_id)

                # 2. Check stock against database value
                if product.stock_quantity < item.quantity:
                    messages.error(
                        request, 
                        f"Insufficient stock for {product.name} (Available: {product.stock_quantity})."
                    )
                    transaction.set_rollback(True)
                    return render(request, "sale_form.html", {"form": form, "formset": formset})

                # 3. Save line item pricing
                item.sale = sale
                item.unit_price = product.price
                item.discount = item.discount or Decimal("0.00")
                item.tax = item.tax or Decimal("0.00")
                item.total = (item.unit_price * Decimal(str(item.quantity))) - item.discount + item.tax
                subtotal += item.total
                item.save()

                # 4. Atomic inventory deduction directly in SQL
                Product.objects.filter(pk=product.pk).update(
                    stock_quantity=F("stock_quantity") - item.quantity
                )

            # 5. Finalize sale header totals
            sale.subtotal = subtotal
            sale.discount = sale.discount or Decimal("0.00")
            sale.tax = sale.tax or Decimal("0.00")
            sale.total_amount = subtotal - sale.discount + sale.tax
            sale.save()

            if sale.payment_type.upper() == "INSTALLMENT":
                return redirect("installments:create_plan", sale_id=sale.pk)

            return redirect("sales:sale_detail", pk=sale.pk)
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        form = SaleForm()
        formset = SaleItemFormSet()

    return render(request, "sale_form.html", {"form": form, "formset": formset})

@login_required
def sale_update(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == "POST":
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            return redirect("sales:sale_list")
    else:
        form = SaleForm(instance=sale)

    return render(request, "sale_form.html", {"form": form, "sale": sale})

@login_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale.objects.select_related("customer"), pk=pk)
    items = sale.items.select_related("product").all()
    returns = sale.returns.prefetch_related("items__sale_item__product").all()

    return render(
        request,
        "sale_detail.html",
        {"sale": sale, "items": items, "returns": returns},
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
@transaction.atomic
def sale_return(request, pk):
    sale = get_object_or_404(Sale.objects.select_related("customer"), pk=pk)
    items = sale.items.select_related("product").all()

    if request.method == "POST":
        reason = request.POST.get("reason", "").strip()
        selected_items = []
        refund_total = Decimal("0.00")

        # Extract numeric IDs strictly for inputs named exact pattern 'item_<id>'
        checked_item_ids = []
        for key in request.POST.keys():
            if key.startswith("item_"):
                suffix = key[5:]
                if suffix.isdigit() and request.POST.get(key) == "on":
                    checked_item_ids.append(int(suffix))

        if not checked_item_ids:
            return render(
                request,
                "sale_return.html",
                {
                    "sale": sale,
                    "items": items,
                    "error": "Please select at least one item to return.",
                },
            )

        # Retrieve items bound to this specific sale only
        for item_id in checked_item_ids:
            item = items.filter(pk=item_id).first()
            if not item:
                continue

            raw_qty = request.POST.get(f"quantity_{item.pk}", "0")
            try:
                quantity = int(raw_qty)
            except ValueError:
                quantity = 0

            if 0 < quantity <= item.quantity:
                selected_items.append((item, quantity))
                refund_total += item.unit_price * Decimal(str(quantity))

        if not selected_items:
            return render(
                request,
                "sale_return.html",
                {
                    "sale": sale,
                    "items": items,
                    "error": "Please enter a valid quantity for the selected items.",
                },
            )

        # 1. Create Return Log Header
        sale_return_obj = SaleReturn.objects.create(
            sale=sale,
            refund_amount=refund_total,
            reason=reason or "No reason provided",
        )

        # 2. Process stock & line items
        for item, quantity in selected_items:
            item_refund = item.unit_price * Decimal(str(quantity))

            SaleReturnItem.objects.create(
                sale_return=sale_return_obj,
                sale_item=item,
                quantity=quantity,
                refund_amount=item_refund,
            )

            # Restock inventory directly in DB
            Product.objects.filter(pk=item.product_id).update(
                stock_quantity=F("stock_quantity") + quantity
            )

            # Update line item or remove if 0
            if item.quantity == quantity:
                item.delete()
            else:
                item.quantity -= quantity
                item.discount = item.discount or Decimal("0.00")
                item.tax = item.tax or Decimal("0.00")
                item.total = (item.unit_price * Decimal(str(item.quantity))) - item.discount + item.tax
                item.save()

        # 3. Recalculate Sale Totals directly from DB
        remaining_items = sale.items.all()
        new_subtotal = sum((i.total for i in remaining_items), Decimal("0.00"))

        sale.subtotal = new_subtotal
        sale.discount = sale.discount or Decimal("0.00")
        sale.tax = sale.tax or Decimal("0.00")
        sale.total_amount = max(Decimal("0.00"), new_subtotal - sale.discount + sale.tax)

        # 4. Remove Sale if balance is 0 or no items remain
        if sale.total_amount <= Decimal("0.00") or not remaining_items.exists():
            sale.delete()
            messages.success(
                request, 
                f"Full return processed (${refund_total}). The sale was removed from sales."
            )
            return redirect("sales:sale_list")

        sale.save()
        messages.success(request, f"Successfully processed return. Refund: ${refund_total}")
        return redirect("sales:sale_detail", pk=sale.pk)

    # MUST explicitly return HttpResponse for GET requests
    return render(
        request, 
        "sale_return.html", 
        {"sale": sale, "items": items}
    )
@login_required
def sale_return_list(request):
    """Lists all processed sales returns."""
    search_query = request.GET.get("search", "").strip()
    returns = SaleReturn.objects.select_related("sale", "sale__customer").all()

    if search_query:
        returns = returns.filter(
            Q(sale__customer__full_name__icontains=search_query)
            | Q(sale__pk__icontains=search_query)
            | Q(pk__icontains=search_query)
        )

    paginator = Paginator(returns, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "sale_return_list.html",
        {
            "page_obj": page_obj,
            "search_query": search_query,
        },
    )


@login_required
def sale_return_detail(request, pk):
    """Displays details for a specific sale return, including returned items."""
    sale_return_obj = get_object_or_404(
        SaleReturn.objects.select_related("sale", "sale__customer"),
        pk=pk,
    )
    return_items = sale_return_obj.items.select_related("sale_item__product").all()

    return render(
        request,
        "sale_return_detail.html",
        {
            "sale_return": sale_return_obj,
            "return_items": return_items,
        },
    )

@login_required
def printable_sale_receipt(request, sale_id):
    """Clean, print-optimized receipt view for a completed sale."""
    sale = get_object_or_404(
        Sale.objects.prefetch_related("items__product"), 
        pk=sale_id
    )
    return render(request, "sale_receipt.html", {"sale": sale})