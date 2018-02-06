#! coding:utf-8

import json
import re
from types import GeneratorType

from .utils import try_import
from .versions import PY2

if not PY2:
    unicode = str

JP = try_import('jsonpath_rw_ext', 'parse')
HTMLParser, XHTMLParser, fromstring, tostring = try_import(
    'lxml.html', ['HTMLParser', 'XHTMLParser', 'fromstring', 'tostring'])
OTree = try_import('objectpath', 'Tree')


def get_one(seq, default=None, skip_string_iter=True):
    """
    Return one item from seq or None(by default).
    """
    if skip_string_iter and isinstance(seq, (str, unicode, bytes, bytearray)):
        return seq
    return next(iter(seq)) if seq and hasattr(seq, '__iter__') else default


class SimpleParser(object):
    """
        pip install lxml cssselect jsonpath_rw_ext objectpath
    """
    alias = {
        'jp': 'jsonpath',
        'json': 'jsonpath',
        'json_path': 'jsonpath',
        'op': 'objectpath',
        'object': 'objectpath',
        'object_path': 'objectpath',
        'reg': 're',
        'regex': 're',
        'css': 'html',
        'cssselect': 'html',
        'cssselector': 'html',
    }

    def __init__(self, encoding='utf-8', json_parser=None, regex_parser=None,
                 html_parser=None, xml_parser=None):
        self._encoding = encoding
        self._json = json_parser or json
        self._re = regex_parser or re
        self._html_parser = html_parser or HTMLParser()
        self._xml_parser = xml_parser or XHTMLParser()

    def _choose_parser(self, name):
        name = self.alias.get(name, name)
        func_name = '%s_parser' % name
        if not hasattr(self, func_name):
            raise ValueError('BadParser name %s' % name)
        return getattr(self, func_name)

    def ensure_list(self, obj):
        if not obj:
            return []
        elif isinstance(obj, (str, unicode, bytes, bytearray)):
            return [obj]
        else:
            return list(obj)

    def re_parser(self, scode, *args):
        result = getattr(self._re, args[0])(*(list(args[1:]) + [scode]))
        return self.ensure_list(result)

    def html_parser(self, scode, *args):
        """
        args[0]: cssselector for the element
        args[1]: text / html / xml
        """
        allow_method = ('text', 'html', 'xml')
        css, method = args
        assert method in allow_method, 'method allow: %s' % allow_method
        result = self.ensure_list(fromstring(
            scode, parser=self._html_parser).cssselect(css))
        result = [tostring(item, method=method, with_tail=0,
                           encoding='unicode') for item in result]
        return result

    def xml_parser(self, scode, *args):
        """
        args[0]: cssselector for the element
        args[1]: text / html / xml
        """
        allow_method = ('text', 'html', 'xml')
        xpath_string, method = args
        assert method in allow_method, 'method allow: %s' % allow_method
        result = self.ensure_list(fromstring(
            scode, parser=self._xml_parser).xpath(xpath_string))
        result = [tostring(item, method=method, with_tail=0,
                           encoding='unicode') for item in result]
        return result

    def ensure_json(self, obj):
        if isinstance(obj, (str, unicode, bytes, bytearray)):
            return self._json.loads(obj, encoding=self._encoding)
        return obj

    def jsonpath_parser(self, scode, json_path):
        scode = self.ensure_json(scode)
        # normalize json_path
        json_path = self._re.sub('\.$', '', self._re.sub(
            '^JSON\.?|^\$?\.?', '$.', json_path))
        jp = JP(json_path)
        return [i.value for i in jp.find(scode)]

    def objectpath_parser(self, scode, object_path):
        scode = self.ensure_json(scode)
        tree = OTree(scode)
        result = tree.execute(object_path)
        if isinstance(result, GeneratorType):
            result = list(result)
        return result

    def const_parser(self, scode, *args):
        return args[0] if args else scode

    def parse(self, scode, args_chain=None, join_with=None, default=''):
        """
        single arg:
            [one_to_many, parser_name, *args]
        args_chain: 
            [['1-n', 're', 'search', '(<.*?>)', '\\1']]
            [['1-n', 'html', 'p', 'html'], ['n-n', 'html', 'p', 'text']]
        """
        for arg in args_chain:
            # py2 not support * unpack
            one_to_many, parser_name, parse_args = (arg[0], arg[1], arg[2:])
            assert self._re.match(
                '^[1n]-[1n]$',
                one_to_many), 'one_to_many should be one of 1-1, 1-n, n-n, n-1'
            inputs, outputs = one_to_many.split('-')
            parser = self._choose_parser(parser_name)
            # set by in_puts
            if inputs == 'n':
                scode = list(
                    map(lambda item: parser(item, *parse_args), scode))
            elif inputs == '1':
                if parser in (self.jsonpath_parser, self.objectpath_parser):
                    scode = parser(scode, *parse_args)
                else:
                    scode = parser(
                        get_one(scode, default=default), *parse_args)
            # get out_puts
            if parser == self.objectpath_parser:
                print('ignore')
                continue

            if outputs == '1':
                # 1-1 or n-1
                scode = get_one(scode, default=default)
            elif inputs == 'n':
                # n-n
                scode = [get_one(i, default=default) for i in scode]
            else:
                # 1-n
                scode = list(scode)
        if join_with:
            scode = join_with.join(map(str, scode))
        return scode
