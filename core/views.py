import json

import anthropic
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from accounts.decorators import admin_required, lecturer_required
from accounts.models import User, Student
from .ai_tutor_prompts import AI_TUTOR_MODES
from .forms import SessionForm, SemesterForm, NewsAndEventsForm
from .models import NewsAndEvents, ActivityLog, Session, Semester

from django.db.models import Sum
from django.utils import timezone

from course.models import Course
from vocabulary.models import UserLessonProgress, Vocabulary
from flashcards.models import FlashcardReview, GrammarPoint, KanjiCharacter
from practice.models import PracticeAttempt
# ########################################################
# News & Events
# ########################################################
def home_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    stats = {
        "vocab_count": Vocabulary.objects.count(),
        "lesson_count": Course.objects.filter(vocabularies__isnull=False).distinct().count(),
        "grammar_count": GrammarPoint.objects.count(),
        "kanji_count": KanjiCharacter.objects.count(),
    }
    return render(request, "core/index.html", {"stats": stats})


def about_view(request):
    return render(request, "core/about.html")


@login_required
def dashboard_view(request):
    logs = ActivityLog.objects.all().order_by("-created_at")[:10]
    gender_count = Student.get_gender_count()

    # All courses that actually have vocabulary content — spans every
    # language/level (JP N5-N1, CN HSK1-6), not just JLPT N5.
    all_courses = Course.objects.filter(vocabularies__isnull=False).distinct().order_by("code")

    progresses = UserLessonProgress.objects.filter(
        user=request.user,
        course__in=all_courses
    ).select_related("course")

    completed_progresses = progresses.filter(completed=True)
    completed_lessons = completed_progresses.count()
    total_lessons = all_courses.count()

    overall_percent = (
        int((completed_lessons / total_lessons) * 100)
        if total_lessons
        else 0
    )

    total_xp = (
        PracticeAttempt.objects.filter(user=request.user)
        .aggregate(total=Sum("xp_awarded"))["total"]
        or 0
    )

    flashcards_due_today = FlashcardReview.objects.filter(
        user=request.user, due_date__lte=timezone.localdate()
    ).count()

    latest_progress = progresses.order_by("-id")[:5]

    if completed_progresses.exists():
        average_score = int(
            sum(progress.score for progress in completed_progresses)
            / completed_progresses.count()
        )
        best_progress = completed_progresses.order_by("-score").first()
    else:
        average_score = 0
        best_progress = None

    completed_course_ids = completed_progresses.values_list("course_id", flat=True)

    next_lesson = (
        all_courses.exclude(id__in=completed_course_ids)
        .order_by("code")
        .first()
    )

    context = {
        "student_count": User.objects.get_student_count(),
        "lecturer_count": User.objects.get_lecturer_count(),
        "superuser_count": User.objects.get_superuser_count(),
        "males_count": gender_count["M"],
        "females_count": gender_count["F"],
        "logs": logs,
        "completed_lessons": completed_lessons,
        "total_lessons": total_lessons,
        "overall_percent": overall_percent,
        "total_xp": total_xp,
        "flashcards_due_today": flashcards_due_today,
        "latest_progress": latest_progress,
        "average_score": average_score,
        "best_progress": best_progress,
        "next_lesson": next_lesson,
    }

    return render(request, "core/dashboard.html", context)

@login_required
def post_add(request):
    if request.method == "POST":
        form = NewsAndEventsForm(request.POST)
        title = request.POST.get("title")
        if form.is_valid():
            form.save()

            messages.success(request, (title + " has been uploaded."))
            return redirect("home")
        else:
            messages.error(request, "Please correct the error(s) below.")
    else:
        form = NewsAndEventsForm()
    return render(
        request,
        "core/post_add.html",
        {
            "title": "Add Post",
            "form": form,
        },
    )


@login_required
@lecturer_required
def edit_post(request, pk):
    instance = get_object_or_404(NewsAndEvents, pk=pk)
    if request.method == "POST":
        form = NewsAndEventsForm(request.POST, instance=instance)
        title = request.POST.get("title")
        if form.is_valid():
            form.save()

            messages.success(request, (title + " has been updated."))
            return redirect("home")
        else:
            messages.error(request, "Please correct the error(s) below.")
    else:
        form = NewsAndEventsForm(instance=instance)
    return render(
        request,
        "core/post_add.html",
        {
            "title": "Edit Post",
            "form": form,
        },
    )


