from django.urls import path

from . import api_views

app_name = "stylist_api"

urlpatterns = [
    path("health/", api_views.health, name="health"),
    path("bootstrap/", api_views.bootstrap, name="bootstrap"),
    path("requests/", api_views.create_request, name="create_request"),
    path("requests/<uuid:request_id>/status/", api_views.request_status, name="request_status"),
    path("requests/<uuid:request_id>/", api_views.request_detail, name="request_detail"),
]
