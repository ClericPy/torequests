# python3.5+ # pip install uvloop aiohttp.

from asyncio import (Task, gather, get_event_loop, iscoroutine, new_event_loop,
                     set_event_loop_policy, wait)
from asyncio.futures import _chain_future
from concurrent.futures import ALL_COMPLETED
from functools import wraps
from logging import getLogger
from time import sleep as time_sleep
from time import time as time_time
from typing import (Callable, Coroutine, Dict, List, Optional, Sequence, Set,
                    Union)
from urllib.parse import urlparse

from aiohttp import ClientError, ClientSession, ClientTimeout
from frequency_controller.async_tools import Frequency

from ._py3_patch import NewResponse, _py36_all_task_patch
from .exceptions import FailureException
from .main import Error, NewFuture, Pool, ProcessPool

logger = getLogger("torequests")

try:
    import uvloop

    set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    logger.debug("Not found uvloop, using default_event_loop.")

__all__ = "NewTask Loop Asyncme coros Frequency Requests".split(" ")

NotSet = object()


class NewTask(Task):
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

    def __init__(self,
                 coro,
                 *,
                 loop=None,
                 callback: Union[Callable, Sequence] = None,
                 extra_args=None):
        assert iscoroutine(coro), repr(coro)
        super().__init__(coro, loop=loop)
        self._callback_result = NotSet
        self.extra_args = extra_args or ()
        self.task_start_time = time_time()
        self.task_end_time = 0.0
        self.task_cost_time = 0.0
        if callback:
            if not isinstance(callback, (list, tuple, set)):
                callback = [callback]
            self.add_done_callback(self.set_task_time)
            for fn in callback:
                # custom callback will update the _callback_result
                self.add_done_callback(self.wrap_callback(fn))

    @staticmethod
    def wrap_callback(function: Callable) -> Callable:
        """Set the callback's result as self._callback_result."""

        @wraps(function)
        def wrapped(task):
            task._callback_result = function(task)
            return task._callback_result

        return wrapped

    @staticmethod
    def set_task_time(task: 'NewTask'):
        task.task_end_time = time_time()
        task.task_cost_time = task.task_end_time - task.task_start_time

    @property
    def _done_callbacks(self) -> list:
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
        if self._callback_result is NotSet:
            result = self.result()
        else:
            result = self._callback_result
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
                 n: int = None,
                 interval: float = 0,
                 timeout: Optional[float] = None,
                 default_callback: Optional[Callable] = None,
                 loop=None,
                 **kwargs):
        self._loop = loop
        self.default_callback = default_callback
        self.async_running = False
        self._timeout = timeout
        self.frequency = Frequency(n, interval)

    @property
    def loop(self):
        # lazy init
        if self._loop is None:
            self._loop = get_event_loop()
        if self._loop.is_closed():
            self._loop = new_event_loop()
        return self._loop

    def _wrap_coro_function_with_frequency(self, coro_func):
        """Decorator set the coro_function has n/interval control."""

        @wraps(coro_func)
        async def new_coro_func(*args, **kwargs):
            if self.frequency:
                async with self.frequency:
                    result = await coro_func(*args, **kwargs)
                    return result
            else:
                result = await coro_func(*args, **kwargs)
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
        if not iscoroutine(coro):
            raise TypeError("A await in coroutines. object is required")
        loop = loop or self.loop
        future = NewFuture(callback=callback)

        def callback_func():
            try:
                _chain_future(NewTask(coro, loop=loop), future)
            except Exception as exc:
                if future.set_running_or_notify_cancel():
                    future.set_exception(exc)
                raise

        loop.call_soon_threadsafe(callback_func)
        return future

    def apply(self,
              coro_function: Callable,
              args: Optional[Sequence] = None,
              kwargs: Optional[dict] = None,
              callback: Optional[Callable] = None):
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
            print(task.x)
            # <NewTask pending coro=<test() running at dummy.py:154>>
            # (Frequency(None / None, pending: None, interval: 0s), 1)
        """
        args = args or ()
        kwargs = kwargs or {}
        coro = self._wrap_coro_function_with_frequency(coro_function)(*args,
                                                                      **kwargs)
        return self.submit(coro, callback=callback)

    def submit(self, coro, callback: Optional[Callable] = None):
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
            # <NewTask pending coro=<test() running at temp_code.py:6>>
            # (Frequency(None / None, pending: None, interval: 0s), 0)
        """
        callback = callback or self.default_callback
        if self.async_running:
            return self.run_coroutine_threadsafe(coro, callback=callback)
        else:
            return NewTask(coro, loop=self.loop, callback=callback)

    def submitter(self, f: Callable) -> Callable:
        """Decorator to submit a coro-function as NewTask to self.loop with control.
        Use default_callback frequency of loop."""
        f = self._wrap_coro_function_with_frequency(f)

        @wraps(f)
        def wrapped(*args, **kwargs):
            return self.submit(f(*args, **kwargs))

        return wrapped

    @property
    def x(self):
        """return self.run()"""
        return self.run()

    async def wait(self, fs, timeout=None, return_when=ALL_COMPLETED):
        if fs:
            return await wait(
                fs, loop=self.loop, timeout=timeout, return_when=return_when)

    @property
    def todo_tasks(self) -> List[Task]:
        """Return tasks in loop which its state is pending."""
        tasks = [
            task for task in self.all_tasks if task._state == NewTask._PENDING
        ]
        return tasks

    @property
    def done_tasks(self) -> List[Task]:
        """Return tasks in loop which its state is not pending."""
        tasks = [
            task for task in self.all_tasks if task._state != NewTask._PENDING
        ]
        return tasks

    def run(self, tasks: List[Task] = None, timeout=NotSet):
        """Block, run loop until all tasks completed."""
        timeout = self._timeout if timeout is NotSet else timeout
        if self.async_running or self.loop.is_running():
            return self.wait_all_tasks_done(timeout)
        else:
            tasks = [task for task in tasks or self.todo_tasks]
            return self.loop.run_until_complete(
                self.wait(tasks, timeout=timeout))

    def wait_all_tasks_done(self,
                            timeout=NotSet,
                            delay: float = 0.5,
                            interval: float = 0.1):
        """Block, only be used while loop running in a single non-main thread. Not SMART!"""
        timeout = self._timeout if timeout is NotSet else timeout
        timeout = timeout or float("inf")
        start_time = time_time()
        time_sleep(delay)
        while 1:
            if not self.todo_tasks:
                return self.all_tasks
            if time_time() - start_time > timeout:
                return self.done_tasks
            time_sleep(interval)

    def close(self):
        """Close the event loop."""
        self.loop.close()

    @property
    def all_tasks(self) -> Set[Task]:
        """Return all tasks of the current loop."""
        return _py36_all_task_patch(loop=self.loop)

    async def pendings(self,
                       tasks: Optional[List[Task]] = None) -> Sequence[Task]:
        """Used for await in coroutines.
        `await loop.pendings()`
        `await loop.pendings(tasks)`
        """
        tasks = tasks or self.todo_tasks
        await gather(*tasks, loop=self.loop)
        return tasks