@login_required
@lecturer_required
def delete_post(request, pk):
    post = get_object_or_404(NewsAndEvents, pk=pk)
    title = post.title
    post.delete()
    messages.success(request, (title + " has been deleted."))
    return redirect("home")


# ########################################################
# Session
# ########################################################
@login_required
@lecturer_required
def session_list_view(request):
    """Show list of all sessions"""
    sessions = Session.objects.all().order_by("-is_current_session", "-session")
    return render(request, "core/session_list.html", {"sessions": sessions})


@login_required
@lecturer_required
def session_add_view(request):
    """check request method, if POST we add session otherwise show empty form"""
    if request.method == "POST":
        form = SessionForm(request.POST)
        if form.is_valid():
            data = form.data.get(
                "is_current_session"
            )  # returns string of 'True' if the user selected Yes
            print(data)
            if data == "true":
                sessions = Session.objects.all()
                if sessions:
                    for session in sessions:
                        if session.is_current_session == True:
                            unset = Session.objects.get(is_current_session=True)
                            unset.is_current_session = False
                            unset.save()
                    form.save()
                else:
                    form.save()
            else:
                form.save()
            messages.success(request, "Session added successfully. ")
            return redirect("session_list")

    else:
        form = SessionForm()
    return render(request, "core/session_update.html", {"form": form})


@login_required
@lecturer_required
def session_update_view(request, pk):
    session = Session.objects.get(pk=pk)
    if request.method == "POST":
        form = SessionForm(request.POST, instance=session)
        data = form.data.get("is_current_session")
        if data == "true":
            sessions = Session.objects.all()
            if sessions:
                for session in sessions:
                    if session.is_current_session == True:
                        unset = Session.objects.get(is_current_session=True)
                        unset.is_current_session = False
                        unset.save()

            if form.is_valid():
                form.save()
                messages.success(request, "Session updated successfully. ")
                return redirect("session_list")
        else:
            form = SessionForm(request.POST, instance=session)
            if form.is_valid():
                form.save()
                messages.success(request, "Session updated successfully. ")
                return redirect("session_list")

    else:
        form = SessionForm(instance=session)
    return render(request, "core/session_update.html", {"form": form})


@login_required
@lecturer_required
def session_delete_view(request, pk):
    session = get_object_or_404(Session, pk=pk)

    if session.is_current_session:
        messages.error(request, "You cannot delete current session")
        return redirect("session_list")
    else:
        session.delete()
        messages.success(request, "Session successfully deleted")
    return redirect("session_list")


# ########################################################


# ########################################################
# Semester
# ########################################################
@login_required
@lecturer_required
def semester_list_view(request):
    semesters = Semester.objects.all().order_by("-is_current_semester", "-semester")
    return render(
        request,
        "core/semester_list.html",
        {
            "semesters": semesters,
        },
    )


@login_required
@lecturer_required
def semester_add_view(request):
    if request.method == "POST":
        form = SemesterForm(request.POST)
        if form.is_valid():
            data = form.data.get(
                "is_current_semester"
            )  # returns string of 'True' if the user selected Yes
            if data == "True":
                semester = form.data.get("semester")
                ss = form.data.get("session")
                session = Session.objects.get(pk=ss)
                try:
                    if Semester.objects.get(semester=semester, session=ss):
                        messages.error(
                            request,
                            semester
                            + " semester in "
                            + session.session
                            + " session already exist",
                        )
                        return redirect("add_semester")
                except:
                    semesters = Semester.objects.all()
                    sessions = Session.objects.all()
                    if semesters:
                        for semester in semesters:
                            if semester.is_current_semester == True:
                                unset_semester = Semester.objects.get(
                                    is_current_semester=True
                                )
                                unset_semester.is_current_semester = False
                                unset_semester.save()
                        for session in sessions:
                            if session.is_current_session == True:
                                unset_session = Session.objects.get(
                                    is_current_session=True
                                )
                                unset_session.is_current_session = False
                                unset_session.save()

                    new_session = request.POST.get("session")
                    set_session = Session.objects.get(pk=new_session)
                    set_session.is_current_session = True
                    set_session.save()
                    form.save()
                    messages.success(request, "Semester added successfully.")
                    return redirect("semester_list")

            form.save()
            messages.success(request, "Semester added successfully. ")
            return redirect("semester_list")
    else:
        form = SemesterForm()
    return render(request, "core/semester_update.html", {"form": form})


