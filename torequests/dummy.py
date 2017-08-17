# python3.5+ # pip install uvloop aiohttp.

import asyncio
import json
import threading
import time
from functools import partial, wraps
from urllib.parse import urlparse

import aiohttp
from aiohttp.client_reqrep import ClientResponse

from .exceptions import FailureException
from .logs import dummy_logger
from .main import NewFuture

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    dummy_logger.debug('Not found uvloop, using default_event_loop.')

# conver ClientResponse attribute into Requests-like
ClientResponse.text = property(lambda self: self.content.decode(self.encoding))
ClientResponse.url_string = property(lambda self: str(self._url))
ClientResponse.ok = property(lambda self: self.status in range(200, 300))
ClientResponse.encoding = property(
    lambda self: self.request_encoding or self._get_encoding())
ClientResponse.json = lambda self, encoding=None, loads=json.loads: loads(
    self.content.decode(encoding or self.encoding))


class NewTask(asyncio.tasks.Task):
    _PENDING = 'PENDING'
    _CANCELLED = 'CANCELLED'
    _FINISHED = 'FINISHED'
    _RESPONSE_ARGS = ('encoding', 'request_encoding', 'content')

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
    def cx(self):
        return self.callback_result

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

    def __init__(self, n=None, interval=0, default_callback=None, loop=None):
        try:
            self.loop = loop or asyncio.get_event_loop()
            if self.loop.is_running():
                raise NotImplementedError("Cannot use aioutils in "
                                          "asynchroneous environment")
        except Exception as e:
            dummy_logger.debug("Rebuilding a new loop for exception: %s" % e)
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        self.default_callback = default_callback
        self.async_running = False

    def wrap_sem(self, coro_func, n=None, interval=0):
        sem = Frequency._ensure_sem(n) if n else n
        interval = interval

        @wraps(coro_func)
        async def new_coro_func(*args, **kwargs):
            if sem:
                with await sem:
                    result = await coro_func(*args, **kwargs)
                    if interval:
                        await asyncio.sleep(interval)
                    return result
            else:
                result = await coro_func(*args, **kwargs)
                if interval:
                    await asyncio.sleep(interval)
                return result
        return new_coro_func

    def run_in_executor(self, executor=None, func=None, *args):
        return self.loop.run_in_executor(executor, func, *args)

    def run_coroutine_threadsafe(self, coro, loop=None, callback=None):
        if not asyncio.iscoroutine(coro):
            raise TypeError('A coroutine object is required')
        loop = loop or self.loop
        future = NewFuture()
        if callback:
            if not isinstance(callback, (list, tuple)):
                callback = [callback]
            for fn in callback:
                future.add_done_callback(future.wrap_callback(fn))

        def callback_func():
            try:
                asyncio.futures._chain_future(NewTask(coro, loop=loop), future)
            except Exception as exc:
                if future.set_running_or_notify_cancel():
                    future.set_exception(exc)
                raise
        loop.call_soon_threadsafe(callback_func)
        return future

    def apply(self, function, args=None, kwargs=None):
        args = args or ()
        kwargs = kwargs or {}
        return self.submitter(function)(*args, **kwargs)

    def submit(self, coro, callback=None):
        callback = callback or self.default_callback
        if self.async_running:
            return self.run_coroutine_threadsafe(coro, callback=callback)
        else:
            task = NewTask(coro, loop=self.loop)
            if callback:
                if not isinstance(callback, (list, tuple)):
                    callback = [callback]
                for fn in callback:
                    task.add_done_callback(task.wrap_callback(fn))
            return task

    def submitter(self, f, n=None, interval=0):
        f = self.wrap_sem(f, n, interval)

        @wraps(f)
        def wrapped(*args, **kwargs):
            return self.submit(f(*args, **kwargs))
        return wrapped

    @property
    def x(self):
        return self.run()

    @property
    def todo_tasks(self):
        tasks = [
            task for task in self.all_tasks if task._state == NewTask._PENDING]
        return tasks

    @property
    def done_tasks(self):
        tasks = [
            task for task in self.all_tasks if task._state != NewTask._PENDING]
        return tasks

    def run(self, tasks=None, timeout=None):
        if self.async_running:
            return self.wait_all_tasks_done(timeout)
        else:
            tasks = tasks or self.todo_tasks
            return self.loop.run_until_complete(asyncio.gather(*tasks, loop=self.loop))

    def run_forever(self):
        self.loop.run_forever()

    def wait_all_tasks_done(self, timeout=None, delay=0.5, interval=0.1):
        timeout = timeout or float('inf')
        start_time = time.time()
        time.sleep(delay)
        while 1:
            if not self.todo_tasks:
                return self.all_tasks
            if time.time() - start_time > timeout:
                return self.done_tasks
            time.sleep(interval)

    def async_run_forever(self, daemon=True):
        thread = threading.Thread(target=self.loop.run_forever)
        thread.setDaemon(daemon)
        thread.start()
        self.async_running = True

    def close(self):
        self.loop.close()

    def stop(self):
        '''stop self.loop directly, often be used with run_forever'''
        try:
            self.loop.stop()
        except Exception as e:
            dummy_logger.error('can not stop loop for: %s' % e)

    @property
    def all_tasks(self):
        return asyncio.Task.all_tasks(loop=self.loop)

    async def pendings(self, tasks=None):
        tasks = tasks or self.todo_tasks
        await asyncio.gather(*tasks, loop=self.loop)


