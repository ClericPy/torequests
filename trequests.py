import requests
from functools import wraps
from concurrent.futures import ThreadPoolExecutor

'''
thanks for requests & tomorrow...
'''


class Tomorrow():

    def __init__(self, future, timeout1):
        self._future = future
        self._timeout1 = timeout1
        self._wait = self._future.result

    def __getattr__(self, name):
        result = self._future.result(self._timeout1)
        return result.__getattribute__(name)


def async(n, base_type, timeout1=None):
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


def threads(n, timeout1=None):
    return async(n, ThreadPoolExecutor, timeout1)


class Pool():
    '''
Obviously, use it like :
from trequests import Pool

requests = Pool(30)
...
then use requests.get/post/put/head/delete/ as usual.
so, this does not support Session...
    '''

    def __init__(self, poolnum, session=None):
        self.poolnum = poolnum
        self.session = session

    def get(self, url, **kws):
        @threads(self.poolnum)
        def get1(url, **kws):
            if self.session:
                return self.session.get(url, **kws)
            return requests.get(url, **kws)
        return get1(url, **kws)

    def post(self, url, **kws):
        @threads(self.poolnum)
        def post1(url, **kws):
            if self.session:
                return self.session.post(url, **kws)
            return requests.post(url, **kws)
        return post1(url, **kws)

    def delete(self, url, **kws):
        @threads(self.poolnum)
        def delete1(url, **kws):
            if self.session:
                return self.session.delete(url, **kws)
            return requests.delete(url, **kws)
        return delete1(url, **kws)

    def put(self, url, **kws):
        @threads(self.poolnum)
        def put1(url, **kws):
            if self.session:
                return self.session.put(url, **kws)
            return requests.put(url, **kws)
        return put1(url, **kws)

    def head(self, url, **kws):
        @threads(self.poolnum)
        def head1(url, **kws):
            if self.session:
                return self.session.head(url, **kws)
            return requests.head(url, **kws)
        return head1(url, **kws)
