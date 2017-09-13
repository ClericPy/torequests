#! coding:utf-8
from __future__ import print_function
from .utils import PY35_PLUS, curlparse, ttime, timepass, slice_by_size, Counts
import time
if PY35_PLUS:
    from .dummy import Requests
else:
    from .main import tPool as Requests


class StressTest(object):
    def __init__(self, curl='', stop=None, chunk=10000, parser=None,
                 logger_function=None, **kwargs):
        self.count = Counts()
        self.req = Requests()
        self.parser = parser or self.content_len
        self.callback = kwargs.pop('callback', self._callback)
        self.chunk = chunk
        self.stop = stop
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

    def _run_with_stop(self):
        if self.stop < self.chunk:
            tries = self.stop
        chunks = slice_by_size(range(self.stop), self.chunk)
        for chunk in chunks:
            tasks = [self.req.request(callback=self.callback, **self.kwargs)
                     for i in chunk]
            self.req.x

    def _run_without_stop(self):
        while 1:
            tasks = [self.req.request(callback=self.callback, **self.kwargs)
                     for i in range(self.chunk)]
            self.req.x

    def run(self):
        if self.stop:
            return self._run_with_stop()
        else:
            return self._run_without_stop()

    @property
    def x(self):
        return self.run()


class RegexMapper(object):
    '''dict-like for regex mapper: input string, output obj.
    support persistence rules;
    flags: set multi flags combined with '|', FLAG1 | FLAG2 | FLAG3
    '''

    def __init__(self, name=None, match_mode='search', flags=None):
        # init regex from string to compiled regex
        self.match_mode = match_mode
        self.rules = []  # list of (str, obj)
        self.rules_compile = []
        pass

    def init_regex(self):
        pass

    def get(self, string, default=None):
        'return only one matching obj'
        return self.find(string, default)

    def find(self, string, default=None):
        'return only one matching obj'
        pass

    def findall(self, string):
        'return all matching obj'
        pass

    def regex_walker(self):
        'return generator'
        pass

    def __getitem__(self, key):
        pass

    def __setitem__(self, key, value):
        pass
