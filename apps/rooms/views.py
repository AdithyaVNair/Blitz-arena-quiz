from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.quizzes.models import Quiz
from apps.accounts.models import User
from .models import Room, RoomPlayer
from . import services


@login_required
def create_room_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.questions.count() == 0:
        messages.error(request, "This quiz doesn't have any questions yet! Add questions before hosting.")
        return redirect('quiz_detail', quiz_id=quiz.id)

    room = services.create_room(quiz=quiz, host=request.user, mode='group')
    return redirect('room_play', code=room.code)


@login_required
def join_room_view(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        if not code:
            messages.error(request, 'Please enter a 6-character room code.')
            return render(request, 'rooms/join.html')
            
        try:
            room = Room.objects.get(code=code)
            if room.status == 'finished':
                messages.error(request, 'This game has already finished.')
                return render(request, 'rooms/join.html')
            return redirect('room_play', code=room.code)
        except Room.DoesNotExist:
            messages.error(request, f"Room '{code}' was not found. Please check the code.")
            
    return render(request, 'rooms/join.html')


@login_required
def room_view(request, code):
    room = get_object_or_404(Room.objects.select_related('quiz', 'host'), code=code.upper())
    is_host = (room.host == request.user)
    
    # Ensure player record exists
    RoomPlayer.objects.get_or_create(room=room, user=request.user)

    return render(request, 'rooms/play.html', {
        'room': room,
        'quiz': room.quiz,
        'is_host': is_host,
    })


@login_required
def results_view(request, code):
    room = get_object_or_404(Room.objects.select_related('quiz'), code=code.upper())
    players = room.players.select_related('user').order_by('-score')
    
    return render(request, 'rooms/results.html', {
        'room': room,
        'quiz': room.quiz,
        'players': players,
    })


def leaderboard_view(request):
    top_players = User.objects.order_by('-xp')[:20]
    return render(request, 'rooms/leaderboard.html', {
        'players': top_players,
    })


from django.http import JsonResponse
from . import matchmaking


@login_required
def duel_view(request):
    quizzes = Quiz.objects.filter(questions__isnull=False).distinct()
    return render(request, 'rooms/duel.html', {
        'quizzes': quizzes,
    })


@login_required
def duel_find_ajax(request):
    quiz_id = request.POST.get('quiz_id')
    quiz_id_int = int(quiz_id) if quiz_id and quiz_id.isdigit() else None
    status, code = matchmaking.find_opponent(request.user, quiz_id_int)
    return JsonResponse({'status': status, 'room_code': code})


@login_required
def duel_poll_ajax(request):
    code = matchmaking.check_match_status(request.user)
    if code:
        return JsonResponse({'status': 'matched', 'room_code': code})
    return JsonResponse({'status': 'waiting'})


@login_required
def duel_cancel_ajax(request):
    matchmaking.cancel_matchmaking(request.user)
    return JsonResponse({'status': 'canceled'})


@login_required
def create_duel_challenge_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.questions.count() == 0:
        messages.error(request, "This quiz doesn't have any questions yet!")
        return redirect('quiz_detail', quiz_id=quiz.id)

    room = services.create_room(quiz=quiz, host=request.user, mode='duel')
    return redirect('room_play', code=room.code)
