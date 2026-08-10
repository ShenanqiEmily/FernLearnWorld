from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import GrammarPoint, KanjiCharacter

User = get_user_model()


class FlashcardsPagesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="smoketest", password="testpass123")

        GrammarPoint.objects.create(
            term="は", title="Topic marker", language="japanese", level="N5",
            topic="particles", explanation_th="test",
            example_sentence="私は学生です。",
        )
        GrammarPoint.objects.create(
            term="是", title="To be", language="chinese", level="HSK1",
            topic="sentence_patterns", explanation_th="test",
            example_sentence="我是学生。",
        )
        KanjiCharacter.objects.create(
            character="一", meaning_th="หนึ่ง", language="japanese", level="N5",
            onyomi="いち",
        )
        self.client.force_login(self.user)

    def test_home_loads(self):
        response = self.client.get("/th/flashcards/")
        self.assertEqual(response.status_code, 200)

    def test_grammar_deck_list_splits_by_language(self):
        response = self.client.get("/th/flashcards/grammar/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ภาษาญี่ปุ่น")
        self.assertContains(response, "ภาษาจีน")

    def test_grammar_study_session_filters_by_level_not_topic(self):
        response = self.client.get("/th/flashcards/grammar/N5/study/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["cards"]), 1)

    def test_kanji_deck_list_loads(self):
        response = self.client.get("/th/flashcards/kanji/")
        self.assertEqual(response.status_code, 200)
