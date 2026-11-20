import time
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.db import transaction
from apps.quizzes.models import Quiz, Question, Option
from . import client


def check_rate_limit(user_id: int) -> bool:
    """Rate-limit: max 5 generations per user per hour."""
    key = f"ai_rate_{user_id}"
    history = cache.get(key, [])
    now = time.time()
    one_hour_ago = now - 3600
    # Keep only timestamps within the last hour
    history = [t for t in history if t > one_hour_ago]

    if len(history) >= 5:
        return False

    history.append(now)
    cache.set(key, history, 3600)
    return True


@login_required
def generate_view(request):
    if request.method == 'POST':
        prompt = request.POST.get('prompt', '').strip()
        count = request.POST.get('count', '5')
        difficulty = request.POST.get('difficulty', 'medium')

        if not prompt:
            messages.error(request, 'Please enter a prompt describing your quiz topic.')
            return render(request, 'ai/generate.html')

        if not check_rate_limit(request.user.id):
            messages.error(request, 'Rate limit reached: Maximum 5 AI generations per hour. Please wait a bit.')
            return render(request, 'ai/generate.html')

        try:
            n = int(count)
        except ValueError:
            n = 5

        try:
            quiz_data = client.generate_quiz(prompt=prompt, n=n, difficulty=difficulty)
            request.session['ai_quiz_preview'] = quiz_data
            messages.success(request, f"Generated '{quiz_data['title']}' with {len(quiz_data['questions'])} questions! Review and edit below.")
            return redirect('ai_preview')
        except Exception as e:
            messages.error(request, f"AI Generation Notice: {str(e)}")
            return render(request, 'ai/generate.html', {
                'initial_prompt': prompt,
                'initial_count': count,
                'initial_difficulty': difficulty,
            })

    return render(request, 'ai/generate.html')


@login_required
def preview_view(request):
    quiz_data = request.session.get('ai_quiz_preview')
    if not quiz_data:
        messages.info(request, 'No quiz preview found. Please generate one first.')
        return redirect('ai_generate')

    if request.method == 'POST':
        if 'save_quiz' in request.POST:
            # User confirmed save: persist to DB
            title = request.POST.get('title', quiz_data.get('title', 'AI Quiz')).strip()
            topic = request.POST.get('topic', quiz_data.get('topic', 'General')).strip()

            with transaction.atomic():
                quiz = Quiz.objects.create(
                    owner=request.user,
                    title=title,
                    topic=topic,
                    is_public=True,
                    created_by_ai=True
                )

                for idx, q_data in enumerate(quiz_data.get('questions', []), start=1):
                    q_text = request.POST.get(f'q_{idx}_text', q_data.get('text')).strip()
                    correct_idx = int(request.POST.get(f'q_{idx}_correct', q_data.get('correct_index', 0)))

                    question = Question.objects.create(
                        quiz=quiz,
                        text=q_text,
                        order=idx,
                        time_limit=20,
                        points=1000
                    )

                    for opt_idx, opt_text in enumerate(q_data.get('options', [])):
                        edited_opt = request.POST.get(f'q_{idx}_opt_{opt_idx}', opt_text).strip()
                        Option.objects.create(
                            question=question,
                            text=edited_opt,
                            is_correct=(opt_idx == correct_idx)
                        )

            # Clear session preview
            del request.session['ai_quiz_preview']
            messages.success(request, f"Quiz '{quiz.title}' saved to your collection!")
            return redirect('quiz_detail', quiz_id=quiz.id)

        elif 'discard_quiz' in request.POST:
            del request.session['ai_quiz_preview']
            messages.info(request, 'AI Quiz preview discarded.')
            return redirect('ai_generate')

    return render(request, 'ai/preview.html', {
        'quiz': quiz_data,
    })
