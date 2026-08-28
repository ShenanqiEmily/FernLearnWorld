from datetime import timedelta
from decimal import Decimal

import omise
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import omise_client
from .models import Coupon, PaymentHistory, Subscription

TIER_LABELS = {
    "monthly": "รายเดือน",
    "yearly": "รายปี",
}

TIER_DURATION_DAYS = {
    "monthly": 30,
    "yearly": 365,
}


def tier_picker(request):
    # Deliberately public (no @login_required) — a pricing page needs to be
    # visible to anonymous visitors deciding whether to sign up at all, and
    # to Google for SEO. Actual purchase (checkout view below) still
    # requires login.
    yearly_monthly_equivalent = (omise_client.PRICING["yearly"] / 12).quantize(Decimal("1"))
    return render(request, "subscriptions/tier_picker.html", {
        "pricing": omise_client.PRICING,
        "yearly_monthly_equivalent": yearly_monthly_equivalent,
    })


def _get_valid_coupon(code):
    if not code:
        return None
    coupon = Coupon.objects.filter(code__iexact=code.strip()).first()
    if coupon and coupon.is_valid():
        return coupon
    return None


@login_required
@require_POST
def check_coupon(request):
    tier = request.POST.get("tier")
    if tier not in omise_client.PRICING:
        return HttpResponseBadRequest("invalid tier")

    original = omise_client.PRICING[tier]
    coupon = _get_valid_coupon(request.POST.get("code"))
    if not coupon:
        return JsonResponse({
            "valid": False,
            "original_amount": str(original),
            "amount": str(original),
        })

    discounted = coupon.calculate_discount(original)
    return JsonResponse({
        "valid": True,
        "original_amount": str(original),
        "amount": str(discounted),
        "is_founding_member": coupon.is_founding_member,
    })


def _finalize_paid_subscription(user, tier, amount, coupon, omise_charge_id):
    """Shared by both the card (synchronous) and PromptPay (polled) success
    paths — creates the Subscription + PaymentHistory rows exactly once."""
    today = timezone.localdate()
    end_date = today + timedelta(days=TIER_DURATION_DAYS[tier])
    is_founding = bool(coupon and coupon.is_founding_member)

    subscription = Subscription.objects.create(
        user=user,
        tier=tier,
        status="active",
        start_date=today,
        end_date=end_date,
        auto_renew=False,  # recurring billing lands in the next sub-step
        is_founding_member=is_founding,
        locked_price=amount if is_founding else None,
    )
    PaymentHistory.objects.create(
        user=user,
        subscription=subscription,
        amount=amount,
        coupon_used=coupon,
        omise_charge_id=omise_charge_id,
        status="successful",
    )
    if coupon:
        coupon.current_uses += 1
        coupon.save(update_fields=["current_uses"])
    return subscription


def _checkout_context(request, tier, original_amount, amount, coupon, error=None):
    return {
        "tier": tier,
        "tier_label": TIER_LABELS[tier],
        "original_amount": original_amount,
        "amount": amount,
        "coupon": coupon,
        "omise_public_key": settings.OMISE_PUBLIC_KEY,
        "error": error,
    }


@login_required
def checkout(request, tier):
    if tier not in omise_client.PRICING:
        return HttpResponseBadRequest("invalid tier")

    original_amount = omise_client.PRICING[tier]

    if request.method != "POST":
        return render(
            request,
            "subscriptions/checkout.html",
            _checkout_context(request, tier, original_amount, original_amount, None),
        )

    coupon = _get_valid_coupon(request.POST.get("coupon_code"))
    amount = coupon.calculate_discount(original_amount) if coupon else original_amount
    payment_method = request.POST.get("payment_method")
    description = f"FernLearnWorld {TIER_LABELS[tier]} subscription - {request.user.username}"

    if payment_method == "card":
        card_token = request.POST.get("omise_token")
        if not card_token:
            return render(request, "subscriptions/checkout.html", _checkout_context(
                request, tier, original_amount, amount, coupon,
                error="ไม่พบข้อมูลบัตร กรุณาลองใหม่",
            ))

        try:
            charge = omise_client.create_card_charge(amount, card_token, description)
        except omise.errors.BaseError as e:
            return render(request, "subscriptions/checkout.html", _checkout_context(
                request, tier, original_amount, amount, coupon,
                error=f"การชำระเงินไม่สำเร็จ: {e}",
            ))

        if charge.status == "successful":
            _finalize_paid_subscription(request.user, tier, amount, coupon, charge.id)
            return redirect("subscriptions:checkout_success")

        PaymentHistory.objects.create(
            user=request.user, amount=amount, coupon_used=coupon,
            omise_charge_id=charge.id, status="failed",
        )
        return render(request, "subscriptions/checkout.html", _checkout_context(
            request, tier, original_amount, amount, coupon,
            error="การชำระเงินไม่สำเร็จ กรุณาลองบัตรใบอื่น",
        ))

    elif payment_method == "promptpay":
        return_uri = request.build_absolute_uri(reverse("subscriptions:checkout_success"))
        try:
            charge = omise_client.create_promptpay_charge(amount, description, return_uri)
        except omise.errors.BaseError as e:
            return render(request, "subscriptions/checkout.html", _checkout_context(
                request, tier, original_amount, amount, coupon,
                error=f"สร้าง QR PromptPay ไม่สำเร็จ: {e}",
            ))

        # No webhook yet in this sub-step — the wait page polls
        # promptpay_status(), which needs this to know what to finalize.
        request.session["pending_promptpay"] = {
            "charge_id": charge.id,
            "tier": tier,
            "amount": str(amount),
            "coupon_id": coupon.id if coupon else None,
        }
        return render(request, "subscriptions/promptpay_wait.html", {
            "charge": charge,
            "tier_label": TIER_LABELS[tier],
            "amount": amount,
        })

    return HttpResponseBadRequest("invalid payment method")


@login_required
def promptpay_status(request, charge_id):
    pending = request.session.get("pending_promptpay")
    if not pending or pending["charge_id"] != charge_id:
        return JsonResponse({"status": "unknown"}, status=404)

    if PaymentHistory.objects.filter(omise_charge_id=charge_id, status="successful").exists():
        return JsonResponse({"status": "successful"})

    charge = omise_client.retrieve_charge(charge_id)
    if charge.status == "successful":
        coupon = None
        if pending["coupon_id"]:
            coupon = Coupon.objects.filter(id=pending["coupon_id"]).first()
        _finalize_paid_subscription(
            request.user, pending["tier"], Decimal(pending["amount"]), coupon, charge_id,
        )
        del request.session["pending_promptpay"]
        return JsonResponse({"status": "successful"})

    return JsonResponse({"status": charge.status})


@login_required
def checkout_success(request):
    subscription = Subscription.objects.current_for(request.user)
    return render(request, "subscriptions/success.html", {"subscription": subscription})
