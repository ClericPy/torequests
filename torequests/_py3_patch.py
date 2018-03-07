# here for python3 patch avoid of python2 SyntaxError
import asyncio
import json
from functools import wraps


def new_future_await(self):
    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(None, self.result, self._timeout)
    for i in future:
        yield i
    return self.x


def aiohttp_response_patch(ClientResponse):
    # convert ClientResponse attribute into requests-like, for py3.5+
    def _encoding_setter(self, value):
        self.request_encoding = value
        return

    def _encoding_deleter(self):
        self.request_encoding = None
        return

    ClientResponse._json = ClientResponse.json
    ClientResponse._text = ClientResponse.text
    ClientResponse.encoding = property(
        lambda self: self.request_encoding or self.get_encoding())
    ClientResponse.encoding = ClientResponse.encoding.setter(_encoding_setter)
    ClientResponse.encoding = ClientResponse.encoding.deleter(_encoding_deleter)
    ClientResponse.text = property(
        lambda self: self.content.decode(self.encoding))
    ClientResponse.url_string = property(lambda self: str(self._url))
    ClientResponse.status_code = property(lambda self: self.status)
    ClientResponse.ok = property(lambda self: self.status in range(200, 300))
    ClientResponse.json = lambda self, encoding=None, loads=json.loads: loads(
        self.content.decode(encoding or self.encoding))


def aiohttp_unclosed_connection_patch(Connection):
    # avoid the Unclosed connection issue for aiohttp
    def wrapper(function):

        @wraps(function)
        def wrapped(self, *args, **kwargs):
            if self._protocol is not None:
                self.close()
            return function(self, *args, **kwargs)

        return wrapped

    Connection.__del__ = wrapper(Connection.__del__)
