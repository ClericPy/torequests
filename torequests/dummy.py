# python3.5+ # pip install uvloop aiohttp.

import asyncio
import threading
import time
from functools import partial, wraps
from urllib.parse import urlparse

import aiohttp
from aiohttp.client_reqrep import ClientResponse
from aiohttp.connector import Connection

from ._py3_patch import (aiohttp_response_patch,
                         aiohttp_unclosed_connection_patch)
from .configs import Config
from .exceptions import FailureException
from .main import NewFuture, Pool, ProcessPool

aiohttp_response_patch(ClientResponse)
aiohttp_unclosed_connection_patch(Connection)

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    Config.dummy_logger.debug('Not found uvloop, using default_event_loop.')


class NewTask(asyncio.tasks.Task):
    _PENDING = 'PENDING'
    _CANCELLED = 'CANCELLED'
    _FINISHED = 'FINISHED'
    _RESPONSE_ARGS = ('encoding', 'request_encoding', 'content')

    def __init__(self, coro, *, loop=None):
        assert asyncio.coroutines.iscoroutine(coro), repr(coro)
        super().__init__(coro, loop=loop)
        self._callback_result = None
        self._done_callbacks = []
        self.task_start_time = time.time()
        self.task_end_time = 0
        self.task_cost_time = 0

    @staticmethod
    def wrap_callback(function):
        """setting callback result as self._callback_result"""

        @wraps(function)
        def wrapped(task):
            task._callback_result = function(task)
            return task._callback_result

        return wrapped

    @property
    def cx(self):
        return self.callback_result

    @property
    def callback_result(self):
        if self._state == self._PENDING:
            self._loop.run_until_complete(self)
        if self._done_callbacks:
            result = self._callback_result
        else:
            result = self.result()
        return result

    @property
    def x(self):
        if self._state == self._PENDING:
            self._loop.run_until_complete(self)
        result = self.result()
        return result

    def _schedule_callbacks(self):
        self.task_end_time = time.time()
        self.task_cost_time = self.task_end_time - self.task_start_time
        super()._schedule_callbacks()

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
            Config.dummy_logger.debug(
                "Rebuilding a new loop for exception: %s" % e)
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
        """if kwargs needed, try like this: func=lambda: foo(*args, **kwargs)"""
        return self.loop.run_in_executor(executor, func, *args)

    def run_in_thread_pool(self, pool_size=None, func=None, *args):
        """if kwargs needed, try like this: func=lambda: foo(*args, **kwargs)"""
        executor = Pool(pool_size)
        return self.loop.run_in_executor(executor, func, *args)

    def run_in_process_pool(self, pool_size=None, func=None, *args):
        """if kwargs needed, try like this: func=lambda: foo(*args, **kwargs)"""
        executor = ProcessPool(pool_size)
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
                    task._done_callbacks.append(fn)
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
            task for task in self.all_tasks if task._state == NewTask._PENDING
        ]
        return tasks

    @property
    def done_tasks(self):
        tasks = [
            task for task in self.all_tasks if task._state != NewTask._PENDING
        ]
        return tasks

    def run(self, tasks=None, timeout=None):
        if self.async_running:
            return self.wait_all_tasks_done(timeout)
        else:
            tasks = tasks or self.todo_tasks
            return self.loop.run_until_complete(
                asyncio.gather(*tasks, loop=self.loop))

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
        """stop self.loop directly, often be used with run_forever"""
        try:
            self.loop.stop()
        except Exception as e:
            Config.dummy_logger.error('can not stop loop for: %s' % e)

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
        return 'Frequency(sem=<%s/%s>, interval=%s%s)' % (
            self.sem._value, self._init_sem_value, self.interval,
            ', name=%s' % self.name if self.name else '')

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
    """
        The `kwargs` is same as kwargs of aiohttp.ClientSession.
        Sometimes the performance is limited by too large "n",
            or raise ValueError: too many file descriptors on select() (win32),
            so n=100 by default.
        frequencies: {host: Frequency obj} or {host: [n, interval]}
    """

    def __init__(self,
                 n=100,
                 interval=0,
                 session=None,
                 return_exceptions=True,
                 default_callback=None,
                 frequencies=None,
                 default_host_frequency=None,
                 **kwargs):
        loop = kwargs.pop('loop', None)
        # for old version arg `catch_exception`
        catch_exception = kwargs.pop('catch_exception', None)
        super().__init__(loop=loop, default_callback=default_callback)
        self.sem = asyncio.Semaphore(n)
        self.n = n
        self.interval = interval
        self.catch_exception = catch_exception if catch_exception \
            is not None else return_exceptions
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
        self.session.connector._limit = n

    def ensure_frequencies(self, frequencies):
        if not frequencies:
            return {}
        if not isinstance(frequencies, dict):
            raise ValueError('frequencies should be dict')
        frequencies = {
            host: Frequency.ensure_frequency(frequencies[host])
            for host in frequencies
        }
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
        url = url.strip()
        host = urlparse(url).netloc
        if host in self.frequencies:
            frequency = self.frequencies[host]
        elif self.default_host_frequency:
            frequency = self.set_frequency(host, *self.default_host_frequency)
        else:
            frequency = self.global_frequency
        sem, interval = frequency.sem, frequency.interval
        proxies = kwargs.pop('proxies', None)
        encoding = kwargs.pop('encoding', None)
        if proxies:
            proxy = '://'.join(proxies.popitem())
            kwargs['proxy'] = proxy
        for retries in range(retry + 1):
            with await sem:
                try:
                    async with self.session.request(method, url,
                                                    **kwargs) as resp:
                        resp.content = await resp.read()
                        resp.request_encoding = encoding
                        return resp
                except Exception as err:
                    error = err
                    continue
                finally:
                    if interval:
                        await asyncio.sleep(interval)
        else:
            kwargs['retry'] = retry
            error_info = dict(
                url=url, kwargs=kwargs, type=type(error), error_msg=str(error))
            error.args = (error_info,)
            Config.dummy_logger.debug('Retry %s & failed: %s.' % (retry,
                                                                  error_info))
            if self.catch_exception:
                return FailureException(error)
            raise error

    def request(self, method, url, callback=None, retry=0, **kwargs):
        """submit the coro of self._request to self.loop"""
        return self.submit(
            self._request(method, url=url, retry=retry, **kwargs),
            callback=(callback or self.default_callback))

    def get(self, url, params=None, callback=None, retry=0, **kwargs):
        return self.request(
            'get',
            url=url,
            params=params,
            callback=callback,
            retry=retry,
            **kwargs)

    def post(self, url, data=None, callback=None, retry=0, **kwargs):
        return self.request(
            'post',
            url=url,
            data=data,
            callback=callback,
            retry=retry,
            **kwargs)

    def delete(self, url, callback=None, retry=0, **kwargs):
        return self.request(
            'delete', url=url, callback=callback, retry=retry, **kwargs)

    def put(self, url, data=None, callback=None, retry=0, **kwargs):
        return self.request(
            'put', url=url, data=data, callback=callback, retry=retry, **kwargs)

    def head(self, url, callback=None, retry=0, **kwargs):
        return self.request(
            'head', url=url, callback=callback, retry=retry, **kwargs)

    def options(self, url, callback=None, retry=0, **kwargs):
        return self.request(
            'options', url=url, callback=callback, retry=retry, **kwargs)

    def patch(self, url, callback=None, retry=0, **kwargs):
        return self.request(
            'patch', url=url, callback=callback, retry=retry, **kwargs)

    def close(self):
        """Should be closed[explicit] while using external session or connector,
        instead of close by self.__del__."""
        try:
            if not self.session.closed:
                if self.session._connector_owner:
                    self.session._connector.close()
                self.session._connector = None
        except Exception as e:
            Config.dummy_logger.error('can not close session for: %s' % e)

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
