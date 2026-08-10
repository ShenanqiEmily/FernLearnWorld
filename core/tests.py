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
