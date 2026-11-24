from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from course.models import Course, Program

# Only genuinely public, anonymous-accessible pages belong here. Course and
# program pages are public (lesson *content* under /vocabulary/ still needs
# login + the subscription paywall). See also robots.txt (core/views.py).
_PAGES = {
    "home": {"changefreq": "daily", "priority": 1.0},
    "programs": {"changefreq": "weekly", "priority": 0.9},
    "about": {"changefreq": "monthly", "priority": 0.6},
    "subscriptions:tier_picker": {"changefreq": "weekly", "priority": 0.8},
    "login": {"changefreq": "yearly", "priority": 0.3},
    "register": {"changefreq": "yearly", "priority": 0.5},
}


class _PublicDomainSitemap(Sitemap):
    """
    Absolute URLs always use settings.SITE_URL (https, no www) rather than
    the Sites framework / request host, so the sitemap never advertises
    *.onrender.com or localhost URLs.
    """

    protocol = urlsplit(settings.SITE_URL).scheme or "https"
    i18n = True  # one <url> per LANGUAGES entry ...
    alternates = True  # ... each listing its hreflang siblings
    x_default = True

    def get_domain(self, site=None):
        return urlsplit(settings.SITE_URL).netloc


class StaticViewSitemap(_PublicDomainSitemap):
    def items(self):
        return list(_PAGES.keys())

    def location(self, item):
        return reverse(item)

    def changefreq(self, item):
        return _PAGES[item]["changefreq"]

    def priority(self, item):
        return _PAGES[item]["priority"]


class ProgramLevelSitemap(_PublicDomainSitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        # Each ?level= shows a different lesson list, so each level gets its
        # own entry. Reuses the view's own Japanese/Chinese level detection
        # (imported here, not at module level, to keep urls.py import light).
        from course.views import get_program_level_config

        items = []
        for program in Program.objects.order_by("pk"):
            levels = get_program_level_config(program, None)["level_options"]
            items += [(program.pk, level) for level in levels] or [(program.pk, "")]
        return items

    def location(self, item):
        pk, level = item
        url = reverse("program_detail", kwargs={"pk": pk})
        return f"{url}?level={level}" if level else url


class CourseSitemap(_PublicDomainSitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Course.objects.exclude(slug="").exclude(slug__isnull=True).order_by("code")

    def location(self, course):
        return reverse("course_detail", kwargs={"slug": course.slug})
