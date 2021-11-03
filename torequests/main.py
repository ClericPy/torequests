#! coding:utf-8
# python2 requires: pip install futures

import atexit
from concurrent.futures import (ProcessPoolExecutor, ThreadPoolExecutor,
                                as_completed)
from concurrent.futures._base import (CANCELLED, CANCELLED_AND_NOTIFIED,
                                      FINISHED, PENDING, RUNNING,
                                      CancelledError, Error, Executor, Future,
                                      TimeoutError)
from concurrent.futures.thread import _threads_queues, _WorkItem
from functools import wraps
from logging import getLogger
from threading import Thread, Timer
from time import sleep
from time import time as time_time
from weakref import WeakSet

from requests import PreparedRequest, RequestException, Session
from requests.adapters import HTTPAdapter
from urllib3 import disable_warnings

from .configs import Config
from .exceptions import FailureException, ValidationError
from .frequency_controller.sync_tools import Frequency
from .versions import PY2, PY3

try:
    from queue import Empty, Queue
except ImportError:
    from Queue import Empty, Queue
if PY3:
    from concurrent.futures.process import BrokenProcessPool

__all__ = [
    "Pool", "ProcessPool", "NewFuture", "Async", "threads",
    "get_results_generator", "run_after_async", "tPool", "get", "post",
    "options", "delete", "put", "head", "patch", "request", "disable_warnings",
    "Workshop"
]
logger = getLogger("torequests")


def _abandon_all_tasks():
    """Only used for abandon_all_tasks and exit the main thread,
    to prevent the main thread waiting for unclosed thread while exiting."""
    _threads_queues.clear()


def ensure_waiting_for_threads():
    if Config.wait_futures_before_exiting:
        _abandon_all_tasks()


atexit.register(ensure_waiting_for_threads)


class NewExecutorPoolMixin(Executor):
    """Add async_func decorator for wrapping a function to return the NewFuture."""

    def async_func(self, function):
        """Decorator for let a normal function return the NewFuture"""

        @wraps(function)
        def wrapped(*args, **kwargs):
            return self.submit(function, *args, **kwargs)

        return wrapped

    def close(self, wait=True):
        """Same as self.shutdown"""
        return self.shutdown(wait=wait)

    def _get_cpu_count(self):
        """Get the cpu count."""
        try:
            from multiprocessing import cpu_count

            return cpu_count()
        except Exception as e:
            logger.error("_get_cpu_count failed for %s" % e)

    @property
    def x(self):
        """Return self.wait_futures_done"""
        return self.wait_futures_done(list(self._all_futures))

    def wait_futures_done(self, tasks=None):
        # ignore the order of tasks
        tasks = tasks or self._all_futures
        fs = []
        try:
            for f in as_completed(tasks, timeout=self._timeout):
                fs.append(f.x)
        except TimeoutError:
            pass
        return fs


class Pool(ThreadPoolExecutor, NewExecutorPoolMixin):
    """Let ThreadPoolExecutor use NewFuture instead of origin concurrent.futures.Future.

    WARNING: NewFutures in Pool will not block main thread without NewFuture.x.

    Basic Usage::

            from torequests.main import Pool
            import time

            pool = Pool()


            def use_submit(i):
                time.sleep(i)
                result = 'use_submit: %s' % i
                print(result)
                return result


            @pool.async_func
            def use_decorator(i):
                time.sleep(i)
                result = 'use_decorator: %s' % i
                print(result)
                return result


            tasks = [pool.submit(use_submit, i) for i in (2, 1, 0)
                    ] + [use_decorator(i) for i in (2, 1, 0)]
            # pool.x can be ignore
            pool.x
            results = [i.x for i in tasks]
            print(results)

            # use_submit: 0
            # use_decorator: 0
            # use_submit: 1
            # use_decorator: 1
            # use_submit: 2
            # use_decorator: 2
            # ['use_submit: 2', 'use_submit: 1', 'use_submit: 0', 'use_decorator: 2', 'use_decorator: 1', 'use_decorator: 0']
    """

    def __init__(self,
                 n=None,
                 timeout=None,
                 default_callback=None,
                 catch_exception=True,
                 *args,
                 **kwargs):
        n = n or kwargs.pop("max_workers", None)
        if PY2 and n is None:
            # python2 n!=None
            n = (self._get_cpu_count() or 1) * 5
        super(Pool, self).__init__(n, *args, **kwargs)
        #: set the default timeout
        self._timeout = timeout
        #: set the default_callback if not set single task's callback
        self.default_callback = default_callback
        #: WeakSet of _all_futures for self.x
        self._all_futures = WeakSet()
        #: catch_exception=True will not raise exceptions, return object FailureException(exception)
        self.catch_exception = catch_exception

    @property
    def all_tasks(self):
        """Keep the same api for dummy, return self._all_futures actually"""
        return self._all_futures

    def submit(self, func, *args, **kwargs):
        """Submit a function to the pool, `self.submit(function,arg1,arg2,arg3=3)`"""

        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError("cannot schedule new futures after shutdown")
            callback = kwargs.pop("callback", self.default_callback)
            future = NewFuture(
                self._timeout,
                args,
                kwargs,
                callback=callback,
                catch_exception=self.catch_exception,
            )
            w = _WorkItem(future, func, args, kwargs)
            self._work_queue.put(w)
            self._adjust_thread_count()
            self._all_futures.add(future)
            return future


