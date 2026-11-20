# Blitz Arena v2

Fast, real-time multiplayer quiz arena with 1v1 duels, live group rooms, and AI-powered quiz generation.

## Tech Stack
- **Backend:** Python 3.12+, Django 5.x, Daphne, Django Channels
- **Database & Cache:** MySQL 8, Redis
- **Frontend:** Server-rendered Django templates + Vanilla JavaScript + CSS Design System (no frameworks, no build step)
- **AI Integration:** Google Gemini / Anthropic Claude (via backend service)

## Quickstart
1. Copy `.env.example` to `.env` and adjust secrets:
   ```bash
   cp .env.example .env
   ```
2. Start MySQL and Redis with Docker:
   ```bash
   docker compose up -d
   ```
3. Run database migrations:
   ```bash
   python manage.py migrate
   ```
4. Start the ASGI server:
   ```bash
   daphne config.asgi:application
   # or for development:
   python manage.py runserver
   ```

