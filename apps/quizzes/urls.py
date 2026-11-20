from django.urls import path
from . import views

urlpatterns = [
    path('', views.my_quizzes_view, name='my_quizzes'),
    path('explore/', views.explore_view, name='explore_quizzes'),
    path('create/', views.create_quiz_view, name='create_quiz'),
    path('<int:quiz_id>/', views.quiz_detail_view, name='quiz_detail'),
    path('<int:quiz_id>/edit/', views.edit_quiz_view, name='edit_quiz'),
    path('<int:quiz_id>/delete/', views.delete_quiz_view, name='delete_quiz'),
    path('<int:quiz_id>/questions/add/', views.add_question_view, name='add_question'),
    path('<int:quiz_id>/questions/<int:question_id>/delete/', views.delete_question_view, name='delete_question'),
]
