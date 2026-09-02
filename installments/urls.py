from django.urls import path
from . import views

app_name = "installments"

urlpatterns = [
    path("", views.plan_list, name="plan_list"),
    path("create/<int:sale_id>/", views.create_plan_for_sale, name="create_plan"),
    path("<int:pk>/", views.plan_detail, name="plan_detail"),
    path("payment/<int:payment_id>/pay/", views.record_payment, name="record_payment"),
    path("payments/", views.payment_ledger, name="payment_ledger"),
    path("overdue/", views.overdue_payments, name="overdue_payments"),
    path("payments/<int:payment_id>/pay/", views.mark_payment_paid, name="mark_payment_paid"),
]