from django.test import TestCase
from apps.accounts.models import User
from apps.quizzes.models import Quiz, Question, Option
from apps.rooms.models import Room, RoomPlayer, Answer
from apps.rooms.services import (
    calculate_score,
    create_room,
    join_room,
    record_answer,
    get_question_payload,
    get_reveal_payload,
    advance_question,
)


class ServicesTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='player1', password='Password123!', avatar='fox')
        self.user2 = User.objects.create_user(username='player2', password='Password123!', avatar='knight')
        
        self.quiz = Quiz.objects.create(owner=self.user1, title='Test Arena', topic='Science')
        self.q1 = Question.objects.create(
            quiz=self.quiz,
            text='What is the chemical symbol for Gold?',
            order=1,
            time_limit=20,
            points=1000
        )
        self.opt_correct = Option.objects.create(question=self.q1, text='Au', is_correct=True)
        self.opt_wrong = Option.objects.create(question=self.q1, text='Ag', is_correct=False)
        Option.objects.create(question=self.q1, text='Fe', is_correct=False)
        Option.objects.create(question=self.q1, text='Pb', is_correct=False)

    def test_calculate_score_formula(self):
        # 1. Instant answer (time_taken = 0) -> 100% of points
        score = calculate_score(points=1000, time_limit_sec=20, time_taken_sec=0.0, is_correct=True)
        self.assertEqual(score, 1000)

        # 2. Halfway answer (time_taken = 10s of 20s) -> 75% of points
        score = calculate_score(points=1000, time_limit_sec=20, time_taken_sec=10.0, is_correct=True)
        self.assertEqual(score, 750)

        # 3. Last second answer (time_taken = 20s of 20s) -> 50% of points
        score = calculate_score(points=1000, time_limit_sec=20, time_taken_sec=20.0, is_correct=True)
        self.assertEqual(score, 500)

        # 4. Wrong answer -> 0 points
        score = calculate_score(points=1000, time_limit_sec=20, time_taken_sec=1.0, is_correct=False)
        self.assertEqual(score, 0)

    def test_room_lifecycle_and_answers(self):
        # Host creates room
        room = create_room(self.quiz, self.user1)
        self.assertEqual(room.players.count(), 1)
        self.assertEqual(room.status, 'lobby')

        # Player 2 joins
        room, p2 = join_room(room.code, self.user2)
        self.assertEqual(room.players.count(), 2)

        # Question payload doesn't leak correct answer
        payload = get_question_payload(room)
        self.assertIsNotNone(payload)
        self.assertEqual(payload['index'], 1)
        self.assertEqual(payload['text'], 'What is the chemical symbol for Gold?')
        self.assertNotIn('is_correct', payload['options'][0])

        # Player 1 answers correctly at 4 seconds (4000ms)
        ans1 = record_answer(room, self.user1, self.q1.id, self.opt_correct.id, 4000)
        # 1000 * (1 - 4/20/2) = 1000 * (1 - 0.1) = 900
        self.assertEqual(ans1.points_awarded, 900)

        # Player 1 tries to answer a second time (should be ignored)
        ans1_second = record_answer(room, self.user1, self.q1.id, self.opt_wrong.id, 5000)
        self.assertEqual(ans1_second.points_awarded, 900)
        self.assertEqual(ans1_second.option, self.opt_correct)

        # Player 2 answers incorrectly
        ans2 = record_answer(room, self.user2, self.q1.id, self.opt_wrong.id, 2000)
        self.assertEqual(ans2.points_awarded, 0)

        # Reveal payload
        reveal = get_reveal_payload(room)
        self.assertEqual(reveal['correct_option_id'], self.opt_correct.id)
        scores_map = {s['name']: s['score'] for s in reveal['scores']}
        self.assertEqual(scores_map['player1'], 900)
        self.assertEqual(scores_map['player2'], 0)

        # Advance room question (only 1 question exists, so room finishes)
        has_more = advance_question(room)
        self.assertFalse(has_more)
        room.refresh_from_db()
        self.assertEqual(room.status, 'finished')
