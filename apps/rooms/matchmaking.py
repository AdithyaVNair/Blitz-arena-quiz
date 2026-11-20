import json
import threading
from django.conf import settings
from apps.quizzes.models import Quiz
from apps.accounts.models import User
from .models import Room, RoomPlayer
from . import services

# In-memory matchmaking queue fallback for development / without Redis
_queue_lock = threading.Lock()
_memory_queue = []
_matched_rooms = {}  # user_id -> room_code


def find_opponent(user: User, quiz_id: int = None) -> tuple[str | None, str | None]:
    """
    Finds an opponent in queue or adds user to queue.
    Returns (status, room_code):
    - ('matched', room_code) if matched with another player
    - ('waiting', None) if placed in queue
    """
    user_id = user.id

    with _queue_lock:
        # Check if already matched
        if user_id in _matched_rooms:
            code = _matched_rooms.pop(user_id)
            return 'matched', code

        # Remove stale entries for this user
        _memory_queue[:] = [entry for entry in _memory_queue if entry['user_id'] != user_id]

        if len(_memory_queue) > 0:
            # Match with first waiting player!
            opponent_entry = _memory_queue.pop(0)
            opponent_user = User.objects.get(id=opponent_entry['user_id'])
            
            # Select quiz: entry quiz or first public quiz with questions
            quiz = None
            if quiz_id:
                quiz = Quiz.objects.filter(id=quiz_id, questions__isnull=False).distinct().first()
            if not quiz and opponent_entry.get('quiz_id'):
                quiz = Quiz.objects.filter(id=opponent_entry['quiz_id'], questions__isnull=False).distinct().first()
            if not quiz:
                quiz = Quiz.objects.filter(questions__isnull=False).distinct().first()

            if not quiz:
                return 'error', None

            # Create duel room
            room = Room.objects.create(
                quiz=quiz,
                host=opponent_user,
                mode='duel',
                status='lobby',
                current_index=0
            )
            RoomPlayer.objects.create(room=room, user=opponent_user)
            RoomPlayer.objects.create(room=room, user=user)

            # Store match notification for opponent
            _matched_rooms[opponent_user.id] = room.code
            return 'matched', room.code
        else:
            # Add to queue
            _memory_queue.append({'user_id': user_id, 'quiz_id': quiz_id})
            return 'waiting', None


def check_match_status(user: User) -> str | None:
    """Checks if the waiting user has been matched."""
    with _queue_lock:
        if user.id in _matched_rooms:
            return _matched_rooms.pop(user.id)
    return None


def cancel_matchmaking(user: User):
    """Removes the user from queue."""
    with _queue_lock:
        _memory_queue[:] = [entry for entry in _memory_queue if entry['user_id'] != user.id]
        _matched_rooms.pop(user.id, None)
