from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db import transaction
from .models import Quiz, Question, Option
from .forms import QuizForm, QuestionCreateForm


@login_required
def my_quizzes_view(request):
    quizzes = Quiz.objects.filter(owner=request.user).prefetch_related('questions')
    return render(request, 'quizzes/list.html', {
        'quizzes': quizzes,
        'page_title': 'My Quizzes',
        'is_explore': False,
    })


def explore_view(request):
    topic = request.GET.get('topic')
    query = request.GET.get('q')
    
    quizzes = Quiz.objects.filter(is_public=True).select_related('owner').prefetch_related('questions')
    
    if topic:
        quizzes = quizzes.filter(topic__iexact=topic)
    if query:
        quizzes = quizzes.filter(title__icontains=query)

    topics = Quiz.objects.filter(is_public=True).values_list('topic', flat=True).distinct()

    return render(request, 'quizzes/explore.html', {
        'quizzes': quizzes,
        'topics': set(filter(None, topics)),
        'selected_topic': topic,
        'search_query': query,
    })


@login_required
def create_quiz_view(request):
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.owner = request.user
            quiz.save()
            messages.success(request, f"Quiz '{quiz.title}' created! Now add your first question.")
            return redirect('add_question', quiz_id=quiz.id)
    else:
        form = QuizForm()

    return render(request, 'quizzes/form.html', {
        'form': form,
        'action_title': 'Create New Quiz',
    })


@login_required
def edit_quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.owner != request.user:
        return HttpResponseForbidden("You can only edit your own quizzes.")

    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quiz details updated successfully.')
            return redirect('quiz_detail', quiz_id=quiz.id)
    else:
        form = QuizForm(instance=quiz)

    return render(request, 'quizzes/form.html', {
        'form': form,
        'quiz': quiz,
        'action_title': f"Edit Quiz: {quiz.title}",
    })


@login_required
def delete_quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.owner != request.user:
        return HttpResponseForbidden("You can only delete your own quizzes.")

    if request.method == 'POST':
        title = quiz.title
        quiz.delete()
        messages.success(request, f"Quiz '{title}' was deleted.")
        return redirect('my_quizzes')

    return render(request, 'quizzes/delete_confirm.html', {'quiz': quiz})


def quiz_detail_view(request, quiz_id):
    quiz = get_object_or_404(Quiz.objects.prefetch_related('questions__options'), id=quiz_id)
    is_owner = request.user.is_authenticated and quiz.owner == request.user
    
    return render(request, 'quizzes/detail.html', {
        'quiz': quiz,
        'is_owner': is_owner,
    })


@login_required
def add_question_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.owner != request.user:
        return HttpResponseForbidden("You can only add questions to your own quizzes.")

    if request.method == 'POST':
        form = QuestionCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = quiz.questions.count() + 1
                question = Question.objects.create(
                    quiz=quiz,
                    text=form.cleaned_data['text'],
                    order=order,
                    time_limit=form.cleaned_data['time_limit'],
                    points=form.cleaned_data['points']
                )
                correct_idx = int(form.cleaned_data['correct_option'])
                for i in range(4):
                    opt_text = form.cleaned_data[f'option_{i}']
                    Option.objects.create(
                        question=question,
                        text=opt_text,
                        is_correct=(i == correct_idx)
                    )
            
            if 'save_and_add_another' in request.POST:
                messages.success(request, f"Question {order} added! Add another below.")
                return redirect('add_question', quiz_id=quiz.id)
            else:
                messages.success(request, f"Question {order} saved!")
                return redirect('quiz_detail', quiz_id=quiz.id)
    else:
        form = QuestionCreateForm()

    return render(request, 'quizzes/add_question.html', {
        'quiz': quiz,
        'form': form,
        'current_count': quiz.questions.count(),
    })


@login_required
def delete_question_view(request, quiz_id, question_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    if quiz.owner != request.user:
        return HttpResponseForbidden("You can only delete questions from your own quizzes.")
    
    question = get_object_or_404(Question, id=question_id, quiz=quiz)
    if request.method == 'POST':
        question.delete()
        # reorder questions
        for idx, q in enumerate(quiz.questions.all().order_by('order'), start=1):
            if q.order != idx:
                q.order = idx
                q.save(update_fields=['order'])
        messages.success(request, "Question removed.")
    
    return redirect('quiz_detail', quiz_id=quiz.id)
