# python3.5+ # pip install uvloop aiohttp.

import asyncio
import time
from functools import wraps
from urllib.parse import urlparse

import aiohttp

from ._py3_patch import NewResponse, _py36_all_task_patch
from .configs import Config
from .exceptions import FailureException
from .main import NewFuture, Pool, ProcessPool, Error

try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    Config.dummy_logger.debug("Not found uvloop, using default_event_loop.")

__all__ = "NewTask Loop Asyncme coros get_results_generator Frequency Requests".split(
    " "
)


class NewTask(asyncio.Task):
    """Add some special method & attribute for asyncio.Task.

    Params:
        :param coro: a standard asyncio await in coroutines.

    Attrs:
        :attr cx: blocking until the task finish and return the callback_result.
        :attr x: blocking until the task finish and return the value as `coro` returned.
        :attr task_start_time: timestamp when the task start up.
        :attr task_end_time: timestamp when the task end up.
        :attr task_cost_time: seconds of task costs.
    """

    _PENDING = "PENDING"
    _CANCELLED = "CANCELLED"
    _FINISHED = "FINISHED"
    _RESPONSE_ARGS = ("encoding", "request_encoding", "content")

    def __init__(self, coro, *, loop=None, callback=None, extra_args=None):
        assert asyncio.coroutines.iscoroutine(coro), repr(coro)
        super().__init__(coro, loop=loop)
        self._callback_result = None
        self.extra_args = extra_args or ()
        if callback:
            if not isinstance(callback, (list, tuple, set)):
                callback = [callback]
            for fn in callback:
                self.add_done_callback(self.wrap_callback(fn))
        self.task_start_time = time.time()
        self.task_end_time = 0
        self.task_cost_time = 0

    @staticmethod
    def wrap_callback(function):
        """Set the callback's result as self._callback_result."""

        @wraps(function)
        def wrapped(task):
            task._callback_result = function(task)
            return task._callback_result

        return wrapped

    def _schedule_callbacks(self, clear_cb=False):
        """Recording the task_end_time and task_cost_time,
            and prevent super()._schedule_callbacks to clean self._callbacks."""
        self.task_end_time = time.time()
        self.task_cost_time = self.task_end_time - self.task_start_time
        callbacks = self._callbacks[:]
        if not callbacks:
            return
        if clear_cb:
            self._callbacks[:] = []
        for callback in callbacks:
            self._loop.call_soon(callback, self, *self.extra_args)

    @property
    def _done_callbacks(self):
        """Keep same api for NewFuture."""
        return self._callbacks

    @property
    def cx(self):
        """Return self.callback_result"""
        return self.callback_result

    @property
    def callback_result(self):
        """Blocking until the task finish and return the callback_result.until"""
        if self._state == self._PENDING:
            self._loop.run_until_complete(self)
        if self._callbacks:
            result = self._callback_result
        else:
            result = self.result()
        return result

    @property
    def x(self):
        """Blocking until the task finish and return the self.result()"""
        if self._state == self._PENDING:
            self._loop.run_until_complete(self)
        return self.result()

    def __getattr__(self, name):
        return getattr(self.x, name)

    def __setattr__(self, name, value):
        if name in self._RESPONSE_ARGS:
            self.x.__setattr__(name, value)
        else:
            object.__setattr__(self, name, value)


