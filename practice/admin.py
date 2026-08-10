from django.contrib import admin

from .models import PracticeAttempt


@admin.register(PracticeAttempt)
class PracticeAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "mode",
        "course",
        "score",
        "best_score",
        "completed",
        "xp_awarded",
        "attempt_count",
        "updated_at",
    )
    list_filter = ("mode", "completed", "course__code")
    search_fields = ("user__username", "course__code")
