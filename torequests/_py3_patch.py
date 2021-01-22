# here for python3 patch avoid of python2 SyntaxError
import asyncio
from functools import wraps
from inspect import isawaitable
from json import loads
from logging import getLogger
from typing import Coroutine, Tuple, Type

from aiohttp import ClientResponse

# python3.7+ 's asyncio.all_tasks'
try:
    _py36_all_task_patch = asyncio.all_tasks
except (ImportError, AttributeError):
    _py36_all_task_patch = asyncio.Task.all_tasks

logger = getLogger("torequests")
NotSet = object()

try:
    import uvloop
    from asyncio import set_event_loop_policy
    set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    logger.debug("Not found uvloop, using the default event loop.")


def _new_future_await(self):
    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(None, self.result, self._timeout)
    for i in future:
        yield i
    return self.x


class NewResponse(ClientResponse):
    """Wrap aiohttp's ClientResponse like requests's Response."""
    # 'strict' / 'ignore' / 'replace'
    DEFAULT_DECODE_ERRORS = 'strict'
    referer_info = None

    def __init__(self, method, url, *, writer, continue100, timer, request_info,
                 traces, loop, session) -> None:
        self._encoding = None
        super().__init__(method=method,
                         url=url,
                         writer=writer,
                         continue100=continue100,
                         timer=timer,
                         request_info=request_info,
                         traces=traces,
                         loop=loop,
                         session=session)

    @property
    def url(self):
        return self._url

    @property
    def status_code(self):
        return self.status

    def __repr__(self):
        return "<%s [%s]>" % (self.__class__.__name__, self.status)

    def __bool__(self):
        return self.ok

    def __iter__(self):
        """Allows you to use a response as an iterator."""
        return self.iter_content(128)

    @property
    def ok(self):
        return self.status in range(200, 400)

    @property
    def is_redirect(self):
        """True if this Response is a well-formed HTTP redirect that could have
        been processed automatically (by :meth:`Session.resolve_redirects`).
        """
        return "location" in self.headers and self.status in range(300, 400)

    @property
    def encoding(self):
        if not self._encoding:
            self._encoding = self.get_encoding()
        return self._encoding

    @encoding.setter
    def encoding(self, encoding):
        self._encoding = encoding
        return encoding

    @property
    def text(self):
        return self._body.decode(self.encoding, self.DEFAULT_DECODE_ERRORS)

    def json(self, encoding=None, loads=loads):
        return loads(
            self._body.decode(encoding or self.encoding,
                              errors=self.DEFAULT_DECODE_ERRORS))

    def release(self) -> None:
        super().release()
        # set content as bytes
        setattr(self, 'content', self._body)
        # set url as string
        setattr(self, '_url', str(self._url))


def retry(tries=1,
          exceptions: Tuple[Type[BaseException]] = (Exception,),
          catch_exception=False):

    def wrapper(function):

        @wraps(function)
        def retry_sync(*args, **kwargs):
            for _ in range(tries):
                try:
                    return function(*args, **kwargs)
                except exceptions as err:
                    error = err
            if catch_exception:
                return error
            raise error

        @wraps(function)
        async def retry_async(*args, **kwargs):
            for _ in range(tries):
                try:
                    return await function(*args, **kwargs)
                except exceptions as err:
                    error = err
            if catch_exception:
                return error
            raise error

        if asyncio.iscoroutinefunction(function):
            return retry_async
        else:
            return retry_sync

    return wrapper


def _exhaust_simple_coro(coro: Coroutine):
    """Run coroutines without event loop, only support simple coroutines which can run without future.
    Or it will raise RuntimeError: await wasn't used with future."""
    while True:
        try:
            coro.send(None)
        except StopIteration as e:
            return e.value


async def _ensure_can_be_await(obj):
    if isawaitable(obj):
        return await obj
    return obj
