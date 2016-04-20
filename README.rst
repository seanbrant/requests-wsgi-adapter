.. code-block:: python

  >>> from django.core.wsgi import get_wsgi_application
  >>>
  >>> import requests
  >>> import wsgiadapter
  >>>
  >>> s = requests.Session()
  >>> s.mount('http://staging/', wsgiadapter.WSGIAdapter(get_wsgi_application()))
  >>> s.get('http://staging/index')
  <Response [200]>
