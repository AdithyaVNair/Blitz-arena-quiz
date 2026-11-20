from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    avatar = models.CharField(max_length=50, default='default', blank=True)
    xp = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.username

