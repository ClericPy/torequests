#! coding:utf-8
from __future__ import print_function
from .utils import PY35_PLUS, curlparse, ttime, timepass, slice_by_size, Counts, md5
import time

if PY3:
    unicode = str

if PY35_PLUS:
    from .dummy import Requests
else:
    from .main import tPool as Requests


class StressTest(object):
    '''changed_callback may be lambda x=None:os._exit(0)'''

    def __init__(self, curl='', n=100, interval=0, num=None, chunk=1,
                 parser=None, logger_function=None, changed_callback=None,
                 allow_changed=1, proc=True, **kwargs):
        self.count = Counts()
        self.req = Requests(n, interval)
        self.init_parse_value = md5(time.time())
        self.last_parse_value = self.init_parse_value
        self.parser = parser or self.content_len
        self.changed_callback = changed_callback
        self.allow_changed = allow_changed
        self.changed_times = 0
        self.callback = kwargs.pop('callback', self._callback)
        self.chunk = chunk
        self.num = num
        self.proc = proc
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
        if self.proc:
            log_str = '[%s] response: %s, %s - %s (+%s), succ_rate: %s%%, %s req/s' % (
                count, response, self.start_time, ttime(), timepass(passed), succ_rate, speed)
            self.logger_function(log_str)
        if self.changed_callback \
                and self.last_parse_value != self.init_parse_value \
                and response != self.last_parse_value:
            if self.proc:
                self.changed_times += 1
                self.logger_function(
                    'responce changed %s times' % self.changed_times)
            if self.changed_times >= self.allow_changed:
                self.changed_callback(response)
        self.last_parse_value = response
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

class RequestCleaner(object):

    def __init__(self, request):
        if isinstance(request, (str, unicode)):
            request = curlparse(request)
        self.request = request
        self.new_request = None

    def result(self):
        return self.new_request

    @property
    def x(self):
        return self.result()

    def check_sortable(self):
        self.sortable = True

    def clean_get_query(self):
        url = self.request.url
        parsed = urlparse(url)
        old_query = parsed.query
        qs = parse_qs(old_query)
        qs['f'] = ['1', '22']
        new_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path,
                              parsed.params, unparse_qs(qs, self.sortable),
                              parsed.fragment))
        return self

    def clean_post_json(self):
        return self

    def clean_post_form(self):
        return self

    def clean_cookie(self):
        return self

    def clean_header(self):
        return self
