# python3.5+ # pip install uvloop aiohttp.

import asyncio
import json
import time
from functools import wraps

import aiohttp
from aiohttp.client_reqrep import ClientResponse

from .log import dummy_logger

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    dummy_logger.debug('Not found uvloop, using default_event_loop.')

ClientResponse.text = property(lambda self: self.content.decode(self.encoding))
ClientResponse.ok = property(lambda self: self.status in range(200, 300))
ClientResponse.json = lambda self, encoding=None: json.loads(
    self.content.decode(encoding or self.encoding))


class RequestsException(Exception):
    '''self.error for reviewing the source exception.'''

    def __init__(self, error):
        self.__dict__ = error.__dict__
        self.error = error
        self.ok = False

    def __bool__(self):
        return False


class NewTask(asyncio.tasks.Task):
    _PENDING = 'PENDING'
    _CANCELLED = 'CANCELLED'
    _FINISHED = 'FINISHED'
    _RESPONSE_ARGS = ('encoding', 'content')
    callback_result = None

    def __init__(self, coro, return_callback=False, *, loop=None):
        assert asyncio.coroutines.iscoroutine(coro), repr(coro)
        super().__init__(coro, loop=loop)

    @staticmethod
    def wrap_callback(f):
        @wraps(f)
        def wrapped(fut):
            fut.callback_result = f(fut)
            return fut.callback_result
        return wrapped

    @property
    def x(self):
        if self._state == self._PENDING:
            self._loop.run_until_complete(self)
        return self.result()

    def __getattr__(self, name):
        return self.x.__getattribute__(name)

    def __setattr__(self, name, value):
        if name in self._RESPONSE_ARGS:
            self.x.__setattr__(name, value)
        else:
            object.__setattr__(self, name, value)


class Loop():

    def __init__(self, loop=None):
        try:
            self.loop = loop or asyncio.get_event_loop()
            if self.loop.is_running():
                raise NotImplementedError("Cannot use aioutils in "
                                          "asynchroneous environment")
        except NotImplementedError:
            dummy_logger.debug(
                "%s is_running, rebuilding a new loop" % self.loop)
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        self.tasks = []

    def submit(self, coro, callback=None):
        task = NewTask(coro, loop=self.loop)
        if callback:
            if not isinstance(callback, (list, tuple)):
                callback = [callback]
            for fn in callback:
                task.add_done_callback(task.wrap_callback(fn))
        self.tasks.append(task)
        return task

    def submitter(self, f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            return self.submit(f(*args, **kwargs))
        return wrapped

    def clear(self):
        self.tasks.clear()
        return True

    @property
    def x(self):
        return self.run()

    @property
    def todo_tasks(self):
        self.tasks = [
            task for task in self.tasks if task._state == NewTask._PENDING]
        return self.tasks

    def run(self):
        self.loop.run_until_complete(asyncio.gather(*self.todo_tasks))

    async def done(self):
        await asyncio.gather(*self.todo_tasks)


class Requests(Loop):
    '''
        The kwargs is the same as kwargs of aiohttp.ClientSession.
        Sometimes the performance is limited by too large "n" .
    '''
    METH = ('get', 'options', 'head', 'post', 'put', 'patch', 'delete')

    def __init__(self, n=100, session=None, time_interval=0, **kwargs):
        loop = kwargs.get('loop')
        super().__init__(loop=loop)
        self.sem = asyncio.Semaphore(n)
        self.time_interval = time_interval
        if session:
            session._loop = self.loop
            self.session = session
        else:
            self.session = aiohttp.ClientSession(loop=self.loop, **kwargs)
        self._initial_request()

    def _initial_request(self):
        for method in self.METH:
            self.__setattr__('%s' % method, self._mock_request_method(method))

    def _mock_request_method(self, method):
        def _new_request(url, callback=None, **kwargs):
            '''support args: retry, callback, catch_exception'''
            return self.submit(self._request(method, url, **kwargs),
                               callback=callback)
        return _new_request

    async def _request(self, method, url, retry=0, catch_exception=False, **kwargs):
        with await self.sem:
            for retries in range(retry + 1):
                try:
                    async with self.session.request(method, url, **kwargs) as resp:
                        resp.status_code = resp.status
                        resp.content = await resp.read()
                        resp.encoding = kwargs.get(
                            'encoding') or resp._get_encoding()
                        if self.time_interval:
                            await asyncio.sleep(self.time_interval)
                        # resp.__bool__ = lambda x: True
                        return resp
                except Exception as err:
                    error = err
                    continue
            else:
                kwargs['retry'] = retry
                kwargs['catch_exception'] = catch_exception
                error_info = dict(url=url, kwargs=kwargs,
                                  type=type(error), error_msg=str(error))
                error.args = (error_info,)
                dummy_logger.error(
                    'Retry=%s but failed: %s.' %
                    (retry, error_info))
                if catch_exception:
                    return RequestsException(error)
                raise error

    def close(self):
        '''Should be closed[explicit] while using external session or connector,
        instead of close by __del__.'''
        self.session.close()

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
