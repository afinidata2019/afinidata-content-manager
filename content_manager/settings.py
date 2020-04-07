"""
Django settings for content_manager project.

Generated by 'django-admin startproject' using Django 2.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
from django.core.exceptions import ImproperlyConfigured


def get_env_variable(var_name):
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = "Set the %s environment variable" % var_name
        raise ImproperlyConfigured(error_msg)


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'h+$+@guqjpn=8q*_-&sf(s4eri$)3@4#&yn9u3tgfkxkxht9m2'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'reply_repo.apps.ReplyRepoConfig',
    'support.apps.SupportConfig',
    'posts.apps.PostsConfig',
    'static.apps.StaticConfig',
    'messenger_users.apps.MessengerUsersConfig',
    'utilities.apps.UtilitiesConfig',
    'dash.apps.DashConfig',
    'upload.apps.UploadConfig',
    'django_nose',
    'rest_framework',
    'random_codes.apps.RandomCodesConfig',
    #'django_extensions'
]

MIDDLEWARE = [
    'request_logging.middleware.LoggingMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'content_manager.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'libraries': {
                'staticfiles': 'django.templatetags.static',
            },
        },
    },
]

WSGI_APPLICATION = 'content_manager.wsgi.application'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Celery broker:
CELERY_BROKER = os.getenv('CELERY_BROKER', "pyamqp://guest@localhost/")


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

print('engine: ', os.getenv('CM_DATABASE_ENGINE'))
print('db name: ', os.getenv('CM_DATABASE_NAME'))


## Hacky, should depend instead on production.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'cm_db.sqlite3',
        'TEST': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'cm_db.sqlite3',
        }
    },
    'messenger_users_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'messenger_users_db.sqlite3',
        'TEST': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'messenger_users_db.sqlite3',
        }
    }
}

if os.getenv('CM_DATABASE_HOST'):
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('CM_DATABASE_ENGINE'),
            'NAME': os.getenv('CM_DATABASE_NAME'),
            'USER': os.getenv('CM_DATABASE_USER'),
            'PASSWORD': os.getenv('CM_DATABASE_PASSWORD'),
            'HOST': os.getenv('CM_DATABASE_HOST'),
            'PORT': os.getenv('CM_DATABASE_PORT'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'charset': 'utf8mb4'
            }
        },
        'messenger_users_db': {
            'ENGINE': os.getenv('CM_DATABASE_ENGINE'),
            'NAME': os.getenv('CM_DATABASE_USERS_NAME'),
            'USER': os.getenv('CM_DATABASE_USER'),
            'PASSWORD': os.getenv('CM_DATABASE_PASSWORD'),
            'HOST': os.getenv('CM_DATABASE_HOST'),
            'PORT': os.getenv('CM_DATABASE_PORT'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'charset': 'utf8mb4'
            }
        }
    }

DATABASE_ROUTERS = ['messenger_users.routers.MessengerUsersRouter']


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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

# Use nose to run all tests
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# Tell nose to measure coverage on the 'foo' and 'bar' apps
NOSE_ARGS = [
    '--verbosity=3',
    # '--with-coverage',
    # '--cover-tests',
    # '--cover-package=content_manager,messenger_users,posts',
    # '--with-doctest'
 #   '--cover-package=foo,bar',
]

# REST config
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 35
}

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = '/static/'

DOMAIN_URL = 'http://localhost:8000'