class Loop:
    """Handle the event loop like a thread pool."""

    def __init__(self,
                 n=None,
                 interval=0,
                 timeout=None,
                 default_callback=None,
                 loop=None,
                 **kwargs):
        self._loop = loop
        self.default_callback = default_callback
        self.async_running = False
        self.n = n
        self.interval = interval
        self._timeout = timeout
        self.frequency = Frequency(self.n, self.interval, "loop_sem")

    @property
    def loop(self):
        return self._loop or asyncio.get_event_loop()

    def _wrap_coro_function_with_sem(self, coro_func):
        """Decorator set the coro_function has sem/interval control."""
        sem = self.frequency.sem
        interval = self.frequency.interval

        @wraps(coro_func)
        async def new_coro_func(*args, **kwargs):
            if sem:
                async with sem:
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
        """If `kwargs` needed, try like this: func=lambda: foo(*args, **kwargs)"""
        return self.loop.run_in_executor(executor, func, *args)

    def run_in_thread_pool(self, pool_size=None, func=None, *args):
        """If `kwargs` needed, try like this: func=lambda: foo(*args, **kwargs)"""
        executor = Pool(pool_size)
        return self.loop.run_in_executor(executor, func, *args)

    def run_in_process_pool(self, pool_size=None, func=None, *args):
        """If `kwargs` needed, try like this: func=lambda: foo(*args, **kwargs)"""
        executor = ProcessPool(pool_size)
        return self.loop.run_in_executor(executor, func, *args)

    def run_coroutine_threadsafe(self, coro, loop=None, callback=None):
        """Be used when loop running in a single non-main thread."""
        if not asyncio.iscoroutine(coro):
            raise TypeError("A await in coroutines. object is required")
        loop = loop or self.loop
        future = NewFuture(callback=callback)

        def callback_func():
            try:
                asyncio.futures._chain_future(NewTask(coro, loop=loop), future)
            except Exception as exc:
                if future.set_running_or_notify_cancel():
                    future.set_exception(exc)
                raise

        loop.call_soon_threadsafe(callback_func)
        return future

    def apply(self, coro_function, args=None, kwargs=None, callback=None):
        """Submit a coro_function(*args, **kwargs) as NewTask to self.loop with loop.frequncy control.

        ::

            from torequests.dummy import Loop
            import asyncio
            loop = Loop()

            async def test(i):
                result = await asyncio.sleep(1)
                return (loop.frequency, i)

            task = loop.apply(test, [1])
            print(task)
            # loop.x can be ignore
            loop.x
            print(task.x)

            # <NewTask pending coro=<new_coro_func() running at torequests/torequests/dummy.py:154>>
            # (Frequency(sem=<0/0>, interval=0, name=loop_sem), 1)
        """
        args = args or ()
        kwargs = kwargs or {}
        coro = self._wrap_coro_function_with_sem(coro_function)(*args, **kwargs)
        return self.submit(coro, callback=callback)

    def submit(self, coro, callback=None):
        """Submit a coro as NewTask to self.loop without loop.frequncy control.

        ::

            from torequests.dummy import Loop
            import asyncio
            loop = Loop()

            async def test(i):
                result = await asyncio.sleep(1)
                return (loop.frequency, i)

            coro = test(0)
            task = loop.submit(coro)
            print(task)
            # loop.x can be ignore
            loop.x
            print(task.x)

            # <NewTask pending coro=<test() running at torequests/temp_code.py:58>>
            # (Frequency(sem=<0/0>, interval=0, name=loop_sem), 0)
        """
        callback = callback or self.default_callback
        if self.async_running:
            return self.run_coroutine_threadsafe(coro, callback=callback)
        else:
            return NewTask(coro, loop=self.loop, callback=callback)

    def submitter(self, f):
        """Decorator to submit a coro-function as NewTask to self.loop with sem control.
        Use default_callback frequency of loop."""
        f = self._wrap_coro_function_with_sem(f)

        @wraps(f)
        def wrapped(*args, **kwargs):
            return self.submit(f(*args, **kwargs))

        return wrapped

    @property
    def x(self):
        """return self.run()"""
        return self.run()

    @property
    def todo_tasks(self):
        """Return tasks in loop which its state is pending."""
        tasks = [task for task in self.all_tasks if task._state == NewTask._PENDING]
        return tasks

    @property
    def done_tasks(self):
        """Return tasks in loop which its state is not pending."""
        tasks = [task for task in self.all_tasks if task._state != NewTask._PENDING]
        return tasks

    def run(self, tasks=None, timeout=None):
        """Block, run loop until all tasks completed."""
        timeout = self._timeout if timeout is None else timeout
        if self.async_running or self.loop.is_running():
            return self.wait_all_tasks_done(timeout)
        else:
            tasks = tasks or self.todo_tasks
            return self.loop.run_until_complete(asyncio.gather(*tasks, loop=self.loop))

    def wait_all_tasks_done(self, timeout=None, delay=0.5, interval=0.1):
        """Block, only be used while loop running in a single non-main thread."""
        timeout = self._timeout if timeout is None else timeout
        timeout = timeout or float("inf")
        start_time = time.time()
        time.sleep(delay)
        while 1:
            if not self.todo_tasks:
                return self.all_tasks
            if time.time() - start_time > timeout:
                return self.done_tasks
            time.sleep(interval)

    def close(self):
        """Close the event loop."""
        self.loop.close()

    @property
    def all_tasks(self):
        """Return all tasks of the current loop."""
        return _py36_all_task_patch(loop=self.loop)

    async def pendings(self, tasks=None):
        """Used for await in coroutines.
        `await loop.pendings()`
        `await loop.pendings(tasks)`
        """
        tasks = tasks or self.todo_tasks
        await asyncio.gather(*tasks, loop=self.loop)


