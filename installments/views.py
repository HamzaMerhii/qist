from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction

from .models import InstallmentPlan, Installment
from .forms import InstallmentPlanForm
from sales.models import Sale


@login_required
def plan_list(request):
    search_query = request.GET.get("search", "").strip()
    plans = InstallmentPlan.objects.select_related("sale__customer").all()

    if search_query:
        plans = plans.filter(
            Q(sale__id__icontains=search_query)
            | Q(sale__customer__full_name__icontains=search_query)
            | Q(status__icontains=search_query)
        )

    paginator = Paginator(plans, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(
        request,
        "plan_list.html",
        {"page_obj": page_obj, "search_query": search_query},
    )


@login_required
def plan_detail(request, pk):
    plan = get_object_or_404(
        InstallmentPlan.objects.select_related("sale__customer"), pk=pk
    )
    installments = plan.installments.all()
    return render(
        request,
        "plan_detail.html",
        {"plan": plan, "installments": installments},
    )


@login_required
@transaction.atomic
def create_plan_for_sale(request, sale_id):
    sale = get_object_or_404(Sale, pk=sale_id)

    if request.method == "POST":
        form = InstallmentPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.sale = sale

            # Calculate balances
            remaining = sale.total_amount - plan.down_payment
            plan.remaining_balance = remaining
            plan.save()

            # Schedule Calculation
            per_installment = (remaining / plan.total_installments).quantize(Decimal("0.01"))
            current_date = timezone.now().date()

            days_step = 30
            for i in range(1, plan.total_installments + 1):
                current_date = current_date + timedelta(days=days_step)
                Installment.objects.create(
                    plan=plan,
                    sequence_number=i,
                    amount_due=per_installment,
                    due_date=current_date,
                    original_due_date=current_date,
                    status="PENDING",
                )

            return redirect("installments:plan_detail", pk=plan.pk)
    else:
        form = InstallmentPlanForm(initial={"down_payment": Decimal("0.00")})

    return render(
        request,
        "plan_form.html",
        {"form": form, "sale": sale},
    )