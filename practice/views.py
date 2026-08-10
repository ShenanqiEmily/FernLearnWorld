import random
import re

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse

from course.models import Course
from vocabulary.models import Vocabulary
from vocabulary.views import award_badge, get_lesson_data
from flashcards.models import LEVEL_CHOICES, GrammarPoint, KanjiCharacter
from flashcards.views import LANGUAGE_LABELS, LANGUAGE_LEVEL_ORDER

from .config import PASS_THRESHOLD, PRACTICE_MODES
from .models import PracticeAttempt

SOURCE_MODELS = {
    "grammar": GrammarPoint,
    "kanji": KanjiCharacter,
}

MATCHING_SIZE = 8
TYPING_SIZE = 10
MC_SIZE = 10
SENTENCE_BUILDER_SIZE = 8


def _relevant_courses():
    return Course.objects.filter(vocabularies__isnull=False).distinct()


def _relevant_levels(model):
    return list(
        model.objects.exclude(level="")
        .order_by("level")
        .values_list("level", flat=True)
        .distinct()
    )


def _mode_percent(user, mode_key, mode_cfg):
    source = mode_cfg.get("source", "vocabulary")

    if source == "vocabulary":
        courses = _relevant_courses()
        total = courses.count()
        if not total:
            return 0
        completed = (
            PracticeAttempt.objects.filter(
                user=user, mode=mode_key, course__in=courses, completed=True
            )
            .values("course_id")
            .distinct()
            .count()
        )
        return int((completed / total) * 100)

    model = SOURCE_MODELS[source]
    levels = _relevant_levels(model)
    total = len(levels)
    if not total:
        return 0
    completed = (
        PracticeAttempt.objects.filter(
            user=user, mode=mode_key, level__in=levels, completed=True
        )
        .values("level")
        .distinct()
        .count()
    )
    return int((completed / total) * 100)


def _mode_url(key, cfg):
    if key == "speaking":
        return reverse("practice:speaking_picker")
    if key == "vocab_mc":
        return reverse("practice:vocab_mc_picker")
    return reverse("practice:mode_picker", kwargs={"mode": key})


@login_required
def hub(request):
    mode_percents = {
        key: (_mode_percent(request.user, key, cfg) if cfg["playable"] else 0)
        for key, cfg in PRACTICE_MODES.items()
    }
    mode_urls = {
        key: (_mode_url(key, cfg) if cfg["playable"] else "")
        for key, cfg in PRACTICE_MODES.items()
    }

    total_xp = (
        PracticeAttempt.objects.filter(user=request.user).aggregate(
            total=Sum("xp_awarded")
        )["total"]
        or 0
    )

    return render(request, "practice/hub.html", {
        "practice_modes": PRACTICE_MODES,
        "mode_order": list(PRACTICE_MODES.keys()),
        "mode_percents": mode_percents,
        "mode_urls": mode_urls,
        "total_xp": total_xp,
    })


def _course_picker(request, mode_key):
    courses = _relevant_courses().order_by("code")

    return render(request, "practice/course_picker.html", {
        "mode": PRACTICE_MODES[mode_key],
        "mode_key": mode_key,
        "japanese_courses": courses.filter(code__startswith="JP-"),
        "chinese_courses": courses.filter(code__startswith="CN-"),
    })


@login_required
def speaking_picker(request):
    return _course_picker(request, "speaking")


@login_required
def vocab_mc_picker(request):
    return _course_picker(request, "vocab_mc")


@login_required
def speaking(request, course_code):
    vocabularies, course = get_lesson_data(course_code)

    return render(request, "practice/speaking.html", {
        "vocabularies": vocabularies,
        "course": course,
        "course_code": course_code,
        "mode": PRACTICE_MODES["speaking"],
    })


@login_required
def vocab_mc(request, course_code):
    vocabularies, course = get_lesson_data(course_code)

    return render(request, "practice/vocab_mc.html", {
        "vocabularies": vocabularies,
        "course": course,
        "course_code": course_code,
        "mode": PRACTICE_MODES["vocab_mc"],
    })


# ---------------------------------------------------------------
# Generic engine-driven modes (matching / typing / mc / sentence_builder)
# ---------------------------------------------------------------

def _level_label(level):
    return dict(LEVEL_CHOICES).get(level, level)


