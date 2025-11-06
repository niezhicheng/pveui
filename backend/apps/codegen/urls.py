from django.urls import path
from .views import GenerateFromSpecView

urlpatterns = [
    path('generate/', GenerateFromSpecView.as_view()),
]


