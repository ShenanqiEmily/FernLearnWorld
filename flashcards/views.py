from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.db.models.functions import TruncDate
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from vocabulary.models import Vocabulary
from vocabulary.views import award_badge

from .models import LEVEL_CHOICES, FlashcardReview, GrammarPoint, KanjiCharacter

CATEGORY_MODELS = {
    "vocabulary": Vocabulary,
    "grammar": GrammarPoint,
    "kanji": KanjiCharacter,
}

CATEGORY_LABELS = {
    "vocabulary": "คำศัพท์ (Vocabulary)",
    "grammar": "ไวยากรณ์ (Grammar)",
    "kanji": "คันจิ (Kanji)",
}

GROUP_FIELD = {
    "vocabulary": "level",
    "grammar": "level",
    "kanji": "level",
}

LANGUAGE_LABELS = {
    "japanese": "ภาษาญี่ปุ่น",
    "chinese": "ภาษาจีน",
}

LANGUAGE_LEVEL_ORDER = {
    "japanese": ["N5", "N4", "N3", "N2", "N1"],
    "chinese": ["HSK1", "HSK2", "HSK3", "HSK4", "HSK5", "HSK6"],
}

SESSION_SIZE = 20


def _get_model_or_404(category):
    model = CATEGORY_MODELS.get(category)
    if model is None:
        raise Http404("Unknown flashcard category")
    return model


def _content_type_for(category):
    return ContentType.objects.get_for_model(_get_model_or_404(category))


def _group_labels(category):
    return dict(LEVEL_CHOICES)


def _user_streak(user):
    if not user.is_authenticated:
        return 0

    dates = set(
        FlashcardReview.objects.filter(user=user, last_reviewed_at__isnull=False)
        .annotate(day=TruncDate("last_reviewed_at"))
        .values_list("day", flat=True)
        .distinct()
    )
    if not dates:
        return 0

    today = timezone.localdate()
    cursor = today if today in dates else today - timedelta(days=1)

    streak = 0
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _due_count(user, category=None):
    if not user.is_authenticated:
        return 0

    qs = FlashcardReview.objects.filter(user=user, due_date__lte=timezone.localdate())
    if category:
        qs = qs.filter(content_type=_content_type_for(category))
    return qs.count()


def _reviewed_ids(user, content_type):
    if not user.is_authenticated:
        return set()
    return set(
        FlashcardReview.objects.filter(user=user, content_type=content_type)
        .values_list("object_id", flat=True)
    )


def _serialize_card(obj, category):
    if category == "vocabulary":
        return {
            "category": category,
            "object_id": obj.id,
            "front_main": obj.word,
            "front_sub": obj.reading or obj.pinyin,
            "back_main": obj.meaning_th,
            "back_sub": obj.meaning_en,
            "example_sentence": obj.example_sentence,
            "example_reading": obj.example_reading,
            "example_translation": obj.example_translation_th,
            "tts_lang": "zh-CN" if obj.language == "chinese" else "ja-JP",
        }

    if category == "grammar":
        return {
            "category": category,
            "object_id": obj.id,
            "front_main": obj.term,
            "front_sub": obj.title,
            "back_main": obj.explanation_th,
            "back_sub": "",
            "example_sentence": obj.example_sentence,
            "example_reading": obj.example_reading,
            "example_translation": obj.example_translation_th,
            "tts_lang": "zh-CN" if obj.language == "chinese" else "ja-JP",
        }

    # kanji
    back_sub = (
        f"Pinyin: {obj.pinyin}" if obj.language == "chinese"
        else f"On: {obj.onyomi or '-'} / Kun: {obj.kunyomi or '-'}"
    )
    return {
        "category": category,
        "object_id": obj.id,
        "front_main": obj.character,
        "front_sub": obj.onyomi or obj.kunyomi or obj.pinyin,
        "back_main": obj.meaning_th,
        "back_sub": back_sub,
        "example_sentence": obj.example_word,
        "example_reading": obj.example_reading,
        "example_translation": "",
        "tts_lang": "zh-CN" if obj.language == "chinese" else "ja-JP",
    }


def home(request):
    query = (request.GET.get("q") or "").strip()

    categories = []
    for category, model in CATEGORY_MODELS.items():
        categories.append({
            "key": category,
            "label": CATEGORY_LABELS[category],
            "total": model.objects.count(),
            "due": _due_count(request.user, category),
        })

    search_results = []
    if query:
        vocab_matches = Vocabulary.objects.filter(
            Q(word__icontains=query) | Q(meaning_th__icontains=query)
        )[:15]
        grammar_matches = GrammarPoint.objects.filter(
            Q(term__icontains=query) | Q(title__icontains=query)
        )[:15]
        kanji_matches = KanjiCharacter.objects.filter(
            Q(character__icontains=query) | Q(meaning_th__icontains=query)
        )[:15]

        search_results = (
            [_serialize_card(v, "vocabulary") for v in vocab_matches]
            + [_serialize_card(g, "grammar") for g in grammar_matches]
            + [_serialize_card(k, "kanji") for k in kanji_matches]
        )

    total_cards = sum(c["total"] for c in categories)
    reviewed_cards = 0
    if request.user.is_authenticated:
        reviewed_cards = FlashcardReview.objects.filter(
            user=request.user, repetitions__gte=1
        ).count()
    overall_percent = int((reviewed_cards / total_cards) * 100) if total_cards else 0

    return render(request, "flashcards/home.html", {
        "categories": categories,
        "query": query,
        "search_results": search_results,
        "due_today_total": sum(c["due"] for c in categories),
        "streak": _user_streak(request.user),
        "overall_percent": overall_percent,
    })