@login_required
def mode_picker(request, mode):
    mode_cfg = PRACTICE_MODES.get(mode)
    if not mode_cfg or not mode_cfg["playable"] or mode_cfg["mechanic"] in ("speaking", "vocab_mc"):
        raise Http404("Unknown or non-playable practice mode")

    source = mode_cfg["source"]
    if source == "vocabulary":
        return _course_picker(request, mode)

    model = SOURCE_MODELS[source]

    def levels_for(language):
        return [
            (level, _level_label(level))
            for level in LANGUAGE_LEVEL_ORDER[language]
            if model.objects.filter(language=language, level=level).exists()
        ]

    return render(request, "practice/level_picker.html", {
        "mode": mode_cfg,
        "mode_key": mode,
        "japanese_levels": levels_for("japanese"),
        "chinese_levels": levels_for("chinese"),
    })


def _clean_sentence(text):
    """Grammar example_sentence fields may pack 2 examples as '1) A / 2) B' —
    pull out just the first clean sentence for modes that need a single one."""
    first = (text or "").split(" / ")[0]
    return re.sub(r"^\d+\)\s*", "", first).strip()


def _play_matching(request, mode, mode_cfg, group):
    if mode_cfg["source"] == "vocabulary":
        vocabularies, course = get_lesson_data(group)
        items = [
            {"id": v.id, "front": v.word, "back": v.meaning_th}
            for v in vocabularies if v.meaning_th
        ][:MATCHING_SIZE]
        title = course.title if course else group
    else:
        qs = KanjiCharacter.objects.filter(level=group)
        items = [
            {"id": k.id, "front": k.character, "back": k.meaning_th}
            for k in qs if k.meaning_th
        ][:MATCHING_SIZE]
        title = _level_label(group)

    if not items:
        raise Http404("No content available for this deck yet")

    return render(request, "practice/play_matching.html", {
        "mode": mode_cfg,
        "mode_key": mode,
        "group": group,
        "title": title,
        "items": items,
    })


def _play_typing(request, mode, mode_cfg, group):
    vocabularies, course = get_lesson_data(group)
    items = []

    for v in vocabularies:
        aliases = [a.strip() for a in (v.speech_aliases or "").split(",") if a.strip()]

        if mode == "listening_dictation":
            items.append({
                "id": v.id,
                "prompt_type": "audio",
                "prompt": "",
                "tts_text": v.word,
                "answer": v.reading or v.pinyin or v.word,
                "aliases": aliases + [v.word],
                "language": v.language,
            })
        else:  # vocab_fill_blank
            sentence = v.example_sentence or ""
            if sentence and v.word in sentence:
                prompt = sentence.replace(v.word, "＿＿＿", 1)
            else:
                prompt = f"คำที่แปลว่า “{v.meaning_th}” คือคำว่าอะไร"
            items.append({
                "id": v.id,
                "prompt_type": "blank",
                "prompt": prompt,
                "tts_text": "",
                "answer": v.word,
                "aliases": aliases,
                "language": v.language,
            })

    items = items[:TYPING_SIZE]
    if not items:
        raise Http404("No content available for this deck yet")

    return render(request, "practice/play_typing.html", {
        "mode": mode_cfg,
        "mode_key": mode,
        "group": group,
        "title": course.title if course else group,
        "items": items,
    })


def _play_mc(request, mode, mode_cfg, group):
    if mode == "grammar_error_correction":
        pool = list(GrammarPoint.objects.filter(level=group))
        random.shuffle(pool)
        items = []
        for g in pool[:MC_SIZE]:
            wrong_pool = [p.term for p in pool if p.id != g.id]
            if len(wrong_pool) < 3:
                continue
            options = random.sample(wrong_pool, 3) + [g.term]
            random.shuffle(options)
            items.append({
                "id": g.id,
                "front_type": "text",
                "front": g.explanation_th,
                "options": options,
                "correct": g.term,
                "tts_text": "",
                "language": g.language,
            })
        title = _level_label(group)

    elif mode == "kanji_recognition":
        pool = list(KanjiCharacter.objects.filter(level=group))
        random.shuffle(pool)
        items = []
        for k in pool[:MC_SIZE]:
            reading = k.onyomi or k.kunyomi or k.pinyin
            if not reading:
                continue
            wrong_pool = [
                (p.onyomi or p.kunyomi or p.pinyin)
                for p in pool if p.id != k.id and (p.onyomi or p.kunyomi or p.pinyin)
            ]
            if len(wrong_pool) < 3:
                continue
            options = random.sample(wrong_pool, 3) + [reading]
            random.shuffle(options)
            items.append({
                "id": k.id,
                "front_type": "character",
                "front": k.character,
                "options": options,
                "correct": reading,
                "tts_text": "",
                "language": k.language,
            })
        title = _level_label(group)

    else:  # listening_audio_quiz
        vocabularies, course = get_lesson_data(group)
        pool = list(vocabularies)
        random.shuffle(pool)
        items = []
        for v in pool[:MC_SIZE]:
            wrong_pool = [p.meaning_th for p in pool if p.id != v.id and p.meaning_th]
            if len(wrong_pool) < 3:
                continue
            options = random.sample(wrong_pool, 3) + [v.meaning_th]
            random.shuffle(options)
            items.append({
                "id": v.id,
                "front_type": "audio",
                "front": "",
                "options": options,
                "correct": v.meaning_th,
                "tts_text": v.word,
                "language": v.language,
            })
        title = course.title if course else group

    if not items:
        raise Http404("No content available for this deck yet")

    return render(request, "practice/play_mc.html", {
        "mode": mode_cfg,
        "mode_key": mode,
        "group": group,
        "title": title,
        "items": items,
    })


