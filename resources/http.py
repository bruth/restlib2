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

codes = AttrDict(
    'HTTP Status Codes',

    # Informational 1xx
    CONTINUE = '100 Continue',
    SWITCHING_PROTOCOLS = '101 Switching Protocols',

    # Successful 2xx
    OK = '200 OK',
    CREATED = '201 Created',
    ACCEPTED = '202 Accepted',
    NON_AUTHORITATIVE_INFORMATION = '203 Non-Authoritative Information',
    NO_CONTENT = '204 No Content',
    RESET_CONTENT = '205 Reset Content',
    PARTIAL_CONTENT = '206 Partial Content',

    # Redirection 3xx,
    MULTIPLE_CHOICES = '300 Multiple Choices',
    MOVED_PERMANENTLY = '301 Moved Permanently',
    FOUND = '302 Found',
    SEE_OTHER = '303 See Other',
    NOT_MODIFIED = '304 Not Modified',
    USE_PROXY = '305 Use Proxy',
    # UNKNOWN = '306 Unknown'),
    TEMPORARY_REDIRECT = '307 Temporary Redirect',

    # Client Errors 4xx,
    BAD_REQUEST = '400 Bad Request',
    UNAUTHORIZED = '401 Unauthorized',
    PAYMENT_REQUIRED = '402 Payment Required',
    FORBIDDEN = '403 Forbidden',
    NOT_FOUND = '404 Not Found',
    METHOD_NOT_ALLOWED = '405 Method Not Allowed',
    NOT_ACCEPTABLE = '406 Not Acceptable',
    PROXY_AUTHENTICATION_REQUIRED = '407 Proxy Authentication Required',
    REQUEST_TIMEOUT = '408 Request Timeout',
    CONFLICT = '409 Conflict',
    GONE = '410 Gone',
    LENGTH_REQUIRED = '411 Length Required',
    PRECONDITION_FAILED = '412 Precondition Failed',
    REQUEST_ENTITY_TOO_LARGE = '413 Request Entity Too Large',
    REQUEST_URI_TOO_LONG = '414 Request-URI Too Long',
    UNSUPPORTED_MEDIA_TYPE = '415 Unsupported Media Type',
    REQUESTED_RANGE_NOT_SATISFIABLE = '416 Requested Range Not Satisfiable',
    EXPECTATION_FAILED = '417 Expectation Failed',
    UNPROCESSABLE_ENTITY = '422 Unprocessable Entity',
    PRECONDITION_REQUIRED = '428 Precondition Required',
    TOO_MANY_REQUESTS = '429 Too Many Requests',

    # Server Errors 5xx
    INTERNAL_SERVER_ERROR = '500 Internal Server Error',
    NOT_IMPLEMENTED = '501 Not Implemented',
    BAD_GATEWAY = '502 Bad Gateway',
    SERVICE_UNAVAILABLE = '503 Service Unavailable',
    GATEWAY_TIMEOUT = '504 Gateway Timeout',
    HTTP_VERSION_NOT_SUPPORTED = '505 HTTP Version Not Supported',
)
