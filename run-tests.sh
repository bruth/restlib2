#!/bin/sh

ARGS="$@"

if [ ! $ARGS ]; then
        ARGS="restlib2"
fi

DJANGO_SETTINGS_MODULE='restlib2.tests.settings' PYTHONPATH=. coverage run `which django-admin.py` test "$ARGS"
rm -rf docs/coverage
coverage html