def Asyncme(func, n=None, interval=0, default_callback=None, loop=None):
    return coros(n, interval, default_callback, loop)(func)


def coros(n=None, interval=0, default_callback=None, loop=None):
    submitter = partial(
        Loop(default_callback, loop).submitter, n=n, interval=interval)

    return submitter


def get_results_generator(*args):
    raise NotImplementedError


class Frequency:
    __slots__ = ('sem', 'interval', '_init_sem_value', 'name')

    def __init__(self, sem=None, interval=0, name=''):
        self.sem = self.ensure_sem(sem)
        self.interval = interval
        self.name = name

    @classmethod
    def ensure_frequency(cls, obj):
        if isinstance(obj, cls):
            return obj
        else:
            return cls(*obj)

    def __getitem__(self, key):
        if key in self.__slots__:
            return self.__getattribute__(key)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return '<Frequency %s (sem=%s/%s, interval=%s)>' % (self.name, self.sem._value,
                                                                  self._init_sem_value, self.interval)

    def ensure_sem(self, sem):
        sem = self._ensure_sem(sem)
        self._init_sem_value = sem._value
        return sem

    @classmethod
    def _ensure_sem(cls, sem):
        if isinstance(sem, asyncio.Semaphore):
            return sem
        elif isinstance(sem, (int, float)) and sem > 0:
            return asyncio.Semaphore(int(sem))
        raise ValueError(
            'sem should be an asyncio.Semaphore object or int/float')


class Requests(Loop):
    '''
        The kwargs is the same as kwargs of aiohttp.ClientSession.
        Sometimes the performance is limited by too large "n", 
            or raise ValueError: too many file descriptors in select() (win32).
        frequencies: {url_host: Frequency obj}

    '''
    METH = ('get', 'options', 'head', 'post', 'put', 'patch', 'delete')

    def __init__(self, n=100, interval=0, session=None,
                 catch_exception=True, default_callback=None,
                 frequencies=None, default_host_frequency=None, **kwargs):
        loop = kwargs.pop('loop', None)
        super().__init__(loop=loop, default_callback=default_callback)
        self.sem = asyncio.Semaphore(n)
        self.interval = interval
        self.catch_exception = catch_exception
        self.default_host_frequency = default_host_frequency
        if self.default_host_frequency:
            assert isinstance(self.default_host_frequency, (list, tuple))
        self.global_frequency = Frequency(self.sem, self.interval)
        self.frequencies = self.ensure_frequencies(frequencies)
        if session:
            session._loop = self.loop
            self.session = session
        else:
            self.session = aiohttp.ClientSession(loop=self.loop, **kwargs)
        self.session._connector._limit = n
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

    def request(self, method, url, callback=None, **kwargs):
        return self.submit(self._request(method, url, **kwargs),
                               callback=(callback or self.default_callback))

    def ensure_frequencies(self, frequencies):
        if not frequencies:
            return {}
        if not isinstance(frequencies, dict):
            raise ValueError('frequencies should be dict')
        frequencies = {host: Frequency.ensure_frequency(
            frequencies[host]) for host in frequencies}
        return frequencies

    def set_frequency(self, host, sem=None, interval=None):
        sem = sem or self.sem
        interval = self.interval if interval is None else interval
        frequency = Frequency(sem, interval, host)
        frequencies = {host: frequency}
        self.update_frequency(frequencies)
        return frequency

    def update_frequency(self, frequencies):
        self.frequencies.update(self.ensure_frequencies(frequencies))

    async def _request(self, method, url, retry=0, **kwargs):
        host = urlparse(url).netloc
        if host in self.frequencies:
            frequency = self.frequencies[host]
        elif self.default_host_frequency:
            frequency = self.set_frequency(host, *self.default_host_frequency)
        else:
            frequency = self.global_frequency
        sem, interval = frequency.sem, frequency.interval
        proxies = kwargs.pop('proxies', None)
        if proxies:
            proxy = '://'.join(proxies.popitem())
            kwargs['proxy'] = proxy
        for retries in range(retry + 1):
            with await sem:
                try:
                    async with self.session.request(method, url, **kwargs) as resp:
                        resp.status_code = resp.status
                        resp.content = await resp.read()
                        resp.request_encoding = kwargs.get('encoding')
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

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