def Asyncme(func,
            n: Optional[int] = None,
            interval: Optional[float] = 0,
            default_callback: Optional[Callable] = None,
            loop=None):
    """Wrap coro_function into the function return NewTask."""
    return coros(n, interval, default_callback, loop)(func)


def coros(n: Optional[int] = None,
          interval: Optional[float] = 0,
          default_callback: Optional[Callable] = None,
          loop=None):
    """Decorator for wrap coro_function into the function return NewTask."""
    submitter = Loop(
        n=n, interval=interval, default_callback=default_callback,
        loop=loop).submitter

    return submitter


class Requests(Loop):
    """Wrap the aiohttp with NewTask.

    :param n: sometimes the performance is limited by too large "n",
            or raise ValueError: too many file descriptors on select() (win32),
            so n=100 by default.
    :param interval: sleep after each task done if n.
    :param session: special aiohttp.ClientSession.
    :param catch_exception: whether catch and return the Exception instead of raising it.
    :param default_callback: None
    :param frequencies: None or {host: Frequency obj} or {host: [n, interval]}
    :param default_host_frequency: None, or tuple like: (2, 1). global_frequency is shared by hosts, default_host_frequency will be setdefault as a new one.
    :param kwargs: will used for aiohttp.ClientSession.

    ::

        # ====================== sync environment ======================
        from torequests.dummy import Requests
        from torequests.logs import print_info
        req = Requests(frequencies={'p.3.cn': (2, 1)})
        tasks = [
            req.get(
                'http://p.3.cn',
                retry=1,
                timeout=5,
                callback=lambda x: (len(x.content), print_info(x.status_code)))
            for i in range(4)
        ]
        req.x
        results = [i.cx for i in tasks]
        print_info(results)
        # [2020-02-11 15:30:54] temp_code.py(11): 200
        # [2020-02-11 15:30:54] temp_code.py(11): 200
        # [2020-02-11 15:30:55] temp_code.py(11): 200
        # [2020-02-11 15:30:55] temp_code.py(11): 200
        # [2020-02-11 15:30:55] temp_code.py(16): [(612, None), (612, None), (612, None), (612, None)]

        # ====================== async with ======================
        from torequests.dummy import Requests
        from torequests.logs import print_info
        import asyncio


        async def main():
            async with Requests(frequencies={'p.3.cn': (2, 1)}) as req:
                tasks = [
                    req.get(
                        'http://p.3.cn',
                        retry=1,
                        timeout=5,
                        callback=lambda x: (len(x.content), print_info(x.status_code))
                    ) for i in range(4)
                ]
                await req.wait(tasks)
                results = [task.cx for task in tasks]
                print_info(results)


        if __name__ == "__main__":
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
            loop.close()
        # [2020-02-11 15:30:55] temp_code.py(36): 200
        # [2020-02-11 15:30:55] temp_code.py(36): 200
        # [2020-02-11 15:30:56] temp_code.py(36): 200
        # [2020-02-11 15:30:56] temp_code.py(36): 200
        # [2020-02-11 15:30:56] temp_code.py(41): [(612, None), (612, None), (612, None), (612, None)]

    """

    def __init__(self,
                 n: Optional[int] = None,
                 interval: Optional[float] = 0,
                 session: Optional[ClientSession] = None,
                 catch_exception: bool = True,
                 default_callback: Optional[Callable] = None,
                 frequencies: Optional[Dict[str, Frequency]] = None,
                 default_host_frequency: Union[Frequency, None, Sequence,
                                               Dict] = None,
                 *,
                 loop=None,
                 return_exceptions: Optional[bool] = None,
                 **kwargs):
        super().__init__(
            loop=loop,
            default_callback=default_callback,
        )
        # Requests object use its own frequency control, instead of the parent class's.
        self.n = n
        self.interval = interval
        # be compatible with old version's arg `return_exceptions`
        self.catch_exception = (catch_exception if return_exceptions is None
                                else return_exceptions)
        self.frequencies = self.ensure_frequencies(frequencies)
        self.default_host_frequency = default_host_frequency
        self.global_frequency = Frequency(self.n, self.interval)
        self.session_kwargs = kwargs
        self._closed = False
        self._session = session
        if self._session is not None:
            session._loop = self.loop
            self._session = session
            if self.n:
                self._session.connector._limit = self.n

    async def _ensure_session(self) -> ClientSession:
        """ensure using the same loop, lazy init session."""
        if self._session is None:
            # new version (>=4.0.0) of aiohttp will not need loop arg.
            self._session = ClientSession(**self.session_kwargs)
            if self.n:
                self._session.connector._limit = self.n
        return self._session

    @property
    def session(self) -> Coroutine:
        return self._ensure_session()

    def ensure_frequencies(self, frequencies: Dict[str, Frequency]):
        """Ensure frequencies is dict of host-frequencies."""
        if not frequencies:
            return {}
        if not isinstance(frequencies, dict):
            raise ValueError("frequencies should be dict")
        frequencies = {
            host: Frequency.ensure_frequency(frequencies[host])
            for host in frequencies
        }
        return frequencies

    def set_frequency(self, host: str, n: Optional[int] = None,
                      interval=NotSet) -> Frequency:
        """Set frequency for host with n and interval."""
        frequency = Frequency(
            n or self.n,
            self.interval if interval is NotSet else interval,
            loop=self.loop)
        self.update_frequency({host: frequency})
        return frequency

    def update_frequency(self, frequencies: Dict[str, Frequency]):
        """Update the frequencies with dict of new frequencies."""
        self.frequencies.update(self.ensure_frequencies(frequencies))

    async def _request(self,
                       method: str,
                       url: str,
                       retry: Optional[int] = 0,
                       **kwargs) -> Union[NewResponse, FailureException]:
        url = url.strip()
        parsed_url = urlparse(url)
        scheme = parsed_url.scheme
        host = parsed_url.netloc
        # attempt to get a frequency, host > default_host_frequency > global_frequency
        frequency = self.frequencies.get(host)
        if not frequency:
            if self.default_host_frequency:
                frequency = self.frequencies.setdefault(
                    host,
                    Frequency.ensure_frequency(self.default_host_frequency))
            else:
                frequency = self.global_frequency
        if 'timeout' in kwargs:
            # for timeout=(1,2) and timeout=5
            timeout = kwargs['timeout']
            if isinstance(timeout, (int, float)):
                kwargs['timeout'] = ClientTimeout(
                    sock_connect=timeout, sock_read=timeout)
            elif isinstance(timeout, (tuple, list)):
                kwargs['timeout'] = ClientTimeout(
                    sock_connect=timeout[0], sock_read=timeout[1])
            elif timeout is None or isinstance(timeout, ClientTimeout):
                pass
            else:
                raise ValueError('Bad timeout type')
        if "verify" in kwargs:
            kwargs["ssl"] = kwargs.pop('verify')
        if "proxies" in kwargs:
            kwargs["proxy"] = "%s://%s" % (scheme, kwargs['proxies'][scheme])
        kwargs["url"] = url
        kwargs["method"] = method
        # non-official request args
        referer_info = kwargs.pop("referer_info", None)
        encoding = kwargs.pop("encoding", None)
        for retries in range(retry + 1):
            async with frequency:
                try:
                    session = await self.session
                    async with session.request(**kwargs) as resp:
                        await resp.read()
                        r = NewResponse(
                            resp, encoding=encoding, referer_info=referer_info)
                        return r
                except (ClientError, Error) as err:
                    error = err
                    continue
        else:
            kwargs["retry"] = retry
            if referer_info:
                kwargs["referer_info"] = referer_info
            if encoding:
                kwargs["encoding"] = encoding
            logger.debug("Retry %s & failed: %s." % (retry, error))
            failure = FailureException(error)
            setattr(failure, 'request', kwargs)
            if self.catch_exception:
                return failure
            else:
                raise failure

    def request(self,
                method: str,
                url: str,
                callback: Optional[Callable] = None,
                retry: Optional[int] = 0,
                **kwargs):
        """Submit the coro of self._request to self.loop"""
        return self.submit(
            self._request(method, url=url, retry=retry, **kwargs),
            callback=(callback or self.default_callback),
        )

    def get(self,
            url: str,
            params: Optional[dict] = None,
            callback: Optional[Callable] = None,
            retry=0,
            **kwargs):
        return self.request(
            "get",
            url=url,
            params=params,
            callback=callback,
            retry=retry,
            **kwargs)

    def post(self,
             url: str,
             data=None,
             callback: Optional[Callable] = None,
             retry=0,
             **kwargs):
        return self.request(
            "post",
            url=url,
            data=data,
            callback=callback,
            retry=retry,
            **kwargs)

    def delete(self,
               url: str,
               callback: Optional[Callable] = None,
               retry: Optional[int] = 0,
               **kwargs):
        return self.request(
            "delete", url=url, callback=callback, retry=retry, **kwargs)

    def put(self,
            url: str,
            data=None,
            callback: Optional[Callable] = None,
            retry: Optional[int] = 0,
            **kwargs):
        return self.request(
            "put", url=url, data=data, callback=callback, retry=retry, **kwargs)

    def head(self,
             url: str,
             callback: Optional[Callable] = None,
             retry: Optional[int] = 0,
             **kwargs):
        return self.request(
            "head", url=url, callback=callback, retry=retry, **kwargs)

    def options(self,
                url: str,
                callback: Optional[Callable] = None,
                retry: Optional[int] = 0,
                **kwargs):
        return self.request(
            "options", url=url, callback=callback, retry=retry, **kwargs)

    def patch(self,
              url: str,
              callback: Optional[Callable] = None,
              retry: Optional[int] = 0,
              **kwargs):
        return self.request(
            "patch", url=url, callback=callback, retry=retry, **kwargs)

    async def close(self):
        if self._closed:
            return
        try:
            session = await self._ensure_session()
            if session and not session.closed:
                await session.close()
            self._closed = True
        except Exception as e:
            logger.error("can not close session for: %s" % e)

    def __del__(self):
        _exhaust_simple_coro(self.close())

    def __enter__(self):
        return self

    def __exit__(self, *args):
        _exhaust_simple_coro(self.close())

    async def __aenter__(self):
        await self.session
        return self

    async def __aexit__(self, *args):
        await self.close()


def _exhaust_simple_coro(coro: Coroutine):
    """Run coroutines without event loop, only support simple coroutines which can run without future.
    Or it will raise RuntimeError: await wasn't used with future."""
    while True:
        try:
            coro.send(None)
        except StopIteration as e:
            return e.value
