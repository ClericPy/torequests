#! coding:utf-8
# compatible for win32 / python 2 & 3
# TODO clean_url; frequency_tester; frequency_checker; string_converter;
# regex_mappers
import argparse
import json
import logging
import re
import shlex

from requests.compat import (OrderedDict, cookielib, quote, quote_plus,
                             unquote, unquote_plus, urlparse, urlunparse)

dummy_logger = logging.getLogger('torequests.dummy')
main_logger = logging.getLogger('torequests.main')


def init_logger(name='', handler_path_levels=None,
                level=logging.INFO, formatter=None,
                formatter_str=None, datefmt="%Y-%m-%d %H:%M:%S"):
    '''Args:
    name = '' or logger obj.
    handler_path_levels = [['loggerfile.log',13],['','DEBUG'],['','info'],['','notSet']] # [[path,level]]
    level : the least level for the logger.
    formatter = logging.Formatter(
            '%(levelname)-6s  %(asctime)s  %(name)s (%(filename)s: %(lineno)s): %(message)s',
             "%Y-%m-%d %H:%M:%S")
    formatter_str = '%(levelname)-6s  %(asctime)s  %(name)s (%(funcName)s: %(lineno)s): %(message)s'

    custom formatter:
        %(asctime)s  %(created)f  %(filename)s  %(funcName)s  %(levelname)s  %(levelno)s  %(lineno)s   %(message)s   %(module)s    %(name)s   %(pathname)s   %(process)s   %(relativeCreated)s   %(thread)s  %(threadName)s  
    '''
    levels = {'NOTSET': logging.NOTSET, 'DEBUG': logging.DEBUG, 'INFO': logging.INFO,
              'WARNING': logging.WARNING, 'ERROR': logging.ERROR, 'CRITICAL': logging.CRITICAL}
    if not formatter:
        if formatter_str:
            formatter_str = formatter_str
        else:
            formatter_str = '%(levelname)-6s  %(asctime)s  %(name)s (%(filename)s: %(lineno)s): %(message)s'
        formatter = logging.Formatter(formatter_str, datefmt=datefmt)
    logger = name if isinstance(
        name, logging.Logger) else logging.getLogger(str(name))
    logger.setLevel(level)
    handler_path_levels = handler_path_levels or [['', 'INFO']]
    # ---------------------------------------
    for each_handler in handler_path_levels:
        path, handler_level = each_handler
        handler = logging.FileHandler(
            path) if path else logging.StreamHandler()
        handler.setLevel(levels.get(handler_level.upper(), 1) if isinstance(
            handler_level, str) else handler_level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


class FailureException(Exception):
    '''This class mainly used for __bool__, 
        self.error for reviewing the source exception.'''

    def __init__(self, error):
        self.__dict__ = error.__dict__
        self.error = error
        self.ok = False

    def __bool__(self):
        return False

    def __str__(self):
        return repr(self)


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
        '''requests.request(**Curl.parse(curl_bash))'''
        args = Curl.parser.parse_args(shlex.split(cmd.strip()))
        requests_args = {}
        headers = {}
        requests_args['url'] = args.url
        for header in args.header:
            key, value = header.split(":", 1)
            headers[key] = value.strip()
        if args.user_agent:
            headers['User-Agent'] = args.user_agent
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
            if headers.get('Content-Type') == 'application/x-www-form-urlencoded':
                data = dict([(i.split('=')[0], unquote_plus(i.split('=')[1]))
                             for i in data.split('&')])
                requests_args['data'] = data
            elif headers.get('Content-Type') in ('application/json'):
                requests_args['json'] = json.loads(data)
            else:
                data = data.encode(encode)
                requests_args['data'] = data
        requests_args['method'] = args.method.lower()
        return requests_args


curlparse = Curl.parse


class String(object):
    '''Tool kits for string converter'''
    pass


class Time(object):
    '''Tool kits for time converter'''
    pass


class Frequency(object):
    '''guess the anti-crawling frequency'''
    pass


class RegexMapper(object):
    '''dict-like for regex mapper: input string, output obj.
    support persistence rules;
    flags: set multi flags combined with '|', FLAG1 | FLAG2 | FLAG3
    '''

    def __init__(self, name=None, file_path=None, match_mode='search', flags=None):
        # init regex from string to compiled regex
        self.match_mode = match_mode
        self.rules = []  # list of (str, obj)
        self.rules_compile = []
        pass

    def init_regex(self):
        pass

    def get(self, string, default=None):
        'return only one matching obj'
        return self.find(string, default)

    def find(self, string, default=None):
        'return only one matching obj'
        pass

    def findall(self, string):
        'return all matching obj'
        pass

    def regex_walker(self):
        'return generator'
        pass

    def save(self, file_path):
        pass

    def load(self, file_path):
        pass

    def __getitem__(self, key):
        pass

    def __setitem__(self, key, value):
        pass
