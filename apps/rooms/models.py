import random
import string
from django.db import models
from django.conf import settings
from apps.quizzes.models import Quiz, Question, Option


def generate_room_code():
    chars = string.ascii_uppercase + string.digits
    # Exclude ambiguous characters if desired, but 6 alphanumeric is standard
    return ''.join(random.choices(chars, k=6))


class Room(models.Model):
    MODE_CHOICES = (
        ('group', 'Group Match'),
        ('duel', '1v1 Duel'),
    )
    STATUS_CHOICES = (
        ('lobby', 'Lobby'),
        ('live', 'Live'),
        ('finished', 'Finished'),
    )

    code = models.CharField(max_length=6, unique=True, default=generate_room_code)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='rooms')
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hosted_rooms')
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='group')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='lobby')
    current_index = models.IntegerField(default=0)  # 0-based question index
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Room {self.code} ({self.quiz.title}) - {self.status}"


class RoomPlayer(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='players')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='room_entries')
    score = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('room', 'user')
        ordering = ['-score', 'joined_at']

    def __str__(self):
        return f"{self.user.username} in {self.room.code} ({self.score} pts)"


class Answer(models.Model):
    player = models.ForeignKey(RoomPlayer, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='player_answers')
    option = models.ForeignKey(Option, on_delete=models.SET_NULL, null=True, blank=True)
    time_taken_ms = models.IntegerField(default=0)
    points_awarded = models.IntegerField(default=0)

    class Meta:
        unique_together = ('player', 'question')

    def __str__(self):
        return f"{self.player.user.username} - Q{self.question.order}: {self.points_awarded} pts"
