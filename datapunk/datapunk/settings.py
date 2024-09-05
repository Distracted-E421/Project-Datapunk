from pathlib import Path
from pymongo import MongoClient

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-51jbpvv20alp37&m3bka5+9c2vn&2#@4nih^u+wxk*drk#$7n3'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'parsers',
    'visualizations',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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

ROOT_URLCONF = 'datapunk.urls'

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

WSGI_APPLICATION = 'datapunk.wsgi.application'

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# MongoDB Configuration
MONGODB_DATABASES = {
    'mongo_test1': {
        'HOST': 'localhost',
        'PORT': 27017,
        'NAME': 'datapunk_test1',
        'USER': 'dp_service',
        'PASSWORD': '1984'
    },
    'mongo_test2': {
        'HOST': 'localhost',
        'PORT': 27017,
        'NAME': 'datapunk_test2',
        'USER': 'dp_service',
        'PASSWORD': '1984'
    },
    'mongo_test3': {
        'HOST': 'localhost',
        'PORT': 27017,
        'NAME': 'datapunk_test3',
        'USER': 'dp_service',
        'PASSWORD': '1984'
    },
    'mongo_prod1': {
        'HOST': 'localhost',
        'PORT': 27017,
        'NAME': 'datapunk_prod1',
        'USER': 'dp_service',
        'PASSWORD': '1984'
    },
    'mongo_prod2': {
        'HOST': 'localhost',
        'PORT': 27017,
        'NAME': 'datapunk_prod2',
        'USER': 'dp_service',
        'PASSWORD': '1984'
    }
}




# Password validation

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
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