class ProcessPool(ProcessPoolExecutor, NewExecutorPoolMixin):
    """Simple ProcessPool covered ProcessPoolExecutor.
    ::

        from torequests.main import ProcessPool
        import time

        pool = ProcessPool()


        def use_submit(i):
            time.sleep(i)
            result = 'use_submit: %s' % i
            print(result)
            return result


        def main():
            tasks = [pool.submit(use_submit, i) for i in (2, 1, 0)]
            # pool.x can be ignore
            pool.x
            results = [i.x for i in tasks]
            print(results)


        if __name__ == '__main__':
            main()

        # ['use_submit: 2', 'use_submit: 1', 'use_submit: 0']
        # use_submit: 0
        # use_submit: 1
        # use_submit: 2
    """

    def __init__(self,
                 n=None,
                 timeout=None,
                 default_callback=None,
                 catch_exception=True,
                 *args,
                 **kwargs):
        n = n or kwargs.pop("max_workers", None)
        if PY2 and n is None:
            # python2 n!=None
            n = self._get_cpu_count() or 1
        super(ProcessPool, self).__init__(n, *args, **kwargs)
        self._timeout = timeout
        self.default_callback = default_callback
        self._all_futures = WeakSet()
        self.catch_exception = catch_exception

    def submit(self, func, *args, **kwargs):
        """Submit a function to the pool, `self.submit(function,arg1,arg2,arg3=3)`"""

        with self._shutdown_lock:
            if PY3 and self._broken:
                raise BrokenProcessPool(
                    "A child process terminated "
                    "abruptly, the process pool is not usable anymore")
            if self._shutdown_thread:
                raise RuntimeError("cannot schedule new futures after shutdown")
            callback = kwargs.pop("callback", self.default_callback)
            future = NewFuture(
                self._timeout,
                args,
                kwargs,
                callback=callback,
                catch_exception=self.catch_exception,
            )
            w = _WorkItem(future, func, args, kwargs)
            self._pending_work_items[self._queue_count] = w
            self._work_ids.put(self._queue_count)
            self._queue_count += 1
            self._result_queue.put(None)
            self._start_queue_management_thread()
            if PY2:
                self._adjust_process_count()
            self._all_futures.add(future)
            return future

    def async_func(self, *args):
        """Decorator mode not support for ProcessPool for _pickle.PicklingError."""
        raise NotImplementedError


