from handlers.handlers import app
import urllib.parse as url
from tornado.testing import AsyncHTTPTestCase
import unittest


class RequestsTestCase(AsyncHTTPTestCase):
    def get_app(self):
        return app

    def test_index(self):
        response = self.fetch('/')
        self.assertEqual(response.code, 200)

    def test_notification(self):
        response = self.fetch('/notification?id=1&message=test_message')
        self.assertEqual(response.code, 200)


if __name__ == '__main__':
    unittest.main()
