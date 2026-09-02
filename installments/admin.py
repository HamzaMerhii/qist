from django.contrib import admin
from .models import Sale, InstallmentPlan, Installment, Payment


class InstallmentInline(admin.TabularInline):
    model = Installment
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "description", "subtotal", "created_at")


@admin.register(InstallmentPlan)
class InstallmentPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "sale", "down_payment", "number_of_installments", "frequency", "status")
    inlines = [InstallmentInline]


@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    list_display = ("plan", "sequence", "due_date", "amount", "status")
    list_filter = ("status",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "installment", "amount", "method", "paid_at", "recorded_by")
