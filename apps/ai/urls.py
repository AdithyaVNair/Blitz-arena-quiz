from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.generate_view, name='ai_generate'),
    path('preview/', views.preview_view, name='ai_preview'),
]