def Asyncme(func, n=None, interval=0, default_callback=None, loop=None):
    """Wrap coro_function into the function return NewTask."""
    return coros(n, interval, default_callback, loop)(func)


def coros(n=None, interval=0, default_callback=None, loop=None):
    """Decorator for wrap coro_function into the function return NewTask."""
    submitter = Loop(
        n=n, interval=interval, default_callback=default_callback, loop=loop
    ).submitter

    return submitter


def get_results_generator(*args):
    """TODO"""
    raise NotImplementedError


class _mock_sem:
    _value = 0

    def __bool__(self):
        return False

    def __nonzero__(self):
        return False


class Frequency:
    """Use sem to control concurrent tasks, use interval to sleep after task done."""

    __slots__ = ("sem", "interval", "_init_sem_value", "name")

    def __init__(self, sem=None, interval=0, name=""):
        self.sem = self.ensure_sem(sem)
        self.interval = interval
        self.name = name

    def ensure_sem(self, sem):
        sem = self._ensure_sem(sem)
        self._init_sem_value = sem._value
        return sem

    @classmethod
    def _ensure_sem(cls, sem):
        if not sem:
            return _mock_sem()
        elif isinstance(sem, asyncio.Semaphore):
            return sem
        elif isinstance(sem, (int, float)) and sem > 0:
            return asyncio.Semaphore(int(sem))
        raise ValueError("sem should be an asyncio.Semaphore object or int/float")

    @classmethod
    def ensure_frequency(cls, obj):
        """Trans [n, interval] into Frequency object."""
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
        return "Frequency(sem=<%s/%s>, interval=%s%s)" % (
            self.sem._value,
            self._init_sem_value,
            self.interval,
            ", name=%s" % self.name if self.name else "",
        )


