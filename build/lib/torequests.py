import requests
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from multiprocessing.dummy import Pool as multiPool
import time


class Tomorrow():

    def __init__(self, future, timeout1):
        self._future = future
        self._timeout1 = timeout1
        self._wait = self._future.result

    def __getattr__(self, name):
        result = self._future.result(self._timeout1)
        return result.__getattribute__(name)


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


def threads(n, timeout1=None):
    return async1(n, ThreadPoolExecutor, timeout1)


def async(func, n=30):
    return threads(n=n)(func)


class tPool():

    '''
    num means Pool size; session is requests.Session; retry is the times when exception raised; retrylog is one bool object and determined whether show the log when retry occured; logging args will show what you want see when finished successfully; delay will run after some seconds, so it only fit float or int.
========================
Usage:
from torequests import tPool
import requests
s = requests.Session()
trequests = tPool(30, session = s)
list1 = [trequests.get(url, timeout=1, retry=1, retrylog=1, logging='finished') for url in ['http://127.0.0.1:8080/']*5]
list2 = [i.content if i.__bool__() else 'fail' for i in list1]
print(list2)

========================
http://127.0.0.1:8080/ finished
http://127.0.0.1:8080/ finished
http://127.0.0.1:8080/ finished
retry http://127.0.0.1:8080/ for the 1 time, as the Exception: HTTPConnectionPool(host='127.0.0.1', port=8080): Read timed out. (read timeout=1)
retry http://127.0.0.1:8080/ for the 1 time, as the Exception: HTTPConnectionPool(host='127.0.0.1', port=8080): Read timed out. (read timeout=1)
http://127.0.0.1:8080/ finished
retry http://127.0.0.1:8080/ for the 2 time, as the Exception: HTTPConnectionPool(host='127.0.0.1', port=8080): Read timed out. (read timeout=1)
[b'success', b'success', b'success', b'success', 'fail']
========================
PS:
http://127.0.0.1:8080/ is one server that route a function like:
    aa=random.randint(0,1)
    if aa:
        print(aa)
        return 'success'
    time.sleep(5)
    return 'fail'
========================
as you see, only the requests.get is async.
    '''

    def __init__(self, num, session=None):
        self.num = num
        self.session = session

    def get(self, url, retry=0, retrylog=False, logging=None, delay=0, **kws):
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
            return
        return get1(url, **kws)

    def post(self, url, retry=0, retrylog=False, logging=None, delay=0, **kws):
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
            return
        return post1(url, **kws)

    def delete(self, url, retry=0, retrylog=False, logging=None, delay=0, **kws):
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
            return
        return delete1(url, **kws)

    def put(self, url, retry=0, retrylog=False, logging=None, delay=0, **kws):
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
            return
        return put1(url, **kws)

    def head(self, url, retry=0, retrylog=False, logging=None, delay=0, **kws):
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
            return
        return head1(url, **kws)


class pPool():

    '''
Using tomorrow to generate an async Pool like gevent.pool.Pool or multiprocessing.dummy.Pool, no need for close.

pp=pPool(30)
ss=pp.map(func, argvs,autocheck=1)
========================
Autocheck means return the real response instead of Tomorrow Class.
As it's async, you can use print func as logging. 
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
from trequests import mPool

pp = mPool(30)
ss = pp.get(urls)
========================
It's just use multiprocessing.dummy Pool, no more special features but sync, and not supports to use it.

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
