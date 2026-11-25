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
    SITE_URL="https://fernlearnworld.com",
    CANONICAL_REDIRECT_HOSTS=["fernlearnworld.onrender.com", "www.fernlearnworld.com"],
    CANONICAL_REDIRECT_EXEMPT_PATHS=["/healthz"],
)
class CanonicalDomainRedirectTests(SimpleTestCase):
    def _get(self, host, path="/th/courses/?page=2&utm_source=x"):
        mw = CanonicalDomainRedirectMiddleware(lambda r: HttpResponse("ok"))
        return mw(RequestFactory().get(path, HTTP_HOST=host))

    def test_onrender_host_301s_to_canonical_with_path_and_query(self):
        resp = self._get("fernlearnworld.onrender.com")
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp["Location"], "https://fernlearnworld.com/th/courses/?page=2&utm_source=x")

    def test_www_host_301s_to_apex(self):
        resp = self._get("WWW.fernlearnworld.com:443", "/")
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp["Location"], "https://fernlearnworld.com/")

    def test_canonical_host_passes_through(self):
        self.assertEqual(self._get("fernlearnworld.com").status_code, 200)

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
# served on a non-canonical host.
@override_settings(SITE_URL="https://fernlearnworld.com", ALLOWED_HOSTS=["*"], CANONICAL_REDIRECT_HOSTS=[])
class CanonicalSeoUrlTests(TestCase):
    def test_canonical_tag_uses_main_domain_even_on_onrender_host(self):
        resp = self.client.get("/th/", HTTP_HOST="fernlearnworld.onrender.com")
        self.assertContains(resp, '<link rel="canonical" href="https://fernlearnworld.com/th/">')
        self.assertNotContains(resp, "onrender.com")

    def test_sitemap_uses_main_domain(self):
        resp = self.client.get("/sitemap.xml", HTTP_HOST="fernlearnworld.onrender.com")
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode()
        self.assertIn("<loc>https://fernlearnworld.com/", body)
        self.assertNotIn("onrender.com", body)
        self.assertNotIn("http://fernlearnworld.com", body)
