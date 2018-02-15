#! coding:utf-8
# compatible for win32 / python 2 & 3
from __future__ import print_function

import argparse
import hashlib
import importlib
import os
import re
import shlex
import signal
import sys
import time
from timeit import default_timer
from functools import wraps

from .exceptions import ImportErrorModule
from .configs import Config
from .main import run_after_async
from .versions import PY2, PY3

if PY2:
    from urllib import quote, quote_plus, unquote_plus
    from urlparse import parse_qs, parse_qsl, urlparse, unquote, urljoin, urlsplit, urlunparse
    from cgi import escape
    import HTMLParser
    unescape = HTMLParser.HTMLParser().unescape

if PY3:
    from urllib.parse import parse_qs, parse_qsl, urlparse, quote, quote_plus, unquote, unquote_plus, urljoin, urlsplit, urlunparse
    from html import escape, unescape
    unicode = str


def simple_cmd():
    """
    **Deprecated**. The best use of another: fire. pip install fire
    """
    parser = argparse.ArgumentParser(
        prog='Simple command-line function toolkit.',
        description="""Input function name and args and kwargs.
        python xxx.py main -a 1 2 3 -k a=1,b=2,c=3""")
    parser.add_argument('-f', '--func_name', default='main')
    parser.add_argument('-a', '--args', dest='args', nargs='*')
    parser.add_argument('-k', '--kwargs', dest='kwargs')
    parser.add_argument(
        '-i',
        '-s',
        '--info',
        '--show',
        '--status',
        dest='show',
        action='store_true',
        help='show the args, kwargs and function\'s source code.')
    params = parser.parse_args()
    func_name = params.func_name
    func = globals().get(func_name)
    if not (callable(func)):
        Config.utils_logger.warn('invalid func_name: %s' % func_name)
        return
    args = params.args or []
    kwargs = params.kwargs or {}
    if kwargs:
        import re
        items = [re.split('[:=]', i) for i in re.split('[,;]+', kwargs)]
        kwargs = dict(items)
    if params.show:
        from inspect import getsource
        Config.utils_logger.info('args: %s; kwargs: %s' % (args, kwargs))
        Config.utils_logger.info(getsource(func))
        return
    func(*args, **kwargs)


