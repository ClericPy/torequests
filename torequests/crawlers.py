#! coding:utf-8

from __future__ import division

import json
import os
import time
from copy import deepcopy
from functools import wraps

from .logs import print_info
from .utils import (Counts, ensure_dict_key_title, ensure_request, md5,
                    parse_qsl, slice_by_size, timepass, ttime, unparse_qsl,
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

__all__ = 'CleanRequest Seed StressTest'.split(' ')


class CommonRequests(object):

    def __init__(self,
                 request,
                 n=10,
                 interval=0,
                 ensure_response=None,
                 retry=0,
                 timeout=10,
                 logger_function=None,
                 encoding=None,
                 **kwargs):
        #: If not set, will use print_info, logger_function should handle result(str) and **kwargs
        self.logger_function = logger_function or print_info
        #: torequests's async requests tool.
        self.req = Requests(n=n, interval=interval, **kwargs)
        #: default encoding or detected by response
        self.encoding = encoding
        request = ensure_request(request)
        if 'headers' in request:
            request['headers'] = ensure_dict_key_title(request['headers'])
        #: request: dict or curl-string or url;
        #: self.request should not be modified
        self.request = request
        #: max reties for bad response.
        self.retry = retry
        #: default timeout
        self.timeout = timeout
        #: function to check the same response.
        self.ensure_response = ensure_response or self._ensure_response
        self.init_original_response()

    def _ensure_response(self, r):
        if hasattr(r, 'x'):
            r = r.x
        if r:
            # r.content is not need to be encode.
            return '%s-%s' % (md5(r.content, n=8, skip_encode=True),
                              len(r.content))
        return r

    def init_original_response(self):
        """Get the original response for comparing, confirm ``is_cookie_necessary``"""
        if 'json' in self.request:
            self.request['data'] = json.dumps(self.request.pop('json')).encode(
                self.encoding)
        r1 = self.req.request(
            retry=self.retry, timeout=self.timeout, **self.request)
        resp = r1.x
        assert resp, ValueError(
            'original_response should not be failed. %s' % self.request)
        self.encoding = self.encoding or resp.encoding
        self.original_response = self.ensure_response(r1)
        return self.original_response

    def check_response_unchanged(self, resp):
        if hasattr(resp, 'x'):
            resp = resp.x
        return self.ensure_response(resp) == self.original_response


class CleanRequest(CommonRequests):
    """Clean the non-sense request args but return the original response.

    Basic Usage::

        >>> from torequests.crawlers import CleanRequest
        >>> request = '''curl 'https://p.3.cn?skuIds=1&nonsense=1&nonce=0' -H 'Pragma: no-cache' -H 'DNT: 1' -H 'Accept-Encoding: gzip, deflate' -H 'Accept-Language: zh-CN,zh;q=0.9' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Cache-Control: no-cache' -H 'Referer: https://p.3.cn?skuIds=1&nonsense=1&nonce=0' -H 'Cookie: ASPSESSIONIDSQRRSADB=MLHDPOPCAMBDGPFGBEEJKLAF' -H 'Connection: keep-alive' --compressed'''
        >>> c = CleanRequest(request)
        >>> c.x
        {'url': 'https://p.3.cn', 'method': 'get'}
    """

    def __init__(self,
                 request,
                 n=10,
                 interval=0,
                 ensure_response=None,
                 retry=0,
                 timeout=10,
                 logger_function=None,
                 encoding='utf-8',
                 **kwargs):
        """request: dict or curl-string or url.
        Cookie need to be set in headers."""
        #: request args which can be ignored.
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
        #: The list of async-requests task.
        self.tasks = []
        #: If the post-data should be seen as json.
        self.has_json_data = False
        #: The cleaned request to be return at last.
        self.new_request = deepcopy(self.request)

    def init_original_response(self):
        """Get the original response for comparing, confirm is_cookie_necessary"""
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
                new_request = deepcopy(self.request)
                new_request['headers']['Cookie'] = ''
                r2 = self.req.request(
                    retry=self.retry, timeout=self.timeout, **new_request)
                no_cookie_resp = self.ensure_response(r2)
        resp = r1.x
        assert resp, ValueError(
            'original_response should not be failed. %s' % self.request)
        self.original_response = self.ensure_response(r1)
        self.encoding = self.encoding or resp.encoding
        if no_cookie_resp == self.original_response:
            self.ignore['headers'].append('Cookie')
            self.is_cookie_necessary = False
        return self.original_response

    @classmethod
    def sort_url_qsl(cls, raw_url, **kwargs):
        """Do nothing but sort the params of url.

            raw_url: the raw url to be sorted; 
            kwargs: (optional) same kwargs for ``sorted``.
        """
        parsed_url = urlparse(raw_url)
        qsl = parse_qsl(parsed_url.query)
        return cls._join_url(parsed_url, sorted(qsl, **kwargs))

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
        """Only clean the url params and return self."""
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
        """Only clean the post-data and return self. 
        
        Including form-data / bytes-data / json-data."""
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
        """Only clean the cookie from headers and return self."""
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
        """Only clean the headers (cookie include) and return self."""
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
        """Remove the non-sense args from the self.ignore, return self.new_request"""
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
            headers = {key.title(): headers[key] for key in headers}
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
        """Clean the url + post-data + headers, return self."""
        return self.clean_url().clean_post_data().clean_headers()

    def result(self):
        """Whole task, clean_all + reset_new_request, return self.new_request."""
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
        """Property as self.result()"""
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
        """Property return the value for keys of __slots__."""
        return [getattr(k) for k in self.__slots__]

    @property
    def as_dict(self):
        """Property return key-value dict from __slots__."""
        return {k: getattr(self, k) for k in self.__slots__}

    @property
    def as_json(self, ensure_ascii=False):
        """Property return key-value json-string from __slots__."""
        return json.dumps(self.as_dict, ensure_ascii=ensure_ascii)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'Seed(%s)' % self.as_json


class StressTest(CommonRequests):
    """StressTest for a request(dict/curl-string/url).

    Basic Usage::

        >>> from torequests.crawlers import StressTest
        >>> StressTest('http://p.3.cn', retry=2, timeout=2).x
        [2018-09-06 00:19:40](L481): [1] response: f3f97a64-612, start at 2018-09-06 00:19:40 (+00:00:00), 0.040s, 24.98 req/s [100.00 %]
        [2018-09-06 00:19:40](L481): [2] response: f3f97a64-612, start at 2018-09-06 00:19:40 (+00:00:00), 0.041s, 48.16 req/s [100.00 %]
        [2018-09-06 00:19:40](L481): [3] response: f3f97a64-612, start at 2018-09-06 00:19:40 (+00:00:00), 0.045s, 65.89 req/s [100.00 %]
        [2018-09-06 00:19:40](L481): [4] response: f3f97a64-612, start at 2018-09-06 00:19:40 (+00:00:00), 0.046s, 85.96 req/s [100.00 %]
        [2018-09-06 00:19:40](L481): [5] response: f3f97a64-612, start at 2018-09-06 00:19:40 (+00:00:00), 0.048s, 104.09 req/s [100.00 %]
        [2018-09-06 00:19:40](L481): [6] response: f3f97a64-612, start at 2018-09-06 00:19:40 (+00:00:00), 0.051s, 117.57 req/s [100.00 %]
        [2018-09-06 00:19:40](L481): [7] response: f3f97a64-612, start at 2018-09-06 00:19:40 (+00:00:00), 0.053s, 131.98 req/s [100.00 %]
    """

    def __init__(self,
                 request,
                 n=10,
                 interval=0,
                 ensure_response=None,
                 retry=0,
                 timeout=10,
                 logger_function=None,
                 encoding=None,
                 total_tries=None,
                 total_time=None,
                 shutdown=None,
                 shutdown_changed=True,
                 chunk_size=100,
                 **kwargs):
        """request: dict or curl-string or url.
        logger_function: should handle result and **kwargs, which have `cost`
        Cookie need to be set in headers."""
        logger_function = logger_function or self._logger_function
        super(StressTest, self).__init__(
            request=request,
            n=n,
            interval=interval,
            ensure_response=ensure_response,
            retry=retry,
            timeout=timeout,
            logger_function=logger_function,
            encoding=encoding,
            **kwargs)
        #: counter for all response fetched
        self.counter = Counts()
        #: counter for success response fetched
        self.succ_counter = Counts()
        #: timestamp for starting up, time.time()
        self.start_time = time.time()
        #: readable-time-string for starting up, ttime(self.start_time)
        self.start_time_readable = ttime(self.start_time)
        #: the limit of total response count, stop the script while reaching.
        self.total_tries = total_tries or float('inf')
        #: the limit of time run-time, stop the script while reaching.
        self.total_time = total_time or float('inf')
        #: shutdown function, ``os._exit(0)`` if not set.
        self.shutdown = shutdown or self._shutdown
        #: shutdown if response changed.
        self.shutdown_changed = shutdown_changed
        #: fetch requests chunk_size each time, default 100
        self.chunk_size = chunk_size
        #: StressTest callback function, will be wrapped.
        self.st_callback = self.st_callback_wrapper(self.ensure_response)

    def _shutdown(self):
        return os._exit(0)

    @property
    def speed(self):
        """Speed property, the unit can be `req / s`. 

        Returns: the num of request is fetched in one second."""
        return round(self.counter.now / self.passed, 2)

    @property
    def succ_rate(self):
        """The request rate of success. Returns :string like `100.00%`"""
        return '%.2f %%' % (self.succ_counter.now * 100 / self.counter.now)

    @property
    def passed(self):
        """This attribute returns the seconds after starting up."""
        return time.time() - self.start_time

    def _logger_function(self, text, **kwargs):
        cost = kwargs.get("cost", None)
        cost = ' %.3fs,' % cost if cost is not None else ''
        log_str = '[%s] response: %s, start at %s (+%s),%s %.2f req/s [%s]' % (
            self.counter.now, text, self.start_time_readable,
            timepass(self.passed), cost, self.speed, self.succ_rate)
        print_info(log_str)

    def st_callback_wrapper(self, func):
        """add shutdown checker for origin callback function."""

        @wraps(func)
        def wrapper(r):
            # if tries end or timeout or shutdown_changed => shutdown
            result = func(r)
            self.counter.x
            succ = result == self.original_response
            if self.counter.now >= self.total_tries:
                print_info('shutdown for: total_tries: %s' % self.total_time)
                self.shutdown()
            if self.passed >= self.total_time:
                print_info('shutdown for: total_time: %s' % self.total_time)
                self.shutdown()
            if succ:
                self.succ_counter.x
            elif self.shutdown_changed:
                print_info('shutdown for: shutdown_changed: %s => %s' %
                           (self.original_response, result))
                self.shutdown()
            self.logger_function(result, cost=time.time() - r.task_start_time)
            return result

        return wrapper

    def start(self):
        """Start the task cycle."""
        while 1:
            tasks = [
                self.req.request(
                    callback=self.st_callback,
                    retry=self.retry,
                    timeout=self.timeout,
                    **self.request) for _ in range(self.chunk_size)
            ]
            self.req.x

    @property
    def x(self):
        """This attribute returns self.start()"""
        return self.start()
