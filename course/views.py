from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Avg, Max, Min, Count, Q
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView
from django.core.paginator import Paginator
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django_filters.views import FilterView

from accounts.models import User, Student
from core.models import Session, Semester
from result.models import TakenCourse
from accounts.decorators import lecturer_required, student_required
from .forms import (
    ProgramForm,
    CourseAddForm,
    CourseAllocationForm,
    EditCourseAllocationForm,
    UploadFormFile,
    UploadFormVideo,
)
from .filters import ProgramFilter, CourseAllocationFilter
from .models import Program, Course, CourseAllocation, Upload, UploadVideo
from vocabulary.models import Vocabulary, UserLessonProgress
from django.conf import settings



# ========================================================
# FernLearnWorld lesson-level progress helpers
# ========================================================

def normalize_level_value(level):
    """
    Normalize level value from URL/course code.
    Examples:
    n5 -> N5
    HSK 3 -> HSK3
    3 -> HSK3 only when Chinese context calls it explicitly
    """
    return (level or "").upper().replace(" ", "").strip()


def get_course_level_from_code(code):
    """
    Return level from a course code.

    Supported examples:
    JP-N5-001      -> N5
    JP-N1-006      -> N1
    CN-HSK3-001    -> HSK3
    HSK3-001       -> HSK3
    CN-3-001       -> HSK3
    """
    parts = (code or "").split("-")

    if len(parts) >= 2 and parts[0] == "JP":
        return parts[1]

    if len(parts) >= 2 and parts[0] == "CN":
        raw_level = normalize_level_value(parts[1])
        if raw_level.startswith("HSK"):
            return raw_level
        if raw_level in ["1", "2", "3", "4", "5", "6"]:
            return f"HSK{raw_level}"
        return raw_level

    if parts and normalize_level_value(parts[0]).startswith("HSK"):
        return normalize_level_value(parts[0])

    return ""


def get_course_prefix_from_code(code):
    """
    Return prefix for all lessons in the same level.

    Supported examples:
    JP-N5-001      -> JP-N5-
    JP-N1-006      -> JP-N1-
    CN-HSK3-001    -> CN-HSK3-
    HSK3-001       -> HSK3-
    CN-3-001       -> CN-3-
    """
    parts = (code or "").split("-")

    if len(parts) >= 2:
        return f"{parts[0]}-{parts[1]}-"

    return ""


def get_level_label_from_level(level):
    """
    Make a user-facing label from a level value.
    N5 -> JLPT N5
    HSK3 -> HSK 3
    """
    level = normalize_level_value(level)

    if level.startswith("HSK"):
        return f"HSK {level.replace('HSK', '')}"

    if level.startswith("N"):
        return f"JLPT {level}"

    return level or "Course"


def get_course_filter_for_level(program, selected_level):
    """
    Return a queryset filter for the selected level.
    This supports the code styles commonly used in FernLearnWorld:
    Japanese: JP-N5-001
    Chinese: CN-HSK3-001, HSK3-001, or CN-3-001
    """
    selected_level = normalize_level_value(selected_level)

    if selected_level.startswith("N"):
        return Q(code__startswith=f"JP-{selected_level}-")

    if selected_level.startswith("HSK"):
        hsk_number = selected_level.replace("HSK", "")
        return (
            Q(code__startswith=f"CN-{selected_level}-") |
            Q(code__startswith=f"{selected_level}-") |
            Q(code__startswith=f"CN-{hsk_number}-")
        )

    return Q()


def calculate_level_progress(user, courses):
    """
    Calculate level progress from UserLessonProgress.completed=True only.

    Formula:
    completed lessons / total lessons * 100
    """
    total_lessons = courses.count()

    completed_course_ids = set(
        UserLessonProgress.objects.filter(
            user=user,
            course__in=courses,
            completed=True,
        ).values_list("course_id", flat=True)
    )

    completed_lessons = len(completed_course_ids)

    progress_percent = (
        int((completed_lessons / total_lessons) * 100)
        if total_lessons
        else 0
    )

    return {
        "completed_course_ids": completed_course_ids,
        "completed_lessons": completed_lessons,
        "total_lessons": total_lessons,
        "progress_percent": progress_percent,
    }


