#! coding:utf-8
# compatible for win32 / python 2 & 3
import argparse
import hashlib
import re
import shlex
import time

from .versions import PY2, PY3, PY35_PLUS


if PY2:
    from urllib import quote, quote_plus, unquote_plus
    from urlparse import parse_qs, urlparse, unquote, urljoin, urlsplit, urlunparse
    from cgi import escape
    import HTMLParser
    unescape = HTMLParser.HTMLParser().unescape

if PY3:
    from urllib.parse import parse_qs, urlparse, quote, quote_plus, unquote, unquote_plus, urljoin, urlsplit, urlunparse
    from html import escape, unescape


class Config:
    TIMEZONE = 8


def simple_cmd():
    parser = argparse.ArgumentParser(
        prog='Simple command-line function toolkit.',
        description='''Input function name and args and kwargs.
        python xxx.py main -a 1 2 3 -k a=1,b=2,c=3''')
    parser.add_argument('-f', '--func_name', default='main')
    parser.add_argument('-a', '--args', dest='args', nargs='*')
    parser.add_argument('-k', '--kwargs', dest='kwargs')
    parser.add_argument('-i', '-s', '--info', '--show',
                        '--status', dest='show', action='store_true',
                        help='show the args, kwargs and function\'s source code.')
    params = parser.parse_args()
    func_name = params.func_name
    func = globals().get(func_name)
    if not (callable(func)):
        print('invalid func_name: %s' % func_name)
        return
    args = params.args or []
    kwargs = params.kwargs or {}
    if kwargs:
        import re
        items = [re.split('[:=]', i) for i in re.split('[,;]+', kwargs)]
        kwargs = dict(items)
    if params.show:
        from inspect import getsource
        print('args: %s; kwargs: %s' % (args, kwargs))
        print(getsource(func))
        return
    func(*args, **kwargs)


class Curl(object):

    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('curl')
        self.parser.add_argument('url')
        self.parser.add_argument('-X', '--method', default='get')
        self.parser.add_argument('-A', '--user-agent')
        self.parser.add_argument('-u', '--user')  # <user[:password]>
        self.parser.add_argument('-x', '--proxy')  # proxy.com:port
        self.parser.add_argument('-d', '--data')
        self.parser.add_argument('--data-binary')
        self.parser.add_argument('--connect-timeout', type=float)
        self.parser.add_argument('-H', '--header', action='append',
                                 default=[])  # key: value
        self.parser.add_argument('--compressed', action='store_true')

    def parse(self, cmd, encode='utf-8'):
        '''requests.request(**Curl.parse(curl_bash));
         curl_bash sometimes should use r'...' '''
        assert '\n' not in cmd, 'curl_bash should not contain \\n, try r"...".'
        args, unknown = self.parser.parse_known_args(shlex.split(cmd.strip()))
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
            if headers.get('content-type') == 'tpplication/x-www-form-urlencoded':
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


curlparse = Curl().parse


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
    '''From itertools import chain.'''
    for it in iterables:
        for element in it:
            yield element


def slice_into_pieces(seq, n):
    '''return a generation of pieces'''
    length = len(seq)
    if length % n == 0:
        size = length // n
    else:
        size = length // n + 1
    for it in slice_by_size(seq, size):
        yield it


def slice_by_size(seq, size):
    '''return as a generation of chunks'''
    filling = null
    for it in zip(*(itertools_chain(seq, [filling] * size),) * size):
        if filling in it:
            it = tuple(i for i in it if i is not filling)
        if it:
            yield it


def ttime(timestamp=None, tzone=None, fail='', fmt='%Y-%m-%d %H:%M:%S'):
    '''
    %z not work.
    Translate timestamp into human readable: %Y-%m-%d %H:%M:%S.
    tzone: time compensation, by "+ time.timezone + tzone * 3600";
           eastern eight(+8) time zone by default(can be set with Config.TIMEZONE).
    fail: while raise an exception, return fail arg.
    # example:
    print(ttime())
    print(ttime(1486572818.4218583298472936253)) # 2017-02-09 00:53:38
    '''
    tzone = Config.TIMEZONE if tzone is None else tzone
    timestamp = timestamp if timestamp != None else time.time()
    timestamp = int(str(timestamp).split('.')[0][:10])
    try:
        timestamp = time.time() if timestamp is None else timestamp
        return time.strftime(fmt, time.localtime(timestamp + time.timezone + tzone * 3600))
    except:
        return fail


