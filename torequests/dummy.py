# python3.5+ # pip install uvloop aiohttp.

import asyncio
import logging
import time
from functools import wraps

import aiohttp

log_level = logging.INFO
logging.basicConfig(level=log_level,
                    format='%(levelname)-6s: %(asctime)s [%(lineno)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    logging.debug('Not found uvloop, using default_event_loop.')


class NewTask(asyncio.tasks.Task):
    _PENDING = 'PENDING'
    _CANCELLED = 'CANCELLED'
    _FINISHED = 'FINISHED'

    def __init__(self, coro, *, loop=None):
        assert asyncio.coroutines.iscoroutine(coro), repr(coro)
        super().__init__(coro, loop=loop)

    @property
    def x(self):
        if self._state == self._PENDING:
            self._loop.run_until_complete(self)
        return self.result()

    def __getattr__(self, name):
        return self.x.__getattribute__(name)


class RequestsError(IOError):
    __slots__ = ('url', 'kwargs', 'info', 'error')

    def __init__(self, error, url=None, kwargs=None):
        self.url = url
        self.error = error
        self.kwargs = kwargs or {}
        self.info = dict(url=url, kwargs=self.kwargs, error=error)

    def __str__(self):
        return '<RequestsError: %s>' % self.info

    def __repr__(self):
        return '<RequestsError: %s>' % self.error


class Loop():

    def __init__(self, loop=None, **kwargs):
        try:
            self.loop = loop or asyncio.get_event_loop(**kwargs)
            if self.loop.is_running():
                raise NotImplementedError("Cannot use aioutils in "
                                          "asynchroneous environment")
        except NotImplementedError:
            logging.warn("%s is_running, init a new loop" % self.loop)
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        self.tasks = []

    def submit(self, coro, callback=None):
        task = NewTask(coro, loop=self.loop)
        task.add_done_callback(callback) if callback else 0
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
    def todo(self):
        self.tasks = [
            task for task in self.tasks if task._state == NewTask._PENDING]
        return self.tasks

    def run(self):
        self.loop.run_until_complete(asyncio.gather(*self.todo))

    async def done(self):
        await asyncio.gather(*self.todo)


class Requests(Loop):
    '''sometimes the performance is limited by too large "n" .'''

    METH = ('get', 'options', 'head', 'post', 'put', 'patch', 'delete')

    def __init__(self, n=100, loop=None, **kwargs):
        super().__init__(loop=loop, **kwargs)
        self.sem = asyncio.Semaphore(n)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self._initial_request()

    def _initial_request(self):
        for method in self.METH:
            self.__setattr__('%s' %
                             method, self._mock_request_method(method))

    def _mock_request_method(self, method):
        def _new_req(url, callback=None, **kwargs):
            '''support args: retry, callback'''
            return self.submit(self._request(method, url, **kwargs),
                               callback=callback)
        return _new_req

    async def _request(self, method, url, retry=0, **kwargs):
        with await self.sem:
            for retries in range(retry + 1):
                try:
                    async with self.session.request(method, url, **kwargs) as response:
                        response.content = await response.read()
                        encoding = kwargs.get(
                            'encoding') or response._get_encoding()
                        response.text = response.content.decode(encoding)
                        return response
                except Exception as err:
                    error = err
                    continue
            else:
                logging.error(
                    'Retry=%s up, but failed again:\n%s, kwargs: %s.\n%s' %
                    (retry, url, kwargs, error))
                raise RequestsError(error, url, kwargs)

    def close(self):
        self.session.close()

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