class Curl(object):
    """
    translate curl string into a dict of requests kwargs.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('curl')
    parser.add_argument('url')
    parser.add_argument('-X', '--method', default='get')
    parser.add_argument('-A', '--user-agent')
    parser.add_argument('-u', '--user')  # <user[:password]>
    parser.add_argument('-x', '--proxy')  # proxy.com:port
    parser.add_argument('-d', '--data')
    parser.add_argument('--data-binary')
    parser.add_argument('--connect-timeout', type=float)
    parser.add_argument(
        '-H', '--header', action='append', default=[])  # key: value
    parser.add_argument('--compressed', action='store_true')

    @classmethod
    def parse(cls, cmd, encode='utf-8'):
        """requests.request(**Curl.parse(curl_bash));
           curl_bash sometimes should use r'...' """
        assert '\n' not in cmd, 'curl_bash should not contain \\n, try r"...".'
        if cmd.startswith('http'):
            return {'url': cmd, 'method': 'get'}
        args, unknown = cls.parser.parse_known_args(shlex.split(cmd.strip()))
        requests_args = {}
        headers = {}
        requests_args['url'] = args.url
        for header in args.header:
            key, value = header.split(":", 1)
            headers[key.lower()] = value.strip()
        if args.user_agent:
            headers['user-agent'] = args.user_agent
        if headers:
            requests_args['headers'] = headers
        if args.user:
            requests_args['auth'] = tuple(
                u for u in args.user.split(':', 1) + [''])[:2]
        # if args.proxy:
        # pass
        data = args.data or args.data_binary
        if data:
            if data.startswith('$'):
                data = data[1:]
            args.method = 'post'
            if headers.get(
                    'content-type') == 'tpplication/x-www-form-urlencoded':
                data = dict([(i.split('=')[0], unquote_plus(i.split('=')[1]))
                             for i in data.split('&')])
                requests_args['data'] = data
            # elif headers.get('content-type', '') in ('application/json',):
            # requests_args['json'] = json.loads(data)
            else:
                data = data.encode(encode)
                requests_args['data'] = data
        requests_args['method'] = args.method.lower()
        return requests_args


curlparse = Curl.parse


class Null(object):

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


null = Null()


def itertools_chain(*iterables):
    """From itertools import chain."""
    for it in iterables:
        for element in it:
            yield element


def slice_into_pieces(seq, n):
    """return a generation of pieces"""
    length = len(seq)
    if length % n == 0:
        size = length // n
    else:
        size = length // n + 1
    for it in slice_by_size(seq, size):
        yield it


def slice_by_size(seq, size):
    """return as a generation of chunks"""
    filling = null
    for it in zip(*(itertools_chain(seq, [filling] * size),) * size):
        if filling in it:
            it = tuple(i for i in it if i is not filling)
        if it:
            yield it


def ttime(timestamp=None, tzone=None, fail='', fmt='%Y-%m-%d %H:%M:%S'):
    """
    Translate timestamp into human-readable: %Y-%m-%d %H:%M:%S. %z not work.

    tzone: time compensation, by "+ time.timezone + tzone * 3600";
           eastern eight(+8) time zone by default(can be set with Config.TIMEZONE).

    fail: while raise an exception, return fail arg.
    > print(ttime())
    > print(ttime(1486572818.421858323)) # 2017-02-09 00:53:38
    """
    tzone = Config.TIMEZONE if tzone is None else tzone
    timestamp = timestamp if timestamp != None else time.time()
    timestamp = int(str(timestamp).split('.')[0][:10])
    try:
        timestamp = time.time() if timestamp is None else timestamp
        return time.strftime(
            fmt, time.localtime(timestamp + time.timezone + tzone * 3600))
    except:
        return fail


def ptime(timestr=None, tzone=None, fail=0, fmt='%Y-%m-%d %H:%M:%S'):
    """
    %Y-%m-%d %H:%M:%S -> timestamp. %z not work.
    tzone: timestamp compensation, by " - time.timezone - tzone * 3600";
           local time zone by default(can be set with Config.TIMEZONE).
    """
    tzone = Config.TIMEZONE if tzone is None else tzone
    timestr = timestr or ttime()
    try:
        return time.mktime(time.strptime(timestr,
                                         fmt)) - (time.timezone + tzone * 3600)
    except:
        return fail


def timeago(seconds=0, ms=False):
    """translate seconds into human-readable"""
    millisecond = seconds * 1000
    SS, MS = divmod(millisecond, 1000)
    MM, SS = divmod(SS, 60)
    HH, MM = divmod(MM, 60)
    DD, HH = divmod(HH, 24)
    string = "%02d:%02d:%02d" % (HH, MM, SS)
    if DD:
        string = '%s%s' % ("%d day%s, " % (DD, ''
                                           if abs(DD) == 1 else 's'), string)
    if ms:
        string = '%s%s' % (string, "%s%03d" % (',', int(MS) if MS else 0))
    return string


def timepass_with_ms(seconds=0):
    return timeago(seconds, ms=True)


# alias name
timepass = timeago


def read_second(seconds=None, accuracy=6, lang='en', sep=' '):
    """
    seconds: time.time() if seconds is None else seconds
    accuracy: 6 by default (means second), determine the length of elements.
    lang: en or cn.
    sep: join by sep, if sep=None, return a original list.
    ```
    print(read_second(6666))
    # 1 hours 51 mins 6 s
    print(read_second(66666666, accuracy=3))
    # 2 years 1 months 11 days
    print(read_second(666666666, 'cn'))
    # 21 年 1 月 21 天 1 小时 11 分钟 6 秒
    print(read_second(666666666, sep=None))
    # ['21 years', '1 months', '21 days', '1 hours', '11 mins', '6 s']
    ```
    """
    time_list = []
    seconds = time.time() if seconds is None else seconds
    readable = (u'年', u'月', u'天', u'小时', u'分钟',
                u'秒') if lang == 'cn' else ('years', 'months', 'days', 'hours',
                                            'mins', 's')
    if seconds <= 0:
        time_list.append(u'0 %s' % readable[-1])
    else:
        for i in zip((31536000, 2592000, 86400, 3600, 60, 1), readable):
            new = seconds // i[0]
            if new:
                time_list.append('%s %s' % (new, i[1]))
            seconds = seconds - new * i[0]
    result = time_list[:accuracy]
    if sep is None:
        return result
    else:
        return sep.join(result)


def md5(string, n=32, encoding='utf-8', skip_encode=False):
    """
    obj -> str
    """
    todo = string if skip_encode else unicode(string).encode(encoding)
    if n == 32:
        return hashlib.md5(todo).hexdigest()
    if n == 16:
        return hashlib.md5(todo).hexdigest()[8:-8]
    if isinstance(n, (tuple, list)):
        return hashlib.md5(todo).hexdigest()[n[0]:n[1]]


class Counts(object):
    __slots__ = ('start', 'step', 'current')

    def __init__(self, start=0, step=1):
        self.start = start
        self.step = step
        self.current = start

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

    def add(self):
        self.current += self.step
        return self.current

    def sub(self):
        self.current -= self.step
        return self.current


def unique(seq, return_as=None):
    """Unique the seq in order. 
    Instead of the slow way: 
        lambda seq: (x for index, x in enumerate(seq) if seq.index(x)==index)
    return_as: generator for default, or list / set / str..."""
    seen = set()
    add = seen.add
    generator = (x for x in seq if x not in seen and not add(x))
    if return_as:
        if return_as == str:
            return ''.join(map(str, generator))
        return return_as(generator)
    else:
        # python2 not support yield from
        return generator


def unparse_qs(qs, sort=False, reverse=False):
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
    result = []
    items = qsl
    if sort:
        items = sorted(items, key=lambda x: x[0], reverse=reverse)
    for keys, values in items:
        query_name = quote(keys)
        result.append(query_name + "=" + quote(values))
    return "&".join(result)


class Regex(object):
    """Input string, return a list of mapping object"""

    def __init__(self, ensure_mapping=False):
        """
        ensure_mapping: ensure mapping one to one, 
                        if False, will return all(more than 1) 
                        mapped object list."""
        self.container = []
        self.ensure_mapping = ensure_mapping

    def register(self, patterns, obj=None, instances=None, **reg_kwargs):
        patterns = patterns if isinstance(patterns,
                                          (list, tuple, set)) else [patterns]
        instances = instances or []
        instances = instances if isinstance(
            instances, (list, tuple, set)) else [instances]
        for pattern in patterns:
            pattern_compiled = re.compile(pattern, **reg_kwargs)
            self.container.append((pattern_compiled, obj, instances))
            if self.ensure_mapping:
                # check all instances to avoid one-to-many instances.
                self.check_instances()
            else:
                # no need to check all instances.
                for instance in instances:
                    assert self.search(instance) or self.match(instance), \
                        'instance %s not fit pattern %s' % (instance, pattern)

    def register_function(self, patterns, instances=None, **reg_kwargs):

        def wrapper(function):
            self.register(patterns, function, instances=instances, **reg_kwargs)
            return function

        return wrapper

    def search(self, string, default=None):
        default = default if default else []
        result = [item[1] for item in self.container if item[0].search(string)]
        if self.ensure_mapping:
            assert len(result) < 2, '%s matches more than one pattern: %s' % (
                string, result)
        return result if result else default

    def match(self, string, default=None):
        default = default if default else []
        result = [item[1] for item in self.container if item[0].match(string)]
        if self.ensure_mapping:
            assert len(result) < 2, '%s matches more than one pattern: %s' % (
                string, result)
        return result if result else default

    def fuzzy(self, key, limit=5):
        instances = [i[2] for i in self.container if i[2]]
        if not instances:
            return
        instances = sum(instances, [])
        from fuzzywuzzy import process
        maybe = process.extract(key, instances, limit=limit)
        return maybe

    def check_instances(self):
        for item in self.container:
            for instance in item[2]:
                assert self.search(instance) or self.match(instance), \
                    'instance %s not fit pattern %s' % (
                        instance, item[0].pattern)

    def show_all(self, as_string=True):
        """python2 will not show flags"""
        result = []
        for item in self.container:
            key = str(item[0])[10:] if PY3 else item[0].pattern
            instances = item[2] or []
            value = '%s "%s"' % (item[1].__name__,
                                 (item[1].__doc__ or '')) if callable(
                                     item[1]) else str(item[1])
            value = '%s %s' % (type(item[1]), value)
            result.append(' => '.join((','.join(instances), key, value)))
        return '\n'.join(result) if as_string else result


def kill_after(seconds, timeout=2):
    pid = os.getpid()
    kill = os.kill
    run_after_async(seconds, kill, pid, signal.SIGTERM)
    run_after_async(seconds + timeout, kill, pid, 9)


class UA:
    __slots__ = ()
    Android = 'Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Mobile Safari/537.36'
    iPhone = 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1'
    iPad = 'Mozilla/5.0 (iPad; CPU OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1'
    Firefox = 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0'
    Chrome = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
    IE6 = 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)'
    IE9 = 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;'


def try_import(module_name, names=None, default=ImportErrorModule, warn=True):
    """
    Try import module_name, except ImportError and return default.
    Sometimes be used for lazy-import, 
    """
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        if warn:
            if warn is True:
                Config.utils_logger.warn(
                    'Module `%s` not found. Install it to remove this warning' %
                    module_name)
            else:
                warn(module_name, names, default)
        module = ImportErrorModule(
            module_name) if default is ImportErrorModule else default
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
                ImportErrorModule('%s.%s' % (
                    module_name,
                    name)) if default is ImportErrorModule else default)
    return result[0] if len(result) == 1 else result


class Timer(object):
    """
    Usage:
        set a never_use_variable anywhere:
        such as head of function, or head of module
        def test():
            never_use_variable = Timer()
            ...
        then it will show log after del it.

    Args:
        name: will used in log
        log_func=print, or function like Config.utils_logger.info
        default_timer=default_timer -> timeit.default_timer
        rounding=None -> if setted, seconds will be round(xxx, rounding)
        readable=timepass: readable(cost_seconds) -> 00:00:01,234
    Attr:
        self.tick() -> return the expect time_cost_string
        self.string -> return self.tick()
        self.x -> return self.string, and output it
        self.passed -> return seconds passed after self.start
        [staticmethod] watch: decorator for timer a function, args as same as Timer
    Log format:
        inner function:
        WARNING 2018-02-12 00:02:52 torequests.utils: Finish test(a=1, b=2, c=4) cost 00:00:01, started at 2018-02-12 00:02:51.
        function decorator:
        WARNING 2018-02-12 00:02:52 torequests.utils: Finish test(1, 2, c=4) cost 00:00:01, started at 2018-02-12 00:02:51.
        global:
        WARNING 2018-02-12 00:02:52 torequests.utils: Finish <module>: __main__ (e:\github\torequests\temp_code.py) cost 00:00:01, started at 2018-02-12 00:02:51.
    """

    def __init__(self,
                 name=None,
                 log_func=None,
                 default_timer=default_timer,
                 rounding=None,
                 readable=timepass,
                 log_after_del=True,
                 stack_level=1):
        self._log_after_del = False
        if not name:
            f_name = sys._getframe(stack_level).f_code.co_name
            f_local = sys._getframe(stack_level).f_locals
            if f_name != '<module>':
                f_vars = '(%s)' % ', '.join([
                    '%s=%s' % (i, repr(f_local[i]))
                    for i in sorted(f_local.keys())
                ]) if f_local else '()'

            else:
                f_vars = ": %s (%s)" % (f_local.get('__name__'),
                                        f_local.get('__file__'))
            name = '%s%s' % (f_name, f_vars)
        # for key in dir(sys._getframe(1)):
        # print(key, getattr(sys._getframe(1), key))
        self.name = name
        self.start_at = time.time()
        self.log_func = log_func
        self.timer = default_timer
        self.rounding = rounding
        self.readable = readable
        self.start_timer = self.timer()
        self._log_after_del = log_after_del

    @property
    def string(self):
        """
        only return the expect_string
        """
        return self.tick()

    @property
    def x(self):
        """
        call self.log_func(self) and return expect_string
        """
        passed_string = self.string
        if self.log_func:
            self.log_func(self)
        else:
            Config.utils_logger.warn(
                'Finish %(name)s cost %(passed)s, started at %(start)s.' %
                (dict(
                    name=self.name,
                    start=ttime(self.start_at),
                    passed=passed_string)))
        return passed_string

    @property
    def passed(self):
        """
        return the cost_seconds after start
        """
        return self.timer() - self.start_timer

    def tick(self):
        """
        return the time cost string as expect
        """
        string = self.passed
        if self.rounding:
            string = round(string)
        if self.readable:
            string = self.readable(string)
        return string

    @staticmethod
    def watch(*timer_args, **timer_kwargs):

        def wrapper(function):

            @wraps(function)
            def inner(*args, **kwargs):
                args1 = ', '.join(map(repr, args)) if args else ''
                kwargs1 = ', '.join([
                    '%s=%s' % (i, repr(kwargs[i]))
                    for i in sorted(kwargs.keys())
                ])
                arg = ', '.join(filter(None, [args1, kwargs1]))
                name = '%s(%s)' % (function.__name__, arg)
                _ = Timer(name=name, *timer_args, **timer_kwargs)
                result = function(*args, **kwargs)
                return result

            return inner

        return wrapper

    def __del__(self):
        if self._log_after_del:
            self.x
