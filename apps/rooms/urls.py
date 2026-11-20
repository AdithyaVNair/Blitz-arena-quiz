from django.urls import path
from . import views

urlpatterns = [
    path('join/', views.join_room_view, name='join_room'),
    path('create/<int:quiz_id>/', views.create_room_view, name='create_room'),
    path('duel/', views.duel_view, name='duel_matchmaking'),
    path('duel/find/', views.duel_find_ajax, name='duel_find'),
    path('duel/poll/', views.duel_poll_ajax, name='duel_poll'),
    path('duel/cancel/', views.duel_cancel_ajax, name='duel_cancel'),
    path('duel/challenge/<int:quiz_id>/', views.create_duel_challenge_view, name='create_duel_challenge'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('<str:code>/', views.room_view, name='room_play'),
    path('<str:code>/results/', views.results_view, name='room_results'),
]
