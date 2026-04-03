from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('create_quiz/', views.create_quiz, name='create_quiz'),
    path('add_question/<int:quiz_id>/', views.add_question, name='add_question'),
    path('join_quiz/', views.join_quiz, name='join_quiz'),
    path('quiz/<int:quiz_id>/', views.quiz_play, name='quiz_play'),
    path('delete_quiz/<int:quiz_id>/', views.delete_quiz, name='delete_quiz'),
]
