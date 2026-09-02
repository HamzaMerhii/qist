from django.urls import path
from . import views

app_name = "sales"

urlpatterns = [
    path("", views.sale_list, name="sale_list"),
    path("create/", views.sale_create, name="sale_create"),
    path("<int:pk>/", views.sale_detail, name="sale_detail"),
    path("<int:pk>/items/", views.sale_items, name="sale_items"),
    path("<int:pk>/return/", views.sale_return, name="sale_return"),
    path("<int:pk>/edit/", views.sale_update, name="sale_update"),
    path("<int:pk>/items/", views.sale_items, name="sale_items"),
    path("<int:pk>/return/", views.sale_return, name="sale_return"),
    path("returns/", views.sale_return_list, name="sale_return_list"),
    path("returns/<int:pk>/", views.sale_return_detail, name="sale_return_detail"),
    path("<int:sale_id>/receipt/", views.printable_sale_receipt, name="sale_receipt"),
]