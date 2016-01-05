import requests
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from multiprocessing.dummy import Pool as multiPool


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


class tPool():

    '''
Obviously, use it like :
from trequests import tPool as Pool

requests = Pool(30)
...
then use requests.get/post/put/head/delete/ as usual.
so, this does not support Session...

tt=tPool(30)

ss=[tt.get(i,timeout=1,retry=3) for i in ['http://127.0.0.1:8080']*10]
ss=[i.text for i in ss if i.__bool__()]
    '''

    def __init__(self, num, session=None):
        self.num = num
        self.session = session

    def get(self, url, retry=0, retrylog=False, **kws):
        @threads(self.num)
        def get1(url, **kws):
            for _ in range(retry+1):
                try:
                    if self.session:
                        return self.session.get(url, **kws)
                    return requests.get(url, **kws)
                except:
                    if retrylog:
                        print('retry %s for the %s time' % (url, _))
                    continue
            return
        return get1(url, **kws)

    def post(self, url, retry=0, retrylog=False, **kws):
        @threads(self.num)
        def post1(url, **kws):
            for _ in range(retry+1):
                try:
                    if self.session:
                        return self.session.post(url, **kws)
                    return requests.post(url, **kws)
                except:
                    if retrylog:
                        print('retry %s for the %s time' % (url, _))
                    continue
            return
        return post1(url, **kws)

    def delete(self, url, retry=0, retrylog=False, **kws):
        @threads(self.num)
        def delete1(url, **kws):
            for _ in range(retry+1):
                try:
                    if self.session:
                        return self.session.delete(url, **kws)
                    return requests.delete(url, **kws)
                except:
                    if retrylog:
                        print('retry %s for the %s time' % (url, _))
                    continue
            return
        return delete1(url, **kws)

    def put(self, url, retry=0, retrylog=False, **kws):
        @threads(self.num)
        def put1(url, **kws):
            for _ in range(retry+1):
                try:
                    if self.session:
                        return self.session.put(url, **kws)
                    return requests.put(url, **kws)
                except:
                    if retrylog:
                        print('retry %s for the %s time' % (url, _))
                    continue
            return
        return put1(url, **kws)

    def head(self, url, retry=0, retrylog=False, **kws):
        @threads(self.num)
        def head1(url, **kws):
            for _ in range(retry+1):
                try:
                    if self.session:
                        return self.session.head(url, **kws)
                    return requests.head(url, **kws)
                except:
                    if retrylog:
                        print('retry %s for the %s time' % (url, _))
                    continue
            return
        return head1(url, **kws)


class pPool():

    '''
use it as gevent.pool.Pool or multiprocessing.dummy.Pool, no need for close
pp=pPool(30)
ss=pp.map(func, argvs,autocheck=1)
    '''

    def __init__(self, num):
        self.num = num

    def map(self,  func, argvs, autocheck=1):
        @threads(self.num)
        def get1(argv):
            return func(argv)

        def check(aa):
            try:
                return aa.__rmul__(1)
            except:
                pass
            try:
                return aa.replace('', '')
            except:
                pass
            return aa
        ss = list(map(get1, argvs))
        if autocheck:
            return list(map(check, ss))
        else:
            return ss


class mPool():

    '''
Obviously, use it like :
from trequests import Pool

requests = Pool(30)
...
then use requests.get/post/put/head/delete/ as usual.
so, this does not support Session...
    '''

    def __init__(self,  num, session=None):
        self.num = num
        self.session = session

    def get(self, urls, **kws):
        pp = multiPool(self.num)

        def getit(url):
            if self.session:
                return self.session.get(url, **kws)
            return requests.get(url, **kws)
        ss = pp.map(getit, urls)
        pp.close()
        pp.join()
        return ss

    def post(self, urls, **kws):
        pp = multiPool(self.num)

        def getit(url):
            if self.session:
                return self.session.post(url, **kws)
            return requests.post(url, **kws)
        ss = pp.map(getit, urls)
        pp.close()
        pp.join()
        return ss

    def delete(self, urls, **kws):
        pp = multiPool(self.num)

        def getit(url):
            if self.session:
                return self.session.delete(url, **kws)
            return requests.delete(url, **kws)
        ss = pp.map(getit, urls)
        pp.close()
        pp.join()
        return ss

    def put(self, urls, **kws):
        pp = multiPool(self.num)

        def getit(url):
            if self.session:
                return self.session.put(url, **kws)
            return requests.put(url, **kws)
        ss = pp.map(getit, urls)
        pp.close()
        pp.join()
        return ss

    def head(self, urls, **kws):
        pp = multiPool(self.num)

        def getit(url):
            if self.session:
                return self.session.head(url, **kws)
            return requests.head(url, **kws)
        ss = pp.map(getit, urls)
        pp.close()
        pp.join()
        return ss
