import requests
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from multiprocessing.dummy import Pool as multiPool

__doc__=r'''
Thanks for requests & tomorrow...

========================================

Try it yourself:

========================================
from torequests import mPool
from torequests import tPool
import requests
import time

# requests in single thread
print('##### requests in single thread for 100 work')
aa = time.time()
ss = [requests.get(url)
      for url in ['http://p.3.cn/prices/mgets?skuIds=J_1273600'] * 100]
ss = [len(i.text) for i in ss]
print(ss[-10:],'\n')
print('>',time.time() - aa, 's\n')


# no Session multitreads
print('##### no Session multitreads for 1000 work')
aa = time.time()
mrequests = mPool(50)
ss = mrequests.get(['http://p.3.cn/prices/mgets?skuIds=J_1273600'] * 1000)
ss = [len(i.text) for i in ss]
print(ss[-10:],'\n')
print('>',time.time() - aa, 's\n')

# no Session tomorrow
print('##### no Session tomorrow for 1000 work')

aa = time.time()
trequests = tPool(50)
ss = [trequests.get(url) for url in [
    'http://p.3.cn/prices/mgets?skuIds=J_1273600'] * 1000]
ss = [len(i.text) for i in ss]
print(ss[-10:],'\n')
print('>',time.time() - aa, 's\n')


# with Session multitreads
print('##### with Session multitreads for 1000 work')

aa = time.time()
s = requests.Session()
mrequests = mPool(50, session=s)
ss = mrequests.get(['http://p.3.cn/prices/mgets?skuIds=J_1273600'] * 1000)
ss = [len(i.text) for i in ss]
print(ss[-10:],'\n')
print('>',time.time() - aa, 's\n')

# with Session tomorrow
print('##### with Session tomorrow for 1000 work')
aa = time.time()
s = requests.Session()
trequests = tPool(50, session=s)
ss = [trequests.get(url) for url in [
    'http://p.3.cn/prices/mgets?skuIds=J_1273600'] * 1000]
ss = [len(i.text) for i in ss]
print(ss[-10:],'\n')
print('>',time.time() - aa, 's\n')


===============================

##### requests in single thread for 100 work
[51, 51, 51, 51, 51, 51, 51, 51, 51, 51] 

> 1.8863472938537598 s

##### no Session multitreads for 1000 work
[51, 51, 51, 51, 51, 51, 51, 51, 51, 51] 

> 2.6028215885162354 s

##### no Session tomorrow for 1000 work
[51, 51, 51, 51, 51, 51, 51, 51, 51, 51] 

> 2.633859872817993 s

##### with Session multitreads for 1000 work
[51, 51, 51, 51, 51, 51, 51, 51, 51, 51] 

> 2.1975533962249756 s

##### with Session tomorrow for 1000 work
[51, 51, 51, 51, 51, 51, 51, 51, 51, 51] 

> 2.48775577545166 s
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


class tPool():
    '''
Obviously, use it like :
from trequests import tPool as Pool

requests = Pool(30)
...
then use requests.get/post/put/head/delete/ as usual.
so, this does not support Session...
    '''

    def __init__(self, num, session=None):
        self.num = num
        self.session = session

    def get(self, url, **kws):
        @threads(self.num)
        def get1(url, **kws):
            if self.session:
                return self.session.get(url, **kws)
            return requests.get(url, **kws)
        return get1(url, **kws)

    def post(self, url, **kws):
        @threads(self.num)
        def post1(url, **kws):
            if self.session:
                return self.session.post(url, **kws)
            return requests.post(url, **kws)
        return post1(url, **kws)

    def delete(self, url, **kws):
        @threads(self.num)
        def delete1(url, **kws):
            if self.session:
                return self.session.delete(url, **kws)
            return requests.delete(url, **kws)
        return delete1(url, **kws)

    def put(self, url, **kws):
        @threads(self.num)
        def put1(url, **kws):
            if self.session:
                return self.session.put(url, **kws)
            return requests.put(url, **kws)
        return put1(url, **kws)

    def head(self, url, **kws):
        @threads(self.num)
        def head1(url, **kws):
            if self.session:
                return self.session.head(url, **kws)
            return requests.head(url, **kws)
        return head1(url, **kws)

class pPool():
    '''
use it as gevent.pool.Pool or multiprocessing.dummy.Pool, no need for close
pp=pPool(30)
ss=pp.map1(func, argvs,autocheck=1)
    '''

    def __init__(self, num):
        self.num = num

    def map1(self,  func, argvs,autocheck=1):
        @threads(self.num)
        def get1(argv):
            return func(argv)
        def check(aa):
            try:
                return aa.__rmul__(1)
            except:
                pass
            try:
                return aa.replace('','')
            except:
                pass
            return aa

        if autocheck:
            return list(map(check,map(get1,argvs)))
        else:
            return list(map(get1,argvs))





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
