"""
WSGI config for project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys

# Add the project directory to the sys.path
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
    sys.path.append(path)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

application = get_wsgi_application()

# --- VERCEL TEMPORARY HACK ---
# Run migrations automatically on Vercel so the /tmp/db.sqlite3 gets its tables created.
if os.environ.get('VERCEL') == '1':
    try:
        from django.core.management import call_command
        call_command('migrate', interactive=False)
    except Exception as e:
        print(f"Error running migrations on Vercel startup: {e}")

# Vercel looks for an 'app' variable
app = application