def _play_sentence_builder(request, mode, mode_cfg, group):
    qs = GrammarPoint.objects.filter(level=group)
    items = []
    for g in qs[:SENTENCE_BUILDER_SIZE]:
        sentence = _clean_sentence(g.example_sentence)
        if not sentence:
            continue
        tokens = list(sentence)
        shuffled = tokens[:]
        random.shuffle(shuffled)
        items.append({
            "id": g.id,
            "term": g.term,
            "meaning": _clean_sentence(g.example_translation_th),
            "tokens": shuffled,
            "answer": sentence,
            "language": g.language,
        })

    if not items:
        raise Http404("No content available for this deck yet")

    return render(request, "practice/play_sentence_builder.html", {
        "mode": mode_cfg,
        "mode_key": mode,
        "group": group,
        "title": _level_label(group),
        "items": items,
    })


PLAY_HANDLERS = {
    "matching": _play_matching,
    "typing": _play_typing,
    "mc": _play_mc,
    "sentence_builder": _play_sentence_builder,
}


@login_required
def play(request, mode, group):
    mode_cfg = PRACTICE_MODES.get(mode)
    if not mode_cfg or not mode_cfg["playable"]:
        raise Http404("Unknown or non-playable practice mode")

    handler = PLAY_HANDLERS.get(mode_cfg["mechanic"])
    if not handler:
        raise Http404("Unsupported practice mechanic")

    return handler(request, mode, mode_cfg, group)


@login_required
def complete(request, mode, course_code):
    mode_cfg = PRACTICE_MODES.get(mode)

    if not mode_cfg or not mode_cfg["playable"]:
        raise Http404("Unknown or non-playable practice mode")

    source = mode_cfg.get("source", "vocabulary")
    course = None
    level = ""

    if source == "vocabulary":
        course = Course.objects.filter(code=course_code).first()
    else:
        level = course_code

    try:
        score = int(request.GET.get("score", 0))
    except (TypeError, ValueError):
        score = 0
    score = max(0, min(100, score))
    passed = score >= PASS_THRESHOLD

    xp_earned_this_time = 0
    attempt = None

    if course or level:
        attempt, _ = PracticeAttempt.objects.get_or_create(
            user=request.user, mode=mode, course=course, level=level
        )
        attempt.attempt_count += 1
        attempt.score = score
        attempt.best_score = max(attempt.best_score, score)

        if passed:
            attempt.completed = True
            if attempt.xp_awarded == 0:
                attempt.xp_awarded = mode_cfg["xp_reward"]
                xp_earned_this_time = attempt.xp_awarded

        attempt.save()

        if passed:
            award_badge(request.user, "PRACTICE_FIRST")

            total_xp = (
                PracticeAttempt.objects.filter(user=request.user)
                .aggregate(total=Sum("xp_awarded"))["total"]
                or 0
            )
            if total_xp >= 500:
                award_badge(request.user, "PRACTICE_XP_500")
            if total_xp >= 1000:
                award_badge(request.user, "PRACTICE_XP_1000")

    return render(request, "practice/complete.html", {
        "course": course,
        "course_code": course_code,
        "mode": mode_cfg,
        "mode_key": mode,
        "score": score,
        "passed": passed,
        "xp_earned": xp_earned_this_time,
        "attempt": attempt,
    })
