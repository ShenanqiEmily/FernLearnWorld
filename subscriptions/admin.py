from django.contrib import admin

from .models import Subscription, Coupon, PaymentHistory, AITutorUsage


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user", "tier", "status", "start_date", "end_date", "auto_renew",
        "is_complimentary", "is_founding_member",
    )
    # is_complimentary editable straight from the list — no need to open
    # each row just to grant/revoke free access.
    list_editable = ("is_complimentary",)
    list_filter = ("tier", "status", "auto_renew", "is_complimentary", "is_founding_member", "is_trial")
    search_fields = ("user__username", "user__email")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "discount_value", "valid_from", "valid_until", "current_uses", "max_uses", "is_active", "is_founding_member")
    list_filter = ("discount_type", "is_active", "is_founding_member")
    search_fields = ("code",)


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "status", "coupon_used", "omise_charge_id", "created_at")
    list_filter = ("status",)
    search_fields = ("user__username", "user__email", "omise_charge_id")


@admin.register(AITutorUsage)
class AITutorUsageAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "count")
    list_filter = ("date",)
    search_fields = ("user__username",)
