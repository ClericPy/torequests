#! coding:utf-8
from __future__ import print_function

import json
import time
import traceback

from .utils import (PY35_PLUS, Counts, curlparse, md5, parse_qsl,
                    slice_by_size, timepass, ttime, unparse_qsl, urlparse,
                    urlunparse)
from .versions import PY3, PY35_PLUS, PY2

if PY3:
    unicode = str
    from http.cookies import SimpleCookie

if PY2:
    from Cookie import SimpleCookie

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
                temp = self.req.request(
                    callback=self.cb, timeout=self.timeout, retry=self.retry, **self.request).cx
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


class CleanRequest(object):

    def __init__(self, request, ensure_responce=None, n=10, interval=0,
                 include_cookie=True, retry=1, encoding='utf-8', **kwargs):
        '''request: dict or curl-string.'''
        if isinstance(request, (str, unicode)):
            request = curlparse(request)
        assert isinstance(request, dict), 'request should be dict.'
        self.req = Requests(n=n, interval=interval, **kwargs)
        self.encoding = encoding
        self.request_args = request
        self.retry = retry
        self.include_cookie = include_cookie
        self.ensure_responce = ensure_responce or self._ensure_response
        self.init_responce = self.ensure_responce(
            self.req.request(retry=self.retry, **self.request_args).x)
        self.new_request = dict(self.request_args)
        self.tasks = []
        self.ignore = {'qsl': [], 'cookie': [], 'headers': [],
                       'json_data': [], 'form_data': []}

    def _ensure_response(self, resp):
        return md5(resp.content, skip_encode=True) if resp else None

    def check_response_same(self, task):
        if hasattr(task, 'x'):
            task = task.x
        return self.ensure_responce(task) == self.init_responce

    @classmethod
    def sort_url_qsl(cls, raw_url, **kws):
        parsed_url = urlparse(raw_url)
        qsl = parse_qsl(parsed_url.query)
        return cls._join_url(parsed_url, sorted(qsl, **kws))

    def _check_request(self, key, value, request):
        task = [key, value, self.req.request(retry=self.retry, callback=self.check_response_same,
                                             **request)]
        self.tasks.append(task)

    @classmethod
    def _join_url(cls, parsed_url, new_qsl):
        return urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path,
                           parsed_url.params, unparse_qsl(new_qsl), parsed_url.fragment))

    def clean_url(self):
        raw_url = self.request_args['url']
        parsed_url = urlparse(raw_url)
        qsl = parse_qsl(parsed_url.query)
        for qs in qsl:
            new_url = self._join_url(
                parsed_url, [i for i in qsl if i is not qs])
            new_request_args = dict(self.request_args)
            new_request_args['url'] = new_url
            self._check_request('qsl', qs, new_request_args)
        return self

    def clean_post_json(self):
        if self.request_args['method'] != 'post' or \
                'data' not in self.request_args:
            return self
        try:
            data = self.request_args['data']
            json_data = json.loads(data.decode(self.encoding))
            for key in json_data:
                new_request = dict(self.request_args)
                new_json = dict(json_data)
                new_json.pop(key)
                new_request['data'] = json.dumps(
                    new_json).encode(self.encoding)
                self._check_request('json_data', key, new_request)
            return self
        except json.decoder.JSONDecodeError:
            return self

    def clean_post_form(self):
        if self.request_args['method'] != 'post' or \
                not isinstance(self.request_args.get('data'), dict):
            return self
        form_data = self.request_args['data']
        for key in form_data:
            new_request = dict(self.request_args)
            new_form = dict(form_data)
            new_form.pop(key)
            new_request['data'] = new_form
            self._check_request('form_data', key, new_request)
            return self

    def clean_cookie(self):
        headers = self.request_args.get('headers', {})
        if 'cookie' not in map(lambda x: x.lower(), headers.keys()):
            return self
        headers = {key.lower():headers[key] for key in headers}
        cookies = SimpleCookie(headers['cookie'])
        for k, v in cookies.items():
            new_cookie = '; '.join([i.OutputString() for i in cookies.values() if i != v])
            new_request = dict(self.new_request)
            new_request['headers']['cookie'] = new_cookie
            self._check_request('cookie', k, new_request)
        return self

    def clean_headers(self):
        if self.include_cookie:
            self.clean_cookie()
        if not isinstance(self.request_args.get('headers'), dict):
            return self
        headers = self.request_args['headers']
        for key in headers:
            new_request = dict(self.request_args)
            new_headers = dict(headers)
            new_headers.pop(key)
            new_request['headers'] = new_headers
            self._check_request('headers', key, new_request)
        return self

    def reset_new_request(self):
        raw_url = self.new_request['url']
        parsed_url = urlparse(raw_url)
        qsl = parse_qsl(parsed_url.query)
        new_url = self._join_url(
                parsed_url, [i for i in qsl if i not in self.ignore['qsl']])
        self.new_request['url'] = new_url
        for key in self.ignore['headers']:
            self.new_request['headers'].pop(key)
        
        if self.ignore['cookie']:
            headers = self.new_request['headers']
            headers = {key.lower():headers[key] for key in headers}
            if 'cookie' in headers:
                cookies = SimpleCookie(headers['cookie'])
                new_cookie = '; '.join([i[1].OutputString() for i in cookies.items() if i[0] not in self.ignore['cookie']])
                self.new_request['headers']['cookie'] = new_cookie
        if not self.new_request.get('headers'):
            self.new_request.pop('headers', None)
        if self.new_request['method'] == 'post':
            data = self.new_request.get('data')
            if data:
                if isinstance(data, dict):
                    for key in self.ignore['form_data']:
                        data.pop(key)
                else:
                    json_data = json.loads(data.decode(self.encoding))
                    for key in self.ignore['json_data']:
                        json_data.pop(key)
                    self.new_request['data'] = json.dumps(
                            json_data).encode(self.encoding)


    def clean_all(self):
        self.clean_url().clean_post_form().clean_post_json().clean_headers()
        self.req.x
        for task in self.tasks:
            key, value, fut = task
            if not fut.x:
                # req failed
                continue
            if not fut.cx:
                # response changed
                continue
            self.ignore[key].append(value)
        self.reset_new_request()
        return self.new_request

    def result(self):
        return self.clean_all()

    @property
    def x(self):
        return self.result()

    def __str__(self):
        return json.dumps(self.request_args, ensure_ascii=0)
