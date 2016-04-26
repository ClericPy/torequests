# python2 requires: pip install futures
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from concurrent.futures._base import Future
from concurrent.futures.thread import _WorkItem
from functools import wraps
import time
import requests
from requests import Session


class AsyncPool(ThreadPoolExecutor):

    def __init__(self, num, timeout, timeout_return):
        super(AsyncPool, self).__init__(num)
        self.timeout = timeout
        self.timeout_return = timeout_return

    def async_func(self):
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                return self.submit(f, *args, **kwargs)
            return wrapped
        return decorator

    def submit(self, fn, *args, **kwargs):
        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('cannot schedule new futures after shutdown')
            f = NewFuture(self.timeout, self.timeout_return)
            w = _WorkItem(f, fn, args, kwargs)
            self._work_queue.put(w)
            self._adjust_thread_count()
            return f


class NewFuture(Future):

    """add .x (property) and timeout/timeout_return args for original Future"""

    def __init__(self, timeout=None, timeout_return='TimeoutError'):
        super(NewFuture, self).__init__()
        self._timeout = timeout
        self._timeout_return = timeout_return

    def __getattr__(self, name):
        result = self.result(self._timeout)
        return result.__getattribute__(name)

    @property
    def x(self):
        try:
            return self.result(self._timeout)
        except TimeoutError:
            return self._timeout_return


def Async(f, n=30, timeout=None, timeout_return='TimeoutError'):
    '''Here "Async" is not a class object, upper "A" only be used to differ from keyword "async" since python3.5+.'''
    return AsyncPool(n, timeout, timeout_return).async_func()(f)

# async = Async  # This has be abandoned even before Python3.7 released.


def threads(n=30, timeout=None, timeout_return='TimeoutError'):
    return AsyncPool(n, timeout, timeout_return).async_func()


def get_by_time(fs, timeout=None):
    '''Return a generator'''
    try:
        for i in as_completed(fs, timeout=timeout):
            yield i.x
    except Exception as e:
        yield e


class tPool():

    def __init__(self, num=30, session=None):
        self.num = num
        self.session = session if session else requests

    def get(self, url, retry=0, retrylog=False, logging=None, delay=0, fail_return=False, **kws):
        @threads(self.num)
        def get1(url, **kws):
            for _ in range(retry+1):
                try:
                    time.sleep(delay)
                    ss = self.session.get(url, **kws)
                    if logging:
                        print(url, logging)
                    return ss
                except Exception as e:
                    if retrylog:
                        print('Retry %s for the %s time,Exception:' %
                              (url, _+1), e)
                    continue
            return fail_return
        return get1(url, **kws)

    def post(self, url, retry=0, retrylog=False, logging=None, delay=0, fail_return=False, **kws):
        @threads(self.num)
        def post1(url, **kws):
            for _ in range(retry+1):
                try:
                    time.sleep(delay)
                    ss = self.session.post(url, **kws)
                    if logging:
                        print(url, logging)
                    return ss
                except Exception as e:
                    if retrylog:
                        print('Retry %s for the %s time,Exception:' %
                              (url, _+1), e)
                    continue
            return fail_return
        return post1(url, **kws)

    def delete(self, url, retry=0, retrylog=False, logging=None, delay=0, fail_return=False, **kws):
        @threads(self.num)
        def delete1(url, **kws):
            for _ in range(retry+1):
                try:
                    time.sleep(delay)
                    ss = self.session.delete(url, **kws)
                    if logging:
                        print(url, logging)
                    return ss
                except Exception as e:
                    if retrylog:
                        print('Retry %s for the %s time,Exception:' %
                              (url, _+1), e)
                    continue
            return fail_return
        return delete1(url, **kws)

    def put(self, url, retry=0, retrylog=False, logging=None, delay=0, fail_return=False, **kws):
        @threads(self.num)
        def put1(url, **kws):
            for _ in range(retry+1):
                try:
                    time.sleep(delay)
                    ss = self.session.put(url, **kws)
                    if logging:
                        print(url, logging)
                    return ss
                except Exception as e:
                    if retrylog:
                        print('Retry %s for the %s time,Exception:' %
                              (url, _+1), e)
                    continue
            return fail_return
        return put1(url, **kws)

    def head(self, url, retry=0, retrylog=False, logging=None, delay=0, fail_return=False, **kws):
        @threads(self.num)
        def head1(url, **kws):
            for _ in range(retry+1):
                try:
                    time.sleep(delay)
                    ss = self.session.head(url, **kws)
                    if logging:
                        print(url, logging)
                    return ss
                except Exception as e:
                    if retrylog:
                        print('Retry %s for the %s time,Exception:' %
                              (url, _+1), e)
                    continue
            return fail_return
        return head1(url, **kws)
