from django.urls import path

from .views import AIPingView


urlpatterns = [
    path('ai/ping/', AIPingView.as_view(), name='ai-ping'),
]
