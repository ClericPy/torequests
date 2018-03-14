#! coding:utf-8
# compatible for win32 / python 2 & 3
from __future__ import print_function

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
from functools import wraps
from timeit import default_timer

from .configs import Config
from .exceptions import ImportErrorModule
from .main import run_after_async, threads
from .versions import PY2, PY3
from .logs import print_info

if PY2:
    import repr as reprlib
    from urllib import quote, quote_plus, unquote_plus
    from urlparse import parse_qs, parse_qsl, urlparse, unquote, urljoin, urlsplit, urlunparse
    from cgi import escape
    import HTMLParser
    unescape = HTMLParser.HTMLParser().unescape

if PY3:
    import reprlib
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


def print_mem():
    try:
        import psutil
        print_info("total: %.2f(MB)" % (
            float(psutil.Process(os.getpid()).memory_info().vms) / 1024 / 1024))
    except ImportError:
        print_info('pip install psutil.')


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
            headers[key.title()] = value.strip()
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

    def __nonzero__(self):
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
    timestamp = timestamp if timestamp is not None else time.time()
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


def split_seconds(seconds):
    """divisor: 1, 24, 60, 60, 1000
    units: day, hour, minute, second, millisecond"""
    millisecond = seconds * 1000
    divisors = (1, 24, 60, 60, 1000)
    quotient, result = millisecond, []
    for divisor in divisors[::-1]:
        quotient, remainder = divmod(quotient, divisor)
        result.append(quotient) if divisor == 1 else result.append(remainder)
    return result[::-1]


def timeago(seconds=0, accuracy=4, format=0, lang='en'):
    """translate seconds into human-readable
    seconds: abs(seconds)
    accuracy: 4 by default (units[:accuracy]), determine the length of elements.
    format: index of [led, literal, dict]
    lang: cn or en
    units: day, hour, minute, second, millisecond"""
    assert format in [0, 1,
                      2], ValueError('format arg should be one of 0, 1, 2')
    negative = '-' if seconds < 0 else ''
    seconds = abs(seconds)
    if lang == 'en':
        units = ('day', 'hour', 'minute', 'second', 'millisecond')
    elif lang == 'cn':
        units = (u'天', u'小时', u'分钟', u'秒', u'毫秒')
    times = split_seconds(seconds)
    if format == 2:
        return dict(zip(units, times))

    day, hour, minute, second, millisecond = times

    if format == 0:
        day_str = "%d %s%s, " % (
            day, units[0], 's'
            if day > 1 and lang == 'en' else '') if day else ''
        mid_str = ':'.join(("%02d" % i for i in (hour, minute, second)))
        if accuracy > 4:
            mid_str += ',%03d' % millisecond
        return negative + day_str + mid_str
    elif format == 1:
        # find longest valid fields index (non-zero in front)
        valid_index = 0
        for x, i in enumerate(times):
            if i > 0:
                valid_index = x
                break
        result_str = [
            "%d %s%s" % (num, unit, 's' if num > 1 and lang == 'en' else '')
            for num, unit in zip(times, units)
        ][valid_index:][:accuracy]
        result_str = ' '.join(result_str)
        return negative + result_str


# alias name
timepass = timeago


