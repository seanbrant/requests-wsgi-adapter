import json
import unittest

import requests

import httpbin

from wsgiadapter import WSGIAdapter


class WSGITestHandler(object):

    def __call__(self, environ, start_response):
        headers = {'Content-Type': 'application/json'}
        if environ['PATH_INFO'].startswith('/cookies'):
            headers['Set-Cookie'] = 'c1=v1; Path=/, c2=v2; Path=/'
        start_response('200 OK', headers, exc_info=None)
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


class WSGIAdapterTest(unittest.TestCase):

    def setUp(self):
        self.session = requests.session()
        self.session.mount('http://localhost', WSGIAdapter(app=WSGITestHandler()))
        self.session.mount('https://localhost', WSGIAdapter(app=WSGITestHandler()))

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
        self.assertEqual(response.json()['server_port'], '443')

    def test_request_with_json(self):
        response = self.session.post('http://localhost/index', json={})
        self.assertEqual(response.json()['body'], '{}')
        self.assertEqual(response.json()['content_length'], len('{}'))

    def test_request_with_cookies(self):
        response = self.session.get('http://localhost/cookies')
        self.assertEqual(response.cookies['c1'], 'v1')
        self.assertEqual(self.session.cookies['c2'], 'v2')


def test_multiple_cookies():
    session = requests.session()
    session.mount('http://localhost', WSGIAdapter(app=httpbin.app))
    session.get(
        "http://localhost/cookies/set?flimble=floop&flamble=flaap")
    response = session.get("http://localhost/cookies")
    assert response.json() == {
        'cookies': {'flimble': 'floop', 'flamble': 'flaap'}}


def test_delete_cookies():
    session = requests.session()
    session.mount('http://localhost', WSGIAdapter(app=httpbin.app))
    session.get(
        "http://localhost/cookies/set?flimble=floop&flamble=flaap")
    response = session.get("http://localhost/cookies")
    assert response.json() == {
        'cookies': {'flimble': 'floop', 'flamble': 'flaap'}}
    response = session.get(
        "http://localhost/cookies/delete?flimble")
    result = response.json()
    expected = {'cookies': {'flamble': 'flaap'}}
    assert result == expected, result