class NewFuture(Future):
    """Add `.x` attribute and timeout args for original Future class

    WARNING: Future thread will not stop running until function finished or pid killed.

    :attr cx: blocking until the task finish and return the callback_result.
    :attr x: blocking until the task finish and return the value as `coro` returned.
    :attr task_start_time: timestamp when the task start up.
    :attr task_end_time: timestamp when the task end up.
    :attr task_cost_time: seconds of task costs.
    :param catch_exception: `True` will catch all exceptions and return as :class:`FailureException <FailureException>`
    """

    if PY3:
        from ._py3_patch import _new_future_await

        __await__ = _new_future_await

    def __init__(self,
                 timeout=None,
                 args=None,
                 kwargs=None,
                 callback=None,
                 catch_exception=True):
        super(NewFuture, self).__init__()
        self._timeout = timeout
        self._args = args or ()
        self._kwargs = kwargs or {}
        self._callback_result = None
        self.catch_exception = catch_exception
        self.task_start_time = time_time()
        self.task_end_time = 0
        self.task_cost_time = 0
        self._user_callbacks = set()
        if callback:
            if not isinstance(callback, (list, tuple)):
                callback = [callback]
            for fn in callback:
                self.add_done_callback(fn)
                self._user_callbacks.add(fn)

    def __getattr__(self, name):
        return getattr(self.x, name)

    def _invoke_callbacks(self):
        """Record the task_end_time & task_cost_time, set result for self._callback_result."""
        self.task_end_time = time_time()
        self.task_cost_time = self.task_end_time - self.task_start_time
        with self._condition:
            for callback in self._done_callbacks:
                try:
                    result = callback(self)
                    if callback in self._user_callbacks:
                        self._callback_result = result
                except Exception as e:
                    logger.error("exception calling callback for %s" % e)
            self._condition.notify_all()

    @property
    def _callbacks(self):
        """Keep same api for NewTask."""
        return self._done_callbacks

    @property
    def cx(self):
        """Block the main thead until future finish, return the future.callback_result."""
        return self.callback_result

    @property
    def callback_result(self):
        """Block the main thead until future finish, return the future.callback_result."""
        if self._state in [PENDING, RUNNING]:
            self.x
        if self._user_callbacks:
            return self._callback_result
        else:
            return self.x

    @property
    def x(self):
        """Block the main thead until future finish, return the future.result()."""
        with self._condition:
            result = None
            if not self.done():
                self._condition.wait(self._timeout)
            if not self.done():
                # timeout
                self.set_exception(TimeoutError())
            if self._state in [CANCELLED, CANCELLED_AND_NOTIFIED]:
                # cancelled
                result = CancelledError()
            elif self._state == FINISHED:
                # finished
                if self._exception:
                    result = self._exception
                else:
                    result = self._result
            if isinstance(result, Exception):
                if self.catch_exception:
                    result = FailureException(result)
                    return result
                else:
                    raise result
            return result


def Async(f, n=None, timeout=None):
    """Concise usage for pool.submit.

    Basic Usage Asnyc & threads ::

        from torequests.main import Async, threads
        import time


        def use_submit(i):
            time.sleep(i)
            result = 'use_submit: %s' % i
            print(result)
            return result


        @threads()
        def use_decorator(i):
            time.sleep(i)
            result = 'use_decorator: %s' % i
            print(result)
            return result


        new_use_submit = Async(use_submit)
        tasks = [new_use_submit(i) for i in (2, 1, 0)
                ] + [use_decorator(i) for i in (2, 1, 0)]
        print([type(i) for i in tasks])
        results = [i.x for i in tasks]
        print(results)

        # use_submit: 0
        # use_decorator: 0
        # [<class 'torequests.main.NewFuture'>, <class 'torequests.main.NewFuture'>, <class 'torequests.main.NewFuture'>, <class 'torequests.main.NewFuture'>, <class 'torequests.main.NewFuture'>, <class 'torequests.main.NewFuture'>]
        # use_submit: 1
        # use_decorator: 1
        # use_submit: 2
        # use_decorator: 2
        # ['use_submit: 2', 'use_submit: 1', 'use_submit: 0', 'use_decorator: 2', 'use_decorator: 1', 'use_decorator: 0']
    """
    return threads(n=n, timeout=timeout)(f)


def threads(n=None, timeout=None):
    """Decorator usage like Async."""
    return Pool(n, timeout).async_func


def get_results_generator(future_list, timeout=None, sort_by_completed=False):
    """Return as a generator of tasks order by completed sequence."""
    try:
        # python2 not support yield from
        if sort_by_completed:
            for future in as_completed(future_list, timeout=timeout):
                yield future.x
        else:
            for future in future_list:
                yield future.x
    except TimeoutError:
        return


def run_after_async(seconds, func, *args, **kwargs):
    """Run the function after seconds asynchronously."""
    t = Timer(seconds, func, args, kwargs)
    t.daemon = True
    t.start()
    return t


class FailedRequest(PreparedRequest):
    allow_keys = {
        "method",
        "url",
        "headers",
        "files",
        "data",
        "params",
        "auth",
        "cookies",
        "hooks",
        "json",
    }

    def __init__(self, **kwargs):
        # self.kwargs for retry tPool.request
        self.kwargs = kwargs
        filted_kwargs = {
            key: value
            for key, value in kwargs.items()
            if key in self.allow_keys
        }
        super(FailedRequest, self).__init__()
        self.prepare(**filted_kwargs)


