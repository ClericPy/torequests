#! coding:utf-8
from __future__ import print_function

import json
import time
import traceback

from .parsers import SimpleParser
from .utils import (Counts, curlparse, md5, parse_qsl, slice_by_size, timepass,
                    ttime, unparse_qsl, urlparse, urlunparse)
from .versions import PY2, PY3, PY35_PLUS

if PY3:
    unicode = str
    from http.cookies import SimpleCookie

if PY2:
    from Cookie import SimpleCookie

if PY35_PLUS:
    from .dummy import Requests
else:
    from .main import tPool as Requests


class CleanRequest(object):

    def __init__(self,
                 request,
                 ensure_response=None,
                 n=10,
                 interval=0,
                 include_cookie=True,
                 retry=1,
                 timeout=15,
                 logger_function=None,
                 encoding='utf-8',
                 **kwargs):
        """request: dict or curl-string."""
        if isinstance(request, (str, unicode)):
            request = curlparse(request)
        assert isinstance(request, dict), 'request should be dict.'
        self.req = Requests(n=n, interval=interval, **kwargs)
        self.encoding = encoding
        self.request_args = request
        self.retry = retry
        self.timeout = timeout
        self.include_cookie = include_cookie
        self.ensure_response = ensure_response or self._ensure_response
        self.init_response = self.ensure_response(
            self.req.request(
                retry=self.retry, timeout=self.timeout, **self.request_args).x)
        self.new_request = dict(self.request_args)
        self.tasks = []
        self.logger_function = logger_function or print
        self.ignore = {
            'qsl': [],
            'cookie': [],
            'headers': [],
            'json_data': [],
            'form_data': []
        }

    def _ensure_response(self, resp):
        return md5(resp.content, skip_encode=True) if resp else None

    def check_response_same(self, task):
        if hasattr(task, 'x'):
            task = task.x
        return self.ensure_response(task) == self.init_response

    @property
    def speed(self):
        return self.req.interval / self.req.n

    @classmethod
    def sort_url_qsl(cls, raw_url, **kws):
        parsed_url = urlparse(raw_url)
        qsl = parse_qsl(parsed_url.query)
        return cls._join_url(parsed_url, sorted(qsl, **kws))

    def _check_request(self, key, value, request):
        task = [
            key, value,
            self.req.request(
                retry=self.retry,
                timeout=self.timeout,
                callback=self.check_response_same,
                **request)
        ]
        self.tasks.append(task)

    @classmethod
    def _join_url(cls, parsed_url, new_qsl):
        return urlunparse((parsed_url.scheme, parsed_url.netloc,
                           parsed_url.path, parsed_url.params,
                           unparse_qsl(new_qsl), parsed_url.fragment))

    def clean_url(self):
        raw_url = self.request_args['url']
        parsed_url = urlparse(raw_url)
        qsl = parse_qsl(parsed_url.query)
        for qs in qsl:
            new_url = self._join_url(parsed_url,
                                     [i for i in qsl if i is not qs])
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
                new_request['data'] = json.dumps(new_json).encode(self.encoding)
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
        headers = {key.lower(): headers[key] for key in headers}
        cookies = SimpleCookie(headers['cookie'])
        for k, v in cookies.items():
            new_cookie = '; '.join(
                [i.OutputString() for i in cookies.values() if i != v])
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
        self.logger_function('ignore: %s' % self.ignore)
        for key in self.ignore['headers']:
            self.new_request['headers'].pop(key)

        if not self.new_request.get('headers'):
            self.new_request.pop('headers', None)

        if self.ignore['cookie'] and 'cookie' not in self.ignore['headers']:
            headers = self.new_request['headers']
            headers = {key.lower(): headers[key] for key in headers}
            if 'cookie' in headers:
                cookies = SimpleCookie(headers['cookie'])
                new_cookie = '; '.join([
                    i[1].OutputString()
                    for i in cookies.items()
                    if i[0] not in self.ignore['cookie']
                ])
                self.new_request['headers']['cookie'] = new_cookie

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
                    self.new_request['data'] = json.dumps(json_data).encode(
                        self.encoding)

    def clean_all(self):
        self.clean_url().clean_post_form().clean_post_json().clean_headers()
        tasks_length = len(self.tasks)
        self.logger_function(
            '%s tasks of request, will cost about %s seconds.' %
            (tasks_length, round(self.speed * tasks_length, 2)))
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
