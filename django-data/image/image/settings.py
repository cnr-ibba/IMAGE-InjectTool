"""
Django settings for image project.

Generated by 'django-admin startproject' using Django 1.11.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os

from decouple import config
from celery.schedules import crontab

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', cast=bool, default=False)

ADMINS = [('Admin', 'bioinfo.ibba@gmail.com'), ]

ALLOWED_HOSTS = ['*']


# --- INSTALLED_APPS


# Installed app order:
# - django default applications
# - downloaded applications
# - custom application
INSTALLED_APPS = [
    'channels',
    'registration',  # should be immediately above 'django.contrib.admin'
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    'debug_toolbar',
    'django_celery_beat',
    'djcelery_email',
    'django_simple_cookie_consent',
    'image_app',
    'cryoweb',
    'zooma',
    'language',
    'biosample',
    'accounts',
    'submissions',
    'validation',
    'animals',
    'samples',
    'crbanim',
    'submissions_ws'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'image.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# Setting migration directories for 3rd party modules
# https://stackoverflow.com/a/26947339
MIGRATION_MODULES = {
    'django_simple_cookie_consent': 'image.site-migrations',
}


WSGI_APPLICATION = 'image.wsgi.application'


# --- DATABASES


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'image',
        'USER': config('IMAGE_USER'),
        'PASSWORD': config('IMAGE_PASSWORD'),
        'HOST': 'db',
        'PORT': 5432,
    },
    # https://docs.djangoproject.com/en/1.11/topics/db/multi-db/
    'cryoweb': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'cryoweb',
        'USER': config('IMAGE_USER'),
        'PASSWORD': config('IMAGE_PASSWORD'),
        'HOST': 'db',
        'PORT': 5432,
        'OPTIONS': {
            'options': '-c search_path=apiis_admin'
        },
        'TEST': {
            # https://docs.djangoproject.com/en/1.11/ref/settings/#template
            'TEMPLATE': 'template_cryoweb'
        }
    }
}


# dealing with multiple databases. Is a path at a module in the same directory
# of this configuration file

DATABASE_ROUTERS = ['image.routers.CryowebRouter']


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'UserAttributeSimilarityValidator'),
    },
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'MinimumLengthValidator'),
    },
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'CommonPasswordValidator'),
    },
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'NumericPasswordValidator'),
    },
]


# --- LOGGING


# enable logging on terminal
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': ('%(asctime)s - %(name)s - %(levelname)s - PID '
                       '%(process)d - %(processName)s - %(threadName)s - '
                       '%(message)s')
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'celery': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': True,
        },
        'celery.beat': {
            'level': 'INFO',
            'handlers': ['console'],
        },
        'django.db.backends': {
            'level': 'INFO',
            'handlers': ['console'],
        },
        # HINT: sort applications by name?
        'image_app': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'cryoweb': {
            'level': 'INFO',
            'handlers': ['console'],
        },
        'zooma': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'language': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'biosample': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'accounts': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'submissions': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'validation': {
            'level': 'INFO',
            'handlers': ['console'],
        },
        'animals': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'samples': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'common': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'crbanim': {
            'level': 'INFO',
            'handlers': ['console'],
        },
    },
}


# --- Site settings


# internal ips (used for django-toolbar)
# consider docker network ip addresses
INTERNAL_IPS = [
    '127.0.0.1',
    '172.17.0.1',
    '172.18.0.1',
    '172.19.0.1',
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Rome'

USE_I18N = True

USE_L10N = True

# The PostgreSQL backend stores datetimes as timestamp with time zone.
# In practice, this means it converts datetimes from the connection’s time
# zone to UTC on storage, and from UTC to the connection’s time zone on
# retrieval.
# As a consequence, if you’re using PostgreSQL, you can switch between
# USE_TZ = False and USE_TZ = True freely
USE_TZ = True

# django can accept named URL patterns
# https://stackoverflow.com/a/1519675

# https://docs.djangoproject.com/en/1.11/ref/settings/#std:setting-LOGIN_URL
LOGIN_URL = 'login'

# https://docs.djangoproject.com/en/1.11/ref/settings/#login-redirect-url
LOGIN_REDIRECT_URL = 'image_app:dashboard'

# Static files (CSS, JavaScript, Images) and users' media
# https://docs.djangoproject.com/en/1.8/howto/static-files/
STATIC_URL = '/image/static/'
MEDIA_URL = '/image/media/'

# collect all Django static files in the static folder
STATIC_ROOT = os.path.join(BASE_DIR, "static/")
MEDIA_ROOT = os.path.join(BASE_DIR, "media/")

# This should be set to a list of strings that contain full paths to your
# additional files directory(ies
# STATICFILES_DIRS = [
#     STATIC_ROOT,
# ]

# The numeric mode (i.e. 0o644) to set newly uploaded files to. For more
# information about what these modes mean, see the documentation for os.chmod()
# If this isn’t given or is None, you’ll get operating-system dependent
# behavior. On most platforms, temporary files will have a mode of 0o600,
# and files saved from memory will be saved using the system’s standard umask.
# For security reasons, these permissions aren’t applied to the temporary files
#  that are stored in FILE_UPLOAD_TEMP_DIR.
# This setting also determines the default permissions for collected static
# files when using the collectstatic management command. See collectstatic for
# details on overriding it.
FILE_UPLOAD_PERMISSIONS = 0o644

# restrict access to media URLs
# https://gist.github.com/cobusc/ea1d01611ef05dacb0f33307e292abf4
PROTECTED_MEDIA_ROOT = os.path.join(BASE_DIR, "protected/")
PROTECTED_MEDIA_URL = "/image/protected/"

# Prefix used in nginx config
PROTECTED_MEDIA_LOCATION_PREFIX = "/image/internal/"

# Django registration redux. One-week activation window;
ACCOUNT_ACTIVATION_DAYS = 7

# registration-redux email type
REGISTRATION_EMAIL_HTML = False


# --- Mail settings


# simply displaying them in the console
# https://simpleisbetterthancomplex.com/series/2017/09/25/a-complete-beginners-guide-to-django-part-4.html#console-email-backend
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend')

CELERY_EMAIL_BACKEND = config(
    'CELERY_EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend')

# email backend parameters
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool, default=False)
EMAIL_PORT = config('EMAIL_PORT', cast=int, default=1025)


# --- Redis and Celery settings


# Redis settings
REDIS_HOST = 'redis'
REDIS_PORT = 6379
REDIS_DB = 0

# Celery settings
CELERY_BROKER_URL = 'redis://{}:{}'.format(REDIS_HOST, REDIS_PORT)
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Other Celery settings
CELERY_BEAT_SCHEDULE = {
    'clearsessions': {
        'task': 'image.celery.clearsessions',
        'schedule': crontab(hour=12, minute=0),
    },
    'fetch_biosample_status': {
        'task': "Fetch USI status",
        'schedule': crontab(hour="*", minute='*/15'),
    }
}

# Channels
ASGI_APPLICATION = 'image.routing.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
        },
    },
}