class tPool(object):
    """Async wrapper for requests.

    :param n: thread pool size for concurrent limit.
    :param interval: time.sleep(interval) after each task finished.
    :param timeout: timeout for each task.result(timeout). But it will not shutdown the raw funtion.
    :param session: individually given a available requests.Session instance if necessary.
    :param catch_exception: `True` will catch all exceptions and return as :class:`FailureException <FailureException>`
    :param default_callback: default_callback for tasks which not set callback param.

    Usage::

        from torequests.main import tPool
        from torequests.logs import print_info

        trequests = tPool(2, 1)
        test_url = 'http://p.3.cn'
        ss = [
            trequests.get(
                test_url,
                retry=2,
                callback=lambda x: (len(x.content), print_info(len(x.content))))
            for i in range(3)
        ]
        # or [i.x for i in ss]
        trequests.x
        ss = [i.cx for i in ss]
        print_info(ss)

        # [2020-02-11 11:36:33] temp_code.py(10): 612
        # [2020-02-11 11:36:33] temp_code.py(10): 612
        # [2020-02-11 11:36:34] temp_code.py(10): 612
        # [2020-02-11 11:36:34] temp_code.py(16): [(612, None), (612, None), (612, None)]
    """

    def __init__(
        self,
        n=None,
        interval=0,
        timeout=None,
        session=None,
        catch_exception=True,
        default_callback=None,
        retry_exceptions=(RequestException, Error),
    ):
        self.pool = Pool(n, timeout)
        self.session = session if session else Session()
        self.n = n or 10
        # adapt the concurrent limit.
        custom_adapter = HTTPAdapter(pool_connections=self.n,
                                     pool_maxsize=self.n)
        self.session.mount("http://", custom_adapter)
        self.session.mount("https://", custom_adapter)
        self.interval = interval
        self.catch_exception = catch_exception
        self.default_callback = default_callback
        self.frequency = Frequency(self.n, self.interval)
        self.retry_exceptions = retry_exceptions

    @property
    def all_tasks(self):
        """Return self.pool._all_futures"""
        return self.pool._all_futures

    @property
    def x(self):
        """Return self.pool.x"""
        return self.pool.x

    def close(self, wait=False):
        """Close session, shutdown pool."""
        self.session.close()
        self.pool.shutdown(wait=wait)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()

    def _request(self,
                 method,
                 url,
                 retry=0,
                 response_validator=None,
                 retry_interval=0,
                 **kwargs):
        if not url:
            raise ValueError("url should not be null, but given: %s" % url)
        kwargs["url"] = url
        kwargs["method"] = method
        # non-official request args
        referer_info = kwargs.pop("referer_info", None)
        encoding = kwargs.pop("encoding", None)
        error = Exception()
        for _ in range(retry + 1):
            with self.frequency:
                try:
                    resp = self.session.request(**kwargs)
                    if encoding:
                        resp.encoding = encoding
                    logger.debug("%s done, %s" % (url, kwargs))
                    resp.referer_info = referer_info
                    if response_validator and not response_validator(resp):
                        raise ValidationError(response_validator.__name__)
                    return resp
                except self.retry_exceptions as e:
                    error = e
                    logger.debug(
                        "Retry %s for the %s time, Exception: %r . kwargs= %s" %
                        (url, _ + 1, e, kwargs))
                    if retry_interval:
                        sleep(retry_interval)
                    continue
        # for unofficial request args
        kwargs["retry"] = retry
        if referer_info:
            kwargs["referer_info"] = referer_info
        if encoding:
            kwargs["encoding"] = encoding
        logger.debug("Retry %s times failed again: %s." % (retry, error))
        failure = FailureException(error)
        failure.request = FailedRequest(**kwargs)
        if self.catch_exception:
            return failure
        else:
            raise failure

    def request(self,
                method,
                url,
                callback=None,
                retry=0,
                response_validator=None,
                **kwargs):
        """Similar to `requests.request`, but return as NewFuture."""
        return self.pool.submit(self._request,
                                method=method,
                                url=url,
                                retry=retry,
                                response_validator=response_validator,
                                callback=callback or self.default_callback,
                                **kwargs)

    def get(self,
            url,
            params=None,
            callback=None,
            retry=0,
            response_validator=None,
            **kwargs):
        """Similar to `requests.get`, but return as NewFuture."""
        kwargs.setdefault("allow_redirects", True)
        return self.request("get",
                            url=url,
                            params=params,
                            callback=callback,
                            retry=retry,
                            response_validator=response_validator,
                            **kwargs)

    def post(self,
             url,
             data=None,
             json=None,
             callback=None,
             retry=0,
             response_validator=None,
             **kwargs):
        """Similar to `requests.post`, but return as NewFuture."""
        return self.request("post",
                            url=url,
                            data=data,
                            json=json,
                            callback=callback,
                            retry=retry,
                            response_validator=response_validator,
                            **kwargs)

    def delete(self,
               url,
               callback=None,
               retry=0,
               response_validator=None,
               **kwargs):
        """Similar to `requests.delete`, but return as NewFuture."""
        return self.request("delete",
                            url=url,
                            callback=callback,
                            retry=retry,
                            response_validator=response_validator,
                            **kwargs)

    def put(self,
            url,
            data=None,
            callback=None,
            retry=0,
            response_validator=None,
            **kwargs):
        """Similar to `requests.put`, but return as NewFuture."""
        return self.request("put",
                            url=url,
                            data=data,
                            callback=callback,
                            retry=retry,
                            response_validator=response_validator,
                            **kwargs)

    def head(self,
             url,
             callback=None,
             retry=0,
             response_validator=None,
             allow_redirects=False,
             **kwargs):
        """Similar to `requests.head`, but return as NewFuture."""
        kwargs['allow_redirects'] = allow_redirects
        return self.request("head",
                            url=url,
                            callback=callback,
                            retry=retry,
                            response_validator=response_validator,
                            **kwargs)

    def options(self,
                url,
                callback=None,
                retry=0,
                response_validator=None,
                **kwargs):
        """Similar to `requests.options`, but return as NewFuture."""
        kwargs.setdefault("allow_redirects", True)
        return self.request("options",
                            url=url,
                            callback=callback,
                            retry=retry,
                            response_validator=response_validator,
                            **kwargs)

    def patch(self,
              url,
              callback=None,
              retry=0,
              response_validator=None,
              **kwargs):
        """Similar to `requests.patch`, but return as NewFuture."""
        return self.request("patch",
                            url=url,
                            callback=callback,
                            retry=retry,
                            response_validator=response_validator,
                            **kwargs)


