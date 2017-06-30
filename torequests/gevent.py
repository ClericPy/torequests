#! coding:utf-8
# python2 requires: pip install futures gevent
from gevent import monkey
monkey.patch_all()
import gevent.pool



class Pool(gevent.pool.Pool):

    '''timeout_return while .x called and timeout.'''

    def __init__(self, n=None, timeout=None):
        super(Pool, self).__init__(size=n)
        self.timeout = timeout
        self.timeout_return = timeout_return

    def async_func(self, f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            return self.apply_async(f, *args, **kwargs)
        return wrapped

    def close(self, timeout=None):
        self.kill(timeout=timeout)




def threads(n=None, timeout=None):
    return Pool(n, timeout, timeout_return).async_func