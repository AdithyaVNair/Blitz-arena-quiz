from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import CustomUserCreationForm
from django.http import JsonResponse
import json
from .models import Quiz, QuizAttempt, UserProfile, Question, Option

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'app/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'app/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    recent_attempts = QuizAttempt.objects.filter(user=request.user).order_by('-completed_at')[:5]
    top_users = UserProfile.objects.order_by('-total_points')[:10]
    user_quizzes = Quiz.objects.filter(creator=request.user).order_by('-created_at')
    return render(request, 'app/dashboard.html', {
        'recent_attempts': recent_attempts,
        'top_users': top_users,
        'user_quizzes': user_quizzes
    })

@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    quizzes = Quiz.objects.all().order_by('-created_at')
    users = UserProfile.objects.all().order_by('-date_joined')
    return render(request, 'app/admin_dashboard.html', {
        'quizzes': quizzes,
        'users': users
    })

@login_required
def create_quiz(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        if title:
            quiz = Quiz.objects.create(title=title, description=description, creator=request.user)
            return redirect('add_question', quiz_id=quiz.id)
    return render(request, 'app/create_quiz.html')

@login_required
def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, creator=request.user)
    if request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                text = data.get('question_text')
                if text:
                    question = Question.objects.create(quiz=quiz, text=text, order=quiz.questions.count() + 1)
                    for i in range(1, 5):
                        opt_text = data.get(f'option_{i}')
                        is_correct = str(i) == str(data.get('correct_option'))
                        if opt_text:
                            Option.objects.create(question=question, text=opt_text, is_correct=is_correct)
                    return JsonResponse({"status": "success", "question_count": quiz.questions.count()})
                return JsonResponse({"status": "error", "message": "Question text is required"}, status=400)
            except json.JSONDecodeError:
                return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
        else:
            # Fallback for standard form submission
            text = request.POST.get('question_text')
            if text:
                question = Question.objects.create(quiz=quiz, text=text, order=quiz.questions.count() + 1)
                for i in range(1, 5):
                    opt_text = request.POST.get(f'option_{i}')
                    is_correct = str(i) == str(request.POST.get('correct_option'))
                    if opt_text:
                        Option.objects.create(question=question, text=opt_text, is_correct=is_correct)
                return redirect('add_question', quiz_id=quiz.id)
    return render(request, 'app/add_question.html', {'quiz': quiz})

@login_required
def delete_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, creator=request.user)
    if request.method == 'POST':
        quiz.delete()
    return redirect('dashboard')

@login_required
def join_quiz(request):
    if request.method == 'POST':
        join_code = request.POST.get('join_code')
        try:
            quiz = Quiz.objects.get(join_code=join_code)
            return redirect('quiz_play', quiz_id=quiz.id)
        except Quiz.DoesNotExist:
            return render(request, 'app/join_quiz.html', {'error': 'Invalid code!'})
    return render(request, 'app/join_quiz.html')

@login_required
def quiz_play(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.method == 'POST':
        score = 0
        for question in quiz.questions.all():
            selected_option_id = request.POST.get(f'question_{question.id}')
            if selected_option_id:
                try:
                    option = Option.objects.get(id=selected_option_id, question=question)
                    if option.is_correct:
                        score += 10 # 10 points per question
                except Option.DoesNotExist:
                    pass
        QuizAttempt.objects.create(user=request.user, quiz=quiz, score=score)
        request.user.total_points += score
        request.user.save()
        return redirect('dashboard')
    
    return render(request, 'app/quiz_play.html', {'quiz': quiz})
