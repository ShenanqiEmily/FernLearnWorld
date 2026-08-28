from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views import defaults as default_views
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import JavaScriptCatalog

from core.sitemaps import StaticViewSitemap
from core.views import robots_txt

admin.site.site_header = "Dj-LMS Admin"

sitemaps = {
    "static": StaticViewSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    # Crawlers expect these at a fixed, non-localized path — same reasoning
    # as social-auth/payments below.
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", robots_txt, name="robots_txt"),
    # Social login (Google, Facebook, LINE) — deliberately mounted here,
    # outside i18n_patterns() below, not under accounts/. Two reasons:
    # 1) allauth's own URL names (account_login, account_logout, ...)
    #    must never collide with this project's existing custom
    #    login/register/logout at accounts/.
    # 2) OAuth providers require an exact, pre-registered redirect_uri —
    #    if this lived inside i18n_patterns() the callback URL would carry
    #    a locale prefix that changes with the active language (/th/...,
    #    /en/..., ...), breaking the redirect_uri match for every locale
    #    except whichever one was registered in each provider's console.
    path("social-auth/", include("allauth.urls")),
    # Same reasoning as social-auth above: payment gateways call these
    # endpoints server-to-server with one exact, pre-registered URL — a
    # locale prefix that changes with the active language would break
    # them. The REST API is likewise called by API clients that don't
    # care about (and shouldn't have to know) the UI's current language.
    path("payments/", include("payments.urls")),
    path("accounts/api/", include("accounts.api.urls", namespace="accounts-api")),
]

urlpatterns += i18n_patterns(
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    path("", include("core.urls")),
    path("jet/", include("jet.urls", "jet")),  # Django JET URLS
    path(
        "jet/dashboard/", include("jet.dashboard.urls", "jet-dashboard")
    ),  # Django JET dashboard URLS
    path("accounts/", include("accounts.urls")),
    path("programs/", include("course.urls")),
    path("result/", include("result.urls")),
    path("search/", include("search.urls")),
    path("quiz/", include("quiz.urls")),
    path("classroom/", include("virtual_classroom.urls", namespace="virtual_classroom")),
    path("vocabulary/", include("vocabulary.urls")),
    path("flashcards/", include("flashcards.urls")),
    path("practice/", include("practice.urls")),
    path("subscribe/", include("subscriptions.urls")),
)


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
