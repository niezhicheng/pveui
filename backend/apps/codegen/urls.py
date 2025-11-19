from django.urls import path
from .views import GenerateFromSpecView, AISchemaSuggestView

urlpatterns = [
    path('generate/', GenerateFromSpecView.as_view()),
    path('ai-schema/', AISchemaSuggestView.as_view()),
]


