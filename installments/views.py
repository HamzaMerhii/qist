import calendar
from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from django.core.paginator import Paginator
from django.db.models import Q, Sum
from sales.models import Sale
from .models import InstallmentPlan, InstallmentPayment
from .forms import InstallmentPlanForm

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

def add_months(sourcedate, months):
    """Utility to add N months safely using standard library calendar."""
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


@login_required
@transaction.atomic
def create_plan_for_sale(request, sale_id):
    sale = get_object_or_404(Sale, pk=sale_id)

    if sale.total_amount <= Decimal("0.00"):
        messages.error(request, "Cannot create an installment plan for a sale with $0 total.")
        return redirect("sales:sale_detail", pk=sale.pk)

    existing_plan = getattr(sale, "installment_plan", None)
    if existing_plan:
        return redirect("installments:plan_detail", pk=existing_plan.pk)

    if request.method == "POST":
        form = InstallmentPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.sale = sale
            plan.total_amount = sale.total_amount
            
            # Guarantee number_of_months is at least 1
            months = max(1, plan.number_of_months or 1)
            plan.number_of_months = months

            down_payment = plan.down_payment or Decimal("0.00")
            remaining_balance = plan.total_amount - down_payment
            
            if remaining_balance <= Decimal("0.00"):
                messages.error(request, "Down payment cannot exceed or equal the total sale amount.")
                return render(request, "plan_form.html", {"form": form, "sale": sale})

            plan.remaining_balance = remaining_balance
            plan.status = "ACTIVE"
            plan.save()  # MUST SAVE BEFORE CREATING PAYMENTS FOR FOREIGNKEY RELATIONS

            # Calculate installments
            monthly_amount = round(remaining_balance / Decimal(str(months)), 2)
            start_date = plan.start_date or date.today()

            payments_to_create = []
            for i in range(1, months + 1):
                due_date = add_months(start_date, i)
                
                if i == months:
                    current_monthly = remaining_balance - (monthly_amount * Decimal(str(months - 1)))
                else:
                    current_monthly = monthly_amount

                payments_to_create.append(
                    InstallmentPayment(
                        plan=plan,
                        installment_number=i,
                        amount_due=current_monthly,
                        due_date=due_date,
                        status="PENDING",
                    )
                )

            # Bulk insert payments directly into database
            InstallmentPayment.objects.bulk_create(payments_to_create)

            messages.success(request, f"Installment plan created with {months} monthly payments.")
            return redirect("installments:plan_detail", pk=plan.pk)
    else:
        form = InstallmentPlanForm(initial={"total_amount": sale.total_amount})

    return render(
        request,
        "plan_form.html",
        {"form": form, "sale": sale},
    )


@login_required
def plan_detail(request, pk):
    plan = get_object_or_404(
        InstallmentPlan.objects.select_related("sale", "sale__customer"), 
        pk=pk
    )
    payments = plan.payments.all().order_by("installment_number")

    return render(
        request,
        "plan_detail.html",
        {"plan": plan, "payments": payments},
    )


@login_required
@transaction.atomic
def record_payment(request, payment_id):
    payment = get_object_or_404(
        InstallmentPayment.objects.select_related("plan"), 
        pk=payment_id
    )

    if payment.status != "PAID":
        payment.status = "PAID"
        payment.paid_date = date.today()
        payment.save()

        # Update remaining balance on plan
        plan = payment.plan
        plan.remaining_balance = max(Decimal("0.00"), plan.remaining_balance - payment.amount_due)
        
        # Check if entire plan is settled
        if not plan.payments.filter(status="PENDING").exists():
            plan.status = "COMPLETED"
        
        plan.save()
        messages.success(request, f"Payment #{payment.installment_number} recorded successfully.")

    return redirect("installments:plan_detail", pk=payment.plan.pk)



@login_required
def payment_ledger(request):
    """
    Displays all installment plans with Total Amount, Down Payment, 
    Collected Installments, Total Paid, and Remaining Balance.
    """
    query = request.GET.get("q", "").strip()

    plans = InstallmentPlan.objects.select_related(
        "sale__customer"
    ).annotate(
        installments_paid=Sum(
            "payments__amount_due",
            filter=Q(payments__status="PAID")
        )
    ).order_by("-created_at")

    if query:
        plans = plans.filter(
            Q(sale__customer__first_name__icontains=query) |
            Q(sale__customer__last_name__icontains=query) |
            Q(id__icontains=query)
        )

    plan_data = []
    for plan in plans:
        down_payment = plan.down_payment or 0
        collected_installments = plan.installments_paid or 0
        total_paid = down_payment + collected_installments
        remaining_balance = plan.total_amount - total_paid

        plan_data.append({
            "plan": plan,
            "down_payment": down_payment,
            "collected_installments": collected_installments,
            "total_paid": total_paid,
            "remaining_balance": max(remaining_balance, 0),
        })

    return render(
        request, 
        "payment_ledger.html", 
        {"plan_data": plan_data, "query": query}
    )
@login_required
def overdue_payments(request):
    """Dedicated queue for overdue installment payments."""
    today = date.today()
    overdue_list = InstallmentPayment.objects.filter(
        status="PENDING",
        due_date__lt=today
    ).select_related("plan__sale__customer").order_by("due_date")

    return render(
        request, 
        "overdue_payments.html", 
        {"overdue_list": overdue_list, "today": today}
    )


@login_required
def mark_payment_paid(request, payment_id):
    """Action view to mark an installment payment as PAID."""
    payment = get_object_or_404(InstallmentPayment, pk=payment_id)
    
    if request.method == "POST":
        payment.status = "PAID"
        payment.paid_date = date.today()
        payment.save()
        
        # Check if all payments in the plan are complete
        plan = payment.plan
        if not plan.payments.filter(status="PENDING").exists():
            plan.status = "COMPLETED"
            plan.save()
            
        messages.success(request, f"Payment #{payment.installment_number} marked as PAID.")
    
    # Redirect back to referring page or ledger
    next_url = request.POST.get("next", "installments:payment_ledger")
    return redirect(next_url)