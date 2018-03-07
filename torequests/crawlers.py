#! coding:utf-8
from __future__ import print_function

import json
import os
import time
import traceback
from copy import deepcopy
from functools import wraps

from .parsers import SimpleParser
from .utils import (Counts, curlparse, ensure_dict_key_title, ensure_request,
                    md5, parse_qsl, slice_by_size, timepass, ttime, unparse_qsl,
                    urlparse, urlunparse)
from .versions import PY2, PY3, PY35_PLUS

if PY3:
    unicode = str
    from http.cookies import SimpleCookie
    from json.decoder import JSONDecodeError

if PY2:
    from Cookie import SimpleCookie
    JSONDecodeError = ValueError

if PY35_PLUS:
    from .dummy import Requests
else:
    from .main import tPool as Requests


class CommonRequests(object):

    def __init__(self,
                 request,
                 n=10,
                 interval=0,
                 ensure_response=None,
                 retry=0,
                 timeout=15,
                 logger_function=None,
                 encoding=None,
                 **kwargs):
        """request: dict or curl-string or url.
        Cookie need to be set in headers."""
        self.logger_function = logger_function or print
        self.req = Requests(n=n, interval=interval, **kwargs)
        self.encoding = encoding
        request = ensure_request(request)
        if 'headers' in request:
            request['headers'] = ensure_dict_key_title(request['headers'])
        # self.request should not be modified
        self.request = request
        self.retry = retry
        self.timeout = timeout
        self.ensure_response = ensure_response or self._ensure_response
        self.init_original_response()

    def _ensure_response(self, resp):
        if resp:
            return md5(resp.content, skip_encode=True)

    def init_original_response(self):
        """get the original response for comparing, and confirm is_cookie_necessary"""
        if 'json' in self.request:
            self.request['data'] = json.dumps(self.request.pop('json')).encode(
                self.encoding)
        r1 = self.req.request(
            retry=self.retry, timeout=self.timeout, **self.request)
        resp = r1.x
        assert resp, ValueError(
            'original_response should not be failed. %s' % self.request)
        self.encoding = self.encoding or resp.encoding
        self.original_response = self.ensure_response(resp)
        return self.original_response

    def check_response_unchanged(self, resp):
        if hasattr(resp, 'x'):
            resp = resp.x
        return self.ensure_response(resp) == self.original_response


