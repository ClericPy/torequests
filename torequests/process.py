#! coding:utf-8
# python2 requires: pip install futures
import time
import os
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import _WorkItem

from concurrent.futures._base import Future, TimeoutError
from functools import wraps
from .utils import FailureException


class Pool(ProcessPoolExecutor):
    '''
    add async_func(function decorator) for submitting called-function into Pool obj.
    '''

    def __init__(self, n=None, timeout=None):
        super(Pool, self).__init__(n)
        self._timeout = timeout

    def async_func(self, function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            return self.submit(function, *args, **kwargs)
        return wrapped

    def close(self, wait=True):
        self.shutdown(wait=wait)

    def submit(self, func, *args, **kwargs):
        '''self.submit(function,arg1,arg2,arg3=3)'''

        with self._shutdown_lock:
            # now work at python2.x
            # if self._broken:
                # raise BrokenProcessPool('A child process terminated '
                                        # 'abruptly, the process pool is not usable anymore')
            if self._shutdown_thread:
                raise RuntimeError(
                    'cannot schedule new futures after shutdown')
            future = NewFuture(self._timeout, args, kwargs)
            w = _WorkItem(future, func, args, kwargs)
            self._pending_work_items[self._queue_count] = w
            self._work_ids.put(self._queue_count)
            self._queue_count += 1
            # Wake up queue management thread
            self._result_queue.put(None)
            self._start_queue_management_thread()
            return future


class NewFuture(Future):

    """add .x (property) and timeout args for original Future class
    WARNING: Future process will be killed if timeout.
    """

    def __init__(self, timeout=None, args=None, kwargs=None):
        super(NewFuture, self).__init__()
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
            return self.result(self._timeout)
        except TimeoutError as err:
            err.args = (self._args, self._kwargs)
            return FailureException(err)


def Daemon(f, n=None, timeout=None):
    return Pool(n, timeout).async_func(f)

# block coding for _ForkingPickler.dump exception: it's not the same object as
# def processes(n=None, timeout=None):
#     return Pool(n, timeout).async_func