def ptime(timestr=None, tzone=None, fail=0, fmt='%Y-%m-%d %H:%M:%S'):
    '''
    %z not work.
    Translate time string like %Y-%m-%d %H:%M:%S into timestamp.
    tzone: time compensation, by " - time.timezone - tzone * 3600";
           eastern eight(+8) time zone by default(can be set with Config.TIMEZONE).
    '''
    tzone = Config.TIMEZONE if tzone is None else tzone
    timestr = timestr or ttime()
    try:
        return time.mktime(time.strptime(timestr, fmt)) - (time.timezone + tzone * 3600)
    except:
        return fail


def timeago(seconds=None):
    'convert seconds to human readable'
    mm, ss = divmod(seconds, 60)
    hh, mm = divmod(mm, 60)
    dd, hh = divmod(hh, 24)
    s = "%02d:%02d:%02d" % (hh, mm, ss)
    if dd:
        def plural(n):
            return n, abs(n) != 1 and "s" or ""
        s = ("%d day%s, " % plural(dd)) + s
    return s


# alias name
timepass = timeago


def md5(string, n=32, encoding='utf-8', skip_encode=False):
    str_func = unicode if PY2 else str
    todo = string if skip_encode else str_func(string).encode(encoding)
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


def _unique_with_index(seq):
    for x, item in enumerate(seq):
        if seq.index(item) == x:
            yield item
    return


def _unique_without_index(seq):
    temp = []  # set can not save non-hashable obj
    for item in seq:
        if item not in temp:
            yield item
            temp.append(item)
    return


def unique(seq, return_as=None):
    '''unique seq in order. return as generator, or list / set / str...'''
    generator = _unique_with_index(seq) if hasattr(
        seq, 'index') else _unique_without_index(seq)
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

class Regex(object):
    '''Input string, return a list of mapped obj'''

    def __init__(self, ensure_mapping=False):
        '''ensure_mapping: make sure one on one mapping, if False,
                           will return all mapped obj in a list.'''
        self.container = []
        self.ensure_mapping = ensure_mapping

    def register(self, patterns, obj=None, instance=None, **kwargs):
        patterns = patterns if isinstance(
            patterns, (list, tuple)) else [patterns]
        for pattern in patterns:
            pattern_compiled = re.compile(pattern, **kwargs)
            self.container.append((pattern_compiled, obj, instance))
            if self.ensure_mapping:
                self.check_instances()
            elif instance:
                assert self.search(instance) or self.match(instance), \
                    'instance %s not fit pattern %s' % (instance, pattern)

    def register_function(self, pattern, instance=None, **kwargs):
        '''instance of pattern can be set in function.__doc__'''
        def wrapper(function):
            self.register(pattern, function, instance=instance, **kwargs)
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

    def fuzzy(self, key, limit=3):
        instances = [i[2] for i in self.container if i[2]]
        if not instances:
            return
        from fuzzywuzzy import process
        maybe = process.extract(key, instances, limit=limit)
        return maybe

    def check_instances(self):
        for item in self.container:
            if item[2]:
                assert self.search(item[2]) or self.match(item[2]), \
                    'instance %s not fit pattern %s' % (
                        item[2], item[0].pattern)

    def show_all(self, as_string=True):
        '''python2 will not show flags'''
        result = []
        for item in self.container:
            key = str(item[0])[10:] if PY3 else item[0].pattern
            instance = item[2] or 'No instance'
            value = '%s "%s"' % (item[1].__name__, (item[1].__doc__ or '')) if callable(
                item[1]) else str(item[1])
            value = '%s %s' % (type(item[1]), value)
            result.append(' => '.join((instance, key, value)))
        return '\n'.join(result) if as_string else result
