# here for python3 patch avoid of python2 SyntaxError
import asyncio
import json


def new_future_await(self):
    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(None, self.result, self._timeout)
    for i in future:
        yield i
    return self.x


def aiohttp_response_patch(ClientResponse):
    # conver ClientResponse attribute into requests-like, for py3.5+
    ClientResponse.encoding = property(
        lambda self: self.request_encoding or self.get_encoding())
    ClientResponse.text = property(
        lambda self: self.content.decode(self.encoding))
    ClientResponse.url_string = property(lambda self: str(self._url))
    ClientResponse.status_code = property(lambda self: self.status)
    ClientResponse.ok = property(lambda self: self.status in range(200, 300))
    ClientResponse.json = lambda self, encoding=None, loads=json.loads: loads(
        self.content.decode(encoding or self.encoding))
