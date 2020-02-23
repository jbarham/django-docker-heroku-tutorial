from .base import *

# Connect to PosgreSQL database defined in docker-compose.yml.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'djheroku',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'db',
        'PORT': '5432',
    }
}

if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']

    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

    # https://stackoverflow.com/a/50332425
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: True,
    }
