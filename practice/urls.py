from django.urls import path

from . import views

app_name = "practice"

urlpatterns = [
    path("", views.hub, name="hub"),
    path("speaking/", views.speaking_picker, name="speaking_picker"),
    path("speaking/<str:course_code>/", views.speaking, name="speaking"),
    path("vocab-mc/", views.vocab_mc_picker, name="vocab_mc_picker"),
    path("vocab-mc/<str:course_code>/", views.vocab_mc, name="vocab_mc"),
    path("complete/<str:mode>/<str:course_code>/", views.complete, name="complete"),

    # Generic engine-driven modes (matching / typing / mc / sentence_builder)
    path("<str:mode>/", views.mode_picker, name="mode_picker"),
    path("<str:mode>/<str:group>/", views.play, name="play"),
]
