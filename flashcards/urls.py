from django.urls import path

from . import views

app_name = "flashcards"

urlpatterns = [
    path("", views.home, name="home"),
    path("review/", views.submit_review, name="submit_review"),
    path("<str:category>/", views.deck_list, name="deck_list"),
    path("<str:category>/<str:group>/study/", views.study_session, name="study_session"),
]
