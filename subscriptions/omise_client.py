"""
Thin wrapper around the `omise` SDK. Configures the SDK from Django
settings once at import time — omise.api_public/api_secret are process-
global, and Django loads apps once per process, so this is equivalent to
setting them at the top of every view that needs them.

Test vs live mode is entirely determined by which key is configured (Omise
has one API endpoint; pkey_test_/skey_test_ vs pkey_live_/skey_live_ decide
the mode server-side) — nothing here needs to branch on it.
"""
from decimal import Decimal

import omise
from django.conf import settings

omise.api_public = settings.OMISE_PUBLIC_KEY
omise.api_secret = settings.OMISE_SECRET_KEY

CURRENCY = "thb"

# Placeholder launch pricing — the one place to change it.
PRICING = {
    "monthly": Decimal("199"),
    "yearly": Decimal("1990"),
}


def to_satang(amount):
    """Omise amounts are in the smallest currency unit (satang for THB)."""
    return int(amount * 100)


def create_card_charge(amount, card_token, description, metadata=None):
    return omise.Charge.create(
        amount=to_satang(amount),
        currency=CURRENCY,
        card=card_token,
        description=description,
        metadata=metadata or {},
    )


def create_promptpay_charge(amount, description, return_uri, metadata=None):
    """
    PromptPay charges are always asynchronous — the returned charge is
    "pending" until the customer scans the QR code and pays through their
    banking app, at which point the caller has to poll retrieve_charge()
    (or later, a webhook) to find out it went through.
    """
    source = omise.Source.create(
        amount=to_satang(amount),
        currency=CURRENCY,
        type="promptpay",
    )
    charge = omise.Charge.create(
        amount=to_satang(amount),
        currency=CURRENCY,
        source=source.id,
        description=description,
        return_uri=return_uri,
        metadata=metadata or {},
    )
    return charge


def retrieve_charge(charge_id):
    return omise.Charge.retrieve(charge_id)
