#! coding:utf-8
from __future__ import print_function

import json
import time
import traceback
from copy import deepcopy

from .parsers import SimpleParser
from .utils import (Counts, curlparse, ensure_dict_key_title, ensure_request,
                    md5, parse_qsl, slice_by_size, timepass, ttime, unparse_qsl,
                    urlparse, urlunparse)
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
                 retry=1,
                 timeout=15,
                 logger_function=None,
                 encoding='utf-8',
                 **kwargs):
        """request: dict or curl-string or url.
        Cookie need to be set in headers."""
        self.tasks = []
        self.logger_function = logger_function or print
        self.ignore = {
            'qsl': [],
            'Cookie': [],
            'headers': [],
            'json_data': [],
            'form_data': []
        }
        request = ensure_request(request)
        self.req = Requests(n=n, interval=interval, **kwargs)
        self.encoding = encoding
        if 'headers' in request:
            request['headers'] = ensure_dict_key_title(request['headers'])
        # self.request_args should not be modified
        self.request_args = request
        self.retry = retry
        self.timeout = timeout
        self.ensure_response = ensure_response or self._ensure_response
        self.init_original_response()
        self.new_request = deepcopy(self.request_args)

    def init_original_response(self):
        """get the original response for comparing, and confirm is_cookie_necessary"""
        no_cookie_resp = None
        self.is_cookie_necessary = True
        if 'json' in self.request_args:
            self.request_args['data'] = json.dumps(
                self.request_args.pop('json')).encode(self.encoding)
        r1 = self.req.request(
            retry=self.retry, timeout=self.timeout, **self.request_args)
        if 'headers' in self.request_args:
            # test is_cookie_necessary
            cookie = self.request_args['headers'].get('Cookie', None)
            if cookie:
                r2 = self.req.request(
                    retry=self.retry, timeout=self.timeout, **self.request_args)
                no_cookie_resp = self.ensure_response(r2.x)
        if not r1.x:
            raise ValueError('original_response should not be failed. %s' %
                             self.request_args)
        self.original_response = self.ensure_response(r1.x)
        if no_cookie_resp == self.original_response:
            self.ignore['headers'].append('Cookie')
            self.is_cookie_necessary = False

    def _ensure_response(self, resp):
        if resp:
            return md5(resp.content, skip_encode=True)

    def check_response_unchanged(self, task):
        if hasattr(task, 'x'):
            task = task.x
        return self.ensure_response(task) == self.original_response

    @property
    def speed(self):
        return self.req.interval / self.req.n

    @classmethod
    def sort_url_qsl(cls, raw_url, **kws):
        parsed_url = urlparse(raw_url)
        qsl = parse_qsl(parsed_url.query)
        return cls._join_url(parsed_url, sorted(qsl, **kws))

    def _add_task(self, key, value, request):
        task = [
            key, value,
            self.req.request(
                retry=self.retry,
                timeout=self.timeout,
                callback=self.check_response_unchanged,
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
            new_request = deepcopy(self.request_args)
            new_request['url'] = new_url
            self._add_task('qsl', qs, new_request)
        return self

    def clean_post_json(self):
        if self.request_args['method'] != 'post' or \
                'data' not in self.request_args:
            return self
        try:
            data = self.request_args['data']
            json_data = json.loads(data.decode(self.encoding))
            for key in json_data:
                new_request = deepcopy(self.request_args)
                new_json = deepcopy(json_data)
                new_json.pop(key)
                new_request['data'] = json.dumps(new_json).encode(self.encoding)
                self._add_task('json_data', key, new_request)
            return self
        except json.decoder.JSONDecodeError:
            return self

    def clean_post_form(self):
        if self.request_args['method'] != 'post' or \
                not isinstance(self.request_args.get('data'), dict):
            return self
        form_data = self.request_args['data']
        for key in form_data:
            new_request = deepcopy(self.request_args)
            new_form = deepcopy(form_data)
            new_form.pop(key)
            new_request['data'] = new_form
            self._add_task('form_data', key, new_request)
            return self

    def clean_cookie(self):
        if not self.is_cookie_necessary:
            return self
        headers = self.request_args.get('headers', {})
        cookies = SimpleCookie(headers['Cookie'])
        for k, v in cookies.items():
            new_cookie = '; '.join(
                [i.OutputString() for i in cookies.values() if i != v])
            new_request = deepcopy(self.request_args)
            new_request['headers']['Cookie'] = new_cookie
            self._add_task('Cookie', k, new_request)
        return self

    def clean_headers(self):
        if not isinstance(self.request_args.get('headers'), dict):
            return self
        headers = self.request_args['headers']
        if 'Cookie' in headers:
            self.clean_cookie()
        for key in headers:
            # cookie will be checked in other methods.
            if key == 'Cookie':
                continue
            new_request = deepcopy(self.request_args)
            new_headers = deepcopy(headers)
            new_headers.pop(key)
            new_request['headers'] = new_headers
            self._add_task('headers', key, new_request)
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

        if self.ignore['Cookie'] and 'Cookie' not in self.ignore['headers']:
            headers = self.new_request['headers']
            headers = {key.lower(): headers[key] for key in headers}
            if 'Cookie' in headers:
                cookies = SimpleCookie(headers['Cookie'])
                new_cookie = '; '.join([
                    i[1].OutputString()
                    for i in cookies.items()
                    if i[0] not in self.ignore['Cookie']
                ])
                self.new_request['headers']['Cookie'] = new_cookie

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
        return self.clean_url().clean_post_form().clean_post_json(
        ).clean_headers()

    def result(self):
        if not self.tasks:
            self.clean_all()
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

    @property
    def x(self):
        return self.result()

    def __str__(self):
        return json.dumps(self.request_args, ensure_ascii=0)
