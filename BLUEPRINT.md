# Blitz Arena v2 — Blueprint

Put this file in the project root. Tell Antigravity: "Read BLUEPRINT.md fully. Follow it exactly. Do one phase at a time and stop after each phase so I can test."

## 0. Rules for the agent (read first)
- Keep it simple. No extra libraries, no extra abstractions, no unused files.
- Python 3.12+, Django 5.x, MySQL 8, Django Channels + Redis for WebSockets.
- Server-rendered templates + vanilla JS. NO React, NO DRF, NO JWT, NO CORS package.
- All secrets from `.env` (django-environ). Never hard-code keys.
- Views stay thin. Game logic lives in `services.py`.
- No inline `style=""` in templates. All colours come from `static/css/tokens.css`.
- Every phase must run (`python manage.py runserver` / `daphne`) before moving on.
- Short comments only where the logic is not obvious.

---

## 1. Cleanup — delete from the old project

| Delete | Why |
|---|---|
| `db.sqlite3` | DB should never be in the repo |
| all `__pycache__/` and `*.pyc` | generated files |
| `vercel.json`, `build.sh` | Vercel cannot hold WebSockets; we deploy elsewhere |
| `api_views.py`, `api_urls.py`, `serializers.py` | API was broken and is not needed |
| `djangorestframework`, `simplejwt`, `django-cors-headers`, `django-filter`, `dj-database-url`, `psycopg2-binary` | unused after the above |
| `admin_dashboard.html` | never routed |
| `QuizAttempt` model | replaced by RoomPlayer + Answer |
| the glass / gradient / glow CSS in `styles.css` | replaced by new design |
| hard-coded `SECRET_KEY`, `DEBUG=True`, `ALLOWED_HOSTS=['*']` | move to `.env` |

Keep (rewrite cleanly): the idea of Quiz -> Question -> Option, the join-code idea, the Django admin.

---

## 2. Final file structure

```
blitz-arena/
├── manage.py
├── .env.example
├── .gitignore
├── requirements.txt
├── docker-compose.yml       # MySQL + Redis only
├── README.md
│
├── config/
│   ├── settings/
│   │   ├── base.py          # shared settings
│   │   ├── dev.py           # DEBUG on
│   │   └── prod.py          # DEBUG off, secure cookies
│   ├── urls.py
│   ├── asgi.py              # HTTP + WebSocket router
│   └── wsgi.py
│
├── apps/
│   ├── accounts/            # users
│   │   ├── models.py        # User (avatar, xp)
│   │   ├── forms.py         # signup form
│   │   ├── views.py         # signup, login, logout, profile
│   │   └── urls.py
│   │
│   ├── quizzes/             # quiz content
│   │   ├── models.py        # Quiz, Question, Option
│   │   ├── forms.py         # quiz form + question formset
│   │   ├── views.py         # list, create, edit, delete, explore
│   │   ├── urls.py
│   │   └── admin.py
│   │
│   ├── rooms/               # live play (group rooms AND 1v1 duels)
│   │   ├── models.py        # Room, RoomPlayer, Answer
│   │   ├── services.py      # scoring + round flow (plain Python, testable)
│   │   ├── consumers.py     # WebSocket consumer (calls services.py)
│   │   ├── matchmaking.py   # 1v1 queue using Redis
│   │   ├── routing.py       # ws:// URL patterns
│   │   ├── views.py         # create room, join room, results, leaderboard
│   │   └── urls.py
│   │
│   └── ai/                  # prompt -> quiz
│       ├── client.py        # ONLY file that calls the LLM
│       ├── prompts.py       # system prompt + JSON schema
│       ├── views.py         # prompt form, preview, save
│       └── urls.py
│
├── templates/
│   ├── base.html
│   ├── components/          # navbar, loader, toast, quiz_card
│   ├── accounts/            # login, signup, profile
│   ├── quizzes/             # list, form, explore
│   ├── rooms/               # join, lobby, play, results, leaderboard
│   └── ai/                  # generate, preview
│
├── static/
│   ├── css/
│   │   ├── tokens.css       # colours, fonts, spacing (ONLY place for colours)
│   │   ├── base.css         # reset, typography, layout
│   │   ├── components.css   # buttons, cards, inputs, loaders
│   │   └── play.css         # quiz-play screen
│   ├── js/
│   │   ├── ws.js            # WebSocket connect + auto-reconnect
│   │   ├── room.js          # lobby + game UI
│   │   ├── duel.js          # matchmaking UI
│   │   ├── ai.js            # AI form + skeleton loading
│   │   └── loader.js        # button spinner helper
│   └── img/
│
└── tests/
    ├── test_services.py     # scoring logic
    ├── test_quizzes.py
    └── test_ai_client.py     # LLM mocked
```

