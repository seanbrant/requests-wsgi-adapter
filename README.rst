  >>> from wsgiadapter import WSGIAdapter
  >>> s = requests.Session()
  >>> s.mount('http://staging/', WSGIAdapter())
  >>> s.get('http://staging/index.html')
  <Response [200]>
