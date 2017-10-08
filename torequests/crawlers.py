#! coding:utf-8
from __future__ import print_function
from .utils import PY35_PLUS, curlparse, ttime, timepass, slice_by_size, Counts
import time
if PY35_PLUS:
    from .dummy import Requests
else:
    from .main import tPool as Requests


class StressTest(object):
    def __init__(self, curl='', n=100, interval=0, num=None, chunk=1000, parser=None,
                 logger_function=None, **kwargs):
        self.count = Counts()
        self.req = Requests(n, interval)
        self.parser = parser or self.content_len
        self.callback = kwargs.pop('callback', self._callback)
        self.chunk = chunk
        self.num = num
        self.start_time_ts = time.time()
        self.logger_function = logger_function or print
        self.start_time = ttime(self.start_time_ts)
        self.succ = 0
        if curl and curl.startswith('curl '):
            self.kwargs = curlparse(curl)
        else:
            self.kwargs = kwargs

    def content_len(self, r):
        return len(r.content)

    def _callback(self, r):
        passed = time.time() - self.start_time_ts
        count = self.count.x
        ok = bool(r.x)
        if ok:
            self.succ += 1
            response = self.parser(r.x)
        else:
            response = r.x
        succ_rate = round(self.succ / count, 4) * 100
        speed = int(count // passed)
        log_str = '[%s] response: %s, %s - %s (+%s), succ_rate: %s%%, %s req/s' % (
            count, response, ttime(), self.start_time, timepass(passed), succ_rate, speed)
        self.logger_function(log_str)

        return ok

    def _run_with_num(self):
        if self.num < self.chunk:
            tries = self.num
        chunks = slice_by_size(range(self.num), self.chunk)
        for chunk in chunks:
            tasks = [self.req.request(callback=self.callback, **self.kwargs)
                     for i in chunk]
            self.req.x

    def _run_without_num(self):
        while 1:
            tasks = [self.req.request(callback=self.callback, **self.kwargs)
                     for i in range(self.chunk)]
            self.req.x

    def run(self):
        if self.num:
            return self._run_with_num()
        else:
            return self._run_without_num()

    @property
    def x(self):
        return self.run()

class Uptime(object):
    '''TODO'''
