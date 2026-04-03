from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = UserProfile
        fields = ('username', 'email')
