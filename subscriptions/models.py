from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class SubscriptionManager(models.Manager):
    def current_for(self, user):
        """
        The Subscription row that represents this user's current state.
        A user can have many rows over time (free -> trial -> monthly ->
        cancelled -> monthly again, ...) — this picks the most recently
        started active/trial one, falling back to the newest row of any
        status so callers always get *something* for a signed-up user.
        """
        qs = self.filter(user=user)
        current = qs.filter(status__in=["active", "trial"]).order_by("-start_date").first()
        return current or qs.order_by("-start_date").first()


class Subscription(models.Model):
    TIER_CHOICES = (
        ("free", "Free"),
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    )
    STATUS_CHOICES = (
        ("active", "Active"),
        ("trial", "Trial"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions"
    )
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, default="free")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(null=True, blank=True)  # null = doesn't expire (free tier)
    auto_renew = models.BooleanField(default=False)

    # Recurring credit-card billing (Omise Customer + Card token; Phase 2)
    omise_customer_id = models.CharField(max_length=100, blank=True)
    omise_card_id = models.CharField(max_length=100, blank=True)

    # Founding Member: once a founding-member coupon is redeemed, this row's
    # price is locked forever regardless of future price changes.
    is_founding_member = models.BooleanField(default=False)
    locked_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Manual override for staff/devs/testers/one-off VIP grants — see
    # is_paid_access below for the one place this actually takes effect.
    is_complimentary = models.BooleanField(
        default=False,
        verbose_name="ให้สิทธิ์ฟรีแบบ manual (Complimentary)",
        help_text=(
            "ติ๊กเพื่อให้ user คนนี้เข้าถึงได้เหมือน paid tier ทุกอย่าง โดยไม่ต้องจ่ายเงิน "
            "— ใช้สำหรับทีมงาน/นักพัฒนา/ผู้ทดสอบ หรือแจกสิทธิ์พิเศษเป็นกรณีไป "
            "ต้องตั้ง Status เป็น Active (หรือ Trial) ด้วยจึงจะมีผลจริง "
            "เว้น End date ว่างไว้ = ไม่มีวันหมดอายุ, ตั้งวันที่ = หมดอายุตามกำหนดตามปกติ"
        ),
    )

    # Free trial (7 days, no card required up front)
    is_trial = models.BooleanField(default=False)
    trial_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SubscriptionManager()

    class Meta:
        ordering = ["-start_date", "-created_at"]

    def __str__(self):
        return f"{self.user} - {self.tier} ({self.status})"

    @property
    def is_paid_access(self):
        """
        True while this row grants full (paid-tier-equivalent) access. This
        is the single chokepoint every paywall check ultimately reads
        (subscriptions/access.py::user_has_paid_access -> current_for(user)
        -> .is_paid_access) — is_complimentary only needs to be handled
        here, not at every call site.
        """
        if self.status not in ("active", "trial"):
            return False
        if self.end_date and self.end_date < timezone.localdate():
            return False
        if self.is_complimentary:
            return True
        if self.tier == "free" and not self.is_trial:
            return False
        return True

    @classmethod
    def email_has_used_trial(cls, email):
        """
        Anti-abuse check for the 7-day free trial: looks across *all*
        accounts sharing this email (not just the current user), since the
        thing being prevented is someone signing up again with a new
        account to get another trial.
        """
        if not email:
            return False
        return cls.objects.filter(user__email__iexact=email, trial_used=True).exists()


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ("percentage", "Percentage"),
        ("fixed_amount", "Fixed Amount"),
    )

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=15, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    max_uses = models.PositiveIntegerField(null=True, blank=True)  # null = unlimited
    current_uses = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_founding_member = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if not (self.valid_from <= now <= self.valid_until):
            return False
        if self.max_uses is not None and self.current_uses >= self.max_uses:
            return False
        return True

    def calculate_discount(self, amount):
        """amount: Decimal. Returns the discounted amount, never below 0."""
        if self.discount_type == "percentage":
            discount = amount * (self.discount_value / Decimal("100"))
        else:
            discount = self.discount_value
        return max(amount - discount, Decimal("0"))


class PaymentHistory(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("successful", "Successful"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_history"
    )
    subscription = models.ForeignKey(
        Subscription, null=True, blank=True, on_delete=models.SET_NULL, related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    coupon_used = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    omise_charge_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Payment history"

    def __str__(self):
        return f"{self.user} - {self.amount} ({self.status})"


class AITutorUsage(models.Model):
    """Per-user, per-day counter used to enforce the free tier's daily
    AI Tutor message limit (there was no usage tracking of any kind
    before this)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_tutor_usage"
    )
    date = models.DateField(default=timezone.localdate)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "date")
        verbose_name_plural = "AI Tutor usage"

    def __str__(self):
        return f"{self.user} - {self.date}: {self.count}"
