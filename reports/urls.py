from django.urls import path
from . import views

urlpatterns = [
    path("", views.reports_home, name="reports_home"),
    path("sales/", views.sales_report, name="sales_report"),
    path("installments/", views.installment_report, name="installment_report"),
    path("outstanding/", views.outstanding_report, name="outstanding_report"),
    path("collections/", views.collection_report, name="collection_report"),
]