class Requests(Loop):
    """Wrap the aiohttp with NewTask.

    :param n: sometimes the performance is limited by too large "n",
            or raise ValueError: too many file descriptors on select() (win32),
            so n=100 by default.
    :param interval: asyncio.sleep after each task done.
    :param session: special aiohttp.ClientSession.
    :param catch_exception: whether catch and return the Exception instead of raising it.
    :param default_callback: None
    :param frequencies: None or {host: Frequency obj} or {host: [n, interval]}
    :param default_host_frequency: None
    :param kwargs: will used for aiohttp.ClientSession.

    :WARNING: if proxy is not None and **mutable**, should avoid reusing old proxy in the same connection.

        `self.session.connector._force_close = True`, 

        Or use the `connector` param in __init__

        `Requests(connector=TCPConnector(force_close=True))`

    ::

        from torequests.dummy import Requests
        from torequests.logs import print_info
        trequests = Requests(frequencies={'p.3.cn': (2, 2)})
        ss = [
            trequests.get(
                'http://p.3.cn', retry=1, timeout=5,
                callback=lambda x: (len(x.content), print_info(trequests.frequencies)))
            for i in range(4)
        ]
        trequests.x
        ss = [i.cx for i in ss]
        print_info(ss)

        # [2018-03-19 00:57:36]: {'p.3.cn': Frequency(sem=<1/2>, interval=2)}
        # [2018-03-19 00:57:36]: {'p.3.cn': Frequency(sem=<0/2>, interval=2)}
        # [2018-03-19 00:57:38]: {'p.3.cn': Frequency(sem=<1/2>, interval=2)}
        # [2018-03-19 00:57:38]: {'p.3.cn': Frequency(sem=<2/2>, interval=2)}
        # [2018-03-19 00:57:38]: [(612, None), (612, None), (612, None), (612, None)]
    """

    def __init__(self,
                 n=100,
                 interval=0,
                 session=None,
                 catch_exception=True,
                 default_callback=None,
                 frequencies=None,
                 default_host_frequency=None,
                 **kwargs):
        loop = kwargs.pop("loop", None)
        super().__init__(
            loop=loop,
            default_callback=default_callback,
        )
        # Requests object use its own frequency control.
        self.sem = asyncio.Semaphore(n)
        self.n = n
        self.interval = interval
        # be compatible with old version's arg `return_exceptions`
        return_exceptions = kwargs.pop("return_exceptions", None)
        self.catch_exception = (
            return_exceptions if return_exceptions is not None else catch_exception
        )
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
        """Ensure frequencies is dict of host-frequencies."""
        if not frequencies:
            return {}
        if not isinstance(frequencies, dict):
            raise ValueError("frequencies should be dict")
        frequencies = {
            host: Frequency.ensure_frequency(frequencies[host]) for host in frequencies
        }
        return frequencies

    def set_frequency(self, host, sem=None, interval=None):
        """Set frequency for host with sem and interval."""
        # single sem or global sem
        sem = sem or self.sem
        interval = self.interval if interval is None else interval
        frequency = Frequency(sem, interval, host)
        frequencies = {host: frequency}
        self.update_frequency(frequencies)
        return frequency

    def update_frequency(self, frequencies):
        """Update the frequencies with dict of new frequencies."""
        self.frequencies.update(self.ensure_frequencies(frequencies))

    async def _request(self, method, url, retry=0, **kwargs):
        url = url.strip()
        parsed_url = urlparse(url)
        scheme = parsed_url.scheme
        host = parsed_url.netloc
        if host in self.frequencies:
            frequency = self.frequencies[host]
        elif self.default_host_frequency:
            frequency = self.set_frequency(host, *self.default_host_frequency)
        else:
            frequency = self.global_frequency
        if 'timeout' in kwargs:
            if isinstance(kwargs['timeout'], tuple):
                kwargs['timeout'] = aiohttp.client.ClientTimeout(
                    sock_connect=kwargs['timeout'][0],
                    sock_read=kwargs['timeout'][1])
            elif isinstance(kwargs['timeout'], aiohttp.client.ClientTimeout):
                pass
            else:
                kwargs['timeout'] = aiohttp.client.ClientTimeout(
                    sock_connect=kwargs['timeout'], sock_read=kwargs['timeout'])
        sem, interval = frequency.sem, frequency.interval
        proxies = kwargs.pop("proxies", None)
        if "verify" in kwargs:
            kwargs["verify_ssl"] = kwargs.pop("verify")
        if proxies:
            kwargs["proxy"] = "%s://%s" % (scheme, proxies[scheme])
        kwargs["url"] = url
        kwargs["method"] = method
        # non-official request args
        referer_info = kwargs.pop("referer_info", None)
        encoding = kwargs.pop("encoding", None)
        for retries in range(retry + 1):
            async with sem:
                try:
                    async with self.session.request(**kwargs) as resp:
                        await resp.read()
                        r = NewResponse(resp, encoding=encoding)
                        r.referer_info = referer_info
                        return r
                except (aiohttp.ClientError, Error) as err:
                    error = err
                    continue
                finally:
                    if interval:
                        await asyncio.sleep(interval)
        else:
            kwargs["retry"] = retry
            if referer_info:
                kwargs["referer_info"] = referer_info
            if encoding:
                kwargs["encoding"] = encoding
            error.request = kwargs
            Config.dummy_logger.debug("Retry %s & failed: %s." % (retry, error))
            if self.catch_exception:
                failure = FailureException(error)
                failure.request = kwargs
                return failure
            raise error

    def request(self, method, url, callback=None, retry=0, **kwargs):
        """Submit the coro of self._request to self.loop"""
        return self.submit(
            self._request(method, url=url, retry=retry, **kwargs),
            callback=(callback or self.default_callback),
        )

    def get(self, url, params=None, callback=None, retry=0, **kwargs):
        return self.request(
            "get", url=url, params=params, callback=callback, retry=retry, **kwargs
        )

    def post(self, url, data=None, callback=None, retry=0, **kwargs):
        return self.request(
            "post", url=url, data=data, callback=callback, retry=retry, **kwargs
        )

    def delete(self, url, callback=None, retry=0, **kwargs):
        return self.request("delete", url=url, callback=callback, retry=retry, **kwargs)

    def put(self, url, data=None, callback=None, retry=0, **kwargs):
        return self.request(
            "put", url=url, data=data, callback=callback, retry=retry, **kwargs
        )

    def head(self, url, callback=None, retry=0, **kwargs):
        return self.request("head", url=url, callback=callback, retry=retry, **kwargs)

    def options(self, url, callback=None, retry=0, **kwargs):
        return self.request(
            "options", url=url, callback=callback, retry=retry, **kwargs
        )

    def patch(self, url, callback=None, retry=0, **kwargs):
        return self.request("patch", url=url, callback=callback, retry=retry, **kwargs)

    def close(self):
        """Should be closed[explicit] while using external session or connector,
        instead of close by self.__del__."""
        try:
            if not self.session.closed:
                if self.session._connector is not None and self.session._connector_owner:
                    self.session._connector.close()
                self.session._connector = None
        except Exception as e:
            Config.dummy_logger.error("can not close session for: %s" % e)

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