class CleanRequest(CommonRequests):

    def __init__(self,
                 request,
                 n=10,
                 interval=0,
                 ensure_response=None,
                 retry=0,
                 timeout=15,
                 logger_function=None,
                 encoding='utf-8',
                 **kwargs):
        """request: dict or curl-string or url.
        Cookie need to be set in headers."""
        self.ignore = {
            'qsl': [],
            'Cookie': [],
            'headers': [],
            'json_data': [],
            'form_data': [],
            'total_data': []
        }
        super(CleanRequest, self).__init__(
            request=request,
            n=n,
            interval=interval,
            ensure_response=ensure_response,
            retry=retry,
            timeout=timeout,
            logger_function=logger_function,
            encoding=encoding,
            **kwargs)
        self.tasks = []
        self.has_json_data = False
        self.new_request = deepcopy(self.request)

    def init_original_response(self):
        """get the original response for comparing, and confirm is_cookie_necessary"""
        no_cookie_resp = None
        self.is_cookie_necessary = True
        if 'json' in self.request:
            self.request['data'] = json.dumps(self.request.pop('json')).encode(
                self.encoding)
        r1 = self.req.request(
            retry=self.retry, timeout=self.timeout, **self.request)
        if 'headers' in self.request:
            # test is_cookie_necessary
            cookie = self.request['headers'].get('Cookie', None)
            if cookie:
                r2 = self.req.request(
                    retry=self.retry, timeout=self.timeout, **self.request)
                no_cookie_resp = self.ensure_response(r2.x)
        resp = r1.x
        assert resp, ValueError(
            'original_response should not be failed. %s' % self.request)
        self.original_response = self.ensure_response(resp)
        self.encoding = self.encoding or resp.encoding
        if no_cookie_resp == self.original_response:
            self.ignore['headers'].append('Cookie')
            self.is_cookie_necessary = False
        return self.original_response

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
        raw_url = self.request['url']
        parsed_url = urlparse(raw_url)
        qsl = parse_qsl(parsed_url.query)
        for qs in qsl:
            new_url = self._join_url(parsed_url,
                                     [i for i in qsl if i is not qs])
            new_request = deepcopy(self.request)
            new_request['url'] = new_url
            self._add_task('qsl', qs, new_request)
        return self

    def clean_post_data(self):
        data = self.request.get('data')
        if not (data and self.request['method'] == 'post'):
            return self
        # case of total_data
        new_request = deepcopy(self.request)
        new_request.pop('data')
        self._add_task('total_data', data, new_request)

        # case of form_data
        if isinstance(data, dict):
            for key in data:
                new_request = deepcopy(self.request)
                new_form = deepcopy(data)
                new_form.pop(key)
                new_request['data'] = new_form
                self._add_task('form_data', key, new_request)
            return self

        # case of json_data
        try:
            json_data = json.loads(data.decode(self.encoding))
            for key in json_data:
                new_request = deepcopy(self.request)
                new_json = deepcopy(json_data)
                new_json.pop(key)
                new_request['data'] = json.dumps(new_json).encode(self.encoding)
                self._add_task('json_data', key, new_request)
            self.has_json_data = True
            return self
        except JSONDecodeError:
            return self

    def clean_cookie(self):
        if not self.is_cookie_necessary:
            return self
        headers = self.request.get('headers', {})
        cookies = SimpleCookie(headers['Cookie'])
        for k, v in cookies.items():
            new_cookie = '; '.join(
                [i.OutputString() for i in cookies.values() if i != v])
            new_request = deepcopy(self.request)
            new_request['headers']['Cookie'] = new_cookie
            self._add_task('Cookie', k, new_request)
        return self

    def clean_headers(self):
        if not isinstance(self.request.get('headers'), dict):
            return self
        headers = self.request['headers']
        if 'Cookie' in headers:
            self.clean_cookie()
        for key in headers:
            # cookie will be checked in other methods.
            if key == 'Cookie':
                continue
            new_request = deepcopy(self.request)
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
                if (not data) or self.ignore['total_data']:
                    # not need data any more
                    self.new_request.pop('data', None)
                if self.has_json_data and 'data' in self.new_request:
                    json_data = json.loads(data.decode(self.encoding))
                    for key in self.ignore['json_data']:
                        json_data.pop(key)
                    self.new_request['data'] = json.dumps(json_data).encode(
                        self.encoding)
        return self.new_request

    def clean_all(self):
        return self.clean_url().clean_post_data().clean_headers()

    def result(self):
        if not self.tasks:
            self.clean_all()
        tasks_length = len(self.tasks)
        self.logger_function(
            '%s tasks of request, will cost at least %s seconds.' %
            (tasks_length,
             round(self.req.interval / self.req.n * tasks_length, 2)))
        self.req.x
        for task in self.tasks:
            key, value, fut = task
            if fut.x and fut.cx:
                # fut.x == req success & fut.cx == response not changed.
                self.ignore[key].append(value)
        return self.reset_new_request()

    @property
    def x(self):
        return self.result()

    def __str__(self):
        return json.dumps(self.request, ensure_ascii=0)


class Seed(object):
    __slots__ = ('name', 'frequency', 'request', 'item_parsers', 'encoding')

    def __init__(self, name, frequency, request, item_parsers, encoding=None):
        """item_parsers: {'item_name1': parser_chain1, 'item_name2': parser_chain2}"""
        assert isinstance(frequency, (float, int))
        assert isinstance(item_parsers, dict)
        for k, v in item_parsers.items():
            assert isinstance(k, unicode)
            assert isinstance(v, (list, tuple))
        self.name = name
        self.frequency = frequency
        self.request = ensure_request(request)
        self.item_parsers = item_parsers
        self.encoding = encoding

    @property
    def as_list(self):
        return [getattr(k) for k in self.__slots__]

    @property
    def as_dict(self):
        return {k: getattr(self, k) for k in self.__slots__}

    @property
    def as_json(self, ensure_ascii=False):
        return json.dumps(self.as_dict, ensure_ascii=ensure_ascii)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'Seed(%s)' % self.as_json