def get_program_level_config(program, requested_level):
    """
    Resolve the active level and queryset filter for a program detail page.
    Supports Japanese JLPT N5-N1 and Chinese HSK1-HSK6.
    """
    program_title = (program.title or "").lower()
    requested_level = normalize_level_value(requested_level)

    is_japanese_program = (
        program.id == 1
        or "japanese" in program_title
        or "jlpt" in program_title
        or "ญี่ปุ่น" in program_title
    )

    is_chinese_program = (
        program.id == 2
        or "chinese" in program_title
        or "hsk" in program_title
        or "จีน" in program_title
    )

    if is_japanese_program:
        level_options = ["N5", "N4", "N3", "N2", "N1"]

        if requested_level not in level_options:
            requested_level = "N5"

        selected_level = requested_level
        level_label = get_level_label_from_level(selected_level)
        display_course_title = f"{level_label} Japanese Course"
        course_filter = get_course_filter_for_level(program, selected_level)

        return {
            "selected_level": selected_level,
            "level_options": level_options,
            "level_label": level_label,
            "display_course_title": display_course_title,
            "course_filter": course_filter,
        }

    if is_chinese_program:
        level_options = ["HSK1", "HSK2", "HSK3", "HSK4", "HSK5", "HSK6"]

        if requested_level in ["1", "2", "3", "4", "5", "6"]:
            requested_level = f"HSK{requested_level}"

        if requested_level not in level_options:
            requested_level = "HSK1"

        selected_level = requested_level
        hsk_number = selected_level.replace("HSK", "")
        level_label = get_level_label_from_level(selected_level)
        display_course_title = f"{level_label} Chinese Course"
        course_filter = get_course_filter_for_level(program, selected_level)

        return {
            "selected_level": selected_level,
            "level_options": level_options,
            "level_label": level_label,
            "display_course_title": display_course_title,
            "course_filter": course_filter,
        }

    return {
        "selected_level": "",
        "level_options": [],
        "level_label": program.title,
        "display_course_title": program.title,
        "course_filter": Q(),
    }

@method_decorator([login_required], name="dispatch")
class ProgramFilterView(FilterView):
    filterset_class = ProgramFilter
    template_name = "course/program_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Programs"
        return context


@login_required
@lecturer_required
def program_add(request):
    if request.method == "POST":
        form = ProgramForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, request.POST.get("title") + " program has been created."
            )
            return redirect("programs")
        else:
            messages.error(request, "Correct the error(S) below.")
    else:
        form = ProgramForm()

    return render(
        request,
        "course/program_add.html",
        {
            "title": "Add Program",
            "form": form,
        },
    )


@login_required
def program_detail(request, pk):
    program = get_object_or_404(Program, pk=pk)

    level_config = get_program_level_config(
        program=program,
        requested_level=request.GET.get("level"),
    )

    courses = (
        Course.objects
        .filter(program=program)
        .filter(level_config["course_filter"])
        .order_by("code")
    )

    credits = courses.aggregate(Sum("credit"))
    progress = calculate_level_progress(request.user, courses)
    completed_course_ids = progress["completed_course_ids"]

    lesson_list = []
    dev_unlock_all = getattr(settings, "DEV_UNLOCK_ALL_LESSONS", False)
    previous_unlocked = True

    for course in courses:
        is_completed = course.id in completed_course_ids

        if dev_unlock_all:
            is_unlocked = True
        else:
            is_unlocked = previous_unlocked

        lesson_list.append({
            "course": course,
            "is_completed": is_completed,
            "is_unlocked": is_unlocked,
        })

        previous_unlocked = is_completed

    next_lesson = (
        courses
        .exclude(id__in=completed_course_ids)
        .order_by("code")
        .first()
    )

    return render(
        request,
        "course/program_single.html",
        {
            "title": level_config["display_course_title"],
            "program": program,
            "courses": courses,
            "lesson_list": lesson_list,
            "credits": credits,
            "selected_level": level_config["selected_level"],
            "level_options": level_config["level_options"],
            "level_label": level_config["level_label"],
            "display_course_title": level_config["display_course_title"],
            "completed_lessons": progress["completed_lessons"],
            "total_lessons": progress["total_lessons"],
            "level_progress_percent": progress["progress_percent"],
            "next_lesson": next_lesson,
        },
    )

@login_required
@lecturer_required
def program_edit(request, pk):
    program = Program.objects.get(pk=pk)

    if request.method == "POST":
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            form.save()
            messages.success(
                request, str(request.POST.get("title")) + " program has been updated."
            )
            return redirect("programs")
    else:
        form = ProgramForm(instance=program)

    return render(
        request,
        "course/program_add.html",
        {"title": "Edit Program", "form": form},
    )


