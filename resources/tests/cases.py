import unittest
from calendar import timegm
from django.test.client import RequestFactory
from resources.models import Resource
from resources.http import codes

class ResourceTestCase(unittest.TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_default(self):
        "Tests for the default Resource which is very limited."
        resource = Resource()

        self.assertEqual(resource.allowed_methods, ('OPTIONS',))

        request = self.factory.request(REQUEST_METHOD='OPTIONS')
        response = resource(request)
        self.assertEqual(response.status_code, 200)

        # Try another non-default method
        request = self.factory.request()
        response = resource(request)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response['Allow'], 'OPTIONS')

        class PatchResource(Resource):
            allowed_methods = ('PATCH', 'OPTIONS')

            def patch(self, request, response):
                response.status_code = codes.no_content

        resource = PatchResource()

        request = self.factory.request(REQUEST_METHOD='OPTIONS')
        response = resource(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Accept-Patch'], 'application/json')

    def test_service_unavailable(self):
        "Test service availability."
        class IndefiniteUnavailableResource(Resource):
            unavailable = True

        resource = IndefiniteUnavailableResource()

        request = self.factory.request()
        response = resource(request)
        self.assertEqual(response.status_code, 503)
        self.assertTrue('Retry-After' not in response)

        class DeltaUnavailableResource(Resource):
            unavailable = 20

        resource = DeltaUnavailableResource()

        request = self.factory.request()
        response = resource(request)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response['Retry-After'], '20')

        from datetime import datetime, timedelta
        from django.utils.http import http_date

        future = datetime.now() + timedelta(seconds=20)

        class DatetimeUnavailableResource(Resource):
            unavailable = future

        resource = DatetimeUnavailableResource()

        request = self.factory.request()
        response = resource(request)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response['Retry-After'], http_date(timegm(future.utctimetuple())))

    def test_unsupported_media_type(self):
        "Test various Content-* combinations."
        class ReadOnlyResource(Resource):
            def post(self, request, response, *args, **kwargs):
                response.status_code = codes.no_content

        resource = ReadOnlyResource()

        # Works..
        request = self.factory.post('/', data='{"message": "hello world"}', content_type='application/json; charset=utf-8')
        response = resource(request)
        self.assertEqual(response.status_code, 204)

        # Unsupported Media Type
        request = self.factory.post('/', data='<message>hello world</message>', content_type='application/xml')
        response = resource(request)
        self.assertEqual(response.status_code, 415)

    def test_not_acceptable(self):
        "Test various Accept-* combinations."
        class ReadOnlyResource(Resource):
            def get(self, request, response, *args, **kwargs):
                return '{}'

        resource = ReadOnlyResource()

        # Non-explicit
        request = self.factory.request()
        response = resource(request)
        self.assertEqual(response.status_code, 200)

        request = self.factory.request(HTTP_ACCEPT='application/json,application/xml;q=0.9,*/*;q=0.8')
        response = resource(request)
        self.assertEqual(response.status_code, 200)

        request = self.factory.request(HTTP_ACCEPT='text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0')
        response = resource(request)
        self.assertEqual(response.status_code, 406)

        request = self.factory.request(HTTP_ACCEPT='*/*')
        response = resource(request)
        self.assertEqual(response.status_code, 200)

    def test_request_entity_too_large(self):
        "Test request entity too large."
        class TinyResource(Resource):
            max_request_entity_length = 20

            def post(self, request, response, *args, **kwargs):
                response.status_code = codes.no_content

        resource = TinyResource()

        request = self.factory.post('/', data='{"message": "hello"}', content_type='application/json')
        response = resource(request)
        self.assertEqual(response.status_code, 204)

        request = self.factory.post('/', data='{"message": "hello world"}', content_type='application/json')
        response = resource(request)
        self.assertEqual(response.status_code, 413)

    def test_rate_limit(self):
        """Test a global rate limiting implementation.

        This test will take 3 seconds to run to mimic request handling over
        time.
        """
        import time
        from datetime import datetime

        class RateLimitResource(Resource):
            rate_limit_count = 10
            rate_limit_seconds = 2

            # Keep track of requests globally for the resource.. only for test
            # purposes, not thread-safe
            request_frame_start = datetime.now()
            request_count = 0

            def check_too_many_requests(self, request, response, *args, **kwargs):
                interval = (datetime.now() - self.request_frame_start).seconds
                self.request_count += 1

                # Reset frame if the interval is greater than the rate limit seconds,
                # i.e on the 3 second in this test
                if interval > self.rate_limit_seconds:
                    self.request_frame_start = datetime.now()
                    self.request_count = 1

                # Throttle
                elif self.request_count > self.rate_limit_count and interval <= self.rate_limit_seconds:
                    return True
                return False


        resource = RateLimitResource()

        request = self.factory.request(REQUEST_METHOD='OPTIONS')

        for _ in xrange(0, 10):
            response = resource(request)
            self.assertEqual(response.status_code, 200)

        time.sleep(1)

        for _ in xrange(0, 10):
            response = resource(request)
            self.assertEqual(response.status_code, 429)

        time.sleep(2)

        for _ in xrange(0, 10):
            response = resource(request)
            self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(ResourceTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
