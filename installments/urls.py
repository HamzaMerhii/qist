from django.urls import path
from . import views

app_name = "installments"

urlpatterns = [
    path("", views.plan_list, name="plan_list"),
    path("create/<int:sale_id>/", views.create_plan_for_sale, name="create_plan"),
    path("<int:pk>/", views.plan_detail, name="plan_detail"),
    path("payment/<int:payment_id>/pay/", views.record_payment, name="record_payment"),
]