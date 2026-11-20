from django import forms
from .models import Quiz, Question, Option


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'topic', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g. 90s Retro Gaming Trivia'}),
            'topic': forms.TextInput(attrs={'placeholder': 'e.g. Gaming, Science, Cinema'}),
            'is_public': forms.CheckboxInput(),
        }


class QuestionCreateForm(forms.Form):
    text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Enter your question text here...'}),
        label="Question Text"
    )
    time_limit = forms.IntegerField(
        initial=20,
        min_value=5,
        max_value=120,
        label="Time Limit (seconds)"
    )
    points = forms.IntegerField(
        initial=1000,
        min_value=100,
        max_value=5000,
        label="Base Points"
    )
    option_0 = forms.CharField(label="Option A (Blue)", max_length=255)
    option_1 = forms.CharField(label="Option B (Orange)", max_length=255)
    option_2 = forms.CharField(label="Option C (Green)", max_length=255)
    option_3 = forms.CharField(label="Option D (Violet)", max_length=255)
    correct_option = forms.ChoiceField(
        choices=[(0, 'Option A'), (1, 'Option B'), (2, 'Option C'), (3, 'Option D')],
        widget=forms.RadioSelect,
        initial=0,
        label="Correct Answer"
    )