def _build_deck(model, content_type, reviewed_ids, user, filters, value, label):
    card_ids = list(model.objects.filter(**filters).values_list("id", flat=True))

    due = 0
    if user.is_authenticated:
        due = FlashcardReview.objects.filter(
            user=user,
            content_type=content_type,
            object_id__in=card_ids,
            due_date__lte=timezone.localdate(),
        ).count()
    new_count = len([cid for cid in card_ids if cid not in reviewed_ids])

    return {
        "value": value,
        "label": label,
        "total": len(card_ids),
        "due": due,
        "new": new_count,
    }


def deck_list(request, category):
    model = _get_model_or_404(category)
    content_type = _content_type_for(category)
    reviewed_ids = _reviewed_ids(request.user, content_type)

    if category == "grammar":
        level_labels = dict(LEVEL_CHOICES)
        language_groups = []

        for language, levels in LANGUAGE_LEVEL_ORDER.items():
            decks = []
            for level in levels:
                deck = _build_deck(
                    model, content_type, reviewed_ids, request.user,
                    filters={"language": language, "level": level},
                    value=level,
                    label=level_labels.get(level, level),
                )
                if deck["total"] > 0:
                    decks.append(deck)

            if decks:
                language_groups.append({
                    "language": language,
                    "label": LANGUAGE_LABELS.get(language, language),
                    "decks": decks,
                })

        return render(request, "flashcards/deck_list.html", {
            "category": category,
            "category_label": CATEGORY_LABELS[category],
            "language_groups": language_groups,
        })

    group_field = GROUP_FIELD[category]
    group_labels = _group_labels(category)

    groups_present = (
        model.objects.exclude(**{group_field: ""})
        .order_by(group_field)
        .values_list(group_field, flat=True)
        .distinct()
    )

    decks = [
        _build_deck(
            model, content_type, reviewed_ids, request.user,
            filters={group_field: group_value},
            value=group_value,
            label=group_labels.get(group_value, group_value),
        )
        for group_value in groups_present
    ]

    return render(request, "flashcards/deck_list.html", {
        "category": category,
        "category_label": CATEGORY_LABELS[category],
        "decks": decks,
    })


def study_session(request, category, group):
    model = _get_model_or_404(category)
    group_field = GROUP_FIELD[category]
    content_type = _content_type_for(category)

    queryset = model.objects.filter(**{group_field: group})
    if not queryset.exists():
        raise Http404("Deck not found")

    all_ids = list(queryset.values_list("id", flat=True))
    due_ids = []

    if request.user.is_authenticated:
        due_ids = list(
            FlashcardReview.objects.filter(
                user=request.user,
                content_type=content_type,
                object_id__in=all_ids,
                due_date__lte=timezone.localdate(),
            ).order_by("due_date").values_list("object_id", flat=True)
        )
        reviewed_ids = set(
            FlashcardReview.objects.filter(
                user=request.user, content_type=content_type, object_id__in=all_ids
            ).values_list("object_id", flat=True)
        )
        new_ids = [oid for oid in all_ids if oid not in reviewed_ids]
    else:
        new_ids = all_ids

    ordered_ids = (due_ids + new_ids)[:SESSION_SIZE]
    objects_by_id = queryset.in_bulk(ordered_ids)
    cards = [
        _serialize_card(objects_by_id[oid], category)
        for oid in ordered_ids
        if oid in objects_by_id
    ]

    group_labels = _group_labels(category)

    return render(request, "flashcards/study.html", {
        "category": category,
        "category_label": CATEGORY_LABELS[category],
        "group": group,
        "group_label": group_labels.get(group, group),
        "cards": cards,
    })


@login_required
@require_POST
def submit_review(request):
    category = request.POST.get("category")
    object_id = request.POST.get("object_id")
    quality = request.POST.get("quality")

    model = CATEGORY_MODELS.get(category)
    if model is None or quality not in dict(FlashcardReview.QUALITY_CHOICES):
        return JsonResponse({"ok": False, "error": "invalid request"}, status=400)

    card = get_object_or_404(model, pk=object_id)
    content_type = ContentType.objects.get_for_model(model)

    review, _created = FlashcardReview.objects.get_or_create(
        user=request.user,
        content_type=content_type,
        object_id=card.pk,
    )
    review.apply_review(quality)

    reviewed_cards = FlashcardReview.objects.filter(
        user=request.user, repetitions__gte=1
    ).count()
    if reviewed_cards >= 100:
        award_badge(request.user, "FLASHCARD_100")

    streak = _user_streak(request.user)
    if streak >= 7:
        award_badge(request.user, "FLASHCARD_STREAK_7")

    return JsonResponse({
        "ok": True,
        "due_date": review.due_date.isoformat(),
        "interval_days": review.interval_days,
        "due_today_total": _due_count(request.user),
        "streak": streak,
    })
