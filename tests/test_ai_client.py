import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import User
from apps.ai.client import generate_quiz, validate_quiz_json
from apps.ai.views import check_rate_limit


SAMPLE_VALID_QUIZ = {
    "title": "Retro Arcade Classics",
    "topic": "Video Games",
    "questions": [
        {
            "text": "Which company released Space Invaders in 1978?",
            "options": ["Taito", "Nintendo", "Atari", "Namco"],
            "correct_index": 0
        },
        {
            "text": "What was Mario’s original name in Donkey Kong?",
            "options": ["Jumpman", "Plumber", "Red Hat", "Luigi"],
            "correct_index": 0
        },
        {
            "text": "Which arcade cabinet had the famous 'kill screen' at level 256?",
            "options": ["Pac-Man", "Galaga", "Asteroids", "Frogger"],
            "correct_index": 0
        },
        {
            "text": "What color is the ghost 'Blinky' in Pac-Man?",
            "options": ["Red", "Pink", "Cyan", "Orange"],
            "correct_index": 0
        },
        {
            "text": "Which game featured vector wireframe graphics of space rocks?",
            "options": ["Asteroids", "Centipede", "Defender", "Tempest"],
            "correct_index": 0
        }
    ]
}


class AIClientTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='aitester', password='Password123!', avatar='bot')
        self.client = Client()

    def test_json_validation_passes(self):
        self.assertTrue(validate_quiz_json(SAMPLE_VALID_QUIZ))

    def test_json_validation_fails_on_missing_options(self):
        invalid_quiz = {
            "title": "Broken Quiz",
            "topic": "General",
            "questions": [
                {"text": "Only 3 options?", "options": ["A", "B", "C"], "correct_index": 0}
            ]
        }
        self.assertFalse(validate_quiz_json(invalid_quiz))

    def test_json_validation_fails_on_out_of_bounds_index(self):
        invalid_quiz = {
            "title": "Broken Quiz",
            "topic": "General",
            "questions": [
                {"text": "Bad index?", "options": ["A", "B", "C", "D"], "correct_index": 5}
            ]
        }
        self.assertFalse(validate_quiz_json(invalid_quiz))

    @patch('apps.ai.client._call_gemini')
    def test_generate_quiz_success_mock(self, mock_gemini):
        mock_gemini.return_value = json.dumps(SAMPLE_VALID_QUIZ)
        result = generate_quiz("arcade games", n=5, difficulty="medium")
        self.assertEqual(result['title'], "Retro Arcade Classics")
        self.assertEqual(len(result['questions']), 5)
        self.assertEqual(result['questions'][0]['options'][0], "Taito")

    @patch('apps.ai.client._call_gemini')
    def test_generate_quiz_retry_on_invalid_json(self, mock_gemini):
        # 1st call returns bad json, 2nd call returns valid json
        mock_gemini.side_effect = [
            "This is not json at all",
            json.dumps(SAMPLE_VALID_QUIZ)
        ]
        result = generate_quiz("arcade games", n=5)
        self.assertEqual(result['title'], "Retro Arcade Classics")
        self.assertEqual(mock_gemini.call_count, 2)

    def test_rate_limit(self):
        # Check that 5 calls pass, 6th call fails
        for _ in range(5):
            self.assertTrue(check_rate_limit(self.user.id))
        self.assertFalse(check_rate_limit(self.user.id))
