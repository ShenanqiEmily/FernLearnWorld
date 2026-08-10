from datetime import timedelta

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

LEVEL_CHOICES = (
    ("N5", "JLPT N5"),
    ("N4", "JLPT N4"),
    ("N3", "JLPT N3"),
    ("N2", "JLPT N2"),
    ("N1", "JLPT N1"),
    ("HSK1", "HSK 1"),
    ("HSK2", "HSK 2"),
    ("HSK3", "HSK 3"),
    ("HSK4", "HSK 4"),
    ("HSK5", "HSK 5"),
    ("HSK6", "HSK 6"),
)

LANGUAGE_CHOICES = (
    ("japanese", "Japanese"),
    ("chinese", "Chinese"),
)


class GrammarPoint(models.Model):
    TOPIC_CHOICES = (
        ("particles", "Particles (คำช่วย)"),
        ("verb_conjugation", "การผันกริยา"),
        ("adjectives", "คำคุณศัพท์"),
        ("sentence_patterns", "รูปประโยค"),
    )

    term = models.CharField(max_length=100)
    title = models.CharField(max_length=150)
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    topic = models.CharField(max_length=30, choices=TOPIC_CHOICES)
    explanation_th = models.TextField()
    example_sentence = models.TextField(blank=True)
    example_reading = models.TextField(blank=True)
    example_translation_th = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("level", "topic", "term")

    def __str__(self):
        return f"{self.term} ({self.get_level_display()})"


class KanjiCharacter(models.Model):
    character = models.CharField(max_length=10)
    meaning_th = models.TextField()
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    onyomi = models.CharField(max_length=100, blank=True)
    kunyomi = models.CharField(max_length=100, blank=True)
    pinyin = models.CharField(max_length=100, blank=True)
    example_word = models.CharField(max_length=100, blank=True)
    example_reading = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("level", "character")

    def __str__(self):
        return f"{self.character} ({self.get_level_display()})"


class FlashcardReview(models.Model):
    QUALITY_CHOICES = (
        ("again", "Again"),
        ("hard", "Hard"),
        ("good", "Good"),
        ("easy", "Easy"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    card = GenericForeignKey("content_type", "object_id")

    repetitions = models.PositiveIntegerField(default=0)
    ease_factor = models.FloatField(default=2.5)
    interval_days = models.PositiveIntegerField(default=0)
    due_date = models.DateField(default=timezone.localdate)
    last_quality = models.CharField(max_length=10, choices=QUALITY_CHOICES, blank=True)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "content_type", "object_id")

    def __str__(self):
        return f"{self.user} - {self.card} (due {self.due_date})"

    def apply_review(self, quality):
        """Simplified SM-2 (Anki-style). quality in {again, hard, good, easy}."""
        today = timezone.localdate()

        if quality == "again":
            self.repetitions = 0
            self.interval_days = 1
            self.ease_factor = max(1.3, self.ease_factor - 0.2)
        else:
            if quality == "hard":
                self.ease_factor = max(1.3, self.ease_factor - 0.15)
                factor = 1.2
            elif quality == "easy":
                self.ease_factor += 0.15
                factor = self.ease_factor * 1.3
            else:  # good
                factor = self.ease_factor

            self.repetitions += 1
            if self.repetitions == 1:
                self.interval_days = 1
            elif self.repetitions == 2:
                self.interval_days = 6
            else:
                self.interval_days = max(1, round(self.interval_days * factor))

        self.due_date = today + timedelta(days=self.interval_days)
        self.last_quality = quality
        self.last_reviewed_at = timezone.now()
        self.save()
