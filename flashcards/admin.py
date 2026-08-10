from django.contrib import admin

from .models import FlashcardReview, GrammarPoint, KanjiCharacter


@admin.register(GrammarPoint)
class GrammarPointAdmin(admin.ModelAdmin):
    list_display = ("term", "title", "language", "level", "topic")
    list_filter = ("language", "level", "topic")
    search_fields = ("term", "title", "explanation_th")


@admin.register(KanjiCharacter)
class KanjiCharacterAdmin(admin.ModelAdmin):
    list_display = ("character", "meaning_th", "language", "level")
    list_filter = ("language", "level")
    search_fields = ("character", "meaning_th", "onyomi", "kunyomi", "pinyin")


@admin.register(FlashcardReview)
class FlashcardReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "content_type", "object_id", "due_date", "repetitions", "ease_factor")
    list_filter = ("content_type", "last_quality")
    search_fields = ("user__username",)
