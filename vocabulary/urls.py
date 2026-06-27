from django.urls import path
from . import views

app_name = "vocabulary"

urlpatterns = [
    path("", views.vocab_card, name="vocab_card"),

    path("sentence/", views.sentence_practice, name="sentence_practice"),
    path("sentence/<str:course_code>/", views.sentence_practice, name="sentence_by_course"),

    path("speaking/", views.speaking_practice, name="speaking_practice"),
    path("speaking/<str:course_code>/", views.speaking_practice, name="speaking_by_course"),

    path("quiz/", views.quiz_practice, name="quiz_practice"),
    path("quiz/<str:course_code>/", views.quiz_practice, name="quiz_by_course"),

    path("complete/", views.lesson_complete, name="lesson_complete"),
    path("complete/<str:course_code>/", views.lesson_complete, name="lesson_complete_by_course"),

    path("profile-progress/", views.profile_progress, name="profile_progress"),

    path("achievements/", views.achievements_page, name="achievements_page"),
# อันนนี้ อยู่ล่างสุด
    path("<str:course_code>/", views.vocab_card, name="vocab_by_course"),
]