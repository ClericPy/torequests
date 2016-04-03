# python2 requires: pip install futures
import requests
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import time


class Tomorrow():

    def __init__(self, future, timeout, timeout_return):
        self._future = future
        self._timeout = timeout
        self._timeout_return = timeout_return

    def __getattr__(self, name):
        result = self._future.result(self._timeout)
        return result.__getattribute__(name)

    @property
    def x(self):
        try:
            return self._future.result(self._timeout)
        except TimeoutError:
            return self._timeout_return


def async1(n, base_type, timeout=None, timeout_return='TimeoutError'):
    def decorator(f):
        if isinstance(n, int):
            pool = base_type(n)
        elif isinstance(n, base_type):
            pool = n
        else:
            raise TypeError("Invalid type: %s" % type(base_type))

        @wraps(f)
        def wrapped(*args, **kwargs):
            return Tomorrow(pool.submit(f, *args, **kwargs), timeout=timeout, timeout_return=timeout_return)
        return wrapped
    return decorator


def threads(n=30, timeout=None, timeout_return='TimeoutError'):
    return async1(n, ThreadPoolExecutor, timeout)


def async(function, n=30, timeout=None, timeout_return='TimeoutError'):
    return async1(n, base_type=ThreadPoolExecutor, timeout=timeout, timeout_return=timeout_return)(function)


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
