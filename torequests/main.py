#! coding:utf-8
# python2 requires: pip install futures

import time
from concurrent.futures import (ProcessPoolExecutor, ThreadPoolExecutor,
                                as_completed, wait)
from concurrent.futures._base import Executor, Future, TimeoutError
from concurrent.futures.thread import _WorkItem
from functools import wraps
from weakref import WeakSet

from requests import Session
from requests.adapters import HTTPAdapter

from .configs import Config
from .exceptions import FailureException
from .versions import PY2, PY3

if PY3:
    from concurrent.futures.process import BrokenProcessPool


def get_cpu_count():
    try:
        from multiprocessing import cpu_count
        return cpu_count()
    except Exception as e:
        Config.main_logger.error('get_cpu_count failed for %s' % e)


class NewExecutorPoolMixin(Executor):
    """add async_func(function decorator) for submitting."""

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


class Pool(ThreadPoolExecutor, NewExecutorPoolMixin):

    def __init__(self,
                 n=None,
                 timeout=None,
                 default_callback=None,
                 *args,
                 **kwargs):
        n = n or kwargs.pop('max_workers', None)
        if PY2 and n is None:
            # python2 n!=None
            n = (get_cpu_count() or 1) * 5
        super(Pool, self).__init__(n, *args, **kwargs)
        self._timeout = timeout
        self.default_callback = default_callback
        self._all_futures = WeakSet()

    def submit(self, func, *args, **kwargs):
        """self.submit(function,arg1,arg2,arg3=3)"""

        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('cannot schedule new futures after shutdown')
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


class ProcessPool(ProcessPoolExecutor, NewExecutorPoolMixin):

    def __init__(self,
                 n=None,
                 timeout=None,
                 default_callback=None,
                 *args,
                 **kwargs):
        n = n or kwargs.pop('max_workers', None)
        if PY2 and n is None:
            # python2 n!=None
            n = get_cpu_count() or 1
        super(ProcessPool, self).__init__(n, *args, **kwargs)
        self._timeout = timeout
        self.default_callback = default_callback
        self._all_futures = WeakSet()

    def submit(self, func, *args, **kwargs):
        """self.submit(function,arg1,arg2,arg3=3)"""

        with self._shutdown_lock:
            if PY3 and self._broken:
                raise BrokenProcessPool(
                    'A child process terminated '
                    'abruptly, the process pool is not usable anymore')
            if self._shutdown_thread:
                raise RuntimeError('cannot schedule new futures after shutdown')
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
                Config.main_logger.debug('%s done, %s' % (url, kwargs))

                return resp
            except Exception as e:
                error = e
                Config.main_logger.debug(
                    'Retry %s for the %s time, Exception: %s . kwargs= %s' %
                    (url, _ + 1, e, kwargs))
                continue
            finally:
                if self.interval:
                    time.sleep(self.interval)
        kwargs['retry'] = retry
        error_info = dict(
            url=url, kwargs=kwargs, type=type(error), error_msg=str(error))
        error.args = (error_info,)
        Config.main_logger.debug('Retry %s & failed: %s.' % (retry, error_info))
        if self.catch_exception:
            return FailureException(error)
        raise error

    def request(self, method, url, callback=None, retry=0, **kwargs):
        return self.pool.submit(
            self._request,
            method=method,
            url=url,
            retry=retry,
            callback=callback or self.default_callback,
            **kwargs)

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
