from datetime import datetime
from werkzeug.wrappers import Response
from werkzeug.http import http_date
from .http import StatusCode, codes, methods

# Convenience function for checking for existent, callable methods
usable = lambda x, y: callable(getattr(x, y, None))

# ## Resource Metaclass
# Sets up a few helper components for the `Resource` class.
class ResourceMetaclass(type):
    def __new__(cls, name, bases, attrs):

        # Create the new class as is to start. Subclass attributes can be
        # checked for in `attrs` and handled as necessary relative to the base
        # classes.
        new_cls = type.__new__(cls, name, bases, attrs)

        # If `allowed_methods` is not defined explicitly in attrs, this
        # could mean one of two things: that the user wants it to inherit
        # from the parent class (if exists) or for it to be set implicitly.
        # The more explicit (and flexible) behavior will be to not inherit
        # it from the parent class, therefore the user must explicitly
        # re-set the attribute.
        if 'allowed_methods' not in attrs or not new_cls.allowed_methods:
            allowed_methods = []

            for method in methods:
                if usable(new_cls, method.lower()):
                    allowed_methods.append(method)

        # If the attribute is defined in this subclass, ensure all methods that
        # are said to be allowed are actually defined and callable.
        else:
            allowed_methods = list(new_cls.allowed_methods)

            for method in allowed_methods:
                if not usable(new_cls, method.lower()):
                    raise ValueError('The {} method is not defined for the '
                        'resource {}'.format(method, new_cls.__name__))

        # The _HEAD_ handler depends on the _GET_ handler, so remove
        # it if not defined.
        if 'GET' not in allowed_methods and 'HEAD' in allowed_methods:
            allowed_methods.remove('HEAD')

        new_cls.allowed_methods = tuple(allowed_methods)

        return new_cls


