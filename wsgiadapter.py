import datetime
import io
import logging

from requests.adapters import BaseAdapter
from requests.models import Response
from requests.structures import CaseInsensitiveDict
from requests.utils import get_encoding_from_headers

try:
    from http.client import responses
except ImportError:
    from httplib import responses

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

try:
    timedelta_total_seconds = datetime.timedelta.total_seconds
except AttributeError:
    def timedelta_total_seconds(timedelta):
        return (
            timedelta.microseconds + 0.0 +
            (timedelta.seconds + timedelta.days * 24 * 3600) * 10 ** 6) / 10 ** 6


logger = logging.getLogger(__name__)


class Content(object):

    def __init__(self, content):
        self._len = len(content)
        self._read = 0
        self._bytes = io.BytesIO(content)

    def __len__(self):
        return self._len

    def read(self, amt=None):
        if amt:
            self._read += amt
        return self._bytes.read(amt)

    def readline(self):
        line = self._bytes.readline()
        self._read += len(line)
        return line

    def stream(self, amt=None, decode_content=None):
        while self._read < self._len:
            yield self.read(amt)

    def release_conn(self):
        pass


class WSGIAdapter(BaseAdapter):
    server_protocol = 'HTTP/1.1'
    wsgi_version = (1, 0)

    def __init__(self, app, multiprocess=False, multithread=False, run_once=False, log_function=None):
        self.app = app
        self.multiprocess = multiprocess
        self.multithread = multithread
        self.run_once = run_once
        self._log = log_function or self._log
        self.errors = io.BytesIO()

    def send(self, request, *args, **kwargs):
        start = datetime.datetime.utcnow()

        urlinfo = urlparse(request.url)

        if not request.body:
            data = b''
        # requests>=2.11.0 makes request body a bytes object which no longer needs
        # encoding
        elif isinstance(request.body, bytes):
            data = request.body
        else:
            data = request.body.encode('utf-8')

        environ = {
            'CONTENT_TYPE': request.headers.get('Content-Type', 'text/plain'),
            'CONTENT_LENGTH': len(data),
            'PATH_INFO': urlinfo.path,
            'REQUEST_METHOD': request.method,
            'SERVER_NAME': urlinfo.hostname,
            'QUERY_STRING': urlinfo.query,
            'SERVER_PORT': urlinfo.port or ('443' if urlinfo.scheme == 'https' else '80'),
            'SERVER_PROTOCOL': self.server_protocol,
            'wsgi.version': self.wsgi_version,
            'wsgi.url_scheme': urlinfo.scheme,
            'wsgi.input': Content(data),
            'wsgi.errors': self.errors,
            'wsgi.multiprocess': self.multiprocess,
            'wsgi.multithread': self.multithread,
            'wsgi.run_once': self.run_once,
            'wsgi.url_scheme': urlinfo.scheme,
        }

        environ.update(dict(
            ('HTTP_{0}'.format(name).replace('-', '_').upper(), value)
            for name, value in request.headers.items()
        ))

        response = Response()

        def start_response(status, headers, exc_info=None):
            response.status_code = int(status.split(' ')[0])
            response.reason = responses.get(response.status_code, 'Unknown Status Code')
            response.headers = CaseInsensitiveDict(headers)
            response.encoding = get_encoding_from_headers(response.headers)
            response.elapsed = datetime.datetime.utcnow() - start
            self._log(response)

        response.request = request
        response.url = request.url

        response.raw = Content(b''.join(self.app(environ, start_response)))

        return response

    def close(self):
        pass

    def _log(self, response):
        if response.status_code < 400:
            log = logger.info
        elif response.status_code < 500:
            log = logger.warning
        else:
            log = logger.error

        summary = '{status} {method} {url} ({host}) {time}ms'.format(
            status=response.status_code,
            method=response.request.method,
            url=response.request.path_url,
            host=urlparse(response.url).hostname,
            time=round(timedelta_total_seconds(response.elapsed) * 1000, 2),
        )

        log(summary)
