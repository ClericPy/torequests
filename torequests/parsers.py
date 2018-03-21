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
Tree = try_import('objectpath', 'Tree')

__all__ = ['SimpleParser']


def get_one(seq, default=None, skip_string_iter=True):
    """
    Return one item from seq or None(by default).
    """
    if skip_string_iter and isinstance(seq, (str, unicode, bytes, bytearray)):
        return seq
    if not seq:
        return ''
    try:
        return next(iter(seq))
    except TypeError:
        # not hasattr __iter__/__getitem__
        return default


class SimpleParser(object):
    """
        pip install lxml cssselect jsonpath_rw_ext objectpath;
    """
    alias = {
        'py': 'python',
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

    def __init__(self,
                 encoding=None,
                 json_parser=None,
                 regex_parser=None,
                 html_parser=None,
                 xml_parser=None):
        self._encoding = encoding or 'utf-8'
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

    @classmethod
    def prepare_response(cls, r, name, encoding=None):
        name = cls.alias.get(name, name)
        if not r or isinstance(r, unicode) or name == 'python':
            return r
        elif name in ('html', 're'):
            return r.content.decode(encoding) if encoding else r.text
        elif name in ('jsonpath', 'objectpath'):
            return r.content
        elif name == 'xml':
            return r.content
        return r

    @staticmethod
    def ensure_list(obj):
        """
        null obj -> return []; 

        str, unicode, bytes, bytearray -> [obj];

        else -> list(obj)
        """
        if not obj:
            return []
        elif isinstance(obj, (str, unicode, bytes, bytearray)):
            return [obj]
        elif hasattr(obj, '__iter__') or hasattr(obj, '__getitem__'):
            return list(obj)
        else:
            return [obj]

    def ensure_json(self, obj):
        if isinstance(obj, (str, unicode, bytes, bytearray)):
            return self._json.loads(obj, encoding=self._encoding)
        return obj

    def ensure_str(self, obj):
        if isinstance(obj, bytes):
            return obj.decode(self._encoding)
        return obj

    def python_parser(self, obj, *args):
        """operate a python obj"""
        attr, args = args[0], args[1:]
        item = getattr(obj, attr)
        if callable(item):
            item = item(*args)
        return [item]

    def re_parser(self, scode, *args):
        """
        args: [arg1, arg2]

        arg[0] = a valid regex pattern

        arg[1] : if startswith('@') call sub; if startswith('$') call finditer,
                 $0, $1 means group index.

        return an ensure_list
        """

        def gen_match(matches, num):
            for match in matches:
                yield match.group(num)

        scode = self.ensure_str(scode)
        assert self._re.match(
            '^@|^\$\d+', args[1]), ValueError('args1 should match ^@|^\$\d+')
        arg1, arg2 = args[1][0], args[1][1:]
        com = self._re.compile(args[0])
        if arg1 == '@':
            result = com.sub(arg2, scode)
            return self.ensure_list(result)
        else:
            result = com.finditer(scode)
            return gen_match(result, int(arg2))

    def html_parser(self, scode, *args):
        """
        args[0] = cssselector

        args[1] = text / html / xml / @attribute_name
        """
        allow_method = ('text', 'html', 'xml')
        css_path, method = args
        assert method in allow_method or method.startswith(
            '@'), 'method allow: %s or @attr' % allow_method
        result = self.ensure_list(
            fromstring(scode, parser=self._html_parser).cssselect(css_path))
        if method.startswith('@'):
            result = [item.get(method[1:]) for item in result]
        else:
            result = [
                tostring(item, method=method, with_tail=0, encoding='unicode')
                for item in result
            ]
        return result

    def xml_parser(self, scode, *args):
        """
        args[0]: xpath

        args[1]: text / html / xml
        """
        allow_method = ('text', 'html', 'xml')
        xpath_string, method = args
        assert method in allow_method, 'method allow: %s' % allow_method
        result = self.ensure_list(
            fromstring(scode, parser=self._xml_parser).xpath(xpath_string))
        result = [
            tostring(item, method=method, with_tail=0, encoding='unicode')
            for item in result
        ]
        return result

    def jsonpath_parser(self, scode, json_path):
        scode = self.ensure_json(scode)
        # normalize json_path
        json_path = self._re.sub('\.$', '',
                                 self._re.sub('^JSON\.?|^\$?\.?', '$.',
                                              json_path))
        jp = JP(json_path)
        return [i.value for i in jp.find(scode)]

    def objectpath_parser(self, scode, object_path):
        scode = self.ensure_json(scode)
        tree = Tree(scode)
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
        assert args_chain and isinstance(
            args_chain, (list, tuple)
        ) and isinstance(args_chain[0], (list, tuple)), ValueError(
            'args_chain type should be list of list, like: [["1-n", "html", "p", "html"], ["n-n", "html", "p", "text"]].'
        )
        for arg in args_chain:
            # py2 not support * unpack
            one_to_many, parser_name, parse_args = (arg[0], arg[1], arg[2:])
            assert self._re.match(
                '^[1n]-[1n]$',
                one_to_many), 'one_to_many should be one of 1-1, 1-n, n-n, n-1'
            input_count, output_count = one_to_many.split('-')
            parser = self._choose_parser(parser_name)
            # input data to parse.
            if input_count == 'n':
                scode = list(map(lambda item: parser(item, *parse_args), scode))
            if input_count == '1':
                if parser not in (self.jsonpath_parser, self.objectpath_parser,
                                  self.python_parser):
                    # json may remain multi-items
                    scode = get_one(scode, default=default)
                scode = parser(scode, *parse_args)
            # ensure result match n or 1 after parsing.
            if parser in (self.objectpath_parser,):
                # objectpath not need
                continue
            if output_count == '1':
                # 1-1 or n-1
                scode = get_one(scode, default=default)
            elif input_count == 'n':
                # n-n
                scode = [get_one(i, default=default) for i in scode]
            else:
                # 1-n
                scode = list(scode)
        if join_with:
            scode = join_with.join(map(str, scode))
        return scode
