from django.core.management.base import BaseCommand, CommandError

from accounts.models import User
from subscriptions.models import Subscription


class Command(BaseCommand):
    help = (
        "Grant (or revoke) a user permanent complimentary paid-tier access "
        "by email, without going through Django admin. "
        "Usage: python manage.py grant_free_access someone@example.com "
        "       python manage.py grant_free_access someone@example.com --revoke"
    )

    def add_arguments(self, parser):
        parser.add_argument("email", help="Email of the account to grant/revoke access for.")
        parser.add_argument(
            "--revoke", action="store_true",
            help="Revoke complimentary access instead of granting it.",
        )

    def handle(self, *args, **options):
        email = options["email"]
        revoke = options["revoke"]

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise CommandError(f"No user found with email {email!r}")
        except User.MultipleObjectsReturned:
            raise CommandError(
                f"Multiple users share email {email!r} — use Django admin "
                f"(/admin/subscriptions/subscription/) to pick the right one instead."
            )

        if revoke:
            # Also cancel status, not just unset the flag: is_paid_access
            # only reads is_complimentary as a *bypass* of the tier check —
            # if the row's tier were ever "monthly"/"yearly" (e.g. this was
            # a real paid row someone also flagged complimentary), leaving
            # status=active would keep granting access via tier alone.
            updated = Subscription.objects.filter(
                user=user, is_complimentary=True
            ).update(is_complimentary=False, status="cancelled")
            if updated:
                self.stdout.write(self.style.SUCCESS(
                    f"Revoked complimentary access for {user.username} ({email}) "
                    f"— {updated} subscription row(s) updated."
                ))
            else:
                self.stdout.write(f"{user.username} ({email}) had no complimentary access to revoke.")
            return

        subscription = Subscription.objects.current_for(user)
        if subscription and subscription.status in ("active", "trial"):
            subscription.is_complimentary = True
            subscription.save(update_fields=["is_complimentary"])
        else:
            # tier="free" deliberately: is_complimentary is meant to be the
            # sole thing keeping this row's access on, so that unticking it
            # straight from the Django admin list (list_editable) is enough
            # on its own to revoke access — no need to separately notice
            # and change tier/status too.
            subscription = Subscription.objects.create(
                user=user, tier="free", status="active", is_complimentary=True,
            )

        self.stdout.write(self.style.SUCCESS(
            f"Granted complimentary access to {user.username} ({email}) "
            f"— subscription id={subscription.id}, status={subscription.status}."
        ))
