from django.contrib import messages
from django.db.models import Sum
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
from practice.models import PracticeAttempt
from subscriptions.access import user_can_access_course


def get_lesson_data(course_code=None):
    course = None
    vocabularies = Vocabulary.objects.all()

    if course_code:
        course = Course.objects.filter(code=course_code).first()
        vocabularies = vocabularies.filter(course__code=course_code)

    return list(vocabularies), course


def _paywall_redirect(request, course):
    """None if the user may view this lesson, otherwise a redirect to the
    subscribe page with a (non-scary, inviting) explanatory message."""
    if user_can_access_course(request.user, course):
        return None
    messages.info(
        request,
        "บทเรียนนี้อยู่ในแพ็กเกจสมาชิก สมัครเลยเพื่อปลดล็อกบทเรียนเต็มรูปแบบ 🎉",
    )
    return redirect("subscriptions:tier_picker")


@login_required
def vocab_card(request, course_code=None):
    vocabularies, course = get_lesson_data(course_code)

    blocked = _paywall_redirect(request, course)
    if blocked:
        return blocked

    return render(request, "vocabulary/vocab_card.html", {
        "vocabularies": vocabularies,
        "course_code": course_code,
        "course": course,
    })


@login_required
def sentence_practice(request, course_code=None):
    vocabularies, course = get_lesson_data(course_code)

    blocked = _paywall_redirect(request, course)
    if blocked:
        return blocked

    return render(request, "vocabulary/sentence_practice.html", {
        "vocabularies": vocabularies,
        "course_code": course_code,
        "course": course,
    })


def speaking_practice(request, course_code=None):
    # Speaking practice now lives in Practice Hub (templates/practice/speaking.html);
    # this legacy route has no template of its own, so send visitors there instead
    # of letting it 500. Kept (rather than removed) in case anything external
    # still links to it.
    if course_code:
        return redirect("practice:speaking", course_code=course_code)
    return redirect("practice:speaking_picker")

@login_required
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

    blocked = _paywall_redirect(request, course)
    if blocked:
        return blocked

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

            completed_course_ids = UserLessonProgress.objects.filter(
                user=request.user, completed=True
            ).values_list("course_id", flat=True)

            words_learned = Vocabulary.objects.filter(
                course_id__in=completed_course_ids
            ).count()

            if words_learned >= 100:
                award_badge(request.user, "VOCAB_100")

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
    ).select_related("course").order_by("-updated_at")

    # All courses that actually have vocabulary content — spans every
    # language/level (JP N5-N1, CN HSK1-6), not just JLPT N5.
    total_lessons = Course.objects.filter(vocabularies__isnull=False).distinct().count()
    completed_lessons = progresses.filter(completed=True).count()

    if total_lessons > 0:
        overall_percent = int((completed_lessons / total_lessons) * 100)
    else:
        overall_percent = 0

    total_xp = (
        PracticeAttempt.objects.filter(user=request.user)
        .aggregate(total=Sum("xp_awarded"))["total"]
        or 0
    )

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

    earned_at_by_achievement = {
        ua.achievement_id: ua.earned_at for ua in earned_achievements
    }
    earned_ids = set(earned_at_by_achievement.keys())

    all_achievements = list(Achievement.objects.all().order_by("id"))
    for achievement in all_achievements:
        achievement.is_earned = achievement.id in earned_ids
        achievement.earned_at = earned_at_by_achievement.get(achievement.id)

    total_count = len(all_achievements)
    earned_count = len(earned_ids)
    progress_percent = (
        int((earned_count / total_count) * 100) if total_count else 0
    )

    return render(
        request,
        "vocabulary/achievements.html",
        {
            "all_achievements": all_achievements,
            "earned_count": earned_count,
            "total_count": total_count,
            "progress_percent": progress_percent,
        },
    )