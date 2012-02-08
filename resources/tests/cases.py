import unittest
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request
from resources.models import Resource

class ResourceTestCase(unittest.TestCase):
    def test_default(self):
        "Tests for the default Resource which is very limited."
        params = dict(
            query_string = None,
            method = 'OPTIONS',
            input_stream = None,
            content_type = '',
            content_length = None,
            headers = None,
            data = None,
        )

        resource = Resource()

        environ = EnvironBuilder(**params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 200)

        # Try another non-default method
        params['method'] = 'PUT'

        environ = EnvironBuilder(**params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.headers['allow'], 'OPTIONS')

    def test_content_type(self):
        "Tests for the default Resource which is very limited."
        params = dict(
            query_string = None,
            method = 'OPTIONS',
            input_stream = None,
            content_type = '',
            content_length = None,
            headers = None,
            data = None,
        )

        class ReadOnlyResource(Resource):
            def get(self, request, response, *args, **kwargs):
                return '{}'

        resource = ReadOnlyResource()

        environ = EnvironBuilder(**params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['allow'], 'GET, HEAD, OPTIONS')

        params['method'] = 'GET'
        params['content_type'] = 'application/json; charset=utf-8'
        environ = EnvironBuilder(**params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-length'], '2')
        self.assertEqual(response.data, '{}')

        # Explicit Accept
        params['headers'] = {'Accept': 'application/xml'}
        environ = EnvironBuilder(**params)
        request = environ.get_request(cls=Request)
        response = resource(request)
        self.assertEqual(response.status_code, 406)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(ResourceTestCase)
    unittest.TextTestRunner(verbosity=2).run(suite)