def get(url,
        params=None,
        callback=None,
        retry=0,
        response_validator=None,
        **kwargs):
    return tPool().get(url,
                       params=params,
                       callback=callback,
                       retry=retry,
                       response_validator=response_validator,
                       **kwargs)


def post(url,
         data=None,
         json=None,
         callback=None,
         retry=0,
         response_validator=None,
         **kwargs):
    return tPool().post(url,
                        data=data,
                        json=json,
                        callback=callback,
                        retry=retry,
                        response_validator=response_validator,
                        **kwargs)


def delete(url, callback=None, retry=0, response_validator=None, **kwargs):
    return tPool().delete(url,
                          callback=callback,
                          retry=retry,
                          response_validator=response_validator,
                          **kwargs)


def put(url,
        data=None,
        callback=None,
        retry=0,
        response_validator=None,
        **kwargs):
    return tPool().put(url,
                       data=data,
                       callback=callback,
                       retry=retry,
                       response_validator=response_validator,
                       **kwargs)


def head(url, callback=None, retry=0, response_validator=None, **kwargs):
    return tPool().head(url,
                        callback=callback,
                        retry=retry,
                        response_validator=response_validator,
                        **kwargs)


def options(url, callback=None, retry=0, response_validator=None, **kwargs):
    return tPool().options(url,
                           callback=callback,
                           retry=retry,
                           response_validator=response_validator,
                           **kwargs)


def patch(url, callback=None, retry=0, response_validator=None, **kwargs):
    return tPool().patch(url,
                         callback=callback,
                         retry=retry,
                         response_validator=response_validator,
                         **kwargs)


def request(method,
            url,
            callback=None,
            retry=0,
            response_validator=None,
            **kwargs):
    return tPool().request(method,
                           url,
                           callback=callback,
                           retry=retry,
                           response_validator=response_validator,
                           **kwargs)


