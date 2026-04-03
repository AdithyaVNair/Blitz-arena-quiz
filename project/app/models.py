from django.db import models
from django.contrib.auth.models import AbstractUser
import random
import string

def generate_join_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class UserProfile(AbstractUser):
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='app_user_set',
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='app_user_set',
        blank=True,
    )

    avatar = models.CharField(max_length=255, blank=True, null=True, default='avatar1.png')
    total_points = models.IntegerField(default=0)

    def __str__(self):
        return self.username

class Quiz(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    creator = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='created_quizzes')
    join_code = models.CharField(max_length=6, unique=True, default=generate_join_code)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.quiz.title} - Question {self.order}"

class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text} ({'Correct' if self.is_correct else 'Wrong'})"

class QuizAttempt(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.IntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - {self.score}"

