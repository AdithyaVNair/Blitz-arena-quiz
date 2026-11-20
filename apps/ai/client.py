import json
import re
import os
from django.conf import settings
from .prompts import SYSTEM_PROMPT


def validate_quiz_json(data: dict) -> bool:
    """Validates the structure, options count (4), and correct_index (0-3)."""
    if not isinstance(data, dict):
        return False
    if not data.get('title') or not data.get('topic') or not isinstance(data.get('questions'), list):
        return False
    if len(data['questions']) == 0:
        return False

    for q in data['questions']:
        if not isinstance(q, dict):
            return False
        if not q.get('text') or not isinstance(q.get('options'), list):
            return False
        if len(q['options']) != 4:
            return False
        if any(not isinstance(opt, str) or not opt.strip() for opt in q['options']):
            return False
        correct_idx = q.get('correct_index')
        if not isinstance(correct_idx, int) or correct_idx not in range(4):
            return False

    return True


def clean_json_text(text: str) -> str:
    """Strips markdown code fences if model accidentally wrapped output."""
    text = text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
    return text.strip()


def _call_gemini(user_content: str) -> str:
    from google import genai
    api_key = settings.GEMINI_API_KEY or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment or .env")
    
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=f"{SYSTEM_PROMPT}\n\nTask:\n{user_content}",
    )
    return response.text


def _call_claude(user_content: str) -> str:
    import anthropic
    api_key = settings.ANTHROPIC_API_KEY or os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set in environment or .env")
    
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}]
    )
    return message.content[0].text


def generate_quiz(prompt: str, n: int = 5, difficulty: str = 'medium') -> dict:
    """
    Exposes ONE function: generate_quiz(prompt, n, difficulty) -> dict.
    Provider chosen by env var AI_PROVIDER (claude or gemini).
    Validates: exactly 4 options, correct_index in range, no empty text.
    On invalid JSON retries once, then raises friendly ValueError.
    """
    n = max(5, min(20, int(n)))
    provider = getattr(settings, 'AI_PROVIDER', 'gemini').lower()

    user_query = f"Create a quiz with {n} questions on topic: '{prompt}'. Difficulty level: {difficulty}."

    last_error = None
    for attempt in range(2):  # Try once, retry once on error
        try:
            if provider == 'claude':
                raw_text = _call_claude(user_query)
            else:
                raw_text = _call_gemini(user_query)

            clean_text = clean_json_text(raw_text)
            data = json.loads(clean_text)

            if validate_quiz_json(data):
                # Ensure exactly n questions if more were returned
                data['questions'] = data['questions'][:n]
                return data
            else:
                last_error = "Generated content did not match quiz requirements (4 options, valid answer index)."
        except json.JSONDecodeError as e:
            last_error = f"AI returned invalid JSON: {str(e)}"
        except Exception as e:
            last_error = str(e)

    raise ValueError(f"Could not generate quiz: {last_error}")
