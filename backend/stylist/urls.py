from django.urls import path

from . import views

app_name = "stylist"

urlpatterns = [
    path("", views.home, name="home"),
    path("requests/<uuid:request_id>/submitted/", views.submitted, name="submitted"),
    path("requests/<uuid:request_id>/status/", views.request_status, name="status"),
    path("requests/<uuid:request_id>/result/", views.result, name="result"),
]
