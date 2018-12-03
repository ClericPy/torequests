#! coding:utf-8
# compatible for win32 / python 2 & 3
from __future__ import division, print_function

import argparse
import hashlib
import importlib
import json
import os
import pickle
import re
import shlex
import signal
import sys
import time
import timeit
from fractions import Fraction
from functools import wraps
from threading import Thread, Lock

from .configs import Config
from .exceptions import ImportErrorModule
from .logs import print_info
from .main import run_after_async, threads
from .versions import PY2, PY3

if PY2:
    import repr as reprlib
    from urllib import quote, quote_plus, unquote_plus
    from urlparse import (
        parse_qs,
        parse_qsl,
        urlparse,
        unquote,
        urljoin,
        urlsplit,
        urlunparse,
    )
    from cgi import escape
    import HTMLParser

    unescape = HTMLParser.HTMLParser().unescape

if PY3:
    import reprlib
    from urllib.parse import (
        parse_qs,
        parse_qsl,
        urlparse,
        quote,
        quote_plus,
        unquote,
        unquote_plus,
        urljoin,
        urlsplit,
        urlunparse,
    )
    from html import escape, unescape

    unicode = str

__all__ = "parse_qs parse_qsl urlparse quote quote_plus unquote unquote_plus urljoin urlsplit urlunparse escape unescape simple_cmd print_mem curlparse Null null itertools_chain slice_into_pieces slice_by_size ttime ptime split_seconds timeago timepass md5 Counts unique unparse_qs unparse_qsl Regex kill_after UA try_import ensure_request Timer ClipboardWatcher Saver guess_interval split_n find_one register_re_findone".split(
    " "
)


def simple_cmd():
    """
    ``Deprecated``: Not better than ``fire`` -> pip install fire
    """
    parser = argparse.ArgumentParser(
        prog="Simple command-line function toolkit.",
        description="""Input function name and args and kwargs.
        python xxx.py main -a 1 2 3 -k a=1,b=2,c=3""",
    )
    parser.add_argument("-f", "--func_name", default="main")
    parser.add_argument("-a", "--args", dest="args", nargs="*")
    parser.add_argument("-k", "--kwargs", dest="kwargs")
    parser.add_argument(
        "-i",
        "-s",
        "--info",
        "--show",
        "--status",
        dest="show",
        action="store_true",
        help="show the args, kwargs and function's source code.",
    )
    params = parser.parse_args()
    func_name = params.func_name
    func = globals().get(func_name)
    if not (callable(func)):
        Config.utils_logger.warning("invalid func_name: %s" % func_name)
        return
    args = params.args or []
    kwargs = params.kwargs or {}
    if kwargs:
        items = [re.split("[:=]", i) for i in re.split("[,;]+", kwargs)]
        kwargs = dict(items)
    if params.show:
        from inspect import getsource

        Config.utils_logger.info("args: %s; kwargs: %s" % (args, kwargs))
        Config.utils_logger.info(getsource(func))
        return
    func(*args, **kwargs)


def print_mem(unit="MB"):
    """Show the proc-mem-cost with psutil, use this only for lazinesssss.

    :param unit: B, KB, MB, GB.
    """
    try:
        import psutil

        B = float(psutil.Process(os.getpid()).memory_info().vms)
        KB = B / 1024
        MB = KB / 1024
        GB = MB / 1024
        result = vars()[unit]
        print_info("memory usage: %.2f(%s)" % (result, unit))
        return result
    except ImportError:
        print_info("pip install psutil first.")


