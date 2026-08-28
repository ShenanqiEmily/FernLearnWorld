from django.apps import AppConfig
from django.db.models.signals import post_migrate


def sync_site_domain(sender, **kwargs):
    """
    django.contrib.sitemaps (and allauth's account_email templates, etc.)
    build absolute URLs from Site.objects.get_current().domain — NOT from
    the incoming request — so without this it silently stays "example.com"
    (Django's built-in default) forever, regardless of ALLOWED_HOSTS or
    what's actually in the browser's address bar. Runs on every migrate,
    so a domain change (e.g. attaching a custom domain on Render) takes
    effect on the next deploy without a manual admin edit.
    """
    from django.conf import settings
    from django.contrib.sites.models import Site

    domain = settings.RENDER_EXTERNAL_HOSTNAME or "127.0.0.1:8000"
    Site.objects.update_or_create(
        id=settings.SITE_ID,
        defaults={"domain": domain, "name": "FernLearnWorld"},
    )


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        post_migrate.connect(sync_site_domain, sender=self)
