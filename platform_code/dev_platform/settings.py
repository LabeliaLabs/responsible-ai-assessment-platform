"""
Django settings for dev_platform project.

Generated by 'django-admin startproject' using Django 3.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import mimetypes
import os

from django.utils.translation import ugettext_lazy as _

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ["SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "assessment.apps.AssessmentConfig",
    "home.apps.HomeConfig",
    "bootstrap4",
    "django.contrib.postgres",
    "django_countries",
    "markdownify",
    "modeltranslation",
    "ckeditor",
]

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "dev_platform.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "home.context_processors.add_footer_list",
                "home.context_processors.add_platform_management",
                "django.template.context_processors.i18n",
            ],
        },
    },
]

WSGI_APPLICATION = "dev_platform.wsgi.application"

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": os.environ.get("SQL_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.environ.get("SQL_DATABASE", "platform_db"),
        "USER": os.environ.get("SQL_USER", "postgres"),
        "PASSWORD": os.environ["SQL_PASSWORD"],  # TODO change
        "HOST": os.environ.get("SQL_HOST", "localhost"),
        "PORT": os.environ.get("SQL_PORT", "5432"),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTH_USER_MODEL = "home.User"

# Private token to send HTTP to gitlab API
PRIVATE_TOKEN = os.environ.get("PRIVATE_TOKEN", None)
PROJECT_ID = os.environ.get("PROJECT_ID", None)

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/
# Language by default for the user if the middleware LocaleMiddleware doesn't success
# to identify the user language based on the url/request
LANGUAGE_CODE = "fr"

# Lists of languages site supports.
LANGUAGES = (
    ("en", _("English")),
    ("fr", _("French")),
)

LOCALE_PATHS = (os.path.join(BASE_DIR, "locale/"),)

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOGOUT_REDIRECT_URL = "home:homepage"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "./dev.log",
            "backupCount": 10,
            "formatter": "app",
            "maxBytes": 10485760,  # 10MB
        },
    },
    "loggers": {
        "monitoring": {
            "handlers": ["file"],
            "level": "INFO",
            "propagate": True,
        },
    },
    "formatters": {
        "app": {
            "format": (
                "%(asctime)s [%(levelname)-s] " "(%(module)s.%(funcName)s) %(message)s"
            ),
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/
mimetypes.add_type("text/css", ".css", True)
STATIC_URL = "/static/"
STATICFILES_DIRS = ["assessment/static"]  # []
STATIC_ROOT = os.path.join(BASE_DIR, "static")
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

# Email configuration
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CKEDITOR_CONFIGS = {
    "default": {
        "skin": "moono-lisa",
        "toolbar_Basic": [["Source", "-", "Bold", "Italic"]],
        "toolbar_Full": [
            [
                "Format",
                "Bold",
                "Italic",
                "Underline",
                "Strike",
                "SpellChecker",
                "Undo",
                "Redo",
            ],
            {
                "name": "paragraph",
                "items": [
                    "NumberedList",
                    "BulletedList",
                    "-",
                    "Outdent",
                    "Indent",
                    "-",
                ],
            },
            ["Link", "Unlink"],
            # ["Table", "HorizontalRule"],
            ["TextColor", "BGColor"],
            ["Source"],
        ],
        "toolbar": "Full",
        "height": 90,
        "width": "",
        "removePlugins": "easyimage, cloudservices",
    }
}
