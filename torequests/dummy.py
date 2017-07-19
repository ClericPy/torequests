# python3.5+ # pip install uvloop aiohttp.

import asyncio
import json
import time
from functools import wraps

import aiohttp
from aiohttp.client_reqrep import ClientResponse

from .utils import FailureException, dummy_logger, urlparse

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    dummy_logger.debug('Not found uvloop, using default_event_loop.')

# conver ClientResponse attribute into Requests-like
ClientResponse.text = property(lambda self: self.content.decode(self.encoding))
ClientResponse.ok = property(lambda self: self.status in range(200, 300))
ClientResponse.json = lambda self, encoding=None: json.loads(
    self.content.decode(encoding or self.encoding))


class NewTask(asyncio.tasks.Task):
    _PENDING = 'PENDING'
    _CANCELLED = 'CANCELLED'
    _FINISHED = 'FINISHED'
    _RESPONSE_ARGS = ('encoding', 'content')

    def __init__(self, coro, *, loop=None):
        assert asyncio.coroutines.iscoroutine(coro), repr(coro)
        super().__init__(coro, loop=loop)
        self._callback_result = None
        self._callback_history = []

    @staticmethod
    def wrap_callback(function):
        @wraps(function)
        def wrapped(future):
            future._callback_history.append(function)
            future._callback_result = function(future)
            return future._callback_result
        return wrapped

    @property
    def callback_result(self):
        if self._state == self._PENDING:
            self._loop.run_until_complete(self)
        if self._callback_history:
            return self._callback_result
        else:
            return self.x

    @property
    def x(self):
        if self._state == self._PENDING:
            self._loop.run_until_complete(self)
        return self.result()

    def __getattr__(self, name):
        try:
            object.__getattribute__(self, name)
        except AttributeError:
            return self.x.__getattribute__(name)

    def __setattr__(self, name, value):
        if name in self._RESPONSE_ARGS:
            self.x.__setattr__(name, value)
        else:
            object.__setattr__(self, name, value)


class Loop():

    def __init__(self, n=100, loop=None, default_callback=None):
        try:
            self.loop = loop or asyncio.get_event_loop()
            if self.loop.is_running():
                raise NotImplementedError("Cannot use aioutils in "
                                          "asynchroneous environment")
        except Exception as e:
            dummy_logger.debug("Rebuilding a new loop for exception: %s" % e)
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        self.tasks = []
        self.default_callback = default_callback
        self.sem = asyncio.Semaphore(n)

    def wrap_sem(self, coro_func, sem=None):
        sem = sem or self.sem

        @wraps(coro_func)
        async def new_coro_func(*args, **kwargs):
            with await sem:
                result = await coro_func(*args, **kwargs)
                return result
        return new_coro_func

    def apply(self, function, args=None, kwargs=None):
        args = args or ()
        kwargs = kwargs or {}
        return self.submitter(function)(*args, **kwargs)

    def submit(self, coro, callback=None):
        task = NewTask(coro, loop=self.loop)
        callback = callback or self.default_callback
        if callback:
            if not isinstance(callback, (list, tuple)):
                callback = [callback]
            for fn in callback:
                task.add_done_callback(task.wrap_callback(fn))
        self.tasks.append(task)
        return task

    def submitter(self, f):
        f = self.wrap_sem(f)

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

    def run_forever(self):
        self.loop.run_forever()

    def async_run_forever(self):
        from threading import Timer
        Timer(0, self.loop.run_forever).start()

    def stop(self):
        '''stop self.loop directly, often be used with run_forever'''
        try:
            self.loop.stop()
        except Exception as e:
            dummy_logger.error('can not stop loop for: %s' % e)
            pass

    async def done(self):
        await asyncio.gather(*self.todo_tasks)


def Async(func, n=100, default_callback=None):
    return threads(n, default_callback)(func)


def threads(n=100, default_callback=None):
    return Loop(n, default_callback).submitter


def get_results_generator(*args):
    raise NotImplementedError('Not finished')


class Requests(Loop):
    '''
        The kwargs is the same as kwargs of aiohttp.ClientSession.
        Sometimes the performance is limited by too large "n" .
        frequency: {url_host: (Semaphore obj, internal)}
        
    '''
    METH = ('get', 'options', 'head', 'post', 'put', 'patch', 'delete')

    def __init__(self, n=100, session=None, time_interval=0, catch_exception=True,
                 default_callback=None, frequency=None, **kwargs):
        loop = kwargs.pop('loop', None)
        super().__init__(n=n, loop=loop)
        self.time_interval = time_interval
        self.catch_exception = catch_exception
        self.default_callback = default_callback
        self.default_frequency = (self.sem, self.time_interval)
        self.frequency = frequency or {}
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
            '''support args: retry, callback'''
            return self.submit(self._request(method, url, **kwargs),
                               callback=(callback or self.default_callback))
        return _new_request

    def set_frequency(self, host, n=None, interval=None):
        self.frequency[host] = (asyncio.Semaphore(n) if n else self.sem,
                                           interval or self.time_interval)

    def update_frequency(self, host_frequency_dict):
        self.frequency.update(**host_frequency_dict)

    async def _request(self, method, url, retry=0, **kwargs):
        netloc = urlparse(url).netloc
        sem, interval = self.frequency.get(
            netloc, self.default_frequency)
        for retries in range(retry + 1):
            with await sem:
                try:
                    async with self.session.request(method, url, **kwargs) as resp:
                        resp.status_code = resp.status
                        resp.content = await resp.read()
                        resp.encoding = kwargs.get(
                            'encoding') or resp._get_encoding()
                        return resp
                except Exception as err:
                    error = err
                    continue
                finally:
                    if interval:
                        await asyncio.sleep(interval)
        else:
            kwargs['retry'] = retry
            error_info = dict(url=url, kwargs=kwargs,
                              type=type(error), error_msg=str(error))
            error.args = (error_info,)
            dummy_logger.debug(
                'Retry %s & failed: %s.' %
                (retry, error_info))
            if self.catch_exception:
                return FailureException(error)
            raise error

    def close(self):
        '''Should be closed[explicit] while using external session or connector,
        instead of close by __del__.'''
        try:
            self.session.close()
        except Exception as e:
            dummy_logger.error('can not close session for: %s' % e)
            pass

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
