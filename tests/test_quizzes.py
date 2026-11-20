from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import User
from apps.quizzes.models import Quiz, Question, Option


class QuizzesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            username='quizmaster',
            email='master@blitz.com',
            password='Password123!',
            avatar='fox'
        )
        self.other_user = User.objects.create_user(
            username='stranger',
            email='stranger@blitz.com',
            password='Password123!',
            avatar='bot'
        )
        self.quiz = Quiz.objects.create(
            owner=self.owner,
            title='Retro Arcade Classics',
            topic='Gaming',
            is_public=True
        )
        self.question = Question.objects.create(
            quiz=self.quiz,
            text='Who is Mario’s arch-nemesis?',
            order=1,
            time_limit=20,
            points=1000
        )
        Option.objects.create(question=self.question, text='Bowser', is_correct=True)
        Option.objects.create(question=self.question, text='Luigi', is_correct=False)
        Option.objects.create(question=self.question, text='Toad', is_correct=False)
        Option.objects.create(question=self.question, text='Yoshi', is_correct=False)

    def test_quiz_model_and_relations(self):
        self.assertEqual(self.quiz.questions.count(), 1)
        self.assertEqual(self.question.options.count(), 4)
        correct_opts = self.question.options.filter(is_correct=True)
        self.assertEqual(correct_opts.count(), 1)
        self.assertEqual(correct_opts.first().text, 'Bowser')

    def test_explore_page_shows_public_quiz(self):
        response = self.client.get(reverse('explore_quizzes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Retro Arcade Classics')

    def test_my_quizzes_requires_login(self):
        response = self.client.get(reverse('my_quizzes'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('my_quizzes')}")

    def test_my_quizzes_lists_only_owned(self):
        self.client.login(username='quizmaster', password='Password123!')
        response = self.client.get(reverse('my_quizzes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Retro Arcade Classics')

        # Other user has none
        self.client.login(username='stranger', password='Password123!')
        response = self.client.get(reverse('my_quizzes'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Retro Arcade Classics')

    def test_owner_can_edit_and_delete(self):
        self.client.login(username='quizmaster', password='Password123!')
        
        # Edit
        response = self.client.post(reverse('edit_quiz', args=[self.quiz.id]), {
            'title': 'Updated Title',
            'topic': 'Gaming',
            'is_public': True
        })
        self.assertRedirects(response, reverse('quiz_detail', args=[self.quiz.id]))
        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.title, 'Updated Title')

        # Non-owner cannot delete
        self.client.login(username='stranger', password='Password123!')
        response = self.client.post(reverse('delete_quiz', args=[self.quiz.id]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Quiz.objects.filter(id=self.quiz.id).exists())

        # Owner can delete
        self.client.login(username='quizmaster', password='Password123!')
        response = self.client.post(reverse('delete_quiz', args=[self.quiz.id]))
        self.assertRedirects(response, reverse('my_quizzes'))
        self.assertFalse(Quiz.objects.filter(id=self.quiz.id).exists())

    def test_add_question_formset(self):
        self.client.login(username='quizmaster', password='Password123!')
        response = self.client.post(reverse('add_question', args=[self.quiz.id]), {
            'text': 'What year was Pac-Man released?',
            'time_limit': 15,
            'points': 1000,
            'option_0': '1980',
            'option_1': '1985',
            'option_2': '1977',
            'option_3': '1990',
            'correct_option': '0',
            'save_and_finish': '1'
        })
        self.assertRedirects(response, reverse('quiz_detail', args=[self.quiz.id]))
        self.assertEqual(self.quiz.questions.count(), 2)
        new_q = self.quiz.questions.get(order=2)
        self.assertEqual(new_q.options.filter(is_correct=True).first().text, '1980')
