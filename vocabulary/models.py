from django.db import models
from course.models import Course
from django.conf import settings

class Vocabulary(models.Model):
    LANGUAGE_CHOICES = (
        ("japanese", "Japanese"),
        ("chinese", "Chinese"),
    )

    LEVEL_CHOICES = (
        ("N5", "JLPT N5"),
        ("N4", "JLPT N4"),
        ("N3", "JLPT N3"),
        ("N2", "JLPT N2"),
        ("N1", "JLPT N1"),
        ("HSK3", "HSK 3"),
        ("HSK4", "HSK 4"),
        ("HSK5", "HSK 5"),
        ("HSK6", "HSK 6"),
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="vocabularies",
        null=True,
        blank=True
    )

    word = models.CharField(max_length=100)
    reading = models.CharField(max_length=100, blank=True)
    pinyin = models.CharField(max_length=100, blank=True)
    meaning_th = models.TextField()
    meaning_en = models.TextField(blank=True)
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)

    example_sentence = models.TextField(blank=True)
    example_reading = models.TextField(blank=True)
    example_translation_th = models.TextField(blank=True)
    example_translation_en = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["level", "word"]

    def __str__(self):
        return f"{self.word} ({self.level})"
    
from django.contrib.auth import get_user_model

User = get_user_model()


class UserLessonProgress(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )

    score = models.IntegerField(
        default=0
    )

    completed = models.BooleanField(
        default=False
    )

    vocab_completed = models.BooleanField(
        default=False
    )

    sentence_completed = models.BooleanField(
        default=False
    )

    speaking_completed = models.BooleanField(
        default=False
    )

    quiz_completed = models.BooleanField(
        default=False
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        unique_together = (
            "user",
            "course"
        )

    def __str__(self):
        return f"{self.user.username} - {self.course.code}"

class Achievement(models.Model):
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=10, default="🏆")

    def __str__(self):
        return self.title


class UserAchievement(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE
    )

    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "achievement")

    def __str__(self):
        return f"{self.user} - {self.achievement.title}"
    
    
        