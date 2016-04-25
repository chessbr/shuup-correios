# -*- coding: utf-8 -*-
import os
import tempfile

SECRET_KEY = "x"


INSTALLED_APPS = (
    # django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    # shoop themes
    'shoop.themes.classic_gray',
    # shoop
    'shoop.addons',
    'shoop.admin',
    'shoop.core',
    'shoop.default_tax',
    'shoop.front',
    'shoop.front.apps.auth',
    'shoop.front.apps.customer_information',
    'shoop.front.apps.personal_order_history',
    'shoop.front.apps.registration',
    'shoop.front.apps.simple_order_notification',
    'shoop.front.apps.simple_search',
    'shoop.notify',
    'shoop.simple_cms',
    'shoop.customer_group_pricing',
    'shoop.campaigns',
    'shoop.simple_supplier',
    'shoop.order_printouts',
    'shoop.testing',
    'shoop.utils',
    'shoop.xtheme',
    # external apps
    'bootstrap3',
    'django_jinja',
    'easy_thumbnails',
    'filer',
    'registration',
    'rest_framework',

    "shoop_correios"
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(
            tempfile.gettempdir(),
            'shoop_correios_tests.sqlite3'
        ),
    }
}


class DisableMigrations(object):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return "notmigrations"

SOUTH_TESTS_MIGRATE = False
MIGRATION_MODULES = DisableMigrations()
MEDIA_ROOT = os.path.join(os.path.dirname(__file__), "var", "media")

TEMPLATES = [
    {
        "BACKEND": "django_jinja.backend.Jinja2",
        "APP_DIRS": True,
        "OPTIONS": {
            "match_extension": ".jinja",
            "newstyle_gettext": True,
        },
        "NAME": "jinja2",
    },
]
