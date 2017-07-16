#! coding:utf-8
# python2 requires: pip install futures
import time
import os
from multiprocessing.pool import Pool, ApplyResult
from multiprocessing.context import TimeoutError
from functools import wraps
from .utils import FailureException
from .main import Async


class ProcessPool(Pool):
    '''
    add async_func(function decorator) for submitting called-function into ProcessPool obj.
    '''

    def __init__(self, n=None, timeout=None):
        super(ProcessPool, self).__init__(n)
        self._timeout = timeout
        self._apply = Async(self.apply, n)

    def async_func(self, function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            wrapped._pool = self
            return self._apply(function, args, kwargs)
        return wrapped

    def close(self, wait=True):
        self.shutdown(wait=wait)

    def apply(self, func, args=(), kwds={}):
        '''
        Equivalent of `func(*args, **kwds)`.
        '''
        assert self._state == 0
        return self.apply_async(func, args, kwds).x

    def apply_async(self, func, args=(), kwds={}, callback=None,
                    error_callback=None):
        '''
        Asynchronous version of `apply()` method.
        '''
        if self._state != 0:
            raise ValueError("Pool not running")
        result = NewApplyResult(self._cache, callback, error_callback,
                                args=args, kwargs=kwds, timeout=self._timeout)
        self._taskqueue.put(([(result._job, None, func, args, kwds)], None))
        return result


class NewApplyResult(ApplyResult):

    """add .x (property) and timeout args for original Future class
    WARNING: Future process will be killed if timeout.
    """

    def __init__(self, cache, callback, error_callback, timeout=None, args=None, kwargs=None):
        super(NewApplyResult, self).__init__(cache, callback, error_callback)
        self._timeout = timeout
        self._args = args or ()
        self._kwargs = kwargs or {}

    def __getattr__(self, name):
        try:
            object.__getattribute__(self, name)
        except AttributeError:
            return self.x.__getattribute__(name)

    @property
    def x(self):
        try:
            return self.get(self._timeout)
        except Exception as err:
            err.args = (self._args, self._kwargs)
            return FailureException(err)


def Process(f, n=None, timeout=None):
    return ProcessPool(n, timeout).async_func(f)

# block coding for _ForkingPickler.dump PicklingError: it's not the same object as
# def processes(n=None, timeout=None):
#     return ProcessPool(n, timeout).async_func
