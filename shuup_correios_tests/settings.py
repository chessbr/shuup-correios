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
    # shuup themes
    'shuup.themes.classic_gray',
    # shuup
    'shuup.addons',
    'shuup.admin',
    'shuup.core',
    'shuup.default_tax',
    'shuup.front',
    'shuup.front.apps.auth',
    'shuup.front.apps.customer_information',
    'shuup.front.apps.personal_order_history',
    'shuup.front.apps.registration',
    'shuup.front.apps.simple_order_notification',
    'shuup.front.apps.simple_search',
    'shuup.notify',
    'shuup.simple_cms',
    'shuup.customer_group_pricing',
    'shuup.campaigns',
    'shuup.simple_supplier',
    'shuup.order_printouts',
    'shuup.testing',
    'shuup.utils',
    'shuup.xtheme',
    # external apps
    'bootstrap3',
    'django_jinja',
    'easy_thumbnails',
    'filer',
    'registration',
    'rest_framework',

    "shuup_correios"
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'my-default',
    },
    'correios': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        'LOCATION': 'unique-snowflake',
    }
}
CORREIOS_CACHE_NAME = 'correios'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(
            tempfile.gettempdir(),
            'shuup_correios_tests.sqlite3'
        ),
    }
}

SESSION_SERIALIZER = "django.contrib.sessions.serializers.PickleSerializer"


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

LANGUAGES = [
    ('en', 'English'),
    ('fi', 'Finnish'),
    ('ja', 'Japanese'),
    ('zh-hans', 'Simplified Chinese'),
    ('pt-br', 'Portuguese (Brazil)'),
]
PARLER_DEFAULT_LANGUAGE_CODE = 'en-us'
PARLER_LANGUAGES = {
    None: [{"code": c, "name": n} for (c, n) in LANGUAGES],
    'default': {
        'hide_untranslated': False,
    }
}