@login_required
@lecturer_required
def semester_update_view(request, pk):
    semester = Semester.objects.get(pk=pk)
    if request.method == "POST":
        if (
            request.POST.get("is_current_semester") == "True"
        ):  # returns string of 'True' if the user selected yes for 'is current semester'
            unset_semester = Semester.objects.get(is_current_semester=True)
            unset_semester.is_current_semester = False
            unset_semester.save()
            unset_session = Session.objects.get(is_current_session=True)
            unset_session.is_current_session = False
            unset_session.save()
            new_session = request.POST.get("session")
            form = SemesterForm(request.POST, instance=semester)
            if form.is_valid():
                set_session = Session.objects.get(pk=new_session)
                set_session.is_current_session = True
                set_session.save()
                form.save()
                messages.success(request, "Semester updated successfully !")
                return redirect("semester_list")
        else:
            form = SemesterForm(request.POST, instance=semester)
            if form.is_valid():
                form.save()
                return redirect("semester_list")

    else:
        form = SemesterForm(instance=semester)
    return render(request, "core/semester_update.html", {"form": form})


@login_required
@lecturer_required
def semester_delete_view(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    if semester.is_current_semester:
        messages.error(request, "You cannot delete current semester")
        return redirect("semester_list")
    else:
        semester.delete()
        messages.success(request, "Semester successfully deleted")
    return redirect("semester_list")

# ai tutor
@login_required
def ai_tutor(request):
    modes = {
        key: {
            "label": mode["label"],
            "icon": mode["icon"],
            "description": mode["description"],
            "suggested_prompts": mode["suggested_prompts"],
        }
        for key, mode in AI_TUTOR_MODES.items()
    }

    return render(request, "ai/ai_tutor.html", {
        "ai_tutor_modes": modes,
        "ai_tutor_mode_order": list(AI_TUTOR_MODES.keys()),
    })


@login_required
@require_POST
def ai_tutor_chat(request):
    mode = request.POST.get("mode")
    message = (request.POST.get("message") or "").strip()

    mode_config = AI_TUTOR_MODES.get(mode)
    if not mode_config or not message:
        return JsonResponse({"ok": False, "error": "invalid request"}, status=400)

    if not settings.ANTHROPIC_API_KEY:
        return JsonResponse({
            "ok": False,
            "error": "ยังไม่ได้ตั้งค่า ANTHROPIC_API_KEY กรุณาเพิ่มคีย์ใน .env ก่อนใช้งาน AI Tutor",
        }, status=400)

    try:
        history = json.loads(request.POST.get("history") or "[]")
    except ValueError:
        history = []

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    try:
        response = client.messages.create(
            model=settings.AI_TUTOR_MODEL,
            max_tokens=1024,
            system=mode_config["system_prompt"],
            messages=history + [{"role": "user", "content": message}],
        )
    except anthropic.AuthenticationError:
        return JsonResponse({"ok": False, "error": "ANTHROPIC_API_KEY ไม่ถูกต้อง"}, status=502)
    except anthropic.RateLimitError:
        return JsonResponse({"ok": False, "error": "AI ถูกใช้งานถี่เกินไป กรุณารอสักครู่แล้วลองใหม่"}, status=502)
    except anthropic.APIStatusError as e:
        return JsonResponse({"ok": False, "error": f"AI service error: {e.message}"}, status=502)
    except anthropic.APIConnectionError:
        return JsonResponse({"ok": False, "error": "เชื่อมต่อ AI ไม่ได้ กรุณาตรวจสอบอินเทอร์เน็ต"}, status=502)

    reply = next((block.text for block in response.content if block.type == "text"), "")

    return JsonResponse({"ok": True, "reply": reply})