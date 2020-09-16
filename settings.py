"""
Django settings for atomresponder project.

Generated by 'django-admin startproject' using Django 3.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'v4@s4afv#a()mya1*@eyb5j4i!-7_@!upy6*c44(7ao2@6t=a2'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'kinesisresponder',
    'atomresponder',
    'rabbitmq'
]

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = [
    "--with-coverage",
    "--cover-package=atomresponder",
    "--cover-package=kinesisresponder",
    "--cover-package=rabbitmq",
    "--with-xunit"
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

ROOT_URLCONF = 'urls'

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

WSGI_APPLICATION = 'wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get("DB_NAME", "atomresponder"),
        'USER': os.environ.get("DB_USER", "atomresponder"),
        'PASSWORD': os.environ.get("DB_PASSWD", "atomresponder"),
        'HOST': os.environ.get("DB_HOST", 'localhost'),
        'PORT': os.environ.get("DB_PORT", "5432"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'normal': {
            'format': "{asctime} {name}|{funcName} [{levelname}] {message}",
            'style': "{"
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'normal',
        },
    },
    'loggers': {
        'pika': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'rabbitmq': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = 'static/'

### Vidispine configuration. These should be the locations that the _server portion_ can access VS, not the browser.
VIDISPINE_URL=os.environ.get("VIDISPINE_URL","http://vidispine.local:80")
VIDISPINE_USERNAME=os.environ.get("VIDISPINE_USER","admin")
VIDISPINE_PASSWORD=os.environ.get("VIDISPINE_PASSWORD","admin")

### Local cache locations
ATOM_RESPONDER_DOWNLOAD_PATH=os.environ.get("LOCAL_DOWNLOAD_PATH", "/path/to/download")
ATOM_RESPONDER_DOWNLOAD_BUCKET=os.environ.get("DOWNLOAD_BUCKET", "bucketname")

### Connection to Kinesis
ATOM_RESPONDER_STREAM_NAME=os.environ.get("MEDIA_ATOM_STREAM","streamname") #Kinesis stream to connect to
MEDIA_ATOM_ROLE_ARN=os.environ.get("MEDIA_ATOM_ROLE_ARN","somearn")     #Role to use when connecting to the stream
MEDIA_ATOM_AWS_ACCESS_KEY_ID=os.environ.get("MEDIA_ATOM_AWS_ACCESS_KEY_ID","somekey")   #AWS creds to use when assuming the role
MEDIA_ATOM_AWS_SECRET_ACCESS_KEY=os.environ.get("MEDIA_ATOM_AWS_SECRET_ACCESS_KEY","somesecret")
SESSION_NAME="pluto-atomresponder"  #Session description for temporary credentials associated with role

### Ingest parameters
ATOM_RESPONDER_SHAPE_TAG=os.environ.get("ATOM_RESPONDER_SHAPE_TAG", "lowres")
ATOM_RESPONDER_IMPORT_PRIORITY=os.environ.get("ATOM_RESPONDER_IMPORT_PRIORITY", "HIGH")

### Connection to media atom tool, for resending
ATOM_TOOL_HOST='https://atomtool'
ATOM_TOOL_SECRET='sauce'
GNM_ATOM_RESPONDER_LAUNCHDETECTOR_URL = "https://launchdetector"

### Message queue configuration.
RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.environ.get("RABBITMQ_PORT", "5672"))
RABBITMQ_VHOST = os.environ.get("RABBITMQ_VHOST", "prexit")
RABBITMQ_EXCHANGE = 'pluto-atomresponder'
RABBITMQ_USER = os.environ.get("RABBITMQ_USER","pluto-ng")
RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_PASSWD","")
