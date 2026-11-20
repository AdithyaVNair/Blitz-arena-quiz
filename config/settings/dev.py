from .base import *

DEBUG = True

DB_ENGINE = env('DB_ENGINE', default='django.db.backends.mysql')

if DB_ENGINE == 'django.db.backends.sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'dev_db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': env('DB_NAME', default='blitz'),
            'USER': env('DB_USER', default='blitz'),
            'PASSWORD': env('DB_PASSWORD', default='blitz'),
            'HOST': env('DB_HOST', default='127.0.0.1'),
            'PORT': env('DB_PORT', default='3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
            },
        }
    }

USE_IN_MEMORY_CHANNEL_LAYER = env.bool('USE_IN_MEMORY_CHANNEL_LAYER', default=False)

if USE_IN_MEMORY_CHANNEL_LAYER:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        }
    }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [env('REDIS_URL', default='redis://127.0.0.1:6379/0')],
            },
        },
    }

