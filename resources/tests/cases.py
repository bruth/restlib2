import unittest
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request
from resources.models import Resource

class ResourceTestCase(unittest.TestCase):
    def setUp(self):
        self.params = dict(
            query_string = None,
            method = 'GET',
            input_stream = None,
            content_type = '',
            content_length = None,
            headers = None,
            data = None,
        )

    def test_default(self):
        "Tests for the default Resource which is very limited."
        resource = Resource()

        self.params['method'] = 'OPTIONS'
        environ = EnvironBuilder(**self.params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 200)

        # Try another non-default method
        self.params['method'] = 'GET'
        environ = EnvironBuilder(**self.params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.headers['allow'], 'OPTIONS')

        class MethodsResource(Resource):
            allowed_methods = ('GET',)

            def get(self, request, response, *args, **kwargs):
                return ''

        resource = MethodsResource()
        environ = EnvironBuilder(**self.params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 200)

    def test_service_unavailable(self):
        class IndefiniteUnavailableResource(Resource):
            offline = True

        resource = IndefiniteUnavailableResource()
        environ = EnvironBuilder(**self.params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 503)
        self.assertTrue('retry-after' not in response.headers)

        class DeltaUnavailableResource(Resource):
            offline = 20

        resource = DeltaUnavailableResource()
        environ = EnvironBuilder(**self.params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers['retry-after'], 20)

        from datetime import datetime, timedelta
        from werkzeug.http import http_date

        future = datetime.now() + timedelta(seconds=20)

        class DatetimeUnavailableResource(Resource):
            offline = future

        resource = DatetimeUnavailableResource()
        environ = EnvironBuilder(**self.params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers['retry-after'], http_date(future))

    def test_content_type(self):
        "Test trivial read-only resource with GET, HEAD, and OPTIONS."
        class ReadOnlyResource(Resource):
            def get(self, request, response, *args, **kwargs):
                return '{}'

        resource = ReadOnlyResource()

        self.params['method'] = 'OPTIONS'
        environ = EnvironBuilder(**self.params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['allow'], 'GET, HEAD, OPTIONS')

        self.params['method'] = 'GET'
        self.params['content_type'] = 'application/json; charset=utf-8'
        environ = EnvironBuilder(**self.params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-length'], '2')
        self.assertEqual(response.data, '{}')

    def test_no_accept_headers(self):
        "No Accept-* should pass through."
        class ReadOnlyResource(Resource):
            def get(self, request, response, *args, **kwargs):
                return '{}'

        resource = ReadOnlyResource()

        # Non-explicit
        self.params['method'] = 'GET'
        environ = EnvironBuilder(**self.params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 200)

    def test_accept_headers(self):
        "Process request with Accept-* headers."
        class ReadOnlyResource(Resource):
            def get(self, request, response, *args, **kwargs):
                return '{}'

        resource = ReadOnlyResource()

        self.params['method'] = 'GET'
        self.params['headers'] = {'Accept': 'application/xml'}
        environ = EnvironBuilder(**self.params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 406)

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
            # purposes
            request_frame_start = datetime.now()
            request_count = 0

            def too_many_requests(self, request, response, *args, **kwargs):
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

        self.params['method'] = 'OPTIONS'
        environ = EnvironBuilder(**self.params)
        request = environ.get_request(cls=Request)

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
