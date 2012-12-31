#!/bin/sh

DJANGO_SETTINGS_MODULE='restlib2.tests.settings' PYTHONPATH=. coverage run `which django-admin.py` test restlib2
rm -rf docs/coverage
coverage html
