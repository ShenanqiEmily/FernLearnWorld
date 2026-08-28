"""
Shared paywall-eligibility checks, used by vocabulary/views.py,
flashcards/views.py and core/views.py (AI Tutor). All access decisions
route through Subscription.objects.current_for(user).is_paid_access — no
duplicate "is this user paid" logic lives anywhere else.
"""
from django.utils import timezone

from course.views import get_course_prefix_from_code
from course.models import Course

from subscriptions.models import Subscription, AITutorUsage

FREE_LESSON_LIMIT = 3
FREE_FLASHCARD_LEVELS = {"N5", "HSK1"}
AI_TUTOR_FREE_DAILY_LIMIT = 5


def user_has_paid_access(user):
    if not user.is_authenticated:
        return False
    subscription = Subscription.objects.current_for(user)
    return bool(subscription and subscription.is_paid_access)


def lesson_position(course):
    """
    1-indexed position of `course` among all lessons at the same level
    within its program, ordered by code — same convention already used by
    course/views.py::course_single's current_lesson_number.
    """
    prefix = get_course_prefix_from_code(course.code)
    level_course_ids = list(
        Course.objects.filter(program=course.program, code__startswith=prefix)
        .order_by("code")
        .values_list("id", flat=True)
    )
    try:
        return level_course_ids.index(course.id) + 1
    except ValueError:
        return 1


def user_can_access_course(user, course):
    """
    course=None (e.g. a mixed-course review quiz with no single course
    context) is always allowed — this check only gates specific lessons.
    """
    if course is None:
        return True
    if lesson_position(course) <= FREE_LESSON_LIMIT:
        return True
    return user_has_paid_access(user)


def user_can_access_flashcard_level(user, level):
    if level in FREE_FLASHCARD_LEVELS:
        return True
    return user_has_paid_access(user)


def has_ai_tutor_quota_remaining(user):
    """
    Read-only check — does NOT consume a slot. Call this before making the
    actual Anthropic request; only call record_ai_tutor_usage() once that
    request has genuinely succeeded, so a failed call (bad API key, rate
    limit, network error, ...) never costs the user one of their 5 free
    messages for something that wasn't their fault.
    """
    if user_has_paid_access(user):
        return True
    usage, _ = AITutorUsage.objects.get_or_create(
        user=user, date=timezone.localdate()
    )
    return usage.count < AI_TUTOR_FREE_DAILY_LIMIT


def record_ai_tutor_usage(user):
    """Call only after a message has actually gotten a successful AI reply."""
    if user_has_paid_access(user):
        return
    usage, _ = AITutorUsage.objects.get_or_create(
        user=user, date=timezone.localdate()
    )
    usage.count += 1
    usage.save(update_fields=["count"])
