#! coding:utf-8
from __future__ import print_function
from .utils import PY35_PLUS, curlparse, ttime, timepass, slice_by_size, Counts, md5
from .versions import PY3, PY35_PLUS
import time
import traceback

if PY3:
    unicode = str

if PY35_PLUS:
    from .dummy import Requests
else:
    from .main import tPool as Requests


class StressTest(object):
    '''changed_callback may be lambda x=None:os._exit(0)'''

    def __init__(self, curl='', n=100, interval=0, stop=None, chunk=1,
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
        self.stop = stop
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


class Uptimer(object):
    '''TODO'''
    INIT_TEMP_VALUE = md5(str(time.time()**2))

    def __init__(self, request, ensure_resp_cb=None, timeout=None, retry=0):
        '''request: dict or curl-string.'''
        self.req = Requests()
        self.last_cb_resp = self.INIT_TEMP_VALUE
        self.cb = ensure_resp_cb or self.default_callback
        if isinstance(request, (str, unicode)):
            request = curlparse(request)
        self.request = request
        self.timeout = timeout
        self.retry = retry

    def default_callback(self, resp):
        if resp.x:
            temp = md5(resp.content, skip_encode=True)
        else:
            temp = None
        return temp

    def check_ok(self, temp):
        if self.last_cb_resp == self.INIT_TEMP_VALUE:
            return True
        elif temp == self.last_cb_resp:
            return True
        else:
            return False

    def start(self, duration=None, interval=10, stop=0):
        duration = duration or float('inf')
        stop = stop or float('inf')
        start_at = time.time()
        start_at_time = ttime()
        count = 0
        while time.time() - start_at < duration or count < stop:
            try:
                temp = self.req.request(callback=self.cb, timeout=self.timeout, retry=self.retry, **self.request).cx
                log_str = '[%s] response: %s, %s - %s (+%s), interval=%s, stop=%s' % (
                    count, temp, start_at_time, ttime(), timepass(time.time() - start_at), interval, stop)
                print(log_str)
                if not self.check_ok(temp):
                    return False
            except:
                traceback.print_exc()
                return False
            finally:
                count += 1
            time.sleep(interval)
            self.last_cb_resp = temp
        return True

    def guess_safe_interval(self, start_interval=60, step=-1, stop=0, duration=3600):
        for interval in range(start_interval, 0, step):
            ok = self.start(duration=duration, interval=interval, stop=stop)
            if not ok:
                break
            safe_interval = interval
        print('safe interval = %s' % safe_interval)
        return safe_interval

class RequestCleaner(object):

    def __init__(self, request):
        '''request: dict or curl-string.'''
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
