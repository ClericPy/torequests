#! coding:utf-8
# python2 requires: pip install futures
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from concurrent.futures._base import Future
from concurrent.futures.thread import _WorkItem
from functools import wraps

from requests import Session
from requests.adapters import HTTPAdapter

from .log import main_logger
from .utils import RequestsException


class Pool(ThreadPoolExecutor):

    def __init__(self, n=None, timeout=None):
        if n is None and (not isinstance(range, type)):
            # python2 n!=None
            n = 20
        super(Pool, self).__init__(n)
        self._timeout = timeout

    def async_func(self, f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            return self.submit(f, *args, **kwargs)
        return wrapped

    def close(self, wait=True):
        self.shutdown(wait=wait)

    def submit(self, func, *args, **kwargs):
        '''self.submit(function,arg1,arg2,arg3=3)'''

        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError(
                    'cannot schedule new futures after shutdown')
            future = NewFuture(self._timeout, args, kwargs)
            callback = kwargs.pop('callback', None)
            if callback:
                if not isinstance(callback, (list, tuple)):
                    callback = [callback]
                for fn in callback:
                    future.add_done_callback(future.wrap_callback(fn))
            w = _WorkItem(future, func, args, kwargs)
            self._work_queue.put(w)
            self._adjust_thread_count()
            return future


class NewFuture(Future):

    """add .x (property) and timeout args for original Future
    WARNING: Future thread will not stop running until function finished or pid killed.
    """

    def __init__(self, timeout=None, args=None, kwargs=None):
        super(NewFuture, self).__init__()
        self._timeout = timeout
        self._args = args or ()
        self._kwargs = kwargs or {}

    def __getattr__(self, name):
        return self.result(self._timeout).__getattribute__(name)

    @staticmethod
    def wrap_callback(function):
        @wraps(function)
        def wrapped(future):
            future.callback_result = function(future)
            return future.callback_result
        return wrapped

    @property
    def x(self):
        return self.result(self._timeout)


def Async(f, n=None, timeout=None):
    return threads(n=n, timeout=timeout)(f)


def threads(n=None, timeout=None):
    return Pool(n, timeout).async_func


def get_results_generator(future_list, timeout=None, sort_by_completed=False):
    '''Return as a generator, python2 not support yield from...'''
    if sort_by_completed:
        for future in as_completed(future_list, timeout=timeout):
            yield future.x
    else:
        for future in future_list:
            yield future.x

class tPool():

    def __init__(self, n=None, session=None, timeout=None, time_interval=0,
                 catch_exception=False):
        self.pool = Pool(n, timeout)
        self.session = session if session else Session()
        pool_size = n or 10
        custom_adapter = HTTPAdapter(
            pool_connections=pool_size, pool_maxsize=pool_size)
        self.session.mount('http://', custom_adapter)
        self.session.mount('https://', custom_adapter)
        self.time_interval = time_interval
        self.catch_exception = catch_exception

    def close(self, wait=True):
        self.session.close()
        self.pool.shutdown(wait=wait)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()

    def request(self, url, mode, retry=0, **kwargs):
        for _ in range(retry + 1):
            try:
                resp = self.session.request(mode, url, **kwargs)
                main_logger.debug('%s done, %s' % (url, kwargs))

                return resp
            except Exception as e:
                error = e
                main_logger.debug('Retry %s for the %s time, Exception: %s . kwargs= %s' %
                                  (url, _ + 1, e, kwargs))
                continue
            finally:
                if self.time_interval:
                    time.sleep(self.time_interval)
        kwargs['retry'] = retry
        error_info = dict(url=url, kwargs=kwargs,
                          type=type(error), error_msg=str(error))
        error.args = (error_info,)
        main_logger.error(
            'Retry %s & failed: %s.' %
            (retry, error_info))
        if self.catch_exception:
            return RequestsException(error)
        raise error

    def get(self, url, **kwargs):
        return self.pool.submit(self.request, url, 'get', **kwargs)

    def post(self, url, **kwargs):
        return self.pool.submit(self.request, url, 'post', **kwargs)

    def delete(self, url, **kwargs):
        return self.pool.submit(self.request, url, 'delete', **kwargs)

    def put(self, url, **kwargs):
        return self.pool.submit(self.request, url, 'put', **kwargs)

    def head(self, url, **kwargs):
        return self.pool.submit(self.request, url, 'head', **kwargs)
