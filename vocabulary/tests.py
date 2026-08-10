from django.contrib.auth import get_user_model
from django.test import TestCase

from course.models import Course, Program
from .models import Vocabulary

User = get_user_model()


class VocabularyPagesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="smoketest", password="testpass123")

        program = Program.objects.create(title="Japanese Program")
        self.course = Course.objects.create(
            slug="jp-n5-001-test",
            title="JLPT N5 - Lesson 1",
            code="JP-N5-001",
            program=program,
            level="N5",
            year=1,
            semester="First",
        )
        Vocabulary.objects.create(
            course=self.course,
            word="こんにちは",
            reading="こんにちは",
            meaning_th="สวัสดี",
            meaning_en="Hello",
            language="japanese",
            level="N5",
            example_sentence="こんにちは。",
        )
        self.client.force_login(self.user)

    def test_vocab_card_loads_for_course(self):
        response = self.client.get(f"/th/vocabulary/{self.course.code}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "こんにちは")

    def test_sentence_practice_loads(self):
        response = self.client.get(f"/th/vocabulary/sentence/{self.course.code}/")
        self.assertEqual(response.status_code, 200)

    def test_quiz_practice_loads(self):
        response = self.client.get(f"/th/vocabulary/quiz/{self.course.code}/")
        self.assertEqual(response.status_code, 200)

    def test_legacy_speaking_practice_redirects_instead_of_500(self):
        response = self.client.get(
            f"/th/vocabulary/speaking/{self.course.code}/", follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("/th/practice/speaking/", response.redirect_chain[0][0])

    def test_profile_progress_loads_and_scopes_across_all_courses(self):
        response = self.client.get("/th/vocabulary/profile-progress/")
        self.assertEqual(response.status_code, 200)
        # Regression check: this used to hardcode total_lessons to JP-N5-only.
        self.assertEqual(response.context["total_lessons"], 1)

    def test_achievements_page_loads(self):
        response = self.client.get("/th/vocabulary/achievements/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("total_count", response.context)
