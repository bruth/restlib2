from .structures import AttrDict

class Method(object):
    """An HTTP method which defines whether this method is safe and
    idempotent.

    ref: http://www.w3.org/Protocols/rfc2616/rfc2616-sec5.html
    """
    def __init__(self, method, safe, idempotent, cacheable):
        self.method = method
        self.safe = safe
        self.idempotent = idempotent
        self.cacheable = cacheable

    def __str__(self):
        return self.method

    def __repr__(self):
        props = []

        if self.safe:
            props.append('Safe')
        if self.idempotent:
            props.append('Idempotent')
        if self.cacheable:
            props.append('Cacheable')

        if props:
            return '<Method: %s (%s)>' % (str(self), ', '.join(props))
        return '<Method: %s>' % str(self)

    def __eq__(self, obj):
        if isinstance(obj, basestring):
            return obj == str(self)
        return super(Method, self).__cmp__(obj)


class StatusCode(object):
    """HTTP response status code which may be used within ``Resource``
    methods for constructing a response.

    ref: http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
    """
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message

    def __repr__(self):
        return '<StatusCode: %s (%d)>' % (self.message, self.status_code)

    def __eq__(self, obj):
        return obj == self.status_code


methods = AttrDict(
    'HTTP Methods',

    GET = Method('GET', True, True, True),
    HEAD = Method('HEAD', True, True, True),
    OPTIONS = Method('OPTIONS', True, True, False),
    POST = Method('POST', False, False, False),
    PUT = Method('PUT', False, True, False),
    DELETE = Method('DELETE', False, True, False),
    # PATCH Method introduced; ref: http://tools.ietf.org/html/rfc5789
    PATCH = Method('PATCH', False, False, False),
)

codes = AttrDict(
    'HTTP Status Codes',

    # Informational 1xx
    CONTINUE = StatusCode(100, 'Continue'),
    SWITCHING_PROTOCOLS = StatusCode(101, 'Switching Protocols'),

    # Successful 2xx
    OK = StatusCode(200, 'OK'),
    CREATED = StatusCode(201, 'Created'),
    ACCEPTED = StatusCode(202, 'Accepted'),
    NON_AUTHORITATIVE_INFORMATION = StatusCode(203, 'Non-Authoritative Information'),
    NO_CONTENT = StatusCode(204, 'No Content'),
    RESET_CONTENT = StatusCode(205, 'Reset Content'),
    PARTIAL_CONTENT = StatusCode(206, 'Partial Content'),

    # Redirection 3xx,
    MULTIPLE_CHOICES = StatusCode(300, 'Multiple Choices'),
    MOVED_PERMANENTLY = StatusCode(301, 'Moved Permanently'),
    FOUND = StatusCode(302, 'Found'),
    SEE_OTHER = StatusCode(303, 'See Other'),
    NOT_MODIFIED = StatusCode(304, 'Not Modified'),
    USE_PROXY = StatusCode(305, 'Use Proxy'),
    # UNKNOWN = StatusCode(306, 'Unknown'),
    TEMPORARY_REDIRECT = StatusCode(307, 'Temporary Redirect'),

    # Client Errors 4xx,
    BAD_REQUEST = StatusCode(400, 'Bad Request'),
    UNAUTHORIZED = StatusCode(401, 'Unauthorized'),
    PAYMENT_REQUIRED = StatusCode(402, 'Payment Required'),
    FORBIDDEN = StatusCode(403, 'Forbidden'),
    NOT_FOUND = StatusCode(404, 'Not Found'),
    METHOD_NOT_ALLOWED = StatusCode(405, 'Method Not Allowed'),
    NOT_ACCEPTABLE = StatusCode(406, 'Not Acceptable'),
    PROXY_AUTHENTICATION_REQUIRED = StatusCode(407, 'Proxy Authentication Required'),
    REQUEST_TIMEOUT = StatusCode(408, 'Request Timeout'),
    CONFLICT = StatusCode(409, 'Conflict'),
    GONE = StatusCode(410, 'Gone'),
    LENGTH_REQUIRED = StatusCode(411, 'Length Required'),
    PRECONDITION_FAILED = StatusCode(412, 'Precondition Failed'),
    REQUEST_ENTITY_TOO_LARGE = StatusCode(413, 'Request Entity Too Large'),
    REQUEST_URI_TOO_LONG = StatusCode(414, 'Request-URI Too Long'),
    UNSUPPORTED_MEDIA_TYPE = StatusCode(415, 'Unsupported Media Type'),
    REQUESTED_RANGE_NOT_SATISFIABLE = StatusCode(416, 'Requested Range Not Satisfiable'),
    EXPECTATION_FAILED = StatusCode(417, 'Expectation Failed'),
    UNPROCESSABLE_ENTITY = StatusCode(422, 'Unprocessable Entity'),
    PRECONDITION_REQUIRED = StatusCode(428, 'Precondition Required'),
    TOO_MANY_REQUESTS = StatusCode(429, 'Too Many Requests'),

    # Server Errors 5xx
    INTERNAL_SERVER_ERROR = StatusCode(500, 'Internal Server Error'),
    NOT_IMPLEMENTED = StatusCode(501, 'Not Implemented'),
    BAD_GATEWAY = StatusCode(502, 'Bad Gateway'),
    SERVICE_UNAVAILABLE = StatusCode(503, 'Service Unavailable'),
    GATEWAY_TIMEOUT = StatusCode(504, 'Gateway Timeout'),
    HTTP_VERSION_NOT_SUPPORTED = StatusCode(505, 'HTTP Version Not Supported'),
)
