import datetime
import io
import logging
import re

from urllib3._collections import HTTPHeaderDict

from requests.adapters import BaseAdapter
from requests.models import Response
from requests.utils import get_encoding_from_headers
from requests.cookies import extract_cookies_to_jar

try:
    from http.client import responses
except ImportError:
    from httplib import responses

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

try:
    from urllib.parse import unquote
except ImportError:
    from urllib2 import unquote as unquote2

    def unquote(s, encoding):
        return unquote2(s.decode(encoding))


try:
    timedelta_total_seconds = datetime.timedelta.total_seconds
except AttributeError:

    def timedelta_total_seconds(timedelta):
        return (
            timedelta.microseconds
            + 0.0
            + (timedelta.seconds + timedelta.days * 24 * 3600) * 10 ** 6
        ) / 10 ** 6


logger = logging.getLogger(__name__)


class Content(object):
    def __init__(self, content, length=None):
        self._read = 0
        if isinstance(content, bytes):
            self._bytes = io.BytesIO(content)
            self._len = len(content)
        else:
            self._bytes = content
            self._len = length

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

    def close(self):
        self._bytes.close()


class MockObject(object):
    def __getattr__(self, name):
        setattr(self, name, MockObject())
        return getattr(self, name)


def make_headers(headers):
    if hasattr(headers, "items"):
        headers = headers.items()
    header_dict = HTTPHeaderDict()
    for key, value in headers:
        header_dict.add(key, value)
    return header_dict


class WSGIAdapter(BaseAdapter):
    server_protocol = "HTTP/1.1"
    wsgi_version = (1, 0)
    status_reply_pattern = re.compile(r'(\d{3})\s(.*)')

    def __init__(
        self,
        app,
        multiprocess=False,
        multithread=False,
        run_once=False,
        log_function=None,
    ):
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
            data = b""
        elif isinstance(request.body, str):
            data = request.body.encode("utf-8")
        else:
            data = request.body

        if isinstance(data, bytes):
            length = len(data)
        else:
            length = int(request.headers.get("Content-Length"))

        environ = {
            "CONTENT_TYPE": request.headers.get("Content-Type", ""),
            "CONTENT_LENGTH": length,
            "PATH_INFO": unquote(urlinfo.path, encoding="latin-1"),
            "SCRIPT_NAME": "",
            "REQUEST_METHOD": request.method,
            "SERVER_NAME": urlinfo.hostname,
            "QUERY_STRING": urlinfo.query,
            "SERVER_PORT": str(
                urlinfo.port or (443 if urlinfo.scheme == "https" else 80)
            ),
            "SERVER_PROTOCOL": self.server_protocol,
            "wsgi.version": self.wsgi_version,
            "wsgi.input": Content(data, length),
            "wsgi.errors": self.errors,
            "wsgi.multiprocess": self.multiprocess,
            "wsgi.multithread": self.multithread,
            "wsgi.run_once": self.run_once,
            "wsgi.url_scheme": urlinfo.scheme,
        }

        environ.update(
            dict(
                ("HTTP_{0}".format(name).replace("-", "_").upper(), value)
                for name, value in request.headers.items()
            )
        )

        response = Response()
        resp = MockObject()

        def start_response(status, headers, exc_info=None):
            headers = make_headers(headers)
            response.status_code = int(match.group(1))
            response.reason = match.group(2)
            response.headers = headers
            resp._original_response.msg = headers
            extract_cookies_to_jar(response.cookies, request, resp)
            response.encoding = get_encoding_from_headers(response.headers)
            response.elapsed = datetime.datetime.utcnow() - start
            self._log(response)

        response.request = request
        response.url = request.url

        response.raw = Content(b"".join(self.app(environ, start_response)))
        response.raw._original_response = resp._original_response

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

        summary = "{status} {method} {url} ({host}) {time}ms".format(
            status=response.status_code,
            method=response.request.method,
            url=response.request.path_url,
            host=urlparse(response.url).hostname,
            time=round(timedelta_total_seconds(response.elapsed) * 1000, 2),
        )

        log(summary)
