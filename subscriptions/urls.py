from django.urls import path

from . import views

app_name = "subscriptions"

urlpatterns = [
    path("", views.tier_picker, name="tier_picker"),
    path("checkout/<str:tier>/", views.checkout, name="checkout"),
    path("check-coupon/", views.check_coupon, name="check_coupon"),
    path("promptpay/<str:charge_id>/status/", views.promptpay_status, name="promptpay_status"),
    path("success/", views.checkout_success, name="checkout_success"),
]
