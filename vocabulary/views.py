from django.shortcuts import render
from .models import Vocabulary
from course.models import Course
from django.shortcuts import render, redirect
from .models import Vocabulary, UserLessonProgress

from course.models import Course
from .models import Vocabulary
from .models import Achievement, UserAchievement
from django.contrib.auth.decorators import login_required
from .models import Achievement, UserAchievement


def get_lesson_data(course_code=None):
    course = None
    vocabularies = Vocabulary.objects.all()

    if course_code:
        course = Course.objects.filter(code=course_code).first()
        vocabularies = vocabularies.filter(course__code=course_code)

    return list(vocabularies), course


def vocab_card(request, course_code=None):
    vocabularies, course = get_lesson_data(course_code)

    return render(request, "vocabulary/vocab_card.html", {
        "vocabularies": vocabularies,
        "course_code": course_code,
        "course": course,
    })


def sentence_practice(request, course_code=None):
    vocabularies, course = get_lesson_data(course_code)

    return render(request, "vocabulary/sentence_practice.html", {
        "vocabularies": vocabularies,
        "course_code": course_code,
        "course": course,
    })


def speaking_practice(request, course_code=None):
    if not course_code:
        course_code = "JP-N5-001"

    vocabularies, course = get_lesson_data(course_code)

    try:
        start_index = int(request.GET.get("start", 0))
    except:
        start_index = 0

    if start_index < 0:
        start_index = 0

    if vocabularies and start_index >= len(vocabularies):
        start_index = 0

    return render(request, "vocabulary/speaking_practice.html", {
        "vocabularies": vocabularies,
        "course_code": course_code,
        "course": course,
        "start_index": start_index,
    })

def quiz_practice(request, course_code=None):
    if not course_code:
        course_code = "JP-N5-001"

    if course_code == "JP-N5-025":
        vocabularies = list(
            Vocabulary.objects.filter(
                course__code__startswith="JP-N5"
            )
            .exclude(course__code="JP-N5-025")
            .order_by("?")[:50]
        )

        course = Course.objects.filter(code="JP-N5-025").first()

    else:
        vocabularies, course = get_lesson_data(course_code)

    return render(request, "vocabulary/quiz_practice.html", {
        "vocabularies": vocabularies,
        "course_code": course_code,
        "course": course,
    })  


def award_badge(user, badge_code):
    achievement = Achievement.objects.filter(code=badge_code).first()

    if achievement:
        UserAchievement.objects.get_or_create(
            user=user,
            achievement=achievement,
        )

def lesson_complete(request, course_code=None):
    vocabularies, course = get_lesson_data(course_code)
    score = int(request.GET.get("score", 0))
    passed = score >= 70

    if request.user.is_authenticated and course:
        UserLessonProgress.objects.update_or_create(
            user=request.user,
            course=course,
            defaults={
                "score": score,
                "completed": passed,
                "vocab_completed": True,
                "sentence_completed": True,
                "speaking_completed": True,
                "quiz_completed": True,
            },
        )

        if passed:
            award_badge(request.user, "FIRST_LESSON")

        if score >= 90:
            award_badge(request.user, "QUIZ_90")

        completed_count = UserLessonProgress.objects.filter(
            user=request.user,
            completed=True,
            course__code__startswith="JP-N5",
        ).count()

        if completed_count >= 25:
            award_badge(request.user, "N5_GRADUATE")

    return render(
        request,
        "vocabulary/lesson_complete.html",
        {
            "course": course,
            "course_code": course_code,
            "score": score,
            "passed": passed,
            "vocabularies_count": len(vocabularies),
        },
    )


@login_required
def profile_progress(request):
    progresses = UserLessonProgress.objects.filter(
        user=request.user
    ).select_related("course")

    total_lessons = Course.objects.filter(code__startswith="JP-N5").count()
    completed_lessons = progresses.filter(completed=True).count()

    if total_lessons > 0:
        overall_percent = int((completed_lessons / total_lessons) * 100)
    else:
        overall_percent = 0

    total_xp = completed_lessons * 120

    return render(request, "vocabulary/profile_progress.html", {
        "progresses": progresses,
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "overall_percent": overall_percent,
        "total_xp": total_xp,
    })

@login_required
def achievements_page(request):
    earned_achievements = UserAchievement.objects.filter(
        user=request.user
    ).select_related("achievement")

    earned_ids = earned_achievements.values_list("achievement_id", flat=True)

    all_achievements = Achievement.objects.all().order_by("id")

    return render(
        request,
        "vocabulary/achievements.html",
        {
            "earned_achievements": earned_achievements,
            "earned_ids": earned_ids,
            "all_achievements": all_achievements,
        },
    )