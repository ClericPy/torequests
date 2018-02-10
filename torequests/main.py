#! coding:utf-8
# python2 requires: pip install futures
import sys
import time
from weakref import WeakSet
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed, wait
from concurrent.futures._base import Future, TimeoutError, Executor
from concurrent.futures.thread import _WorkItem
from functools import wraps

from requests import Session
from requests.adapters import HTTPAdapter

from .exceptions import FailureException
from .logs import main_logger
from .versions import PY2, PY3

if PY3:
    from concurrent.futures.process import BrokenProcessPool


class NewExecutorPool(Executor):
    """add async_func(function decorator) for submitting called-function into NewExecutorPool obj."""

    def __init__(self, n=None, timeout=None, default_callback=None):
        if n is None and (not isinstance(range, type)):
            # python2 n!=None
            n = 20
        super(NewExecutorPool, self).__init__(n)
        self._timeout = timeout
        self.default_callback = default_callback
        self._all_futures = WeakSet()

    def async_func(self, function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            return self.submit(function, *args, **kwargs)

        return wrapped

    def close(self, wait=True):
        self.shutdown(wait=wait)

    @property
    def x(self):
        return self.wait_futures_done(list(self._all_futures))

    def wait_futures_done(self, tasks=None):
        # ignore the order of tasks
        tasks = tasks or self._all_futures
        fs = {f.x for f in wait(tasks).done}
        return fs


class Pool(NewExecutorPool, ThreadPoolExecutor):
    def __init__(self, *args, **kwargs):
        super(Pool, self).__init__(*args, **kwargs)

    def submit(self, func, *args, **kwargs):
        """self.submit(function,arg1,arg2,arg3=3)"""

        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError(
                    'cannot schedule new futures after shutdown')
            future = NewFuture(self._timeout, args, kwargs)
            callback = kwargs.pop('callback', self.default_callback)
            if callback:
                if not isinstance(callback, (list, tuple)):
                    callback = [callback]
                for fn in callback:
                    future.add_done_callback(future.wrap_callback(fn))
            w = _WorkItem(future, func, args, kwargs)
            self._work_queue.put(w)
            self._adjust_thread_count()
            self._all_futures.add(future)
            return future


class ProcessPool(NewExecutorPool, ProcessPoolExecutor):
    def __init__(self, *args, **kwargs):
        super(ProcessPool, self).__init__(*args, **kwargs)

    def submit(self, func, *args, **kwargs):
        """self.submit(function,arg1,arg2,arg3=3)"""

        with self._shutdown_lock:
            if PY3 and self._broken:
                raise BrokenProcessPool(
                    'A child process terminated '
                    'abruptly, the process pool is not usable anymore')
            if self._shutdown_thread:
                raise RuntimeError(
                    'cannot schedule new futures after shutdown')
            future = NewFuture(self._timeout, args, kwargs)
            callback = kwargs.pop('callback', self.default_callback)
            if callback:
                if not isinstance(callback, (list, tuple)):
                    callback = [callback]
                for fn in callback:
                    future.add_done_callback(future.wrap_callback(fn))
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


class NewFuture(Future):
    """add .x (property) and timeout args for original Future class
    
    WARNING: Future thread will not stop running until function finished or pid killed.
    """
    if PY3:
        from ._py3_patch import new_future_await
        __await__ = new_future_await

    def __init__(self, timeout=None, args=None, kwargs=None):
        super(NewFuture, self).__init__()
        self._timeout = timeout
        self._args = args or ()
        self._kwargs = kwargs or {}
        self._callback_result = None

    def __getattr__(self, name):
        try:
            object.__getattribute__(self, name)
        except AttributeError:
            return self.x.__getattribute__(name)

    @staticmethod
    def wrap_callback(function):
        @wraps(function)
        def wrapped(future):
            future._callback_result = function(future)
            return future._callback_result

        return wrapped

    @property
    def cx(self):
        return self.callback_result

    @property
    def callback_result(self):
        if self._state == 'PENDING':
            self.x
        if self._done_callbacks:
            return self._callback_result
        else:
            return self.x

    @property
    def x(self):
        return self.result(self._timeout)


def Async(f, n=None, timeout=None):
    return threads(n=n, timeout=timeout)(f)


def threads(n=None, timeout=None):
    return Pool(n, timeout).async_func


def get_results_generator(future_list, timeout=None, sort_by_completed=False):
    """Return as a generator, python2 not support yield from..."""
    try:
        if sort_by_completed:
            for future in as_completed(future_list, timeout=timeout):
                yield future.x
        else:
            for future in future_list:
                yield future.x
    except TimeoutError:
        return


@threads(1)
def run_after_async(seconds, func, *args, **kwargs):
    time.sleep(seconds)
    return func(*args, **kwargs)


class tPool(object):
    def __init__(self,
                 n=None,
                 interval=0,
                 timeout=None,
                 session=None,
                 catch_exception=True,
                 default_callback=None):
        self.pool = Pool(n, timeout)
        self.session = session if session else Session()
        self.n = n or 10
        custom_adapter = HTTPAdapter(
            pool_connections=self.n, pool_maxsize=self.n)
        self.session.mount('http://', custom_adapter)
        self.session.mount('https://', custom_adapter)
        self.interval = interval
        self.catch_exception = catch_exception
        self.default_callback = default_callback

    @property
    def x(self):
        return self.pool.x

    def close(self, wait=True):
        self.session.close()
        self.pool.shutdown(wait=wait)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()

    def _request(self, method, url, retry=0, **kwargs):
        for _ in range(retry + 1):
            try:
                resp = self.session.request(method, url, **kwargs)
                main_logger.debug('%s done, %s' % (url, kwargs))

                return resp
            except Exception as e:
                error = e
                main_logger.debug(
                    'Retry %s for the %s time, Exception: %s . kwargs= %s' %
                    (url, _ + 1, e, kwargs))
                continue
            finally:
                if self.interval:
                    time.sleep(self.interval)
        kwargs['retry'] = retry
        error_info = dict(
            url=url, kwargs=kwargs, type=type(error), error_msg=str(error))
        error.args = (error_info, )
        main_logger.debug('Retry %s & failed: %s.' % (retry, error_info))
        if self.catch_exception:
            return FailureException(error)
        raise error

    def request(self, method, url, callback=None, **kwargs):
        return self.pool.submit(
            self._request,
            method,
            url,
            callback=callback or self.default_callback,
            **kwargs)

    def get(self, url, callback=None, **kwargs):
        return self.request('get', url, callback, **kwargs)

    def post(self, url, callback=None, **kwargs):
        return self.request('post', url, callback, **kwargs)

    def delete(self, url, callback=None, **kwargs):
        return self.request('delete', url, callback, **kwargs)

    def put(self, url, callback=None, **kwargs):
        return self.request('put', url, callback, **kwargs)

    def head(self, url, callback=None, **kwargs):
        return self.request('head', url, callback, **kwargs)

    def options(self, url, callback=None, **kwargs):
        return self.request('options', url, callback, **kwargs)

    def patch(self, url, callback=None, **kwargs):
        return self.request('patch', url, callback, **kwargs)
