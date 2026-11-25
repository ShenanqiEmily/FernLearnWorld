from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class HomeAndDashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="smoketest", password="testpass123")

    def test_home_is_public_landing_page_for_anonymous_users(self):
        response = self.client.get("/th/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "เข้าสู่ระบบ")

    def test_home_redirects_logged_in_users_to_dashboard(self):
        self.client.force_login(self.user)
        response = self.client.get("/th/", follow=True)
        self.assertRedirects(response, "/th/dashboard/")

    def test_dashboard_requires_login(self):
        response = self.client.get("/th/dashboard/")
        self.assertEqual(response.status_code, 302)

    def test_dashboard_loads_for_logged_in_user(self):
        self.client.force_login(self.user)
        response = self.client.get("/th/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Total XP")


from django.test import RequestFactory, SimpleTestCase, override_settings  # noqa: E402
from django.http import HttpResponse  # noqa: E402

from core.middleware import CanonicalDomainRedirectMiddleware  # noqa: E402


@override_settings(
    DEBUG=False,
    SITE_URL="https://www.fernlearnworld.com",
    CANONICAL_REDIRECT_HOSTS=["fernlearnworld.onrender.com"],
    CANONICAL_REDIRECT_EXEMPT_PATHS=["/healthz"],
)
class CanonicalDomainRedirectTests(SimpleTestCase):
    def _get(self, host, path="/th/courses/?page=2&utm_source=x"):
        mw = CanonicalDomainRedirectMiddleware(lambda r: HttpResponse("ok"))
        return mw(RequestFactory().get(path, HTTP_HOST=host))

    def test_onrender_host_301s_to_www_with_path_and_query(self):
        resp = self._get("fernlearnworld.onrender.com")
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp["Location"], "https://www.fernlearnworld.com/th/courses/?page=2&utm_source=x")

    def test_onrender_host_is_case_and_port_insensitive(self):
        resp = self._get("FernLearnWorld.onrender.com:443", "/")
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp["Location"], "https://www.fernlearnworld.com/")

    def test_www_and_apex_pass_through(self):
        # Render redirects apex -> www itself; we must never touch either.
        self.assertEqual(self._get("www.fernlearnworld.com").status_code, 200)
        self.assertEqual(self._get("fernlearnworld.com").status_code, 200)

    @override_settings(
        CANONICAL_REDIRECT_HOSTS=[
            "fernlearnworld.onrender.com", "www.fernlearnworld.com", "fernlearnworld.com",
        ]
    )
    def test_www_apex_twins_never_redirect_even_if_misconfigured(self):
        # Regression: listing www/apex in env previously caused ERR_TOO_MANY_REDIRECTS.
        self.assertEqual(self._get("www.fernlearnworld.com").status_code, 200)
        self.assertEqual(self._get("fernlearnworld.com").status_code, 200)
        self.assertEqual(self._get("fernlearnworld.onrender.com").status_code, 301)

    def test_localhost_passes_through(self):
        self.assertEqual(self._get("localhost:8000").status_code, 200)
        self.assertEqual(self._get("127.0.0.1").status_code, 200)

    def test_health_check_path_is_exempt(self):
        self.assertEqual(self._get("fernlearnworld.onrender.com", "/healthz").status_code, 200)
        self.assertEqual(self._get("fernlearnworld.onrender.com", "/healthz/").status_code, 200)
        # prefix match must be a whole path segment
        self.assertEqual(self._get("fernlearnworld.onrender.com", "/healthzzz").status_code, 301)

    @override_settings(DEBUG=True)
    def test_disabled_when_debug(self):
        self.assertEqual(self._get("fernlearnworld.onrender.com").status_code, 200)


# Redirect disabled here so we can inspect what the page itself emits when
# served on a non-canonical host. No SITE_URL override: checks the real default.
@override_settings(ALLOWED_HOSTS=["*"], CANONICAL_REDIRECT_HOSTS=[])
class CanonicalSeoUrlTests(TestCase):
    def test_site_url_default_is_www(self):
        from django.conf import settings
        self.assertEqual(settings.SITE_URL, "https://www.fernlearnworld.com")

    def test_canonical_og_and_jsonld_use_www_even_on_onrender_host(self):
        resp = self.client.get("/th/", HTTP_HOST="fernlearnworld.onrender.com")
        self.assertContains(resp, '<link rel="canonical" href="https://www.fernlearnworld.com/th/">')
        self.assertContains(resp, '<meta property="og:url" content="https://www.fernlearnworld.com/th/">')
        self.assertContains(resp, '"url": "https://www.fernlearnworld.com/th/"')
        self.assertNotContains(resp, "onrender.com")
        self.assertNotContains(resp, "//fernlearnworld.com")

    def test_sitemap_uses_www(self):
        resp = self.client.get("/sitemap.xml", HTTP_HOST="fernlearnworld.onrender.com")
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode()
        self.assertIn("<loc>https://www.fernlearnworld.com/", body)
        self.assertNotIn("onrender.com", body)
        self.assertNotIn("//fernlearnworld.com", body)

    def test_robots_sitemap_line_uses_www(self):
        resp = self.client.get("/robots.txt", HTTP_HOST="fernlearnworld.onrender.com")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Sitemap: https://www.fernlearnworld.com/sitemap.xml", resp.content.decode())
