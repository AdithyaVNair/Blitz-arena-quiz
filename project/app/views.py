from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
import json
from .models import Quiz, QuizAttempt, Question, Option

def dashboard(request):
    recent_attempts = QuizAttempt.objects.all().order_by('-completed_at')[:10]
    all_quizzes = Quiz.objects.all().order_by('-created_at')
    return render(request, 'app/dashboard.html', {
        'recent_attempts': recent_attempts,
        'all_quizzes': all_quizzes
    })

def create_quiz(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        if title:
            quiz = Quiz.objects.create(title=title, description=description)
            return redirect('add_question', quiz_id=quiz.id)
    return render(request, 'app/create_quiz.html')

def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
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

def delete_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.method == 'POST':
        quiz.delete()
    return redirect('dashboard')

def join_quiz(request):
    if request.method == 'POST':
        join_code = request.POST.get('join_code')
        try:
            quiz = Quiz.objects.get(join_code=join_code)
            return redirect('quiz_play', quiz_id=quiz.id)
        except Quiz.DoesNotExist:
            return render(request, 'app/join_quiz.html', {'error': 'Invalid code!'})
    return render(request, 'app/join_quiz.html')

def quiz_play(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if request.method == 'POST':
        score = 0
        player_name = request.POST.get('player_name', 'Anonymous')
        if not player_name.strip():
            player_name = 'Anonymous'
            
        for question in quiz.questions.all():
            selected_option_id = request.POST.get(f'question_{question.id}')
            if selected_option_id:
                try:
                    option = Option.objects.get(id=selected_option_id, question=question)
                    if option.is_correct:
                        score += 10 # 10 points per question
                except Option.DoesNotExist:
                    pass
        QuizAttempt.objects.create(player_name=player_name, quiz=quiz, score=score)
        return redirect('dashboard')
    
    return render(request, 'app/quiz_play.html', {'quiz': quiz})
