from django.core.management.base import BaseCommand

from allauth.socialaccount.models import SocialAccount

from accounts.signals import display_name_from_social_extra_data


class Command(BaseCommand):
    help = (
        "Backfill User.first_name for accounts that signed up via social "
        "login (Google/Facebook/LINE) before the display-name fix was "
        "added to accounts.signals.social_login_creates_student — reads "
        "SocialAccount.extra_data already stored in the database, no "
        "re-login required."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without saving anything.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        updated = 0
        skipped = 0

        for social_account in SocialAccount.objects.select_related("user"):
            user = social_account.user
            if user.first_name:
                skipped += 1
                continue

            display_name = display_name_from_social_extra_data(
                social_account.provider, social_account.extra_data
            )
            if not display_name:
                skipped += 1
                continue

            self.stdout.write(
                f"{user.username} ({social_account.provider}): "
                f"first_name -> {display_name!r}"
            )
            if not dry_run:
                user.first_name = display_name
                user.save(update_fields=["first_name"])
            updated += 1

        verb = "Would update" if dry_run else "Updated"
        self.stdout.write(
            self.style.SUCCESS(f"{verb} {updated} user(s), skipped {skipped}.")
        )
