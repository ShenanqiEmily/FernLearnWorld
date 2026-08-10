from django.conf import settings
from django.db import models

from course.models import Course


class PracticeAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="practice_attempts",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="practice_attempts",
        null=True,
        blank=True,
    )
    # For modes whose content isn't tied to a Course (grammar/kanji, which
    # are keyed by language+level, not by lesson) — course stays null and
    # this holds the level code (e.g. "N5", "HSK3") instead.
    level = models.CharField(max_length=20, blank=True, default="")
    mode = models.CharField(max_length=50)

    score = models.IntegerField(default=0)
    best_score = models.IntegerField(default=0)
    attempt_count = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
    xp_awarded = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "mode", "course", "level")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user} - {self.mode} - {self.course.code if self.course else self.level}"
