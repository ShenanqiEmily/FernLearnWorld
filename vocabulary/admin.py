from django.contrib import admin
from .models import Vocabulary, Achievement, UserAchievement


@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = ("word", "language", "level", "course", "meaning_th")
    list_filter = ("language", "level", "course")
    search_fields = (
        "word",
        "reading",
        "pinyin",
        "meaning_th",
        "meaning_en",
        "example_sentence",
    )


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("icon", "title", "code")
    search_fields = ("title", "code")


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ("user", "achievement", "earned_at")
    list_filter = ("achievement",)