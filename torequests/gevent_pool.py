#! coding:utf-8
# python2 requires: pip install futures gevent

'''
TODO
1. callback not work
2. getattr failed
3. catch_exception not work
4. requests not code
'''


from gevent import monkey
monkey.patch_all()

import gevent.pool

from gevent.greenlet import Greenlet, joinall
from functools import wraps


class Pool(gevent.pool.Pool):

    def __init__(self, n=None, timeout=None, catch_exception=False):
        super(Pool, self).__init__(size=n, greenlet_class=NewGreenlet)
        self._timeout = timeout
        self._catch_exception = catch_exception

    def async_func(self, func):
        @wraps(func)
        def wrapped(*args, **kwds):
            callback = kwds.pop('callback', None)
            args = args or ()
            kwds = kwds or {}
            if self.full():
                return NewGreenlet.spawn(self.apply_cb, func, args, kwds,
                                         callback, timeout=self._timeout,
                                         catch_exception=self._catch_exception)
            greenlet = self.spawn(func, *args, **kwds,
                                  timeout=self._timeout,
                                  catch_exception=self._catch_exception)
            if callback is not None:
                greenlet.link(gevent.pool.pass_value(callback))
            return greenlet
        return wrapped


class NewGreenlet(Greenlet):
    def __init__(self, run=None, *args, **kwargs):
        self._timeout = kwargs.pop('timeout', None)
        self._catch_exception = kwargs.pop('catch_exception', None)
        super(NewGreenlet, self).__init__(run, *args, **kwargs)

    # TODO  NOT WORK
    def __getattr__(self, name):
        result = self.get()
        return result.__getattribute__(name)

    @property
    def x(self):
        try:
            self.join(timeout=self._timeout)
            return self.value
        except Exception as err:
            # TODO not work, not raise anything
            if not self._catch_exception:
                raise err
            return err


def Async(function, n, timeout=None, catch_exception=False):
    return threads(n=n, timeout=timeout, catch_exception=catch_exception)(function)


def threads(n=None, timeout=None, catch_exception=False):
    return Pool(n, timeout, catch_exception=catch_exception).async_func
