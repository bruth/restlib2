from django.core.handlers.wsgi import STATUS_CODE_TEXT
from restlib2.structures import AttrDict

STATUS_CODE_TEXT.setdefault(422, 'UNPROCESSABLE ENTITY')

# http://tools.ietf.org/html/rfc6585
STATUS_CODE_TEXT.setdefault(428, 'PRECONDITION REQUIRED')
STATUS_CODE_TEXT.setdefault(429, 'TOO MANY REQUESTS')
STATUS_CODE_TEXT.setdefault(431, 'REQUEST HEADER FIELDS TOO LARGE')
STATUS_CODE_TEXT.setdefault(511, 'NETWORK AUTHENTICATION REQUIRED')

# http://tools.ietf.org/html/draft-tbray-http-legally-restricted-status-02
STATUS_CODE_TEXT.setdefault(451, 'UNAVAILABLE FOR LEGAL REASONS')

# Invert dict for reference by name
codes = AttrDict('HTTP Status Codes',
    [(y, x) for x, y in STATUS_CODE_TEXT.items()])


# PATCH Method introduced - http://tools.ietf.org/html/rfc5789
methods = AttrDict('HTTP Methods',
    GET = 'GET',
    HEAD = 'HEAD',
    OPTIONS = 'OPTIONS',
    POST = 'POST',
    PUT = 'PUT',
    DELETE = 'DELETE',
    PATCH = 'PATCH',
)