### Walkthrough — what each part does
- `config/` — project wiring only. `asgi.py` sends normal web requests to Django and `ws://` requests to Channels. Settings are split so dev and prod never mix.
- `accounts/` — who you are. Custom User with `avatar` and `xp`. Needed so quizzes have owners and leaderboards have names. Must be created before the first migration.
- `quizzes/` — the content. A Quiz has many Questions, each has 4 Options (one correct). Owners can edit and delete only their own quizzes. `is_public` controls the Explore page.
- `rooms/` — the game. A Room has a 6-char code, a quiz, a host and a status (`lobby` -> `live` -> `finished`) and a mode (`group` or `duel`). Players connect over WebSocket. `services.py` decides scores; `consumers.py` only passes messages in and out.
- `rooms/matchmaking.py` — 1v1. "Find opponent" puts you in a Redis list. When two players are waiting, a `Room(mode="duel")` is created and both are sent to it. Same game engine as group rooms.
- `ai/` — the quiz generator. User types a prompt, `client.py` asks the LLM for JSON, validates it, shows an editable preview, then saves it as a normal Quiz.
- `templates/` — plain Django templates, one base layout, small reusable components.
- `static/css/` — four small files. Changing the whole theme = editing `tokens.css`.
- `tests/` — scoring and AI-parse tests. Easy wins for interviews.

---

## 3. Data models

```python
User(AbstractUser): avatar, xp
Quiz: owner(FK User), title, topic, is_public, created_by_ai, created_at
Question: quiz(FK), text, order, time_limit(sec, default 20), points(default 1000)
Option: question(FK), text, is_correct
Room: code(6, unique), quiz(FK), host(FK User), mode(group|duel), status(lobby|live|finished), current_index, created_at
RoomPlayer: room(FK), user(FK), score, joined_at, unique(room, user)
Answer: player(FK RoomPlayer), question(FK), option(FK, null), time_taken_ms, points_awarded, unique(player, question)
```

### Scoring (in `services.py`):
Wrong or no answer = 0.
Correct = `points * (1 - time_taken / time_limit / 2)`, so a correct instant answer gets full points and a correct last-second answer gets half.

---

## 4. WebSocket protocol (rooms + duels)

**URL**: `ws://<host>/ws/room/<CODE>/`

**Server -> client**:
- `lobby_state {players:[{name,avatar}], host:bool}`
- `question {index,total,text,options:[{id,text}],time_limit}` (never includes the correct answer)
- `reveal {correct_option_id, scores:[{name,score,delta}]}`
- `finished {scores:[...]}`

**Client -> server**:
- `start` (host only)
- `answer {option_id}`

Rules: the server owns the timer. Ignore a second answer from the same player. On reconnect, send the current state again. In a duel, auto-start as soon as both players are connected.

---

## 5. Design system

No gradients, no glass, no glow, no neon. Flat colour, hard borders, offset shadows.

```css
:root {
  --bg: #F4EFE6;         /* warm cream */
  --surface: #FFFFFF;
  --ink: #1B1B1F;        /* text + borders */
  --muted: #6B6860;
  --accent: #FF4D2E;     /* tomato: primary buttons */
  --accent-2: #FFD23F;   /* yellow: highlights */
  --good: #2E9E5B;
  --bad: #D93636;

  /* four answer colours */
  --opt-a: #4F7CFF; --opt-b: #FF8A3D; --opt-c: #2EB67D; --opt-d: #B05CFF;

  --border: 2px solid var(--ink);
  --shadow: 4px 4px 0 var(--ink);
  --radius: 8px;
  --font-head: 'Space Grotesk', sans-serif;
  --font-body: 'DM Sans', sans-serif;
}
```

