import unittest
from calendar import timegm
from django.test.client import RequestFactory
from restlib2.resources import Resource
from restlib2.http import codes


class ResourceTestCase(unittest.TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_default(self):
        "Tests for the default Resource which is very limited."
        # Default resource
        resource = Resource()

        # Populated implicitly via the metaclass..
        self.assertEqual(resource.allowed_methods, ('OPTIONS',))

        # OPTIONS is successful, default response with no content is a 204
        request = self.factory.options('/')
        response = resource(request)
        self.assertEqual(response.status_code, codes.ok)

        # Try another non-default method
        request = self.factory.get('/')
        response = resource(request)
        self.assertEqual(response.status_code, codes.method_not_allowed)
        self.assertEqual(response['Allow'], 'OPTIONS')

    def test_default_head(self):
        class GetResource(Resource):
            def get(self, request):
                return '{}'

        resource = GetResource()

        request = self.factory.head('/')
        response = resource(request)
        self.assertEqual(response.status_code, codes.ok)
        self.assertEqual(response.content, '')

    def test_default_patch(self):
        # Resources supporting PATCH requests should have an additional
        # header in the response from an OPTIONS request
        class PatchResource(Resource):
            def patch(self, request):
                pass

        resource = PatchResource()
        request = self.factory.options('/')
        response = resource(request)
        self.assertEqual(response.status_code, codes.ok)
        self.assertEqual(response['Accept-Patch'], 'application/json')

    def test_service_unavailable(self):
        "Test service unavailability."
        class IndefiniteUnavailableResource(Resource):
            unavailable = True

        resource = IndefiniteUnavailableResource()

        # Simply setting `unavailable` to True will provide a 'Retry-After'
        # header
        request = self.factory.request()
        response = resource(request)
        self.assertEqual(response.status_code, codes.service_unavailable)
        self.assertTrue('Retry-After' not in response)

    def test_service_unavailable_retry_seconds(self):
        "Test service unavailability with seconds."
        class DeltaUnavailableResource(Resource):
            unavailable = 20

        resource = DeltaUnavailableResource()

        # Set unavailable, but with a specific number of seconds to retry
        # after
        request = self.factory.request()
        response = resource(request)
        self.assertEqual(response.status_code, codes.service_unavailable)
        self.assertEqual(response['Retry-After'], '20')

    def test_service_unavailable_retry_date(self):
        "Test service unavailability with date."
        from datetime import datetime, timedelta
        from django.utils.http import http_date

        future = datetime.now() + timedelta(seconds=20)

        class DatetimeUnavailableResource(Resource):
            unavailable = future

        resource = DatetimeUnavailableResource()

        request = self.factory.request()
        response = resource(request)
        self.assertEqual(response.status_code, codes.service_unavailable)
        self.assertEqual(response['Retry-After'], http_date(timegm(future.utctimetuple())))

    def test_unsupported_media_type(self):
        "Test various Content-* combinations."
        class NoOpResource(Resource):
            def post(self, request, *args, **kwargs):
                pass

        resource = NoOpResource()

        # Works.. default accept-type is application/json
        request = self.factory.post('/', data='{"message": "hello world"}', content_type='application/json; charset=utf-8')
        response = resource(request)
        self.assertEqual(response.status_code, codes.no_content)

        # Does not work.. XML not accepted by default
        request = self.factory.post('/', data='<message>hello world</message>', content_type='application/xml')
        response = resource(request)
        self.assertEqual(response.status_code, codes.unsupported_media_type)

    def test_not_acceptable(self):
        "Test Accept header."
        class ReadOnlyResource(Resource):
            def get(self, request, *args, **kwargs):
                return '{}'

        resource = ReadOnlyResource()

        # No accept-type is specified, defaults to highest priority one
        # for resource
        request = self.factory.request()
        response = resource(request)
        self.assertEqual(response.status_code, codes.ok)

        # Explicit accept header, application/json wins since it's equal
        # priority and supported
        request = self.factory.request(HTTP_ACCEPT='application/json,application/xml;q=0.9,*/*;q=0.8')
        response = resource(request)
        self.assertEqual(response.status_code, codes.ok)

        # No acceptable type list, */* has an explicit quality of 0 which
        # does not allow the server to use an alternate content-type
        request = self.factory.request(HTTP_ACCEPT='text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0')
        response = resource(request)
        self.assertEqual(response.status_code, codes.not_acceptable)

        # Like the first one, but an explicit "anything goes"
        request = self.factory.request(HTTP_ACCEPT='*/*')
        response = resource(request)
        self.assertEqual(response.status_code, codes.ok)

    def test_request_entity_too_large(self):
        "Test request entity too large."
        class TinyResource(Resource):
            max_request_entity_length = 20

            def post(self, request, *args, **kwargs):
                pass

        resource = TinyResource()

        # No problem..
        request = self.factory.post('/', data='{"message": "hello"}', content_type='application/json')
        response = resource(request)
        self.assertEqual(response.status_code, codes.no_content)

        # Too large
        request = self.factory.post('/', data='{"message": "hello world"}', content_type='application/json')
        response = resource(request)
        self.assertEqual(response.status_code, codes.request_entity_too_large)

    def test_too_many_requests(self):
        """Test a global rate limiting implementation.

        This test will take 3 seconds to run to mimic request handling over
        time.
        """
        import time
        from datetime import datetime

        class RateLimitResource(Resource):
            # Maximum of 10 requests within a 2 second window
            rate_limit_count = 10
            rate_limit_seconds = 2

            # Keep track of requests globally for the resource.. only for test
            # purposes, not thread-safe
            request_frame_start = datetime.now()
            request_count = 0

            # Implement rate-limiting logic
            def is_too_many_requests(self, request, *args, **kwargs):
                # Since the start of the frame, calculate the amount of time
                # that has passed
                interval = (datetime.now() - self.request_frame_start).seconds
                # Increment the request count
                self.request_count += 1

                # Reset frame if the interval is greater than the rate limit seconds,
                # i.e on the 3rd second in this test
                if interval > self.rate_limit_seconds:
                    self.request_frame_start = datetime.now()
                    self.request_count = 1
                # ..otherwise throttle if the count is greater than the limit
                elif self.request_count > self.rate_limit_count:
                    return True
                return False


        resource = RateLimitResource()

        request = self.factory.request(REQUEST_METHOD='OPTIONS')

        # First ten requests are ok
        for _ in xrange(0, 10):
            response = resource(request)
            self.assertEqual(response.status_code, codes.ok)

        # Mimic a slight delay
        time.sleep(1)

        # Another 10 all get throttled..
        for _ in xrange(0, 10):
            response = resource(request)
            self.assertEqual(response.status_code, codes.too_many_requests)

        # Another two seconds exceeds the frame, should be good to go
        time.sleep(2)

        for _ in xrange(0, 10):
            response = resource(request)
            self.assertEqual(response.status_code, codes.ok)


    def test_precondition_required(self):
        "Reject non-idempotent requests without the use of a conditional header."

        class PreconditionResource(Resource):
            # Either etags or last-modified must be used otherwise it
            # is not enforced
            use_etags = True
            require_conditional_request = True

            def patch(self, request):
                pass

            def put(self, request):
                pass

            def delete(self, request):
                pass

            def get_etag(self, request, *args, **kwargs):
                return 'abc123'


        resource = PreconditionResource()

        # Non-idempotent requests fail without a conditional header, these
        # responses should not be cached
        request = self.factory.put('/', data='{"message": "hello world"}', content_type='application/json')
        response = resource(request)
        self.assertEqual(response.status_code, codes.precondition_required)
        self.assertEqual(response['Cache-Control'], 'no-cache, must-revalidate, max-age=0')

        # Add the correct header for testing the Etag
        request = self.factory.put('/', data='{"message": "hello world"}', content_type='application/json',
                HTTP_IF_MATCH='abc123')
        response = resource(request)
        self.assertEqual(response.status_code, codes.no_content)

        # Idempotent requests, such as DELETE, succeed..
        request = self.factory.delete('/')
        response = resource(request)
        self.assertEqual(response.status_code, codes.no_content)

    def test_precondition_failed_etag(self):
        "Test precondition using etags."
        class PreconditionResource(Resource):
            use_etags = True

            def put(self, request):
                pass

            def get(self, request):
                return '{}'

            def get_etag(self, request, *args, **kwargs):
                return 'abc123'

        resource = PreconditionResource()

        # Send a non-safe request with an incorrect Etag.. fail
        request = self.factory.put('/', data='{"message": "hello world"}',
            content_type='application/json', HTTP_IF_MATCH='"def456"')
        response = resource(request)
        self.assertEqual(response.status_code, codes.precondition_failed)
        self.assertEqual(response['Cache-Control'], 'no-cache, must-revalidate, max-age=0')

        # Incorrect Etag match on GET, updated content is returned
        request = self.factory.get('/', HTTP_IF_NONE_MATCH='"def456"')
        response = resource(request)
        self.assertEqual(response.status_code, codes.ok)

        # Successful Etag match on GET, resource not modified
        request = self.factory.get('/', HTTP_IF_NONE_MATCH='"abc123"')
        response = resource(request)
        self.assertEqual(response.status_code, codes.not_modified)

    def test_precondition_failed_last_modified(self):
        "Test precondition using last-modified dates."
        from datetime import datetime, timedelta
        from django.utils.http import http_date

        last_modified_date = datetime.now()

        class PreconditionResource(Resource):
            use_etags = False
            use_last_modified = True

            def put(self, request):
                pass

            def get(self, request):
                return '{}'

            def get_last_modified(self, request, *args, **kwargs):
                return last_modified_date

        resource = PreconditionResource()

        # Send non-safe request with a old last-modified date.. fail
        if_modified_since = http_date(timegm((last_modified_date - timedelta(seconds=10)).utctimetuple()))
        request = self.factory.put('/', data='{"message": "hello world"}',
            content_type='application/json', HTTP_IF_UNMODIFIED_SINCE=if_modified_since)
        response = resource(request)
        self.assertEqual(response.status_code, codes.precondition_failed)
        self.assertEqual(response['Cache-Control'], 'no-cache, must-revalidate, max-age=0')

        # Old last-modified on GET, updated content is returned
        if_modified_since = http_date(timegm((last_modified_date - timedelta(seconds=10)).utctimetuple()))
        request = self.factory.get('/', HTTP_IF_MODIFIED_SINCE=if_modified_since)
        response = resource(request)
        self.assertEqual(response.status_code, codes.ok)

        # Mimic future request on GET, resource not modified
        if_modified_since = http_date(timegm((last_modified_date + timedelta(seconds=20)).utctimetuple()))
        request = self.factory.get('/', HTTP_IF_MODIFIED_SINCE=if_modified_since)
        response = resource(request)
        self.assertEqual(response.status_code, codes.not_modified)

    def test_cache_control_default(self):
        class CacheableResource(Resource):
            def get(self, request):
                return '{}'

        resource = CacheableResource()

        request = self.factory.get('/')
        response = resource(request)
        self.assertFalse('Cache-Control' in response)

    def test_cache_control_seconds(self):
        class CacheableResource(Resource):
            cache_max_age = 60 * 60 # 1 hour

            def get(self, request):
                return '{}'

        resource = CacheableResource()

        request = self.factory.get('/')
        response = resource(request)
        self.assertEqual(response['Cache-Control'], 'max-age=3600')

    def test_cache_control_date(self):
        from datetime import datetime, timedelta
        from django.utils.http import http_date

        class CacheableResource(Resource):
            cache_type = 'private'
            cache_max_age = timedelta(seconds=60 * 60) # 1 hour

            def get(self, request):
                return '{}'

        resource = CacheableResource()

        request = self.factory.get('/')
        response = resource(request)
        self.assertEqual(response['Cache-Control'], 'private')
        self.assertEqual(response['Expires'], http_date(timegm((datetime.now() + timedelta(hours=1)).utctimetuple())))