class _Curl:
    """Curl args parser.

    **Use curlparse function directly.**
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("curl")
    parser.add_argument("url")
    parser.add_argument("-X", "--method", default="get")
    parser.add_argument("-A", "--user-agent")
    parser.add_argument("-u", "--user")  # <user[:password]>
    parser.add_argument("-x", "--proxy")  # proxy.com:port
    parser.add_argument("-d", "--data")
    parser.add_argument("--data-binary")
    parser.add_argument("--connect-timeout", type=float)
    parser.add_argument("-H", "--header", action="append", default=[])  # key: value
    parser.add_argument("--compressed", action="store_true")


def curlparse(string, encoding="utf-8"):
    """Translate curl-string into dict of request.
        :param string: standard curl-string, like `r'''curl ...'''`.
        :param encoding: encoding for post-data encoding.

    Basic Usage::

      >>> from torequests.utils import curlparse
      >>> curl_string = '''curl 'https://p.3.cn?skuIds=1&nonsense=1&nonce=0' -H 'Pragma: no-cache' -H 'DNT: 1' -H 'Accept-Encoding: gzip, deflate' -H 'Accept-Language: zh-CN,zh;q=0.9' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Cache-Control: no-cache' -H 'Referer: https://p.3.cn?skuIds=1&nonsense=1&nonce=0' -H 'Cookie: ASPSESSIONIDSQRRSADB=MLHDPOPCAMBDGPFGBEEJKLAF' -H 'Connection: keep-alive' --compressed'''
      >>> request_args = curlparse(curl_string)
      >>> request_args
      {'url': 'https://p.3.cn?skuIds=1&nonsense=1&nonce=0', 'headers': {'Pragma': 'no-cache', 'Dnt': '1', 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.9', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'Cache-Control': 'no-cache', 'Referer': 'https://p.3.cn?skuIds=1&nonsense=1&nonce=0', 'Cookie': 'ASPSESSIONIDSQRRSADB=MLHDPOPCAMBDGPFGBEEJKLAF', 'Connection': 'keep-alive'}, 'method': 'get'}
      >>> import requests
      >>> requests.request(**request_args)
      <Response [200]>
    """
    assert "\n" not in string, 'curl-string should not contain \\n, try r"...".'
    if string.startswith("http"):
        return {"url": string, "method": "get"}
    args, unknown = _Curl.parser.parse_known_args(shlex.split(string.strip()))
    requests_args = {}
    headers = {}
    requests_args["url"] = args.url
    for header in args.header:
        key, value = header.split(":", 1)
        headers[key.title()] = value.strip()
    if args.user_agent:
        headers["User-Agent"] = args.user_agent
    if headers:
        requests_args["headers"] = headers
    if args.user:
        requests_args["auth"] = tuple(u for u in args.user.split(":", 1) + [""])[:2]
    # if args.proxy:
    # pass
    data = args.data or args.data_binary
    if data:
        if data.startswith("$"):
            data = data[1:]
        args.method = "post"
        if "application/x-www-form-urlencoded" in headers.get("Content-Type", ""):
            data = dict(
                [
                    (i.split("=")[0], unquote_plus(i.split("=")[1]))
                    for i in data.split("&")
                ]
            )
            requests_args["data"] = data
        else:
            data = data.encode(encoding)
            requests_args["data"] = data
    requests_args["method"] = args.method.lower()
    return requests_args


class Null(object):
    """Null instance will return self when be called, it will alway be False."""

    def __init__(self, *args, **kwargs):
        return

    def __call__(self, *args, **kwargs):
        return self

    def __getattr__(self, mname):
        return self

    def __setattr__(self, name, value):
        return self

    def __getitem__(self, key):
        return self

    def __delattr__(self, name):
        return self

    def __repr__(self):
        return ""

    def __str__(self):
        return ""

    def __bool__(self):
        return False

    def __nonzero__(self):
        return False


null = Null()


def itertools_chain(*iterables):
    """For the shortage of Python2's, Python3: `from itertools import chain`."""
    for it in iterables:
        for element in it:
            yield element


def slice_into_pieces(seq, n):
    """Slice a sequence into `n` pieces, return a generation of n pieces"""
    length = len(seq)
    if length % n == 0:
        size = length // n
    else:
        size = length // n + 1
    for it in slice_by_size(seq, size):
        yield it


def slice_by_size(seq, size):
    """Slice a sequence into chunks, return as a generation of chunks with `size`."""
    filling = null
    for it in zip(*(itertools_chain(seq, [filling] * size),) * size):
        if filling in it:
            it = tuple(i for i in it if i is not filling)
        if it:
            yield it


def ttime(timestamp=None, tzone=None, fail="", fmt="%Y-%m-%d %H:%M:%S"):
    """Translate timestamp into human-readable: %Y-%m-%d %H:%M:%S.

    :param timestamp: the timestamp float, or `time.time()` by default.
    :param tzone: time compensation, int(-time.timezone / 3600) by default,
                (can be set with Config.TIMEZONE).
    :param fail: while raising an exception, return it.
    :param fmt: %Y-%m-%d %H:%M:%S, %z not work.
    :rtype: str

    >>> ttime()
    2018-03-15 01:24:35
    >>> ttime(1486572818.421858323)
    2017-02-09 00:53:38
    """
    tzone = Config.TIMEZONE if tzone is None else tzone
    fix_tz = tzone * 3600
    if timestamp is None:
        timestamp = time.time()
    else:
        timestamp = float(timestamp)
        if 1e12 <= timestamp < 1e13:
            # Compatible timestamp with 13-digit milliseconds
            timestamp = timestamp / 1000
    try:
        timestamp = time.time() if timestamp is None else timestamp
        return time.strftime(fmt, time.gmtime(timestamp + fix_tz))
    except:
        import traceback

        traceback.print_exc()
        return fail


def ptime(timestr=None, tzone=None, fail=0, fmt="%Y-%m-%d %H:%M:%S"):
    """Translate %Y-%m-%d %H:%M:%S into timestamp.

    :param timestr: string like 2018-03-15 01:27:56, or time.time() if not set.
    :param tzone: time compensation, int(-time.timezone / 3600) by default,
                (can be set with Config.TIMEZONE).
    :param fail: while raising an exception, return it.
    :param fmt: %Y-%m-%d %H:%M:%S, %z not work.
    :rtype: int

        >>> ptime('2018-03-15 01:27:56')
        1521048476
    """
    tzone = Config.TIMEZONE if tzone is None else tzone
    fix_tz = -(tzone * 3600 + time.timezone)
    #: str(timestr) for datetime.datetime object
    timestr = str(timestr or ttime())
    try:
        return int(time.mktime(time.strptime(timestr, fmt)) + fix_tz)
    except:
        return fail


def split_seconds(seconds):
    """Split seconds into [day, hour, minute, second, ms]

        `divisor: 1, 24, 60, 60, 1000`

        `units: day, hour, minute, second, ms`

    >>> split_seconds(6666666)
    [77, 3, 51, 6, 0]
    """
    ms = seconds * 1000
    divisors = (1, 24, 60, 60, 1000)
    quotient, result = ms, []
    for divisor in divisors[::-1]:
        quotient, remainder = divmod(quotient, divisor)
        result.append(quotient) if divisor == 1 else result.append(remainder)
    return result[::-1]


def timeago(seconds=0, accuracy=4, format=0, lang="en"):
    """Translate seconds into human-readable.

        :param seconds: seconds (float/int).
        :param accuracy: 4 by default (units[:accuracy]), determine the length of elements.
        :param format: index of [led, literal, dict].
        :param lang: en or cn.
        :param units: day, hour, minute, second, ms.

    >>> timeago(93245732.0032424, 5)
    '1079 days, 05:35:32,003'
    >>> timeago(93245732.0032424, 4, 1)
    '1079 days 5 hours 35 minutes 32 seconds'
    >>> timeago(-389, 4, 1)
    '-6 minutes 29 seconds 0 ms'
    """
    assert format in [0, 1, 2], ValueError("format arg should be one of 0, 1, 2")
    negative = "-" if seconds < 0 else ""
    seconds = abs(seconds)
    if lang == "en":
        units = ("day", "hour", "minute", "second", "ms")
    elif lang == "cn":
        units = (u"天", u"小时", u"分钟", u"秒", u"毫秒")
    times = split_seconds(seconds)
    if format == 2:
        return dict(zip(units, times))

    day, hour, minute, second, ms = times

    if format == 0:
        day_str = (
            "%d %s%s, " % (day, units[0], "s" if day > 1 and lang == "en" else "")
            if day
            else ""
        )
        mid_str = ":".join(("%02d" % i for i in (hour, minute, second)))
        if accuracy > 4:
            mid_str += ",%03d" % ms
        return negative + day_str + mid_str
    elif format == 1:
        # find longest valid fields index (non-zero in front)
        valid_index = 0
        for x, i in enumerate(times):
            if i > 0:
                valid_index = x
                break
        else:
            valid_index = x
        result_str = [
            "%d %s%s" % (num, unit, "s" if num > 1 and unit != "ms" else "")
            for num, unit in zip(times, units)
        ][valid_index:][:accuracy]
        result_str = " ".join(result_str)
        return negative + result_str


# alias name
timepass = timeago


def md5(string, n=32, encoding="utf-8", skip_encode=False):
    """str(obj) -> md5_string

    :param string: string to operate.
    :param n: md5_str length.

    >>> from torequests.utils import md5
    >>> md5(1, 10)
    '923820dcc5'
    >>> md5('test')
    '098f6bcd4621d373cade4e832627b4f6'
    """
    todo = string if skip_encode else unicode(string).encode(encoding)
    if n == 32:
        return hashlib.md5(todo).hexdigest()
    elif isinstance(n, (int, float)):
        return hashlib.md5(todo).hexdigest()[(32 - n) // 2 : (n - 32) // 2]
    elif isinstance(n, (tuple, list)):
        return hashlib.md5(todo).hexdigest()[n[0] : n[1]]


class Counts(object):
    """Counter for counting the times been called

    >>> from torequests.utils import Counts
    >>> cc = Counts()
    >>> cc.x
    1
    >>> cc.x
    2
    >>> cc.now
    2
    >>> cc.current
    2
    >>> cc.sub()
    1
    """

    __slots__ = ("start", "step", "current", "total")

    def __init__(self, start=0, step=1):
        self.start = start
        self.step = step
        self.current = start
        self.total = -1

    def clear(self):
        self.current = self.start

    @property
    def x(self):
        return self.add()

    @property
    def s(self):
        return self.sub()

    @property
    def c(self):
        return self.x

    @property
    def now(self):
        return self.current

    def add(self, num=None):
        self.current += num or self.step
        return self.current

    def sub(self, num=None):
        self.current -= num or self.step
        return self.current


def unique(seq, key=None, return_as=None):
    """Unique the seq and keep the order.

    Instead of the slow way:
        `lambda seq: (x for index, x in enumerate(seq) if seq.index(x)==index)`

    :param seq: raw sequence.
    :param return_as: generator for default, or list / set / str...

    >>> from torequests.utils import unique
    >>> a = [1,2,3,4,2,3,4]
    >>> unique(a)
    <generator object unique.<locals>.<genexpr> at 0x05720EA0>
    >>> unique(a, str)
    '1234'
    >>> unique(a, list)
    [1, 2, 3, 4]
    """
    seen = set()
    add = seen.add
    if key:
        generator = (x for x in seq if key(x) not in seen and not add(key(x)))
    else:
        generator = (x for x in seq if x not in seen and not add(x))
    if return_as:
        if return_as == str:
            return "".join(map(str, generator))
        else:
            return return_as(generator)
    else:
        # python2 not support yield from
        return generator


def unparse_qs(qs, sort=False, reverse=False):
    """Reverse conversion for parse_qs"""
    result = []
    items = qs.items()
    if sort:
        items = sorted(items, key=lambda x: x[0], reverse=reverse)
    for keys, values in items:
        query_name = quote(keys)
        for value in values:
            result.append(query_name + "=" + quote(value))
    return "&".join(result)


def unparse_qsl(qsl, sort=False, reverse=False):
    """Reverse conversion for parse_qsl"""
    result = []
    items = qsl
    if sort:
        items = sorted(items, key=lambda x: x[0], reverse=reverse)
    for keys, values in items:
        query_name = quote(keys)
        result.append(query_name + "=" + quote(values))
    return "&".join(result)


class Regex(object):
    """Register some objects(like functions) to the regular expression.

    >>> from torequests.utils import Regex, re
    >>> reg = Regex()
    >>> @reg.register_function('http.*cctv.*')
    ... def mock():
    ...     pass
    ...
    >>> reg.register('http.*HELLOWORLD', 'helloworld', instances='http://helloworld', flags=re.I)
    >>> reg.register('http.*HELLOWORLD2', 'helloworld2', flags=re.I)
    >>> reg.find('http://cctv.com')
    [<function mock at 0x031FC5D0>]
    >>> reg.match('http://helloworld')
    ['helloworld']
    >>> reg.match('non-http://helloworld')
    []
    >>> reg.search('non-http://helloworld')
    ['helloworld']
    >>> len(reg.search('non-http://helloworld2'))
    2
    >>> print(reg.show_all())
    ('http.*cctv.*') =>  => <class 'function'> mock ""
    ('http.*HELLOWORLD', re.IGNORECASE) => http://helloworld => <class 'str'> helloworld
    ('http.*HELLOWORLD2', re.IGNORECASE) =>  => <class 'str'> helloworld2
    >>> reg.fuzzy('non-http://helloworld')
    [('http://helloworld', 95)]
    """

    def __init__(self, ensure_mapping=False):
        """
        :param ensure_mapping: ensure mapping one to one, if False,
         will return all(more than 1) mapped object list."""
        self.container = []
        self.ensure_mapping = ensure_mapping

    def register(self, patterns, obj=None, instances=None, **reg_kwargs):
        """Register one object which can be matched/searched by regex.

        :param patterns: a list/tuple/set of regex-pattern.
        :param obj: return it while search/match success.
        :param instances: instance list will search/match the patterns.
        :param reg_kwargs: kwargs for re.compile.
        """
        assert obj, "bool(obj) should be True."
        patterns = patterns if isinstance(patterns, (list, tuple, set)) else [patterns]
        instances = instances or []
        instances = (
            instances if isinstance(instances, (list, tuple, set)) else [instances]
        )
        for pattern in patterns:
            pattern_compiled = re.compile(pattern, **reg_kwargs)
            self.container.append((pattern_compiled, obj, instances))
            if self.ensure_mapping:
                # check all instances to avoid one-to-many instances.
                self._check_instances()
            else:
                # no need to check all instances.
                for instance in instances:
                    assert self.search(instance) == [obj] or self.match(instance) == [
                        obj
                    ], (
                        "instance %s should fit at least one pattern %s"
                        % (instance, pattern)
                    )

    def register_function(self, patterns, instances=None, **reg_kwargs):
        """Decorator for register."""

        def wrapper(function):
            self.register(patterns, function, instances=instances, **reg_kwargs)
            return function

        return wrapper

    def find(self, string, default=None):
        """Return match or search result.

        :rtype: list"""
        return self.match(string) or self.search(string) or default

    def search(self, string, default=None):
        """Use re.search to find the result

        :rtype: list"""
        default = default if default else []
        result = [item[1] for item in self.container if item[0].search(string)]
        if self.ensure_mapping:
            assert len(result) < 2, "%s matches more than one pattern: %s" % (
                string,
                result,
            )
        return result if result else default

    def match(self, string, default=None):
        """Use re.search to find the result

        :rtype: list"""
        default = default if default else []
        result = [item[1] for item in self.container if item[0].match(string)]
        if self.ensure_mapping:
            assert len(result) < 2, "%s matches more than one pattern: %s" % (
                string,
                result,
            )
        return result if result else default

    def fuzzy(self, key, limit=5):
        """Give suggestion from all instances."""
        instances = [i[2] for i in self.container if i[2]]
        if not instances:
            return
        instances = sum(instances, [])
        from fuzzywuzzy import process

        maybe = process.extract(key, instances, limit=limit)
        return maybe

    def _check_instances(self):
        for item in self.container:
            for instance in item[2]:
                assert self.search(instance) or self.match(
                    instance
                ), "instance %s not fit pattern %s" % (instance, item[0].pattern)

    def show_all(self, as_string=True):
        """, python2 will not show flags"""
        result = []
        for item in self.container:
            pattern = str(item[0])[10:] if PY3 else item[0].pattern
            instances = item[2] or []
            value = (
                '%s "%s"' % (item[1].__name__, (item[1].__doc__ or ""))
                if callable(item[1])
                else str(item[1])
            )
            value = "%s %s" % (type(item[1]), value)
            result.append(" => ".join((pattern, ",".join(instances), value)))
        return "\n".join(result) if as_string else result


def kill_after(seconds, timeout=2):
    """Kill self after seconds"""
    pid = os.getpid()
    kill = os.kill
    run_after_async(seconds, kill, pid, signal.SIGTERM)
    run_after_async(seconds + timeout, kill, pid, 9)


class UA:
    """Some common User-Agents for crawler.

    Android, iPhone, iPad, Firefox, Chrome, IE6, IE9"""

    __slots__ = ()
    Android = "Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Mobile Safari/537.36"
    iPhone = "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1"
    iPad = "Mozilla/5.0 (iPad; CPU OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1"
    Firefox = (
        "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0"
    )
    Chrome = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36"
    IE6 = "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"
    IE9 = "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;"
    WECHAT_ANDROID = "Mozilla/5.0 (Linux; Android 5.0; SM-N9100 Build/LRX21V) > AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 > Chrome/37.0.0.0 Mobile Safari/537.36 > MicroMessenger/6.0.2.56_r958800.520 NetType/WIFI"
    WECHAT_IOS = "Mozilla/5.0 (iPhone; CPU iPhone OS 5_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Mobile/9B176 MicroMessenger/4.3.2"


def try_import(module_name, names=None, default=ImportErrorModule, warn=True):
    """Try import module_name, except ImportError and return default,
        sometimes to be used for catch ImportError and lazy-import.
    """
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        if warn:
            if warn is True:
                Config.utils_logger.warning(
                    "Module `%s` not found. Install it to remove this warning"
                    % module_name
                )
            else:
                warn(module_name, names, default)
        module = (
            ImportErrorModule(module_name) if default is ImportErrorModule else default
        )
    if not names:
        return module
    if not isinstance(names, (tuple, set, list)):
        names = [names]
    result = []
    for name in names:
        if hasattr(module, name):
            result.append(module.__getattribute__(name))
        else:
            result.append(
                ImportErrorModule("%s.%s" % (module_name, name))
                if default is ImportErrorModule
                else default
            )
    return result[0] if len(result) == 1 else result


def ensure_request(request):
    """Used for requests.request / Requests.request with **ensure_request(request)
    :param request: dict or curl-string or url

    >>> from torequests.utils import ensure_request
    >>> ensure_request('''curl http://test.com''')
    {'url': 'http://test.com', 'method': 'get'}
    >>> ensure_request('http://test.com')
    {'method': 'get', 'url': 'http://test.com'}
    >>> ensure_request({'method': 'get', 'url': 'http://test.com'})
    {'method': 'get', 'url': 'http://test.com'}
    >>> ensure_request({'url': 'http://test.com'})
    {'url': 'http://test.com', 'method': 'get'}

    """
    if isinstance(request, dict):
        result = request
    elif isinstance(request, (unicode, str)):
        request = request.strip()
        if request.startswith("http"):
            result = {"method": "get", "url": request}
        elif request.startswith("curl "):
            result = curlparse(request)
    else:
        raise ValueError("request should be dict or str.")
    result["method"] = result.setdefault("method", "get").lower()
    return result


class Timer(object):
    """
    Usage:
        init Timer anywhere:
            such as head of function, or head of module, then it will show log after del it by gc.

        :param name: be used in log or None.
        :param log_func: some function to show process.
        :param default_timer: use `timeit.default_timer` by default.
        :param rounding: None, or seconds will be round(xxx, rounding)
        :param readable: None, or use `timepass`: readable(cost_seconds) -> 00:00:01,234

        ::

            from torequests.utils import Timer
            import time
            Timer()

            @Timer.watch()
            def test(a=1):
                Timer()
                time.sleep(1)

                def test_inner():
                    t = Timer('test_non_del')
                    time.sleep(1)
                    t.x

                test_inner()

            test(3)
            time.sleep(1)
            # [2018-03-10 02:16:48]: Timer [00:00:01]: test_non_del, start at 2018-03-10 02:16:47.
            # [2018-03-10 02:16:48]: Timer [00:00:02]: test(a=3), start at 2018-03-10 02:16:46.
            # [2018-03-10 02:16:48]: Timer [00:00:02]: test(3), start at 2018-03-10 02:16:46.
            # [2018-03-10 02:16:49]: Timer [00:00:03]: <module>: __main__ (temp_code.py), start at 2018-03-10 02:16:46.

    """

    def __init__(
        self,
        name=None,
        log_func=None,
        default_timer=None,
        rounding=None,
        readable=None,
        log_after_del=True,
        stack_level=1,
    ):
        readable = readable or timepass
        self._log_after_del = False
        self.start_at = time.time()
        uid = md5("%s%s" % (self.start_at, id(self)))
        if not name:
            f_name = sys._getframe(stack_level).f_code.co_name
            f_local = sys._getframe(stack_level).f_locals
            if f_name == "<module>":
                f_vars = ": %s (%s)" % (
                    f_local.get("__name__"),
                    os.path.split(f_local.get("__file__"))[-1],
                )
                # f_vars = f_vars.replace(' __main__', '')
            else:
                f_vars = (
                    "(%s)"
                    % ", ".join(
                        [
                            "%s=%s" % (i, repr(f_local[i]))
                            for i in sorted(f_local.keys())
                        ]
                    )
                    if f_local
                    else "()"
                )
            if self not in f_local.values():
                # add self to name space for __del__ way.
                sys._getframe(stack_level).f_locals.update(**{uid: self})
            name = "%s%s" % (f_name, f_vars)
        self.name = name
        self.log_func = log_func
        self.timer = default_timer or timeit.default_timer
        self.rounding = rounding
        self.readable = readable
        self.start_timer = self.timer()
        self._log_after_del = log_after_del

    @property
    def string(self):
        """Only return the expect_string quietly."""
        return self.tick()

    @property
    def x(self):
        """Call self.log_func(self) and return expect_string."""
        self._log_after_del = False
        passed_string = self.string
        if self.log_func:
            self.log_func(self)
        else:
            print_info(
                "Timer [%(passed)s]: %(name)s, start at %(start)s."
                % (
                    dict(
                        name=self.name, start=ttime(self.start_at), passed=passed_string
                    )
                )
            )
        return passed_string

    @property
    def passed(self):
        """Return the cost_seconds after starting up."""
        return self.timer() - self.start_timer

    def tick(self):
        """Return the time cost string as expect."""
        string = self.passed
        if self.rounding:
            string = round(string)
        if self.readable:
            string = self.readable(string)
        return string

    @staticmethod
    def watch(*timer_args, **timer_kwargs):
        """Decorator for Timer."""

        def wrapper(function):
            @wraps(function)
            def inner(*args, **kwargs):
                args1 = ", ".join(map(repr, args)) if args else ""
                kwargs1 = ", ".join(
                    ["%s=%s" % (i, repr(kwargs[i])) for i in sorted(kwargs.keys())]
                )
                arg = ", ".join(filter(None, [args1, kwargs1]))
                name = "%s(%s)" % (function.__name__, arg)
                _ = Timer(name=name, *timer_args, **timer_kwargs)
                result = function(*args, **kwargs)
                return result

            return inner

        return wrapper

    def __del__(self):
        if self._log_after_del:
            # not be called by self.x yet.
            self.x

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.x


def ensure_dict_key_title(dict_obj):
    """Set the dict key as key.title(); keys should be str.
    Always be used to headers.

        >>> from torequests.utils import ensure_dict_key_title
        >>> ensure_dict_key_title({'hello-world':1, 'HELLOWORLD':2})
        {'Hello-World': 1, 'Helloworld': 2}
    """
    if not all((isinstance(i, unicode) for i in dict_obj.keys())):
        return dict_obj
    return {key.title(): value for key, value in dict_obj.items()}


class ClipboardWatcher(object):
    """Watch clipboard with `pyperclip`, run callback while changed."""

    def __init__(self, interval=0.2, callback=None):
        self.pyperclip = try_import("pyperclip")
        self.interval = interval
        self.callback = callback or self.default_callback
        self.temp = self.current

    def read(self):
        """Return the current clipboard content."""
        return self.pyperclip.paste()

    def write(self, text):
        """Rewrite the current clipboard content."""
        return self.pyperclip.copy(text)

    @property
    def current(self):
        """Return the current clipboard content."""
        return self.read()

    def default_callback(self, text):
        """Default clean the \\n in text."""
        text = text.replace("\r\n", "\n")
        text = "%s\n" % text
        flush_print(text, sep="", end="")
        return text

    def watch(self, limit=None, timeout=None):
        """Block method to watch the clipboard changing."""
        start_time = time.time()
        count = 0
        while not timeout or time.time() - start_time < timeout:
            new = self.read()
            if new != self.temp:
                count += 1
                self.callback(new)
                if count == limit:
                    break
            self.temp = new
            time.sleep(self.interval)

    @property
    def x(self):
        """Return self.watch()"""
        return self.watch()

    @threads(1)
    def watch_async(self, limit=None, timeout=None):
        """Non-block method to watch the clipboard changing."""
        return self.watch(limit=limit, timeout=timeout)


class Saver(object):
    """
    Simple object persistent toolkit with pickle/json,
    if only you don't care the performance and security.
    **Do not set the key startswith "_"**

    :param path: if not set, will be ~/_saver.db. print(self._path) to show it.
        Set pickle's protocol < 3 for compatibility between python2/3,
        but use -1 for performance and some other optimizations.
    :param save_mode: pickle / json.
    >>> ss = Saver()
    >>> ss._path
    '/home/work/_saver.json'
    >>> ss.a = 1
    >>> ss['b'] = 2
    >>> str(ss)
    {'a': 1, 'b': 2, 'c': 3, 'd': 4}
    >>> del ss.b
    >>> str(ss)
    "{'a': 1, 'c': 3, 'd': 4}"
    >>> ss._update({'c': 3, 'd': 4})
    >>> ss
    Saver(path="/home/work/_saver.json"){'a': 1, 'c': 3, 'd': 4}
    """

    _instances = {}
    _locks = {}
    _protected_keys = {
        "_auto_backup",
        "_lock",
        "_path",
        "_saver_args",
        "_save_mode",
        "_cache",
        "__getitem__",
        "_keys",
        "_values",
        "__getattr__",
        "__len__",
        "_popitem",
        "_shutdown",
        "__setitem__",
        "__delitem__",
        "_save_obj",
        "_get",
        "__dict__",
        "_clear",
        "_locks",
        "__weakref__",
        "_items",
        "__module__",
        "_pop",
        "__contains__",
        "_load",
        "_save",
        "_update",
        "_set",
        "_protected_keys",
        "_instances",
        "_get_home_path",
        "_save_back_up",
    }
    _protected_keys = _protected_keys | set(object.__dict__.keys())

    def __new__(cls, path=None, save_mode="json", auto_backup=False, **saver_args):
        # BORG
        path = path or cls._get_home_path(save_mode=save_mode)
        return cls._instances.setdefault(path, super(Saver, cls).__new__(cls))

    def __init__(self, path=None, save_mode="json", auto_backup=False, **saver_args):
        super(Saver, self).__init__()
        self._auto_backup = auto_backup
        self._lock = self.__class__._locks.setdefault(path, Lock())
        self._path = path or self._get_home_path(save_mode=save_mode)
        self._saver_args = saver_args
        self._save_mode = save_mode
        self._cache = self._load()

    @classmethod
    def _get_home_path(cls, save_mode=None):
        home = os.path.expanduser("~")
        if save_mode == "json":
            ext = "json"
        elif save_mode == "pickle":
            ext = "pkl"
        else:
            ext = "db"
        file_name = "_saver.%s" % ext
        path = os.path.join(home, file_name)
        return path

    def _save_back_up(self):
        with open(self._path, "rb") as f_raw:
            with open(self._path + ".bk", "wb") as f_bk:
                f_bk.write(f_raw.read())

    def _save_obj(self, obj):
        mode = "wb" if self._save_mode == "pickle" else "w"
        with self._lock:
            with open(self._path, mode) as f:
                if self._save_mode == "json":
                    json.dump(obj, f, **self._saver_args)
                if self._save_mode == "pickle":
                    pickle.dump(obj, f, **self._saver_args)
            if self._auto_backup:
                self._save_back_up()
        return obj

    def _load(self):
        if not (os.path.isfile(self._path) and os.path.getsize(self._path)):
            cache = {}
            self._save_obj(cache)
            return cache
        mode = "rb" if self._save_mode == "pickle" else "r"
        with self._lock:
            with open(self._path, mode) as f:
                if self._save_mode == "json":
                    return json.load(f)
                if self._save_mode == "pickle":
                    return pickle.load(f)

    def _save(self):
        return self._save_obj(self._cache)

    def _set(self, key, value):
        if self._save_mode == "json":
            try:
                json.dumps(value)
            except TypeError:
                Config.utils_logger.warning(
                    "Saver._set(%s, %s) failed: bad type, using str(value) instead."
                    % (key, value)
                )
                value = str(value)
        self._cache[key] = value
        self._save()

    def _get(self, key, default=None):
        return self._cache.get(key, default)

    def __setattr__(self, key, value):
        if key in self._protected_keys:
            object.__setattr__(self, key, value)
        else:
            self._set(key, value)

    def __getattr__(self, key):
        if key in self._protected_keys:
            return object.__getattribute__(self, key)
        return self._get(key)

    def __contains__(self, key):
        return key in self._cache

    def __delattr__(self, key):
        self._cache.pop(key, None)
        self._save()

    def __dir__(self):
        return dir(object)

    def __len__(self):
        return len(self._cache)

    def _clear(self):
        self._cache = {}
        self._save()

    def _shutdown(self):
        if self._auto_backup:
            os.remove(self._path + ".bk")
        return os.remove(self._path)

    def _keys(self):
        return self._cache.keys()

    def _items(self):
        return self._cache.items()

    def _values(self):
        return self._cache.values()

    def _pop(self, key, default=None):
        result = self._cache.pop(key, default)
        self._save()
        return result

    def _popitem(self):
        result = self._cache.popitem()
        self._save()
        return result

    def _update(self, *args, **kwargs):
        self._cache.update(*args, **kwargs)
        self._save()

    def __getitem__(self, key):
        if key in self._cache:
            return self._get(key)
        raise KeyError

    def __setitem__(self, key, value):
        self._set(key, value)

    def __delitem__(self, key):
        self._cache.pop(key, None)
        self._save()

    def __str__(self):
        return str(self._cache)

    def __repr__(self):
        return 'Saver(path="%s")%s' % (self._path, reprlib.repr(self._cache))


def guess_interval(nums, accuracy=0):
    """Given a seq of number, return the median, only calculate interval >= accuracy.

    ::

        from torequests.utils import guess_interval
        import random

        seq = [random.randint(1, 100) for i in range(20)]
        print(guess_interval(seq, 5))
        # sorted_seq: [2, 10, 12, 19, 19, 29, 30, 32, 38, 40, 41, 54, 62, 69, 75, 79, 82, 88, 97, 99]
        # diffs: [8, 7, 10, 6, 13, 8, 7, 6, 6, 9]
        # median: 8
    """
    if not nums:
        return 0
    nums = sorted([int(i) for i in nums])
    if len(nums) == 1:
        return nums[0]
    diffs = [nums[i + 1] - nums[i] for i in range(len(nums) - 1)]
    diffs = [item for item in diffs if item >= accuracy]
    sorted_diff = sorted(diffs)
    result = sorted_diff[len(diffs) // 2]
    return result


def _re_split_mixin(string, sep, reg=False):
    if reg:
        return re.split(sep, string)
    else:
        return string.split(sep)


def split_n(string, seps, reg=False):
    r"""Split strings into n-dimensional list.

    ::

        from torequests.utils import split_n

        ss = '''a b c  d e f  1 2 3  4 5 6
        a b c  d e f  1 2 3  4 5 6
        a b c  d e f  1 2 3  4 5 6'''

        print(split_n(ss, ('\n', '  ', ' ')))
        # [[['a', 'b', 'c'], ['d', 'e', 'f'], ['1', '2', '3'], ['4', '5', '6']], [['a', 'b', 'c'], ['d', 'e', 'f'], ['1', '2', '3'], ['4', '5', '6']], [['a', 'b', 'c'], ['d', 'e', 'f'], ['1', '2', '3'], ['4', '5', '6']]]
        print(split_n(ss, ['\s+'], reg=1))
        # ['a', 'b', 'c', 'd', 'e', 'f', '1', '2', '3', '4', '5', '6', 'a', 'b', 'c', 'd', 'e', 'f', '1', '2', '3', '4', '5', '6', 'a', 'b', 'c', 'd', 'e', 'f', '1', '2', '3', '4', '5', '6']
    """
    deep = len(seps)
    if not deep:
        return string
    return [split_n(i, seps[1:]) for i in _re_split_mixin(string, seps[0], reg=reg)]


def bg(func):
    """Run a function in background, will not block main thread's exit.(thread.daemon=True)
    ::

        from torequests.utils import bg, print_info
        import time

        def test1(n):
            time.sleep(n)
            print_info(n, 'done')

        @bg
        def test2(n):
            time.sleep(n)
            print_info(n, 'done')

        test3 = bg(test1)

        test2(1)
        test3(1)
        print_info('not be blocked')
        time.sleep(2)

        # [2018-06-12 23:46:19](L81): not be blocked
        # [2018-06-12 23:46:20](L81): 1 done
        # [2018-06-12 23:46:20](L81): 1 done
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        t = Thread(target=func, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
        return t

    return wrapper


def countdown(
    seconds=None,
    block=True,
    interval=1,
    daemon=True,
    tick_callback=None,
    finish_callback=None,
):
    """Run a countdown function to wait something, similar to threading.Timer,
     but will show the detail tick by tick_callback.
     ::

        from torequests.utils import countdown

        countdown(3)
        # 3 2 1 
        # countdown finished [3 seconds]: 2018-06-13 00:12:55 => 2018-06-13 00:12:58.
        countdown('2018-06-13 00:13:29')
        # 10 9 8 7 6 5 4 3 2 1 
        # countdown finished [10 seconds]: 2018-06-13 00:13:18 => 2018-06-13 00:13:28.
"""

    def default_tick_callback(s, seconds, *args):
        flush_print(s, sep="", end=" ")

    def default_finish_callback(seconds, start_time):
        print(
            "\ncountdown finished [%s seconds]: %s => %s."
            % (seconds, ttime(start_time), ttime())
        )

    def cd(seconds, interval):
        for s in range(seconds, 0, -interval):
            tick_callback(s, seconds, interval)
            time.sleep(interval)
        if finish_callback:
            finish_callback(seconds, start_time)

    assert seconds or end_time
    start_time = time.time()
    tick_callback = tick_callback or default_tick_callback
    finish_callback = finish_callback or default_finish_callback

    if unicode(seconds).isdigit():
        seconds = int(seconds)
    elif isinstance(seconds, (unicode, str)):
        seconds = int(ptime(seconds) - time.time())
    t = Thread(target=cd, args=(seconds, interval))
    t.daemon = daemon
    t.start()
    if block:
        t.join()


def flush_print(*args, **kwargs):
    """
    Like print_function at python3, support flush, but not support file.
    :param sep: space by default
    :param end: '\\n' by default
    :param flush: True by default

     ::

        import time
        from torequests.utils import flush_print

        flush_print("=" * 10)
        for _ in range(10):
            time.sleep(0.2)
            flush_print("=", sep="", end="")
    """
    # PY2 raise SyntaxError for : def flush_print(*args, sep='', end=''):
    sep, end, flush = (
        kwargs.pop("sep", " "),
        kwargs.pop("end", "\n"),
        kwargs.pop("flush", 1),
    )
    string = sep.join((unicode(i) for i in args))
    sys.stdout.write("%s%s" % (string, end))
    if flush:
        sys.stdout.flush()


class ProgressBar(object):
    """Simple progress bar.
        :param size: total counts of calling ProgressBar.x.
        :param length: length of print log.
        :param sig: string of each printing log.

    Basic Usage::

        pb = ProgressBar(50, 10)
        for _ in range(50):
            time.sleep(0.1)
            pb.x
        print("current completion rate:", pb.completion_rate)
        # ==========
        # ==========
        # current completion rate: 1.0
    """

    def __init__(self, size, length=100, sig="="):
        self.size = size or 0
        self.length = length
        self.sig = sig
        self.current = 0
        self.last_print = 0
        self.printed = 0
        if size:
            # use Fraction for the deviation of division
            self.chunk = Fraction(self.size, self.length)
            flush_print(self.sig * self.length)
        else:
            self.chunk = 1

    def add(self, step):
        # ensure step >= 0
        self.current += step
        count = int((self.current - self.last_print) / self.chunk)
        if count < 1:
            return self.printed
        for _ in range(count):
            self.printed += 1
            flush_print(self.sig, end="")
        self.last_print = count * self.chunk + self.last_print
        if self.current == self.size:
            flush_print()
        return self.printed

    @property
    def x(self):
        return self.add(1)

    @property
    def completion_rate(self):
        return self.current / self.size


class RegMatch(object):
    """JS-like match object. Use index number to get groups, if not match or no group, will return ''."""

    def __init__(self, item):
        self.item = item

    def __getattr__(self, key, default=null):
        return getattr(self.item, key, default)

    def __getitem__(self, index):
        if self.item is None:
            return ""
        if not isinstance(index, int):
            raise IndexError
        try:
            return self.item.group(index)
        except IndexError:
            return ""

    @classmethod
    def find_one(cls, pattern, string, flags=0):
        """JS-like match object. Use index number to get groups, if not match or no group, will return ''.

        Basic Usage::

            >>> from torequests.utils import find_one
            >>> string = "abcd"
            >>> find_one("a.*", string)
            <torequests.utils.RegMatch object at 0x0705F1D0>
            >>> find_one("a.*", string)[0]
            'abcd'
            >>> find_one("a.*", string)[1]
            ''
            >>> find_one("a(.)", string)[0]
            'ab'
            >>> find_one("a(.)", string)[1]
            'b'
            >>> find_one("a(.)", string)[2] or "default"
            'default'
            >>> import re
            >>> item = find_one("a(B)(C)", string, flags=re.I | re.S)
            >>> item
            <torequests.utils.RegMatch object at 0x0705F1D0>
            >>> item[0]
            'abc'
            >>> item[1]
            'b'
            >>> item[2]
            'c'
            >>> item[3]
            ''
            >>> # import re
            >>> # re.findone = find_one
            >>> register_re_findone()
            >>> re.findone('a(b)', 'abcd')[1] or 'default'
            'b'

        """
        item = re.search(pattern, string, flags=flags)
        return cls(item)


find_one = RegMatch.find_one


def register_re_findone():
    """import re; re.findone = find_one"""
    re.findone = find_one