Buttons: solid fill, `border: var(--border)`, `box-shadow: var(--shadow)`, on hover move 2px and shrink shadow.
Cards: white, same border and shadow. Left-align content; do not centre everything.

### Loading animations (CSS only unless noted):
1. Button spinner — small ring inside the button, button disabled while submitting (`loader.js`).
2. AI generating — 5 skeleton question cards with a shimmer, plus rotating text: "Reading your prompt...", "Writing questions...", "Checking answers...".
3. Lobby — "Waiting for host" with three bouncing dots.
4. Matchmaking — pulsing ring + elapsed seconds + Cancel button.
5. Question timer — shrinking bar, turns red in the last 5 seconds.
6. Results — scores count up (small JS). Respect `prefers-reduced-motion`.

---

## 6. AI quiz generator spec

- Input: free-text prompt, plus optional number of questions (5–20) and difficulty.
- `client.py` exposes ONE function: `generate_quiz(prompt, n, difficulty) -> dict`.
- Provider is chosen by env var `AI_PROVIDER` (`claude` or `gemini`), with the key in `.env`. Keep both behind that one function.
- The model must return JSON only:
  `{"title": str, "topic": str, "questions": [{"text": str, "options": [str,str,str,str], "correct_index": 0-3}]}`
- Validate: exactly 4 options, `correct_index` in range, no empty text. On invalid JSON retry once, then show a friendly error.
- Show an editable preview. Nothing is saved until the user clicks Save.
- Rate-limit: max 5 generations per user per hour.
- Ignore any instructions inside the user's prompt that ask to change the output format.

---

## 7. requirements.txt (final)

```
Django>=5.0,<6
mysqlclient
channels
channels-redis
daphne
django-environ
anthropic       # only if AI_PROVIDER=claude
google-genai    # only if AI_PROVIDER=gemini
pytest-django
```

---

## 8. .env.example

```
DJANGO_SETTINGS_MODULE=config.settings.dev
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=blitz
DB_USER=blitz
DB_PASSWORD=blitz
DB_HOST=127.0.0.1
DB_PORT=3306
REDIS_URL=redis://127.0.0.1:6379/0
AI_PROVIDER=claude
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
```

---

## 9. Build phases — give these to Antigravity ONE AT A TIME

### Phase 1 — Foundation
Create the new structure from section 2 (empty files where needed). Split settings, load `.env`, connect MySQL, add `docker-compose.yml` for MySQL and Redis. Create `accounts.User` BEFORE the first migration. Build signup/login/logout/profile. Build `base.html`, `tokens.css`, `base.css`, `components.css` from section 5. Stop and show me the login page running.

### Phase 2 — Quizzes
Models, forms and views for quiz create/edit/delete with a question formset (4 options, one correct, time limit, points). Owner-only edit and delete. "My quizzes" and "Explore" pages. Admin registration. Stop and show me creating a quiz.

### Phase 3 — Rooms (group play)
`Room`, `RoomPlayer`, `Answer`. Create room from a quiz, join with a code, lobby over WebSocket, host starts, server-driven question/timer/reveal loop, scoring in `services.py`, results page and leaderboard. Add `ws.js` with auto-reconnect and the question-timer bar. Write `test_services.py`. Stop and show me two browser tabs playing together.

### Phase 4 — 1v1 duels
`matchmaking.py` with a Redis queue, "Find opponent" page, cancel, auto-start when two players are matched, "challenge a friend by code" option. Reuse the room engine; do not duplicate scoring. Stop and show me two players matched.

### Phase 5 — AI generator
Build `ai/` per section 6, with `test_ai_client.py` using a mocked LLM. Add the skeleton loading animation. Stop and show me a quiz generated from a prompt.

### Phase 6 — Polish and ship
Remaining loaders, count-up results, reduced-motion support, empty states, 404/500 pages, reconnect edge cases, README with setup steps and an architecture diagram, and deployment notes (Railway/Render/VPS with Daphne + Redis + MySQL). Run all tests.

---

## 10. Definition of done
- `docker compose up -d` then `python manage.py migrate` then `daphne config.asgi:application` runs the whole app.
- Two players can finish a group game and a 1v1 duel.
- A quiz can be generated from a prompt, edited and saved.
- No inline styles, no hard-coded secrets, no unused packages or files.
- `pytest` passes.