def md5(string, n=32, encoding='utf-8', skip_encode=False):
    """
    obj -> str
    """
    todo = string if skip_encode else unicode(string).encode(encoding)
    if n == 32:
        return hashlib.md5(todo).hexdigest()
    elif isinstance(n, (int, float)):
        return hashlib.md5(todo).hexdigest()[(32 - n) // 2:(n - 32) // 2]
    elif isinstance(n, (tuple, list)):
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

    def add(self, num=None):
        self.current += num or self.step
        return self.current

    def sub(self, num=None):
        self.current -= num or self.step
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


def ensure_request(request):
    """used for requests.request / Requests.request with **ensure_request(request)
    request: dict or curl-string or url"""
    if isinstance(request, dict):
        result = request
    elif isinstance(request, (unicode, str)):
        request = request.strip()
        if request.startswith('http'):
            result = {'method': 'get', 'url': request}
        elif request.startswith('curl '):
            result = curlparse(request)
    else:
        raise ValueError('request should be dict or str.')
    assert 'method' in result, ValueError('no `method` in request.')
    result['method'] = result['method'].lower()
    return result


class Timer(object):
    """
    Usage:
        init Timer anywhere:
            such as head of function, or head of module
        ```python
        from torequests.utils import Timer, md5
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

        ```
        then it will show log after del it by gc.
    ```
    Args:
        name: be used in log
        log_func=print_info, or function like Config.utils_logger.info
        default_timer=default_timer -> timeit.default_timer
        rounding=None -> if setted, seconds will be round(xxx, rounding)
        readable=timepass: readable(cost_seconds) -> 00:00:01,234
    Attr:
        self.tick() -> return the expect time_cost_string
        self.string -> return self.tick()
        self.x -> return self.string, and output it
        self.passed -> return seconds passed after self.start
        [staticmethod] watch: decorator for timer a function, args as same as Timer
    ```
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
        self.start_at = time.time()
        uid = md5('%s%s' % (self.start_at, id(self)))
        if not name:
            f_name = sys._getframe(stack_level).f_code.co_name
            f_local = sys._getframe(stack_level).f_locals
            if f_name == '<module>':
                f_vars = ": %s (%s)" % (
                    f_local.get('__name__'),
                    os.path.split(f_local.get('__file__'))[-1])
                # f_vars = f_vars.replace(' __main__', '')
            else:
                f_vars = '(%s)' % ', '.join([
                    '%s=%s' % (i, repr(f_local[i]))
                    for i in sorted(f_local.keys())
                ]) if f_local else '()'
            if self not in f_local.values():
                # add self to name space for __del__ way.
                sys._getframe(stack_level).f_locals.update(**{uid: self})
            name = '%s%s' % (f_name, f_vars)
        self.name = name
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
        self._log_after_del = False
        passed_string = self.string
        if self.log_func:
            self.log_func(self)
        else:
            print_info('Timer [%(passed)s]: %(name)s, start at %(start)s.' %
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
            # not be called by self.x yet.
            self.x


def ensure_dict_key_title(dict_obj):
    if not all((isinstance(i, unicode) for i in dict_obj.keys())):
        return dict_obj
    return {key.title(): value for key, value in dict_obj.items()}


class ClipboardWatcher(object):
    """watch clipboard, run callback while changed"""

    def __init__(self, interval=0.5, callback=None):
        self.pyperclip = try_import('pyperclip')
        self.interval = interval
        self.callback = callback or self.default_callback
        self.temp = self.current

    def read(self):
        return self.pyperclip.paste()

    def write(self, text):
        return self.pyperclip.copy(text)

    @property
    def current(self):
        return self.read()

    def default_callback(self, text):
        # clean text
        text = text.replace('\r\n', '\n')
        print_info(text, flush=1)
        return text

    def watch(self, limit=None, timeout=None):
        return self.watch_async(limit, timeout).x

    @threads(1)
    def watch_async(self, limit=None, timeout=None):
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


class Saver(object):
    """
    Simple object persistent toolkit with pickle, if only you don't care the performance.
    """
    _instances = {}

    def __new__(cls, path=None, **pickle_args):
        # BORG
        path = path or cls._get_home_path()
        return cls._instances.setdefault(path, super(Saver, cls).__new__(cls))

    def __init__(self, path=None, **pickle_args):
        """
        path: if not set, will be ~/_saver.pickle. print(self._path) to show it.
        pickle's protocol < 3 for compatibility between python2/3, 
                use -1 for performance and some other optimizations.
        """
        super(Saver, self).__init__()
        super(Saver, self).__setattr__('_path', path or self._get_home_path())
        super(Saver, self).__setattr__('_pickle_args', pickle_args)
        super(Saver, self).__setattr__('_conflict_keys', set(dir(self)))
        super(Saver, self).__setattr__('_cache', self._load())

    @classmethod
    def _get_home_path(cls):
        home = os.path.expanduser('~')
        file_name = '_saver.pickle'
        path = os.path.join(home, file_name)
        return path

    def _save_obj(self, obj):
        with open(self._path, 'wb') as f:
            pickle.dump(obj, f, **self._pickle_args)
        return obj

    def _save(self):
        return self._save_obj(self._cache)

    def _load(self):
        if not os.path.isfile(self._path):
            self._save_obj({})
        with open(self._path, 'rb') as f:
            return pickle.load(f)

    def _set(self, key, value):
        assert isinstance(
            key, unicode
        ) and key not in self._conflict_keys and not key.startswith('__')
        self._cache[key] = value
        self._save()

    def _get(self, key, default=None):
        return self._cache.get(key, default)

    def __setattr__(self, key, value):
        self._set(key, value)

    def __getattr__(self, key):
        if key in self._conflict_keys:
            return object.__getattribute__(self, key)
        return self._get(key)

    def __contain__(self, key):
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
        return (os.remove(self._path))

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
        return result

    def __setitem__(self, key, value):
        self._set(key, value)

    def __delitem__(self, key):
        self._cache.pop(key, None)
        self._save()

    def __str__(self):
        return json.dumps(self._cache, ensure_ascii=0)

    def __repr__(self):
        return 'Saver(path="%s")%s' % (self._path, reprlib.repr(self._cache))
