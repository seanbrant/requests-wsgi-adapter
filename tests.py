# -*- coding: utf-8 -*-
import json
import unittest

import requests
from urllib3._collections import HTTPHeaderDict

from wsgiadapter import WSGIAdapter


class WSGITestHandler(object):
    def __init__(self, extra_headers=None):
        self.extra_headers = extra_headers or tuple()

    def __call__(self, environ, start_response):
        headers = HTTPHeaderDict({'Content-Type': 'application/json'})
        for key, value in self.extra_headers:
            headers.add(key, value)
        start_response('200 OK', headers, exc_info=None)
        return [bytes(json.dumps({
            'result': '__works__',
            'body': environ['wsgi.input'].read().decode('utf-8'),
            'content_type': environ['CONTENT_TYPE'],
            'content_length': environ['CONTENT_LENGTH'],
            'path_info': environ['PATH_INFO'].encode('latin-1').decode('utf-8'),
            'script_name': environ['SCRIPT_NAME'],
            'request_method': environ['REQUEST_METHOD'],
            'server_name': environ['SERVER_NAME'],
            'server_port': environ['SERVER_PORT'],
        }).encode('utf-8'))]


class WSGIAdapterTest(unittest.TestCase):

    def setUp(self):
        self.session = requests.session()
        adapter = WSGIAdapter(app=WSGITestHandler())
        self.session.mount('http://localhost', adapter)
        self.session.mount('http://localhost:5000', adapter)
        self.session.mount('https://localhost', adapter)
        self.session.mount('https://localhost:5443', adapter)

    def test_basic_response(self):
        response = self.session.get('http://localhost/index', headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(response.json()['result'], '__works__')
        self.assertEqual(response.json()['content_type'], 'application/json')
        self.assertEqual(response.json()['script_name'], '')
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

    def test_request_i18n_path(self):
        response = self.session.get('http://localhost/привет', json={})
        self.assertEqual(response.json()['path_info'], u'/привет')
        response = self.session.get('http://localhost/Moselfränkisch', json={})
        self.assertEqual(response.json()['path_info'], u'/Moselfränkisch')

    def test_server_port(self):
        response = self.session.get('http://localhost/index')
        self.assertEqual(response.json()['server_port'], '80')
        response = self.session.get('http://localhost:5000/index')
        self.assertEqual(response.json()['server_port'], '5000')
        response = self.session.get('https://localhost/index')
        self.assertEqual(response.json()['server_port'], '443')
        response = self.session.get('https://localhost:5443/index')
        self.assertEqual(response.json()['server_port'], '5443')


class WSGIAdapterCookieTest(unittest.TestCase):
    def setUp(self):
        app = WSGITestHandler(
            extra_headers=[
                ("Set-Cookie", "c1=v1; Path=/"),
                ("Set-Cookie", "c2=v2; Path=/")])
        self.session = requests.session()
        self.session.mount('http://localhost', WSGIAdapter(app=app))
        self.session.mount('https://localhost', WSGIAdapter(app=app))

    def test_request_with_cookies(self):
        response = self.session.get("http://localhost/cookies")
        self.assertEqual(response.cookies['c1'], 'v1')
        self.assertEqual(self.session.cookies['c1'], 'v1')


def test_multiple_cookies():
    app = WSGITestHandler(
        extra_headers=[
            ("Set-Cookie", "flimble=floop; Path=/"),
            ("Set-Cookie", "flamble=flaap; Path=/")])
    session = requests.session()
    session.mount('http://localhost', WSGIAdapter(app=app))

    session.get(
        "http://localhost/cookies/set?flimble=floop&flamble=flaap")
    assert session.cookies['flimble'] == "floop"
    assert session.cookies['flamble'] == "flaap"


def test_delete_cookies():
    session = requests.session()
    set_app = WSGITestHandler(
        extra_headers=[
            ("Set-Cookie", "flimble=floop; Path=/"),
            ("Set-Cookie", "flamble=flaap; Path=/")])
    delete_app = WSGITestHandler(
        extra_headers=[(
            "Set-Cookie",
            "flimble=; Expires=Thu, 01-Jan-1970 00:00:00 GMT; Max-Age=0; Path=/")])
    session.mount(
        'http://localhost/cookies/set', WSGIAdapter(app=set_app))
    session.mount(
        'http://localhost/cookies/delete', WSGIAdapter(app=delete_app))

    session.get(
        "http://localhost/cookies/set?flimble=floop&flamble=flaap")
    assert session.cookies['flimble'] == "floop"
    assert session.cookies['flamble'] == "flaap"

    session.get(
        "http://localhost/cookies/delete?flimble")
    assert 'flimble' not in session.cookies
    assert session.cookies['flamble'] == "flaap"
