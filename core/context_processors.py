from django.conf import settings


def seo(request):
    """
    `site_url` / `canonical_url` for base.html's canonical + Open Graph tags.

    canonical_url drops the query string on purpose (?next=, ?page=, utm_...
    would otherwise each look like a separate page to Google). A view whose
    query string *does* select different content (program_detail's ?level=)
    passes its own `canonical_url` in the render context, which takes
    precedence over this context processor's value.
    """
    return {
        "site_url": settings.SITE_URL,
        "canonical_url": settings.SITE_URL + request.path,
    }
