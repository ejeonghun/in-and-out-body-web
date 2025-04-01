"""
Django settings for mysite project.

Generated by 'django-admin startproject' using Django 5.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""
from datetime import timedelta
import os
from pathlib import Path

import dotenv
import sentry_sdk

dotenv.load_dotenv(override=True)


"""
prod : 운영 환경
dev : 개발 환경
"""

ENVIRONMENT = os.getenv('ENVIRONMENT') # 운영 환경
SECRETKEY = os.getenv('SECRET_KEY') # 시크릿
LOCAL = os.getenv('LOCAL') # 로컬 환경

print(f'운영환경 : {ENVIRONMENT} 으로 시작됨')

# SECURITY WARNING: don't run with debug turned on in production!
if ENVIRONMENT == 'dev' or ENVIRONMENT == 'debug':
    DEBUG = True
else:
    DEBUG = False

if LOCAL == 'true':
    DEBUG = True
    print('로컬 환경에서 실행됨')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SECRETKEY
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'analysis',
    'fontawesomefree',
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_yasg',
    'django_prometheus',
    'django_apscheduler',
]

if DEBUG:
    INSTALLED_APPS += ['whitenoise.runserver_nostatic']

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

EMAIL_HOST = os.environ['EMAIL_HOST']
EMAIL_USER = os.environ['EMAIL_USER']
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']

# 추가적인 JWT_AUTH 설정
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=5000),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}



MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

if DEBUG:
    MIDDLEWARE += ['whitenoise.middleware.WhiteNoiseMiddleware']

ROOT_URLCONF = 'mysite.urls'

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

WSGI_APPLICATION = 'mysite.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases


if ENVIRONMENT == 'dev':
    DATABASES = {
    'default': {
        'ENGINE': 'django_prometheus.db.backends.postgresql',
        'NAME': os.environ['DEV_POSTGRES_DB_NAME'],
        'USER': os.environ['DEV_POSTGRES_USER'],
        'PASSWORD': os.environ['DEV_POSTGRES_PASSWORD'],
        'HOST': os.environ['DEV_POSTGRES_HOST'],
        'PORT': os.environ['DEV_POSTGRES_PORT'],
        'TEST': {
            'NAME': 'test_' + os.environ['DEV_POSTGRES_DB_NAME'],
            'MIGRATE': True,
            'DEPENDENCIES': [],
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django_prometheus.db.backends.postgresql',
            'NAME': os.environ['POSTGRES_DB_NAME'],
            'USER': os.environ['POSTGRES_USER'],
            'PASSWORD': os.environ['POSTGRES_PASSWORD'],
            'HOST': os.environ['POSTGRES_HOST'],
            'PORT': os.environ['POSTGRES_PORT'],
            'TEST': {
                'NAME': 'test_' + os.environ['POSTGRES_DB_NAME'],
                'MIGRATE': True,
                'SERIALIZE': False,
                'DEPENDENCIES': [],
            },
        }
    }

# AWS S3 Settings
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
AWS_S3_REGION_NAME = os.environ['AWS_S3_REGION_NAME']
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_PRESIGNED_EXPIRATION = 3600 # 단위: 초

# boto3와 django-storages를 사용할 수 있도록 설정
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Seoul'  # Set the global timezone to Korean Standard Time

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'

if DEBUG:
    STATICFILES_DIRS = [os.path.join(f'{BASE_DIR}/analysis', "static")]
else:
    STATIC_ROOT = os.path.join(f'{BASE_DIR}/analysis', 'static')

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'analysis.UserInfo'	# [app].[모델명]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

### django-apscheduler settings
APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a"

# 자동으로 스케쥴러 실행
SCHEDULER_DEFAULT = True

# Prometheus Exporter 설정
PROMETHEUS_EXPORT_MIGRATIONS = False  # 기본 설정 유지

# CSRF Https 적용 옵션
USE_X_FORWARDED_HOST = True

CSRF_TRUSTED_ORIGINS = [ # CSRF 토큰 허용 Origin
    'https://body.aicu.life',
    'http://aicu-office.iptime.org:65002',
    'https://test-body.aicu.life',
    'http://10.0.2.2'
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') # 프록시 허용


"""추 후 HTTP를 완전히 없앨 때 해당 옵션들을 True로 바꿔주어야 함
   현재 HTTP, HTTPS 둘 다 사용하려고 비활성화시켜놓은 상태
"""
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False



ALLOWED_HOSTS = [
    'body.aicu.life',
    'www.body.aicu.life',
    'aicu-office.iptime.org',
    'localhost',
    'test-body.aicu.life',
    '10.0.2.2', # Android Emulator
    'host.docker.internal', # Docker HOST OS addr
    '172.17.0.1', # Docker Host addr
]


# 부정접속 로깅 설정
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s, %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(f'{BASE_DIR}/logs', 'bad_access.log'),  # BASE_DIR에 bad_access.log 파일 경로
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}


# 모니터링 SDK 설정
sentry_sdk.init(
    dsn="https://8c2ca4b3d666763ef090daea2efb03f5@o4509054364745728.ingest.de.sentry.io/4509054367236176",
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)