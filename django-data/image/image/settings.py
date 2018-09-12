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

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', cast=bool, default=False)

ALLOWED_HOSTS = ['*']

# Installed app order:
# - django default applications
# - downloaded applications
# - custom application
INSTALLED_APPS = [
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
    'image_app',
    'cryoweb',
    'zooma',
    'language',
    'biosample',
    'accounts',
    'submissions',
    'validation'
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

WSGI_APPLICATION = 'image.wsgi.application'


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


# enable logging on terminal
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': ('%(asctime)s - %(name)s - %(levelname)s - PID '
                       '%(process)d - %(threadName)s - %(message)s')
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
        'django.db.backends': {
            'level': 'INFO',
            'handlers': ['console'],
        },
        'image_app': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'cryoweb': {
            'level': 'DEBUG',
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
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}

# internal ips (used for django-toolbar)
INTERNAL_IPS = ['127.0.0.1',
                '172.17.0.1']


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
USE_TZ = False

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

# Django registration redux. One-week activation window;
ACCOUNT_ACTIVATION_DAYS = 7

# registration-redux email type
REGISTRATION_EMAIL_HTML = False

# simply displaying them in the console
# https://simpleisbetterthancomplex.com/series/2017/09/25/a-complete-beginners-guide-to-django-part-4.html#console-email-backend
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend')

# email backend parameters
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool, default=False)
EMAIL_PORT = config('EMAIL_PORT', cast=int, default=1025)


# Celery settings
CELERY_BROKER_URL = 'redis://redis:6379'
CELERY_RESULT_BACKEND = 'redis://redis:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TIMEZONE = 'Europe/Rome'
CELERY_ENABLE_UTC = False

# cleanup after 1 hour
# CELERY_TASK_RESULT_EXPIRES = 3600
