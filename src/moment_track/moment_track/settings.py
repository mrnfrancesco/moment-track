"""
Django settings for moment_track project.

Generated by 'django-admin startproject' using Django 1.11.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os

from datetime import timedelta
from django.utils.translation import ugettext_lazy as _

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'uf0#4+i!c8a^r4h8voz16be8=)-n8qgn)p^w4(^^fvw4d!6&1v'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
PAYPAL_TEST = True

ALLOWED_HOSTS = ['*']

# Celery settings
if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine'):
    CELERY_BROKER_URL = 'amqp://<username>:<password>@<host>:<port>//'
else:
    CELERY_BROKER_URL = 'amqp://guest:guest@127.0.0.1:5672//'

CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_BACKEND = 'django-db'


# Project specific settings
MOMENTTRACK_AUDIO_FRAGMENT_DURATION = timedelta(seconds=10)
MOMENTTRACK_MIN_TRANSCRIPTION_CONFIDENCE = .65

GOOGLE_SPEECH_RECOGNITION_API_KEY = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
GOOGLE_CLOUD_SPEECH_CREDENTIALS = None  # INSERT GOOGLE CLOUD SPEECH JSON CREDENTIALS FILE CONTENT HERE


# Application definition

INSTALLED_APPS = [
    'sslserver',
    'django_celery_results',
    'dashboard.apps.DashboardConfig',
    'django.contrib.auth',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.dropbox_oauth2',
    'paypal.standard.ipn',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'phonenumber_field',
    'timedeltatemplatefilter',
    'rest_framework',
    'rest_framework_swagger',
    'django_filters',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'moment_track.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'moment_track.wsgi.application'

SITE_ID = 1

# API settings
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
            'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
    'DEFAULT_VERSION': 'v1',
    'PAGE_SIZE': 10,
}

# API documentation settings
SWAGGER_SETTINGS = {
    'USE_SESSION_AUTH': False,
    'DOC_EXPANSION': 'list',
    'SUPPORTED_SUBMIT_METHODS': ['get'],
}


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine'):
    # Running on production App Engine, so connect to Google Cloud SQL using
    # the unix socket at /cloudsql/<your-cloudsql-connection string>
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': '/cloudsql/<your-cloudsql-connection-string>',
            'NAME': 'moment_track',
            'USER': '<your-database-user>',
            'PASSWORD': '<your-database-password>',
        }
    }
else:
    # Running locally so connect to either a local MySQL instance or connect to
    # Cloud SQL via the proxy. To start the proxy via command line:
    #
    #     $ cloud_sql_proxy -instances=[INSTANCE_CONNECTION_NAME]=tcp:3306
    #
    # See README to know how to set up the environment properly
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'HOST': '127.0.0.1',
            'PORT': '3306',
            'NAME': 'moment_track',
            'USER': 'moment_track',
            'PASSWORD': 'moment_track',
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
            }
        }
    }

# Authentication backends
AUTHENTICATION_BACKENDS = (
    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
)

AUTH_USER_MODEL = 'dashboard.User'

# Django-Allauth settings
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 5
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300
ACCOUNT_PRESERVE_USERNAME_CASING = False
ACCOUNT_SIGNUP_EMAIL_ENTER_TWICE = False
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_USER_DISPLAY = 'dashboard.accounts.user_displayable_name'
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'optional'
SOCIALACCOUNT_AUTO_SIGNUP = False
SOCIALACCOUNT_FORMS = {
    'signup': 'dashboard.forms.PrivateSocialSignupForm'
}
SOCIALACCOUNT_QUERY_EMAIL = True

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/accounts/login'

# E-mail and SMTP backend settings
# https://docs.djangoproject.com/en/1.11/ref/settings/#email-backend
# https://docs.djangoproject.com/en/1.11/topics/email/#smtp-backend
DEFAULT_FROM_EMAIL = 'support@moment-track.it'
EMAIL_SUBJECT_PREFIX = '[Moment Track] '
EMAIL_USE_LOCALTIME = False

EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
# Empty user and password means no authentication
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''

if DEBUG:
    # If in debug mode, just send emails as console messages
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# PayPal settings
if PAYPAL_TEST:
    PAYPAL_BUSINESS_EMAIL_ADDRESS = 'seller@moment-track.it'
    PAYPAL_BUYER_EMAIL_ADDRESS = 'buyer@moment-track.it'
else:
    PAYPAL_BUSINESS_EMAIL_ADDRESS = 'francesco.mrn24@gmail.com'


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_COOKIE_NAME = 'language'
LANGUAGE_COOKIE_AGE = 31536000  # 1 year

LANGUAGE_CODE = 'en'

LANGUAGES = (
    ('en', _('English')),
    ('it', _('Italian')),
)

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

# Uploaded files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
