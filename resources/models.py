from resources import codes, methods

class Response(object):
    pass

class Resource(object):
    def __init__(self):
        self.response = Response()

    def __call__(self, request, *args, **kwargs):
        # 503 Service Unavailable - Upstream

        # 414 Request URI Too Long - Upstream

        # 400 Bad Request - Upstream, note that many services respond
        # with this code when entities are unprocessable. This should
        # really be a 422

        # 401 Unauthorized
        if not self.is_authorized(request):
            return codes.unauthorized

        # 403 Forbidden
        # TODO implement.., arbitrary resource restriction?

        # 501 Not Implemented
        # TODO application-wide block of request methods..

        # 415 Unsupported Media Type
        if not self.content_type_supported(request):
            return codes.unsupported_media_type

        # 413 Request Entity Too Large
        if self.request_entity_too_large(request):
            self.response.headers['retry-after'] = 20
            return codes.request_entity_too_large

        # OPTIONS should alway be available. process is in lieu of this
        # resource's allowed methods
        if request.method == methods.options:
            return self.OPTIONS(request)

        # 405 Method Not Allowed
        if request.method not in self.allowed_methods:
            return codes.method_not_allowed

        # 406 Not Acceptable
        # Has the Accept header?
        if request.headers['accept'] and not self.accept_supported(request):
            return codes.not_acceptable

        # Has the Accept-Language header?
        if request.headers['accept-language'] and not self.accept_language_supported(request):
            return codes.not_acceptable

        # Has the Accept-Charset header?
        if request.headers['accept-charset'] and not self.accept_charset_supported(request):
            return codes.not_acceptable

         # Has the Accept-Encoding header?
        if request.headers['accept-encoding'] and not self.accept_encoding_supported(request):
            return codes.not_acceptable

        # 412 Precondition Failed
        if request.headers['if-match']:
            pass

    def is_authenticated(self, request):
        "Test if this request is authenticated."

    def is_authorized(self, request):
        "Test if this request is authorized."

    def request_entity_too_large(self, request):
        "Check if the request body is too large to process."

    def content_type_supported(self, request):
        return request.headers['content-type'] in self.supported_content_types

    def accept_supported(self, request):
        "Check to see if the media type is supported for response."

    def accept_language_supported(self, request):
        "Check to see if the language is supported for response."

    def accept_charset_supported(self, request):
        "Check to see if the character set is supported for response."

    def accept_encoding_supported(self, request):
        "Check to see if the encoding is supported for response."

    def OPTIONS(self, request):
        # Does not do anything with requests with an entity-body
        self.response.headers['allow'] = self.format_allow_header()
        self.response.headers['content-length'] = 0
        # TODO add never cache headers..