@login_required
@lecturer_required
def program_delete(request, pk):
    program = Program.objects.get(pk=pk)
    title = program.title
    program.delete()
    messages.success(request, "Program " + title + " has been deleted.")

    return redirect("programs")


# ########################################################


# ########################################################
# Course views
# ########################################################
@login_required
def course_single(request, slug):
    course = get_object_or_404(Course, slug=slug)

    files = Upload.objects.filter(course__slug=slug)
    videos = UploadVideo.objects.filter(course__slug=slug)
    lecturers = CourseAllocation.objects.filter(courses__pk=course.id)

    vocabularies = Vocabulary.objects.filter(course=course)
    vocab_count = vocabularies.count()
    sentence_count = (
        vocabularies
        .exclude(example_sentence__isnull=True)
        .exclude(example_sentence="")
        .count()
    )
    sample_vocab = vocabularies.first()

    selected_level = get_course_level_from_code(course.code)
    course_prefix = get_course_prefix_from_code(course.code)

    level_label = get_level_label_from_level(selected_level)

    level_courses = (
        Course.objects
        .filter(program=course.program, code__startswith=course_prefix)
        .order_by("code")
    )

    progress = calculate_level_progress(request.user, level_courses)
    course_ids = list(level_courses.values_list("id", flat=True))

    try:
        current_lesson_number = course_ids.index(course.id) + 1
    except ValueError:
        current_lesson_number = 1

    is_completed = UserLessonProgress.objects.filter(
        user=request.user,
        course=course,
        completed=True,
    ).exists()

    is_final_lesson = (
        progress["total_lessons"] > 0
        and current_lesson_number == progress["total_lessons"]
    )

    lesson_map_url = (
        f"/th/programs/{course.program.id}/detail/?level={selected_level}"
        if selected_level
        else f"/th/programs/{course.program.id}/detail/"
    )

    return render(
        request,
        "course/course_single.html",
        {
            "title": course.title,
            "course": course,
            "files": files,
            "videos": videos,
            "lecturers": lecturers,
            "media_url": settings.MEDIA_ROOT,

            "vocab_count": vocab_count,
            "sentence_count": sentence_count,
            "sample_vocab": sample_vocab,

            "selected_level": selected_level,
            "level_label": level_label,
            "completed_lessons": progress["completed_lessons"],
            "total_lessons": progress["total_lessons"],
            "level_progress_percent": progress["progress_percent"],
            "current_lesson_number": current_lesson_number,
            "is_completed": is_completed,
            "is_final_lesson": is_final_lesson,
            "lesson_map_url": lesson_map_url,
        },
    )

@login_required
@lecturer_required
def course_add(request, pk):
    users = User.objects.all()
    if request.method == "POST":
        form = CourseAddForm(request.POST)
        course_name = request.POST.get("title")
        course_code = request.POST.get("code")
        if form.is_valid():
            form.save()
            messages.success(
                request, (course_name + "(" + course_code + ")" + " has been created.")
            )
            return redirect("program_detail", pk=request.POST.get("program"))
        else:
            messages.error(request, "Correct the error(s) below.")
    else:
        form = CourseAddForm(initial={"program": Program.objects.get(pk=pk)})

    return render(
        request,
        "course/course_add.html",
        {
            "title": "Add Course",
            "form": form,
            "program": pk,
            "users": users,
        },
    )


