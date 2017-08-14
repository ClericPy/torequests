#! coding:utf-8
# compatible for win32 / python 2 & 3
# TODO clean_url; frequency_tester; frequency_checker; string_converter;
# regex_mappers
import argparse
import hashlib
import json
import re
import shlex
import sys
import time

from requests.compat import (quote, quote_plus, unquote, unquote_plus, urljoin,
                             urlparse, urlsplit, urlunparse)

PY2 = (sys.version_info[0] == 2)
PY3 = (sys.version_info[0] == 3)

if PY2:
    from cgi import escape
    import HTMLParser
    unescape = HTMLParser.HTMLParser().unescape
else:
    from html import escape, unescape


class Config(object):
    TIMEZONE = 8


class Curl(object):
    parser = argparse.ArgumentParser()
    parser.add_argument('curl')
    parser.add_argument('url')
    parser.add_argument('-I', '--head', action='store_true')
    parser.add_argument('-X', '--method', default='get')
    parser.add_argument('-A', '--user-agent')
    parser.add_argument('-u', '--user')  # <user[:password]>
    parser.add_argument('-x', '--proxy')  # proxy.com:port
    parser.add_argument('-d', '--data')
    parser.add_argument('--data-binary')
    parser.add_argument('--connect-timeout', type=float)
    parser.add_argument('-H', '--header', action='append',
                        default=[])  # key: value
    parser.add_argument('--compressed', action='store_true')

    @staticmethod
    def parse(cmd, encode='utf-8'):
        '''requests.request(**Curl.parse(curl_bash));
         curl_bash sometimes should use r'...' '''
        assert '\n' not in cmd, 'curl_bash should not contain \\n, try r"...".'
        args = Curl.parser.parse_args(shlex.split(cmd.strip()))
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
        if args.head:
            args.method = 'head'
        if args.user:
            requests_args['auth'] = tuple(
                u for u in args.user.split(':', 1) + [''])[:2]
        # if args.proxy:
            # pass
        data = args.data or args.data_binary
        if data:
            args.method = 'post'
            if headers.get('c') == 'tpplication/x-www-form-urlencoded':
                data = dict([(i.split('=')[0], unquote_plus(i.split('=')[1]))
                             for i in data.split('&')])
                requests_args['data'] = data
            elif headers.get('content-type', '') in ('application/json',):
                requests_args['json'] = json.loads(data)
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

def md5(string, n=32, encoding='utf-8'):
    if n == 32:
        return hashlib.md5(str(string).encode(encoding)).hexdigest()
    if n == 16:
        return hashlib.md5(str(string).encode(encoding)).hexdigest()[8:-8]
    if isinstance(n, (tuple, list)):
        return hashlib.md5(str(string).encode(encoding)).hexdigest()[n[0]:n[1]]


class Counts(object):
    __slots__ = ('start', 'step', 'current')

    def __init__(self, start=0, step=1):
        self.start = start
        self.step = step
        self.current = start

    @property
    def x(self):
        self.current += self.step
        return self.current

    @property
    def c(self):
        return self.x
