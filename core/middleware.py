from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class CanonicalDomainRedirectMiddleware:
    """
    301-redirect requests on secondary hosts (the *.onrender.com service URL,
    www.) to the canonical domain in settings.SITE_URL, keeping path + query
    string — so Google consolidates everything onto https://fernlearnworld.com.

    - Active only when DEBUG=False: local dev (localhost/127.0.0.1) is untouched.
    - Only hosts listed in CANONICAL_REDIRECT_HOSTS are redirected; any other
      host (localhost, an IP, the canonical domain itself) passes through.
    - Paths in CANONICAL_REDIRECT_EXEMPT_PATHS (e.g. a Render health check
      path) are never redirected, so a health check can't fail on a 301.

    Placed first in MIDDLEWARE so the redirect happens in one hop, before
    SecurityMiddleware's http->https redirect and before ALLOWED_HOSTS
    validation (we read the raw Host header on purpose: www. may not be in
    ALLOWED_HOSTS, and that must not turn into a 400 instead of a redirect).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        target = urlsplit(settings.SITE_URL)
        self.target_scheme = target.scheme or "https"
        self.target_host = target.netloc.lower()
        self.redirect_hosts = {
            h.strip().lower()
            for h in getattr(settings, "CANONICAL_REDIRECT_HOSTS", ())
            if h.strip()
        } - {self.target_host}
        self.exempt_paths = tuple(
            getattr(settings, "CANONICAL_REDIRECT_EXEMPT_PATHS", ())
        )

    def __call__(self, request):
        if not settings.DEBUG and self.redirect_hosts:
            host = request.META.get("HTTP_HOST", "").split(":", 1)[0].lower()
            if host in self.redirect_hosts and not self._is_exempt(request.path):
                url = f"{self.target_scheme}://{self.target_host}{request.get_full_path()}"
                return HttpResponsePermanentRedirect(url)
        return self.get_response(request)

    def _is_exempt(self, path):
        return any(
            path == p or path.startswith(p.rstrip("/") + "/")
            for p in self.exempt_paths
        )
