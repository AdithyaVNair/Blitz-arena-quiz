from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

AVATAR_CHOICES = [
    ('fox', 'Cyber Fox'),
    ('knight', 'Pixel Knight'),
    ('owl', 'Neon Owl'),
    ('bear', 'Cosmo Bear'),
    ('bot', 'Turbo Bot'),
]


class SignUpForm(UserCreationForm):
    avatar = forms.ChoiceField(choices=AVATAR_CHOICES, required=False, initial='fox')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'avatar')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'password1' in self.fields:
            self.fields['password1'].help_text = (
                "Password must be at least 8 characters long, contain at least one uppercase letter and one special character."
            )

