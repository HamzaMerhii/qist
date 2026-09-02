from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from customers.models import Customer
from products.models import Product
from .models import Sale, SaleItem, InstallmentPlan, Installment, Payment
from .forms import AddItemForm, SummaryForm, PlanConfigForm, RescheduleForm, PaymentForm
from . import wizard


# ---------------------------------------------------------------------------
# Sale creation wizard: Customer (pre-selected) -> Items -> Summary -> Payment
# Nothing hits the DB until the Payment step is confirmed.
# ---------------------------------------------------------------------------

@login_required
def sale_items(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    cart = wizard.get_cart(request, customer_id)

    query = request.GET.get("q", "").strip()
    results = Product.objects.filter(is_active=True) if hasattr(Product, "is_active") else Product.objects.all()
    if query:
        results = results.filter(Q(name__icontains=query))
    else:
        results = Product.objects.none()

    if request.method == "POST":
        action = request.POST.get("form_action")
        if action == "add_product":
            product = get_object_or_404(Product, pk=request.POST.get("product_id"))
            wizard.add_item(
                request, customer_id,
                description=product.name, sku=str(product.id), unit_price=product.price,
                quantity=1, product_id=product.id,
            )
            return redirect("sale_items", customer_id=customer_id)
        elif action == "add_custom":
            form = AddItemForm(request.POST)
            if form.is_valid():
                d = form.cleaned_data
                wizard.add_item(
                    request, customer_id,
                    description=d["description"], sku=d.get("sku", ""), unit_price=d["unit_price"],
                    quantity=d["quantity"], product_id=None,
                )
                return redirect("sale_items", customer_id=customer_id)
        elif action == "remove_item":
            wizard.remove_item(request, customer_id, int(request.POST.get("index")))
            return redirect("sale_items", customer_id=customer_id)
        elif action == "update_qty":
            wizard.update_item_qty(request, customer_id, int(request.POST.get("index")), request.POST.get("quantity"))
            return redirect("sale_items", customer_id=customer_id)
        elif action == "continue":
            if not cart["items"]:
                messages.error(request, "Add at least one item before continuing.")
            else:
                return redirect("sale_summary", customer_id=customer_id)

    custom_form = AddItemForm()
    items_with_totals = [
        {**item, "index": i, "line_total": wizard.cart_line_total(item)}
        for i, item in enumerate(cart["items"])
    ]
    return render(request, "sale_items.html", {
        "customer": customer,
        "items": items_with_totals,
        "items_subtotal": wizard.cart_subtotal(cart),
        "query": query,
        "results": results,
        "custom_form": custom_form,
    })


@login_required
def sale_summary(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    cart = wizard.get_cart(request, customer_id)
    if not cart["items"]:
        return redirect("sale_items", customer_id=customer_id)

    if request.method == "POST":
        form = SummaryForm(request.POST)
        if form.is_valid():
            cart["discount"] = str(form.cleaned_data["discount"] or 0)
            cart["tax"] = str(form.cleaned_data["tax"] or 0)
            wizard.save_cart(request, customer_id, cart)
            return redirect("sale_payment", customer_id=customer_id)
    else:
        form = SummaryForm(initial={"discount": cart.get("discount", 0), "tax": cart.get("tax", 0)})

    subtotal = wizard.cart_subtotal(cart)
    discount = Decimal(cart.get("discount", "0"))
    tax = Decimal(cart.get("tax", "0"))
    total = subtotal - discount + tax

    items_with_totals = [{**item, "line_total": wizard.cart_line_total(item)} for item in cart["items"]]
    return render(request, "sale_summary.html", {
        "customer": customer, "form": form, "items": items_with_totals,
        "subtotal": subtotal, "discount": discount, "tax": tax, "total": total,
    })


@login_required
def sale_payment(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    cart = wizard.get_cart(request, customer_id)
    if not cart["items"]:
        return redirect("sale_items", customer_id=customer_id)

    subtotal = wizard.cart_subtotal(cart)
    discount = Decimal(cart.get("discount", "0"))
    tax = Decimal(cart.get("tax", "0"))
    total = subtotal - discount + tax

    if request.method == "POST":
        payment_type = request.POST.get("payment_type")
        with transaction.atomic():
            sale = Sale.objects.create(
                customer=customer,
                description=", ".join(i["description"] for i in cart["items"])[:255],
                subtotal=subtotal, discount=discount, tax=tax, total=total,
                status=Sale.Status.COMPLETED if payment_type == "full" else Sale.Status.OPEN,
            )
            SaleItem.objects.bulk_create([
                SaleItem(
                    sale=sale, product_id=i["product_id"], description=i["description"],
                    sku=i.get("sku", ""), quantity=i["quantity"], unit_price=Decimal(i["unit_price"]),
                    discount_pct=Decimal(i.get("discount_pct", "0")),
                )
                for i in cart["items"]
            ])
        wizard.clear_cart(request, customer_id)

        if payment_type == "full":
            messages.success(request, f"Sale {sale.invoice_number} recorded as paid in full.")
            return redirect("customer_detail", pk=customer_id)
        return redirect("plan_configure", sale_id=sale.pk)

    return render(request, "sale_payment.html", {
        "customer": customer, "subtotal": subtotal, "discount": discount, "tax": tax, "total": total,
    })


@login_required
def sale_list(request):
    sales = Sale.objects.select_related("customer").order_by("-created_at")
    paginator = Paginator(sales, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    return render(request, "sale_list.html", {"page_obj": page_obj})


# ---------------------------------------------------------------------------
# Installment configuration + schedule
# ---------------------------------------------------------------------------

@login_required
def plan_configure(request, sale_id):
    sale = get_object_or_404(Sale, pk=sale_id)
    preview = None

    initial = {
        "down_payment": 0,
        "frequency": InstallmentPlan.Frequency.MONTHLY,
        "number_of_installments": 4,
        "first_due_date": timezone.localdate(),
    }

    if request.method == "POST":
        form = PlanConfigForm(request.POST, sale=sale, initial=initial)
        action = request.POST.get("action")
        if form.is_valid():
            data = form.cleaned_data
            temp_plan = InstallmentPlan(
                sale=sale,
                down_payment=data["down_payment"],
                frequency=data["frequency"],
                number_of_installments=data["number_of_installments"],
                first_due_date=data["first_due_date"],
            )
            if action == "generate":
                preview = temp_plan.generate_installments()
            elif action == "confirm":
                plan, _ = InstallmentPlan.objects.update_or_create(
                    sale=sale,
                    defaults={
                        "down_payment": data["down_payment"],
                        "frequency": data["frequency"],
                        "number_of_installments": data["number_of_installments"],
                        "first_due_date": data["first_due_date"],
                    },
                )
                plan.save_installments()
                return redirect("plan_detail", pk=plan.pk)
    else:
        form = PlanConfigForm(initial=initial, sale=sale)

    return render(request, "plan_configure.html", {"form": form, "sale": sale, "preview": preview})


@login_required
def plan_detail(request, pk):
    plan = get_object_or_404(InstallmentPlan, pk=pk)
    installments = plan.installments.all().prefetch_related("payments")
    return render(request, "plan_detail.html", {"plan": plan, "installments": installments})


@login_required
def plan_list(request):
    plans = InstallmentPlan.objects.select_related("sale", "sale__customer").order_by("-created_at")
    paginator = Paginator(plans, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    return render(request, "plan_list.html", {"page_obj": page_obj})


@login_required
def installment_reschedule(request, pk):
    installment = get_object_or_404(Installment, pk=pk)
    if request.method == "POST":
        form = RescheduleForm(request.POST, instance=installment)
        if form.is_valid():
            if not installment.is_rescheduled:
                form.instance.original_due_date = Installment.objects.get(pk=pk).due_date
                form.instance.is_rescheduled = True
            form.save()
            installment.refresh_status()
            return redirect("plan_detail", pk=installment.plan_id)
    else:
        form = RescheduleForm(instance=installment)
    return render(request, "installment_reschedule.html", {"form": form, "installment": installment})


# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------

@login_required
def record_payment(request, installment_id):
    installment = get_object_or_404(Installment, pk=installment_id)
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.installment = installment
            payment.recorded_by = request.user
            payment.save()
            installment.refresh_status()
            return redirect("payment_receipt", pk=payment.pk)
    else:
        form = PaymentForm(initial={"amount": installment.amount_remaining})
    return render(request, "record_payment.html", {"form": form, "installment": installment})


@login_required
def payment_receipt(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    return render(request, "payment_receipt.html", {"payment": payment})


@login_required
def payment_list(request):
    payments = Payment.objects.select_related(
        "installment", "installment__plan", "installment__plan__sale", "installment__plan__sale__customer"
    ).order_by("-paid_at")
    paginator = Paginator(payments, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    return render(request, "payment_list.html", {"page_obj": page_obj})
