import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'restlib2.tests.settings'

from django.core import management
management.call_command('test', 'restlib2')
