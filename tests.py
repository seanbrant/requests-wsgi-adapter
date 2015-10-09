import json
import unittest

import requests

from wsgiadapter import WsgiAdapter


class WSGITestHandler(object):

    def __call__(self, environ, start_response):
        start_response('200 OK', {'Content-Type': 'application/json'})
        return [bytes(json.dumps({
            'result': '__works__',
            'body': environ['wsgi.input'].read().decode('utf-8'),
            'content_type': environ['CONTENT_TYPE'],
            'content_length': environ['CONTENT_LENGTH'],
            'path_info': environ['PATH_INFO'],
            'request_method': environ['REQUEST_METHOD'],
            'server_name': environ['SERVER_NAME'],
            'server_port': environ['SERVER_PORT'],
        }).encode('utf-8'))]


class WsgiAdapterTest(unittest.TestCase):

    def setUp(self):
        self.session = requests.session()
        self.session.mount('http://localhost', WsgiAdapter(app=WSGITestHandler()))
        self.session.mount('https://localhost', WsgiAdapter(app=WSGITestHandler()))

    def test_basic_response(self):
        response = self.session.get('http://localhost/index', headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(response.json()['result'], '__works__')
        self.assertEqual(response.json()['content_type'], 'application/json')
        self.assertEqual(response.json()['path_info'], '/index')
        self.assertEqual(response.json()['request_method'], 'GET')
        self.assertEqual(response.json()['server_name'], 'localhost')

    def test_request_with_body(self):
        response = self.session.post('http://localhost/index', data='__test__')
        self.assertEqual(response.json()['body'], '__test__')
        self.assertEqual(response.json()['content_length'], len('__test__'))

    def test_request_with_https(self):
        response = self.session.get('https://localhost/index')
        self.assertEqual(response.json()['server_port'], 443)
