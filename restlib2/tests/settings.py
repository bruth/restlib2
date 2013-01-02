import os
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS

SECRET_KEY = '123abc'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.dirname(__file__), 'restlib2.db'),
    }
}

ROOT_URLCONF = 'restlib2.tests.cases'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'restlib2',
    'restlib2.tests',
)

TEMPLATE_CONTEXT_PROCESSORS += (
    'django.core.context_processors.request',
)
