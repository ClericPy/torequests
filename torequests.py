# python2 need pip install futures
import requests
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
import time


class Tomorrow():

    def __init__(self, future, timeout1):
        self._future = future
        self._timeout1 = timeout1
        self._wait = self._future.result

    def __getattr__(self, name):
        result = self._future.result(self._timeout1)
        return result.__getattribute__(name)

    @property
    def x(self):
        return self._wait()


def async1(n, base_type, timeout1=None):
    def decorator(f):
        if isinstance(n, int):
            pool = base_type(n)
        elif isinstance(n, base_type):
            pool = n
        else:
            raise TypeError(
                "Invalid type: %s"
                % type(base_type)
            )

        @wraps(f)
        def wrapped(*args, **kwargs):
            return Tomorrow(
                pool.submit(f, *args, **kwargs),
                timeout1=timeout1
            )
        return wrapped
    return decorator


def threads(n=30, timeout1=None):
    return async1(n, ThreadPoolExecutor, timeout1)


def async(func, n=30):
    return threads(n=n)(func)


class tPool():

    def __init__(self, num=30, session=None):
        self.num = num
        self.session = session

    def get(self, url, retry=0, retrylog=False, logging=None, delay=0, fail_return=False, **kws):
        @threads(self.num)
        def get1(url, **kws):
            for _ in range(retry+1):
                try:
                    time.sleep(delay)
                    if self.session:
                        ss = self.session.get(url, **kws)
                        if logging:
                            print(url, logging)
                        return ss
                    ss = requests.get(url, **kws)
                    if logging:
                        print(url, logging)
                    return ss
                except Exception as e:
                    if retrylog:
                        print('retry %s for the %s time, as the Exception:' % (url, _+1), e)
                    continue
            return fail_return
        return get1(url, **kws)

    def post(self, url, retry=0, retrylog=False, logging=None, delay=0, fail_return=False, **kws):
        @threads(self.num)
        def post1(url, **kws):
            for _ in range(retry+1):
                try:
                    time.sleep(delay)
                    if self.session:
                        ss = self.session.post(url, **kws)
                        if logging:
                            print(url, logging)
                        return ss
                    ss = requests.post(url, **kws)
                    if logging:
                        print(url, logging)
                    return ss
                except Exception as e:
                    if retrylog:
                        print('retry %s for the %s time, as the Exception:' % (url, _+1), e)
                    continue
            return fail_return
        return post1(url, **kws)

    def delete(self, url, retry=0, retrylog=False, logging=None, delay=0, fail_return=False, **kws):
        @threads(self.num)
        def delete1(url, **kws):
            for _ in range(retry+1):
                try:
                    time.sleep(delay)
                    if self.session:
                        ss = self.session.delete(url, **kws)
                        if logging:
                            print(url, logging)
                        return ss
                    ss = requests.delete(url, **kws)
                    if logging:
                        print(url, logging)
                    return ss
                except Exception as e:
                    if retrylog:
                        print('retry %s for the %s time, as the Exception:' % (url, _+1), e)
                    continue
            return fail_return
        return delete1(url, **kws)

    def put(self, url, retry=0, retrylog=False, logging=None, delay=0, fail_return=False, **kws):
        @threads(self.num)
        def put1(url, **kws):
            for _ in range(retry+1):
                try:
                    time.sleep(delay)
                    if self.session:
                        ss = self.session.put(url, **kws)
                        if logging:
                            print(url, logging)
                        return ss
                    ss = requests.put(url, **kws)
                    if logging:
                        print(url, logging)
                    return ss
                except Exception as e:
                    if retrylog:
                        print('retry %s for the %s time, as the Exception:' % (url, _+1), e)
                    continue
            return fail_return
        return put1(url, **kws)

    def head(self, url, retry=0, retrylog=False, logging=None, delay=0, fail_return=False, **kws):
        @threads(self.num)
        def head1(url, **kws):
            for _ in range(retry+1):
                try:
                    time.sleep(delay)
                    if self.session:
                        ss = self.session.head(url, **kws)
                        if logging:
                            print(url, logging)
                        return ss
                    ss = requests.head(url, **kws)
                    if logging:
                        print(url, logging)
                    return ss
                except Exception as e:
                    if retrylog:
                        print('retry %s for the %s time, as the Exception:' % (url, _+1), e)
                    continue
            return fail_return
        return head1(url, **kws)
