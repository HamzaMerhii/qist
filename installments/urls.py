from django.urls import path
from . import views

urlpatterns = [
    path("sales/", views.sale_list, name="sale_list"),
    path("sales/<int:customer_id>/items/", views.sale_items, name="sale_items"),
    path("sales/<int:customer_id>/summary/", views.sale_summary, name="sale_summary"),
    path("sales/<int:customer_id>/payment/", views.sale_payment, name="sale_payment"),
    path("configure/<int:sale_id>/", views.plan_configure, name="plan_configure"),
    path("", views.plan_list, name="plan_list"),
    path("<int:pk>/", views.plan_detail, name="plan_detail"),
    path("installment/<int:pk>/reschedule/", views.installment_reschedule, name="installment_reschedule"),
    path("payments/", views.payment_list, name="payment_list"),
    path("payments/<int:installment_id>/record/", views.record_payment, name="record_payment"),
    path("payments/receipt/<int:pk>/", views.payment_receipt, name="payment_receipt"),
]
