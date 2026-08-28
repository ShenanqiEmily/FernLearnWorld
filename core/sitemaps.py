from django.contrib.sitemaps import Sitemap
from django.urls import reverse

# Only genuinely public, anonymous-accessible pages belong here. Course/
# program pages currently require login (paywall), so Google would just hit
# a login redirect for them — deliberately left out until/unless a real
# public course-preview page exists. See also robots.txt (core/views.py).
_PAGES = {
    "home": {"changefreq": "daily", "priority": 1.0},
    "about": {"changefreq": "monthly", "priority": 0.6},
    "subscriptions:tier_picker": {"changefreq": "weekly", "priority": 0.9},
    "login": {"changefreq": "yearly", "priority": 0.3},
    "register": {"changefreq": "yearly", "priority": 0.5},
}


class StaticViewSitemap(Sitemap):
    i18n = True  # one <url> entry per LANGUAGES entry, with hreflang alternates

    def items(self):
        return list(_PAGES.keys())

    def location(self, item):
        return reverse(item)

    def changefreq(self, item):
        return _PAGES[item]["changefreq"]

    def priority(self, item):
        return _PAGES[item]["priority"]