# ## Resource
# Comprehensive ``Resource`` class which implements sensible request
# processing. The process flow is largely derived from Alan Dean's
# [status code activity diagram][0].
#
# ### Implementation Considerations
# [Section 2][1] of the HTTP/1.1 specification states:
#
# > The methods GET and HEAD MUST be supported by all general-purpose servers.
# > All other methods are OPTIONAL;
#
# The `HEAD` handler is already implemented on the `Resource` class, but
# requires the `GET` handler to be implemented. Although not required, the
# `OPTIONS` handler is also implemented.
#
# Response representations should follow the rules outlined in [Section 5.1][2].
#
# [Section 6.1][3] defines that `GET`, `HEAD`, `OPTIONS` and `TRACE` are
# considered _safe_ methods, thus ensure the implementation of these methods do
# not have any side effects. In addition to the safe methods, `PUT` and
# `DELETE` are considered _idempotent_ which means subsequent identical requests
# to the same resource does not result it different responses to the client.
#
# Request bodies on `GET`, `HEAD`, `OPTIONS`, and `DELETE` requests are
# ignored. The HTTP spec does not define any semantics surrounding this
# situtation.
#
# Typical uses of `POST` requests are described in [Section 6.5][4], but in most
# cases should be assumed by clients as _black box_, neither safe nor idempotent.
# If updating an existing resource, it is more appropriate to use `PUT`.
#
#
# [0]: http://code.google.com/p/http-headers-status/downloads/detail?name=http-headers-status%20v3%20draft.png
# [1]: http://tools.ietf.org/html/draft-ietf-httpbis-p2-semantics-18#section-2
# [2]: http://tools.ietf.org/html/draft-ietf-httpbis-p2-semantics-18#section-5.1
# [3]: http://tools.ietf.org/html/draft-ietf-httpbis-p2-semantics-18#section-6.1
# [4]: http://tools.ietf.org/html/draft-ietf-httpbis-p2-semantics-18#section-6.5
class Resource(object):

    __metaclass__ = ResourceMetaclass

    # ### Service Availability
    # Toggle this resource as unavailable. If `True`, the service
    # will be unavailable indefinitely. If an integer or datetime is
    # used, the `Retry-After` header will set. An integer can be used
    # to define a seconds delta from the current time (good for unexpected
    # downtimes). If a datetime is set, the number of seconds will be
    # calculated relative to the current time (good for planned downtime).
    offline = False

    # ### Allowed Methods
    # If `None`, the allowed methods will be determined based on the resource
    # methods define, e.g. `get`, `put`, `post`. A list of methods can be
    # defined explicitly to have not expose defined methods.
    allowed_methods = None

    # ### Request Rate Limiting
    # Enforce request rate limiting. Both `rate_limit_count` and
    # `rate_limit_seconds` must be defined and not zero to be active.
    # By default, the number of seconds defaults to 1 hour, but the count
    # is `None`, therefore rate limiting is not enforced.
    rate_limit_count = None
    rate_limit_seconds = 60 * 60

    # ### Max Request Entity Length
    # If not `None`, checks if the request entity body is too large to
    # be processed.
    max_request_entity_length = None

    # ### Require Conditional Request
    # If `True`, `PUT` and `PATCH` requests are required to have a conditional
    # header for verifying the operation applies to the current state of the
    # resource on the server. This must be used in conjunction with either
    # the `use_etags` or `use_last_modified` option to take effect.
    require_conditional_request = True

    # ### Use ETags
    # If `True`, the `ETag` header will be set on responses and conditional
    # requests are supported. This applies to _GET_, _HEAD_, _PUT_, _PATCH_
    # and _DELETE_ requests.
    use_etags = True

    # ### Use Last Modified
    # If `True`, the `Last-Modified` header will be set on responses and
    # conditional requests are supported. This applies to _GET_, _HEAD_, _PUT_,
    # _PATCH_ and _DELETE_ requests.
    use_last_modified = False

    # ### Supported _Accept_ Mimetypes
    # Define a list of mimetypes supported for encoding response entity
    # bodies. Default to `('application/json',)`
    # _See also: `supported_content_types`_
    supported_accept_types = ('application/json',)

    # ### Supported _Content-Type_ Mimetypes
    # Define a list of mimetypes supported for decoding request entity bodies.
    # This is independent of the mimetypes encoders for request bodies.
    # Default to `('application/json',)`
    # _See also: `supported_accept_types`_
    supported_content_types = ('application/json',)


    # ## Initialize Once, Process Many
    # Every `Resource` class can be initialized once since they are stateless
    # (and thus thread-safe).
    def __call__(self, request, *args, **kwargs):

        # Initilize a new response for this request. Passing the response along
        # the request cycle allows for gradual modification of the headers. The
        # `status_code` is set to `None` initially to allow for detection when
        # it has not been explicitly.
        response = Response()
        response.status_code = 0

        # Process the request, this should modify the provided `response`
        # object.
        output = self.process(request, response, *args, **kwargs)

        if output is response:
            output = None

        self._prepare_response(output, request, response, *args, **kwargs)
        return response

    # Prepares the final state of the response prior to being returned from
    # this resource. It's purpose is to ensure nothing is missing that would
    # make the response unprocessable by user agents.
    def _prepare_response(self, output, request, response, *args, **kwargs):
        if isinstance(output, StatusCode):
            response.status_code = output.status_code
        elif output is not None:
            response.data = output

        # Apply some basic logic for determining the correct status code.
        # TODO
        if not response.status_code:
            response.status_code = codes.ok.status_code

    def process(self, request, response, *args, **kwargs):
        # TODO keep track of a list of request headers used to
        # determine the resource representation for the 'Vary'
        # header.

        # ### 503 Service Unavailable
        # The server does not need to be unavailable for a resource to be
        # unavailable...
        if self.service_unavailable(request, response):
            return codes.service_unavailable

        # ### 414 Request URI Too Long _(not implemented)_
        # This should be be handled upstream by the Web server

        # ### 400 Bad Request _(not implemented)_
        # Note that many services respond with this code when entities are
        # unprocessable. This should really be a 422 Unprocessable Entity

        # ### 401 Unauthorized
        # Check if the request is authorized to access this resource.
        if self.unauthorized(request, response):
            return codes.unauthorized

        # ### 403 Forbidden
        # Check if this resource is forbidden for the request.
        if self.forbidden(request, response):
            return codes.forbidden

        # ### 429 Too Many Requests
        # Both `rate_limit_count` and `rate_limit_seconds` must be none
        # falsy values to be checked.
        if self.rate_limit_count and self.rate_limit_seconds:
            if self.too_many_requests(request, response, *args, **kwargs):
                return codes.too_many_requests

        # ### 501 Not Implemented _(not implemented)_
        # This technically refers to a service-wide response for an
        # unimplemented request method.

        # ### Process an _OPTIONS_ request
        # Enough processing has been performed to allow an OPTIONS request.
        if request.method == methods.options and 'OPTIONS' in self.allowed_methods:
            return self.options(request, response)

        # ## Request Entity Checks
        if request.content_length:
            # ### 415 Unsupported Media Type
            # Check if the entity `Content-Type` supported by for decoding.
            if self.unsupported_media_type(request, response):
                return codes.unsupported_media_type

            # ### 413 Request Entity Too Large
            # Check if the entity is too large for processing
            if self.request_entity_too_large(request, response):
                return codes.request_entity_too_large

        # ### 405 Method Not Allowed
        if self.method_not_allowed(request, response):
            return codes.method_not_allowed

        # ### 406 Not Acceptable
        # Checks Accept and Accept-* headers
        if self.not_acceptable(request, response):
            return codes.not_acceptable

        # ### 412 Precondition Failed
        # Conditional requests applies to GET, HEAD, PUT, and PATCH.
        # For GET and HEAD, the request checks the either the entity changed
        # since the last time it requested it, `If-Modified-Since`, or if the
        # entity tag (ETag) has changed, `If-None-Match`.

        # ### 428 Precondition Required
        # Prevents the "lost udpate" problem and requires client to confirm
        # the state of the resource has not changed since the last `GET`
        # request. This applies to `PUT` and `PATCH` requests.
        if request.method == methods.put or request.method == methods.delete:
            if self.precondition_required(request, response, *args, **kwargs):
                # HTTP/1.1
                response.headers['Cache-Control'] = 'no-cache'
                # HTTP/1.0
                response.headers['Pragma'] = 'no-cache'
                return codes.precondition_required


        # ETags are enabled. Check for conditional request headers. The current
        # ETag value is used for the conditional requests. After the request
        # method handler has been processed, the new ETag will be calculated.
        if self.use_etags:
            etag = self.get_etag(request, *args, **kwargs)

            # Check for conditional GET or HEAD request
            if request.method == methods.get or request.method == methods.head:
                if 'if-none-match' in request.headers:
                    if request.headers['if-none-match'] == etag:
                        return codes.not_modified

            # Check for conditional PUT or PATCH request
            elif request.method == methods.put or request.method == methods.patch:
                if 'if-match' in request.headers:
                    if request.headers['if-match'] != etag:
                        return codes.precondition_failed

        # Last-Modified date enabled. check for conditional request headers. The
        # current modification datetime value is used for the conditional
        # requests. After the request method handler has been processed, the new
        # Last-Modified datetime will be returned.
        elif self.use_last_modified:
            modified = self.get_last_modified(request, *args, **kwargs)
            last_modified = http_date(modified)

            # Check for conditional GET or HEAD request
            if request.method == methods.get or request.method == methods.head:
                if 'if-modified-since' in request.headers:
                    if request.headers['if-modified-since'] == last_modified:
                        return codes.not_modified

            # Check for conditional PUT or PATCH request
            elif request.method == methods.put or request.method == methods.patch:
                if 'if-unmodified-since' in request.headers:
                    if request.headers['if-unmodified-since'] != last_modified:
                        return codes.precondition_failed


        # ### 404 Not Found
        if self.not_found(request, response):
            return codes.not_found

        # ### 410 Gone
        if self.gone(request, response, *args, **kwargs):
            return codes.gone

        if self.precondition_failed(request, response):
            return codes.precondition_failed

        # ### Call Request Method Handler
        handler_output = getattr(self, request.method.lower())(request,
            response, *args, **kwargs)

        # TODO implement post request method handling header augmentation
        if self.use_etags and 'etag' not in response.headers:
            pass

        elif self.use_last_modified and 'last-modified' not in response.headers:
            pass

        return handler_output

    # ## Request Method Handlers

    # ### _HEAD_ Request Handler
    # Default handler for _HEAD_ requests. For this to be available,
    # a _GET_ handler must be defined.
    def head(self, request, response, *args, **kwargs):
        self.get(request, response, *args, **kwargs)
        response.data = ''

    # ### _OPTIONS_ Request Handler
    # Default handler _OPTIONS_ requests.
    def options(self, request, response, *args, **kwargs):
        response.headers['Allow'] = ', '.join(sorted(self.allowed_methods))
        response.headers['Content-Length'] = 0
        # HTTP/1.1
        response.headers['Cache-Control'] = 'no-cache'
        # HTTP/1.0
        response.headers['Pragma'] = 'no-cache'



    # ## Response Status Code Handlers
    # Performs checks for validate each check during request
    # and response processing.

    # ### Service Unavailable
    # Checks if the service is unavailable based on the `offline` flag.
    # Set the `Retry-After` header if possible to inform clients when
    # the resource is expected to be available.
    # See also: `offline`
    def service_unavailable(self, request, response):
        if self.offline:
            if type(self.offline) is int and self.offline > 0:
                retry = self.offline
            elif type(self.offline) is datetime:
                retry = http_date(self.offline)
            else:
                retry = None

            if retry:
                response.headers['retry-after'] = retry
            return True
        return False

    # ### Unauthorized
    # Checks if the request is authorized to access this resource.
    # Default is a no-op.
    def unauthorized(self, request, response):
        return False

    # ### Forbidden
    # Checks if the request is forbidden. Default is a no-op.
    def forbidden(self, request, response, *args, **kwargs):
        return False

    # ### Too Many Requests
    # Checks if this request is rate limited. Default is a no-op.
    def too_many_requests(self, request, response, *args, **kwargs):
        return False

    # ### Request Entity Too Large
    # Check if the request entity is too large to process.
    def request_entity_too_large(self, request, response):
        if self.max_request_entity_length:
            if self.max_request_entity_length > request.content_length:
                return True

    # ### Method Not Allowed
    # Check if the request method is not allowed.
    def method_not_allowed(self, request, response):
        if request.method not in self.allowed_methods:
            response.headers['allow'] = ', '.join(sorted(self.allowed_methods))
            return True
        return False

    # ### Unsupported Media Type
    # Check if this resource can process the request entity body. Note
    # `Content-Type` is set as the empty string, so ensure it is not falsy
    # when processing it.
    def unsupported_media_type(self, request, response):
        if 'content-type' in request.headers and request.content_type:
            if not self.content_type_supported(request, response):
                return True

            if 'content-encoding' in request.headers:
                if not self.content_encoding_supported(request, response):
                    return True

            if 'content-language' in request.headers:
                if not self.content_language_supported(request, response):
                    return True

        return False

    # ### Not Acceptable
    # Check if this resource can return an acceptable response.
    def not_acceptable(self, request, response):
        if 'accept' in request.headers:
            if not self.accept_type_supported(request, response):
                return True

        if 'accept-language' in request.headers:
            if not self.accept_language_supported(request, response):
                return True

        if 'accept-charset' in request.headers:
            if not self.accept_charset_supported(request, response):
                return True

        if 'accept-encoding' in request.headers:
            if not self.accept_encoding_supported(request, response):
                return True

        return False

    # ### Not Found
    # Checks if the requested resource exists.
    def not_found(self, request, response, *args, **kwargs):
        return False

    # ### Gone
    # Checks if the resource _no longer_ exists.
    def gone(self, request, response, *args, **kwargs):
        return False


    # ## Request Accept-* handlers
    # Checks if the requested `Accept` mimetype is supported.
    def accept_type_supported(self, request, response):
        for mt in request.accept_mimetypes:
            if mt in self.supported_accept_types:
                response._accept_type = mt
                return True
        else:
            # **TODO** Only if `Accept` explicitly contains a `*/*;q=0.0`
            # does it preclude from returning a non-matching mimetype.
            # This may be desirable behavior (or not), so add this as an
            # option, e.g. `force_accept_type`
            if not request.accept_mimetypes['*/*'] == 0:
                return False

        # **TODO** Should a header be set notifying which are acceptable?
        response._accept_type = self.supported_content_types[0]
        return True

    # Checks if the requested `Accept-Charset` is supported.
    def accept_charset_supported(self, request, response):
        return True

    # Checks if the requested `Accept-Encoding` is supported.
    def accept_encoding_supported(self, request, response):
        return True

    # Checks if the requested `Accept-Language` is supported.
    def accept_language_supported(self, request, response):
        return True


    # ## Conditionl Request Handlers

    def precondition_required(self, request, response, *args, **kwargs):
        if self.require_conditional_request:
            if self.use_etags and 'if-match' not in request.headers:
                response.data = 'This request is required to be conditional; '\
                    'try using "If-Match"'
                return True
            if self.use_last_modified and 'if-unmodified-since' not in request.headers:
                response.data = 'This request is required to be conditional; '\
                    'try using "If-Unmodified-Since"'
                return True
        return False

    def precondition_failed(request, response, *args, **kwargs):
        pass

    # ### Calculate ETag
    # Calculates an etag for the requested entity.
    # Provides the client an entity tag for future conditional
    # requests.
    # For GET and HEAD requests the `If-None-Match` header may be
    # set to check if the entity has changed since the last request.
    # For PUT, PATCH, and DELETE requests, the `If-Match` header may be
    # set to ensure the entity is the same as the cllient's so the current
    # operation is valid (optimistic concurrency).
    def get_etag(self, request, *args, **kwargs):
        pass

    # ### Calculate Last Modified Datetime
    # Calculates the last modified time for the requested entity.
    # Provides the client the last modified of the entity for future
    # conditional requests.
    def get_last_modified(self, request, *args, **kwargs):
        pass

    # ### Calculate Expiry Datetime
    # Gets the expiry date and time for the requested entity.
    # Informs the client when the entity will be invalid. This is most
    # useful for clients to only refresh when they need to, otherwise the
    # client's local cache is used.
    def get_expiry(self, request, *args, **kwargs):
        pass


    # ## Entity Content-* handlers
    def content_type_supported(self, request, response, *args, **kwargs):
        return request.mimetype in self.supported_content_types

    def content_encoding_supported(self, request, response, *args, **kwargs):
        return True

    def content_language_supported(self, request, response, *args, **kwargs):
        return True
