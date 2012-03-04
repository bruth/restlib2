from django.core.handlers.wsgi import STATUS_CODE_TEXT
from .structures import AttrDict

methods = AttrDict(
    'HTTP Methods',

    GET = 'GET',
    HEAD = 'HEAD',
    OPTIONS = 'OPTIONS',
    POST = 'POST',
    PUT = 'PUT',
    DELETE = 'DELETE',
    # PATCH Method introduced; ref: http://tools.ietf.org/html/rfc5789
    PATCH = 'PATCH',
)


# New codes http://tools.ietf.org/html/draft-nottingham-http-new-status-02
STATUS_CODE_TEXT[422] = 'UNPROCESSABLE ENTITY'
STATUS_CODE_TEXT[428] = 'PRECONDITION REQUIRED'
STATUS_CODE_TEXT[429] = 'TOO MANY REQUESTS'
STATUS_CODE_TEXT[431] = 'REQUEST HEADER FIELDS TOO LARGE'
STATUS_CODE_TEXT[511] = 'NETWORK AUTHENTICATION REQUIRED'

# Invert dict for reference by name
codes = AttrDict(
    'HTTP Status Codes', [
        (y.lower().replace(' ', '_'), x) for x, y in STATUS_CODE_TEXT.items()
    ]
)
