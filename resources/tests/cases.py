import unittest
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request
from resources.models import Resource
from resources.http import codes

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
        "Test service availability."
        class IndefiniteUnavailableResource(Resource):
            unavailable = True

        resource = IndefiniteUnavailableResource()
        environ = EnvironBuilder(**self.params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 503)
        self.assertTrue('retry-after' not in response.headers)

        class DeltaUnavailableResource(Resource):
            unavailable = 20

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
            unavailable = future

        resource = DatetimeUnavailableResource()
        environ = EnvironBuilder(**self.params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers['retry-after'], http_date(future))

    def test_unsupported_media_type(self):
        "Test various Content-* combinations."
        class ReadOnlyResource(Resource):
            def post(self, request, response, *args, **kwargs):
                response.status = codes.no_content

        resource = ReadOnlyResource()

        self.params['method'] = 'POST'

        # Works..
        self.params['content_type'] = 'application/json; charset=utf-8'
        self.params['data'] = '{"message": "hello world"}'
        environ = EnvironBuilder(**self.params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 204)

        # Unsupported Media Type
        self.params['content_type'] = 'application/xml'
        self.params['data'] = '<message>hello world</message>'
        environ = EnvironBuilder(**self.params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 415)

    def test_not_acceptable(self):
        "Test various Accept-* combinations."
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

        self.params['headers'] = {'Accept': 'application/json,application/xml;q=0.9,*/*;q=0.8'}
        environ = EnvironBuilder(**self.params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 200)

        self.params['headers'] = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        environ = EnvironBuilder(**self.params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 406)

        self.params['headers'] = {'Accept': '*/*'}
        environ = EnvironBuilder(**self.params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 406)

    def test_request_entity_too_large(self):
        "Test request entity too large."
        class TinyResource(Resource):
            max_request_entity_length = 20

            def post(self, request, response, *args, **kwargs):
                response.status = codes.no_content

        resource = TinyResource()

        self.params['method'] = 'POST'
        self.params['content_type'] = 'application/json'

        self.params['data'] = '{"message": "hello"}'
        environ = EnvironBuilder(**self.params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 204)

        self.params['data'] = '{"message": "hello world"}'
        environ = EnvironBuilder(**self.params)
        request = environ.get_request(cls=Request)
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