class Workshop:
    """Simple solution for producer-consumer problem.
    WARNING: callback should has its own timeout to avoid blocking to long.

    Demo::

        import time

        from torequests.main import Workshop


        def callback(todo, worker_arg):
            time.sleep(todo)
            if worker_arg == 'worker1':
                return None
            return [todo, worker_arg]


        fc = Workshop(range(1, 5), ['worker1', 'worker2', 'worker3'], callback)

        for i in fc.get_result_as_completed():
            print(i)
        # [2, 'worker2']
        # [3, 'worker3']
        # [1, 'worker2']
        # [4, 'worker3']
        for i in fc.get_result_as_sequence():
            print(i)
        # [1, 'worker3']
        # [2, 'worker3']
        # [3, 'worker3']
        # [4, 'worker2']
"""

    def __init__(self,
                 todo_args,
                 worker_args,
                 callback,
                 timeout=None,
                 wait_empty_secs=1,
                 handle_exceptions=(),
                 max_failure=None,
                 fail_returned=None):
        """
        :param todo_args: args to be send to callback
        :type todo_args: List[Any]
        :param worker_args: args for launching worker threads, you can use like [worker1, worker1, worker1] for concurrent workers
        :type worker_args: List[Any]
        :param callback: callback to consume the todo_arg from queue, handle args like callback(todo_arg, worker_arg)
        :type callback: Callable
        :param timeout: timeout for worker running, defaults to None
        :type timeout: [float, int], optional
        :param wait_empty_secs: seconds to sleep while queue is Empty, defaults to 1
        :type wait_empty_secs: float, optional
        :param handle_exceptions: ignore Exceptions raise from callback, defaults to ()
        :type handle_exceptions: Tuple[Exception], optional
        :param max_failure: stop worker while failing too many times, defaults to None
        :type max_failure: int, optional
        :param fail_returned: returned from callback will be treated as a failure, defaults to None
        :type fail_returned: Any, optional
        """
        self.q = Queue()
        self.futures = self.init_futures(todo_args)
        self.worker_args = worker_args
        self.callback = callback
        self.timeout = timeout or float('inf')
        self.wait_empty_secs = wait_empty_secs
        self.result = None
        self.handle_exceptions = handle_exceptions
        self.max_failure = float('inf') if max_failure is None else max_failure
        self.fail_returned = fail_returned
        self._done = False
        self._done_signal = object()

    def init_futures(self, todo_args):
        futures = []
        for arg in todo_args:
            f = Future()
            f.arg = arg
            futures.append(f)
            self.q.put(f)
        return futures

    def run(self, as_completed=False):
        """run until all tasks finished"""
        if as_completed:
            return list(self.get_result_as_completed())
        return list(self.get_result_as_sequence())

    def get_result_as_sequence(self):
        """return a generator of results with same sequence as self.todo_args"""
        self.start_workers()
        for f in self.futures:
            yield f.result()

    def get_result_as_completed(self):
        """return a generator of results as completed sequence"""
        self.start_workers()
        for f in as_completed(self.futures):
            yield f.result()

    @property
    def done(self):
        self._done = self._done or all((f.done() for f in self.futures))
        return self._done

    def worker(self, worker_arg):
        fails = 0
        start_time = time_time()
        while time_time(
        ) - start_time < self.timeout and fails <= self.max_failure:
            try:
                f = self.q.get(timeout=self.wait_empty_secs)
                if f is self._done_signal:
                    break
            except TimeoutError:
                if self.done:
                    break
                fails += 1
                continue
            try:
                result = self.callback(f.arg, worker_arg)
            except self.handle_exceptions as err:
                logger.error(
                    'Raised {err!r}, worker_arg: {worker_arg}, todo_arg: {arg}'.
                    format_map(
                        dict(err=err,
                             worker_arg=repr(worker_arg)[:100],
                             arg=repr(f.arg)[:100])))
                result = self.fail_returned
            if result == self.fail_returned:
                self.q.put(f)
                fails += 1
                sleep(self.wait_empty_secs)
                continue
            else:
                f.set_result(result)
                if fails > 0:
                    fails -= 1
        self.q.put_nowait

    def start_workers(self):
        self._done = False
        for worker_arg in self.worker_args:
            t = Thread(target=self.worker, args=(worker_arg,))
            t.daemon = True
            t.start()
