from django.db import transaction
from django.utils import timezone
from .models import Room, RoomPlayer, Answer
from apps.quizzes.models import Question, Option


def calculate_score(points: int, time_limit_sec: int, time_taken_sec: float, is_correct: bool) -> int:
    """
    Scoring rule per Blueprint:
    Wrong or no answer = 0.
    Correct = points * (1 - time_taken / time_limit / 2)
    Instant answer gets full points, last-second answer gets half points.
    """
    if not is_correct:
        return 0
    if time_limit_sec <= 0:
        return points
    
    # Clamp time taken to range [0, time_limit_sec]
    clamped_time = max(0.0, min(float(time_limit_sec), float(time_taken_sec)))
    ratio = clamped_time / float(time_limit_sec)
    multiplier = 1.0 - (ratio / 2.0)
    return int(round(points * multiplier))


def create_room(quiz, host, mode='group') -> Room:
    """Create a new game room."""
    room = Room.objects.create(
        quiz=quiz,
        host=host,
        mode=mode,
        status='lobby',
        current_index=0
    )
    # Host automatically joins as a player
    RoomPlayer.objects.create(room=room, user=host, score=0)
    return room


def join_room(room_code: str, user) -> tuple[Room, RoomPlayer]:
    """Join an existing room by 6-char code."""
    room = Room.objects.select_related('quiz', 'host').get(code=room_code.upper().strip())
    player, _ = RoomPlayer.objects.get_or_create(room=room, user=user)
    return room, player


def record_answer(room: Room, user, question_id: int, option_id: int, time_taken_ms: int) -> Answer:
    """
    Records a player's answer.
    Ignores second answers from the same player for the same question.
    """
    player = RoomPlayer.objects.get(room=room, user=user)
    question = Question.objects.get(id=question_id, quiz=room.quiz)

    # Check if already answered
    existing = Answer.objects.filter(player=player, question=question).first()
    if existing:
        return existing

    option = Option.objects.filter(id=option_id, question=question).first() if option_id else None
    is_correct = bool(option and option.is_correct)
    
    time_taken_sec = max(0.0, time_taken_ms / 1000.0)
    points = calculate_score(question.points, question.time_limit, time_taken_sec, is_correct)

    with transaction.atomic():
        answer = Answer.objects.create(
            player=player,
            question=question,
            option=option,
            time_taken_ms=time_taken_ms,
            points_awarded=points
        )
        if points > 0:
            player.score += points
            player.save(update_fields=['score'])
            # Also award XP to the user account
            user.xp += points
            user.save(update_fields=['xp'])

    return answer


def get_current_question(room: Room) -> Question | None:
    """Returns the question at room.current_index."""
    questions = list(room.quiz.questions.all().order_by('order', 'id'))
    if 0 <= room.current_index < len(questions):
        return questions[room.current_index]
    return None


def get_question_payload(room: Room) -> dict | None:
    """
    Protocol: question {index, total, text, options:[{id,text}], time_limit}
    Never includes the correct answer!
    """
    questions = list(room.quiz.questions.all().order_by('order', 'id'))
    total = len(questions)
    if not (0 <= room.current_index < total):
        return None

    q = questions[room.current_index]
    options_payload = [{'id': opt.id, 'text': opt.text} for opt in q.options.all().order_by('id')]

    return {
        'index': room.current_index + 1,
        'total': total,
        'text': q.text,
        'options': options_payload,
        'time_limit': q.time_limit,
    }


def get_reveal_payload(room: Room) -> dict:
    """
    Protocol: reveal {correct_option_id, scores:[{name, avatar, score, delta}]}
    """
    q = get_current_question(room)
    correct_opt = q.options.filter(is_correct=True).first() if q else None
    correct_opt_id = correct_opt.id if correct_opt else None

    # Get players and delta points for this question
    scores = []
    players = room.players.select_related('user').order_by('-score')
    for p in players:
        ans = Answer.objects.filter(player=p, question=q).first() if q else None
        delta = ans.points_awarded if ans else 0
        scores.append({
            'name': p.user.username,
            'avatar': p.user.avatar,
            'score': p.score,
            'delta': delta,
        })

    return {
        'correct_option_id': correct_opt_id,
        'scores': scores,
    }


def get_finished_payload(room: Room) -> dict:
    """
    Protocol: finished {scores:[{name, avatar, score}]}
    """
    players = room.players.select_related('user').order_by('-score')
    scores = [{
        'name': p.user.username,
        'avatar': p.user.avatar,
        'score': p.score,
    } for p in players]

    return {'scores': scores}


def advance_question(room: Room) -> bool:
    """Advances current_index. If no more questions, marks room as finished."""
    total = room.quiz.questions.count()
    room.current_index += 1
    if room.current_index >= total:
        room.status = 'finished'
        room.save(update_fields=['status', 'current_index'])
        return False
    else:
        room.save(update_fields=['current_index'])
        return True