@login_required
@lecturer_required
def course_edit(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == "POST":
        form = CourseAddForm(request.POST, instance=course)
        course_name = request.POST.get("title")
        course_code = request.POST.get("code")
        if form.is_valid():
            form.save()
            messages.success(
                request, (course_name + "(" + course_code + ")" + " has been updated.")
            )
            return redirect("program_detail", pk=request.POST.get("program"))
        else:
            messages.error(request, "Correct the error(s) below.")
    else:
        form = CourseAddForm(instance=course)

    return render(
        request,
        "course/course_add.html",
        {
            "title": "Edit Course",
            # 'form': form, 'program': pk, 'course': pk
            "form": form,
        },
    )


@login_required
@lecturer_required
def course_delete(request, slug):
    course = Course.objects.get(slug=slug)
    # course_name = course.title
    course.delete()
    messages.success(request, "Course " + course.title + " has been deleted.")

    return redirect("program_detail", pk=course.program.id)


# ########################################################


# ########################################################
# Course Allocation
# ########################################################
@method_decorator([login_required], name="dispatch")
class CourseAllocationFormView(CreateView):
    form_class = CourseAllocationForm
    template_name = "course/course_allocation_form.html"

    def get_form_kwargs(self):
        kwargs = super(CourseAllocationFormView, self).get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        # if a staff has been allocated a course before update it else create new
        lecturer = form.cleaned_data["lecturer"]
        selected_courses = form.cleaned_data["courses"]
        courses = ()
        for course in selected_courses:
            courses += (course.pk,)
        # print(courses)

        try:
            a = CourseAllocation.objects.get(lecturer=lecturer)
        except:
            a = CourseAllocation.objects.create(lecturer=lecturer)
        for i in range(0, selected_courses.count()):
            a.courses.add(courses[i])
            a.save()
        return redirect("course_allocation_view")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Assign Course"
        return context


@method_decorator([login_required], name="dispatch")
class CourseAllocationFilterView(FilterView):
    filterset_class = CourseAllocationFilter
    template_name = "course/course_allocation_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Course Allocations"
        return context


@login_required
@lecturer_required
def edit_allocated_course(request, pk):
    allocated = get_object_or_404(CourseAllocation, pk=pk)
    if request.method == "POST":
        form = EditCourseAllocationForm(request.POST, instance=allocated)
        if form.is_valid():
            form.save()
            messages.success(request, "course assigned has been updated.")
            return redirect("course_allocation_view")
    else:
        form = EditCourseAllocationForm(instance=allocated)

    return render(
        request,
        "course/course_allocation_form.html",
        {"title": "Edit Course Allocated", "form": form, "allocated": pk},
    )


@login_required
@lecturer_required
def deallocate_course(request, pk):
    course = CourseAllocation.objects.get(pk=pk)
    course.delete()
    messages.success(request, "successfully deallocate!")
    return redirect("course_allocation_view")


# ########################################################


# ########################################################
# File Upload views
# ########################################################
@login_required
@lecturer_required
def handle_file_upload(request, slug):
    course = Course.objects.get(slug=slug)
    if request.method == "POST":
        form = UploadFormFile(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.course = course
            obj.save()

            messages.success(
                request, (request.POST.get("title") + " has been uploaded.")
            )
            return redirect("course_detail", slug=slug)
    else:
        form = UploadFormFile()
    return render(
        request,
        "upload/upload_file_form.html",
        {"title": "File Upload", "form": form, "course": course},
    )


@login_required
@lecturer_required
def handle_file_edit(request, slug, file_id):
    course = Course.objects.get(slug=slug)
    instance = Upload.objects.get(pk=file_id)
    if request.method == "POST":
        form = UploadFormFile(request.POST, request.FILES, instance=instance)
        # file_name = request.POST.get('name')
        if form.is_valid():
            form.save()
            messages.success(
                request, (request.POST.get("title") + " has been updated.")
            )
            return redirect("course_detail", slug=slug)
    else:
        form = UploadFormFile(instance=instance)

    return render(
        request,
        "upload/upload_file_form.html",
        {"title": instance.title, "form": form, "course": course},
    )


def handle_file_delete(request, slug, file_id):
    file = Upload.objects.get(pk=file_id)
    # file_name = file.name
    file.delete()

    messages.success(request, (file.title + " has been deleted."))
    return redirect("course_detail", slug=slug)


# ########################################################
# Video Upload views
# ########################################################
@login_required
@lecturer_required
def handle_video_upload(request, slug):
    course = Course.objects.get(slug=slug)
    if request.method == "POST":
        form = UploadFormVideo(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.course = course
            obj.save()

            messages.success(
                request, (request.POST.get("title") + " has been uploaded.")
            )
            return redirect("course_detail", slug=slug)
    else:
        form = UploadFormVideo()
    return render(
        request,
        "upload/upload_video_form.html",
        {"title": "Video Upload", "form": form, "course": course},
    )


@login_required
# @lecturer_required
def handle_video_single(request, slug, video_slug):
    course = get_object_or_404(Course, slug=slug)
    video = get_object_or_404(UploadVideo, slug=video_slug)
    return render(request, "upload/video_single.html", {"video": video})


@login_required
@lecturer_required
def handle_video_edit(request, slug, video_slug):
    course = Course.objects.get(slug=slug)
    instance = UploadVideo.objects.get(slug=video_slug)
    if request.method == "POST":
        form = UploadFormVideo(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(
                request, (request.POST.get("title") + " has been updated.")
            )
            return redirect("course_detail", slug=slug)
    else:
        form = UploadFormVideo(instance=instance)

    return render(
        request,
        "upload/upload_video_form.html",
        {"title": instance.title, "form": form, "course": course},
    )


def handle_video_delete(request, slug, video_slug):
    video = get_object_or_404(UploadVideo, slug=video_slug)
    # video = UploadVideo.objects.get(slug=video_slug)
    video.delete()

    messages.success(request, (video.title + " has been deleted."))
    return redirect("course_detail", slug=slug)


# ########################################################


# ########################################################
# Course Registration
# ########################################################
@login_required
@student_required
def course_registration(request):
    if request.method == "POST":
        student = Student.objects.get(student__pk=request.user.id)
        ids = ()
        data = request.POST.copy()
        data.pop("csrfmiddlewaretoken", None)  # remove csrf_token
        for key in data.keys():
            ids = ids + (str(key),)
        for s in range(0, len(ids)):
            course = Course.objects.get(pk=ids[s])
            obj = TakenCourse.objects.create(student=student, course=course)
            obj.save()
        messages.success(request, "Courses registered successfully!")
        return redirect("course_registration")
    else:
        current_semester = Semester.objects.filter(is_current_semester=True).first()
        if not current_semester:
            messages.error(request, "No active semester found.")
            return render(request, "course/course_registration.html")

        # student = Student.objects.get(student__pk=request.user.id)
        student = get_object_or_404(Student, student__id=request.user.id)
        taken_courses = TakenCourse.objects.filter(student__student__id=request.user.id)
        t = ()
        for i in taken_courses:
            t += (i.course.pk,)

        courses = (
            Course.objects.filter(
                program__pk=student.program.id,
                level=student.level,
                semester=current_semester,
            )
            .exclude(id__in=t)
            .order_by("year")
        )
        all_courses = Course.objects.filter(
            level=student.level, program__pk=student.program.id
        )

        no_course_is_registered = False  # Check if no course is registered
        all_courses_are_registered = False

        registered_courses = Course.objects.filter(level=student.level).filter(id__in=t)
        if (
            registered_courses.count() == 0
        ):  # Check if number of registered courses is 0
            no_course_is_registered = True

        if registered_courses.count() == all_courses.count():
            all_courses_are_registered = True

        total_first_semester_credit = 0
        total_sec_semester_credit = 0
        total_registered_credit = 0
        for i in courses:
            if i.semester == "First":
                total_first_semester_credit += int(i.credit)
            if i.semester == "Second":
                total_sec_semester_credit += int(i.credit)
        for i in registered_courses:
            total_registered_credit += int(i.credit)
        context = {
            "is_calender_on": True,
            "all_courses_are_registered": all_courses_are_registered,
            "no_course_is_registered": no_course_is_registered,
            "current_semester": current_semester,
            "courses": courses,
            "total_first_semester_credit": total_first_semester_credit,
            "total_sec_semester_credit": total_sec_semester_credit,
            "registered_courses": registered_courses,
            "total_registered_credit": total_registered_credit,
            "student": student,
        }
        return render(request, "course/course_registration.html", context)


@login_required
@student_required
def course_drop(request):
    if request.method == "POST":
        student = Student.objects.get(student__pk=request.user.id)
        ids = ()
        data = request.POST.copy()
        data.pop("csrfmiddlewaretoken", None)  # remove csrf_token
        for key in data.keys():
            ids = ids + (str(key),)
        for s in range(0, len(ids)):
            course = Course.objects.get(pk=ids[s])
            obj = TakenCourse.objects.get(student=student, course=course)
            obj.delete()
        messages.success(request, "Successfully Dropped!")
        return redirect("course_registration")


# ########################################################


@login_required
def user_course_list(request):
    if request.user.is_lecturer:
        courses = Course.objects.filter(allocated_course__lecturer__pk=request.user.id)

        return render(request, "course/user_course_list.html", {"courses": courses})

    elif request.user.is_student:
        student = Student.objects.get(student__pk=request.user.id)
        taken_courses = TakenCourse.objects.filter(
            student__student__id=student.student.id
        )
        if student.level and student.program:
            courses = Course.objects.filter(level=student.level).filter(
                program__pk=student.program.id
            )
        else:
            courses = Course.objects.filter(vocabularies__isnull=False).distinct()

        return render(
            request,
            "course/user_course_list.html",
            {"student": student, "taken_courses": taken_courses, "courses": courses},
        )

    else:
        return render(request, "course/user_course_list.html")