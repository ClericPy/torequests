#! coding:utf-8
# python2 requires: pip install futures
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures._base import Future, TimeoutError
from concurrent.futures.thread import _WorkItem
from functools import wraps

from requests import Session
from requests.adapters import HTTPAdapter

from .utils import FailureException, main_logger


class Pool(ThreadPoolExecutor):
    '''
    add async_func(function decorator) for submitting called-function into Pool obj.
    '''

    def __init__(self, n=None, timeout=None, default_callback=None):
        if n is None and (not isinstance(range, type)):
            # python2 n!=None
            n = 20
        super(Pool, self).__init__(n)
        self._timeout = timeout
        self.default_callback = default_callback

    def async_func(self, function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            return self.submit(function, *args, **kwargs)
        return wrapped

    def close(self, wait=True):
        self.shutdown(wait=wait)

    @staticmethod
    def wrap_callback(function):
        @wraps(function)
        def wrapped(future):
            future._callback_result = function(future)
            return future._callback_result
        return wrapped

    def submit(self, func, *args, **kwargs):
        '''self.submit(function,arg1,arg2,arg3=3)'''

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
                    future.add_done_callback(self.wrap_callback(fn))
            w = _WorkItem(future, func, args, kwargs)
            self._work_queue.put(w)
            self._adjust_thread_count()
            return future


class NewFuture(Future):

    """add .x (property) and timeout args for original Future class
    WARNING: Future thread will not stop running until function finished or pid killed.
    """

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
    '''Return as a generator, python2 not support yield from...'''
    try:
        if sort_by_completed:
            for future in as_completed(future_list, timeout=timeout):
                yield future.x
        else:
            for future in future_list:
                yield future.x
    except TimeoutError:
        return


class tPool(object):

    def __init__(self, n=None, session=None, timeout=None, time_interval=0,
                 catch_exception=True, default_callback=None):
        self.pool = Pool(n, timeout)
        self.session = session if session else Session()
        pool_size = n or 10
        custom_adapter = HTTPAdapter(
            pool_connections=pool_size, pool_maxsize=pool_size)
        self.session.mount('http://', custom_adapter)
        self.session.mount('https://', custom_adapter)
        self.time_interval = time_interval
        self.catch_exception = catch_exception
        self.default_callback = default_callback

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
        main_logger.debug(
            'Retry %s & failed: %s.' %
            (retry, error_info))
        if self.catch_exception:
            return FailureException(error)
        raise error

    def get(self, url, callback=None, **kwargs):
        return self.pool.submit(self.request, url, 'get',
                                callback=callback or self.default_callback, **kwargs)

    def post(self, url, callback=None, **kwargs):
        return self.pool.submit(self.request, url, 'post',
                                callback=callback or self.default_callback, **kwargs)

    def delete(self, url, callback=None, **kwargs):
        return self.pool.submit(self.request, url, 'delete',
                                callback=callback or self.default_callback, **kwargs)

    def put(self, url, callback=None, **kwargs):
        return self.pool.submit(self.request, url, 'put',
                                callback=callback or self.default_callback, **kwargs)

    def head(self, url, callback=None, **kwargs):
        return self.pool.submit(self.request, url, 'head',
                                callback=callback or self.default_callback, **kwargs)
