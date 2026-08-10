from django.contrib.auth import get_user_model
from django.test import TestCase

from course.models import Course, Program
from vocabulary.models import Vocabulary
from flashcards.models import GrammarPoint, KanjiCharacter
from .models import PracticeAttempt

User = get_user_model()


class PracticeHubTests(TestCase):
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
            course=self.course, word="犬", reading="いぬ", meaning_th="หมา",
            language="japanese", level="N5",
        )
        GrammarPoint.objects.create(
            term="は", title="Topic marker", language="japanese", level="N5",
            topic="particles", explanation_th="test", example_sentence="私は学生です。",
        )
        # kanji_recognition needs 4+ items in the level to build MC distractors
        for char, meaning, onyomi in [
            ("一", "หนึ่ง", "いち"),
            ("二", "สอง", "に"),
            ("三", "สาม", "さん"),
            ("四", "สี่", "し"),
        ]:
            KanjiCharacter.objects.create(
                character=char, meaning_th=meaning, language="japanese",
                level="N5", onyomi=onyomi,
            )
        self.client.force_login(self.user)

    def test_hub_loads(self):
        response = self.client.get("/th/practice/")
        self.assertEqual(response.status_code, 200)

    def test_vocab_mc_full_flow_awards_xp(self):
        response = self.client.get(f"/th/practice/vocab-mc/{self.course.code}/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            f"/th/practice/complete/vocab_mc/{self.course.code}/?score=90"
        )
        self.assertEqual(response.status_code, 200)

        attempt = PracticeAttempt.objects.get(user=self.user, mode="vocab_mc")
        self.assertTrue(attempt.completed)
        self.assertEqual(attempt.xp_awarded, 80)
        self.assertEqual(attempt.course, self.course)

    def test_course_sourced_mode_matching(self):
        response = self.client.get(f"/th/practice/vocab_matching/{self.course.code}/")
        self.assertEqual(response.status_code, 200)

    def test_level_sourced_mode_uses_level_not_course(self):
        response = self.client.get("/th/practice/grammar_sentence_builder/N5/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            "/th/practice/complete/grammar_sentence_builder/N5/?score=100"
        )
        self.assertEqual(response.status_code, 200)

        attempt = PracticeAttempt.objects.get(
            user=self.user, mode="grammar_sentence_builder"
        )
        self.assertIsNone(attempt.course)
        self.assertEqual(attempt.level, "N5")
        self.assertEqual(attempt.xp_awarded, 100)

    def test_kanji_recognition_loads(self):
        response = self.client.get("/th/practice/kanji_recognition/N5/")
        self.assertEqual(response.status_code, 200)

    def test_non_playable_mode_404s(self):
        response = self.client.get("/th/practice/complete/not_a_real_mode/N5/")
        self.assertEqual(response.status_code, 404)
