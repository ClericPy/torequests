#! coding:utf-8

import json
import re
from types import GeneratorType

from .versions import PY2

if not PY2:
    unicode = str

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
        pip install lxml cssselect jsonpath_rw_ext objectpath
        lxml for xml
        cssselect for html
        jsonpath_rw_ext for jsonpath
        objectpath for objectpath

    Usage or test::

        parser = SimpleParser()

        scode = parser
        result = parser.parse(scode, [['1-1', 'py', 'alias']])
        assert isinstance(result, dict), 'test py parser fail.'

        scode = u'{"items": [{"title": "a"}, {"title": "b"}, {"title": "中文"}]}'
        result = parser.parse(
            scode, [['1-n', 'json', '$.items[*]'], ['n-n', 'json', '$.title']])
        assert result == ['a', 'b', u'中文'], 'test json fail.'

        scode = u'{"a": "1", "items": [{"title": "b"}, {"title": "b"}, {"title": "中文"}]}'
        result = parser.parse(
            scode,
            [['1-n', 'object', '$.items[@.title is b]'], ['n-n', 'object', '$.*']])
        assert result == [{'title': 'b'}, {'title': 'b'}], 'test object fail.'

        scode = '<p> hello world </p>'
        result = parser.parse(scode, [['1-n', 're', '<(.*?)>', '@<\\1art>']])
        assert result == ['<part> hello world </part>'], 'test re.sub fail.'
        result = parser.parse(scode, [['1-n', 're', '<(.*?)>', '$1']])
        assert result == ['p', '/p'], 'test re.finditer fail.'

        scode = u'''<?xml version='1.0' encoding='utf-8'?>
        <slideshow
            title="Sample Slide Show"
            date="Date of publication"
            author="Yours Truly"
            >
            <!-- TITLE SLIDE -->
            <slide type="all">
            <title>Wake up to WonderWidgets!</title>
            </slide>

            <!-- OVERVIEW -->
            <slide type="all">
                <title>中文</title>
                <item>Why <em>WonderWidgets</em> are great</item>
                <item/>
                <item>Who <em>buys</em> WonderWidgets</item>
            </slide>

        </slideshow>'''.encode('u8')
        result = parser.parse(scode, [['1-n', 'xml', '//slide', 'xml'],
                                      ['n-n', 'xml', '/slide/title', 'text']])
        assert result == [u'Wake up to WonderWidgets!', u'中文'], 'test xml fail.'

        scode = u'<div><p class="test" >Hello<br>world</p><p>Your<br>world</p>TAIL<p class>Hello<br>world中文!</p>TAIL</div>'
        result = parser.parse(
            scode, [['1-n', 'html', 'p', 'html'], ['n-n', 'html', 'p', 'text']])
        assert result == [u'Helloworld', 'Yourworld',
                          u'Helloworld中文!'], 'test html fail.'
        result = parser.parse(scode, [['1-n', 'html', 'p', '@class']])
        assert result == ['test', None, ''], 'test html fail.'
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
    parser_name_to_lib_name = {'html': 'lxml', 'xml': 'lxml'}

    def __init__(self, encoding='utf-8', *args, **kwargs):
        self._encoding = encoding
        self._json = json
        self._re = re
        self._python_ready = True
        self._re_ready = True
        self._lxml_ready = False
        self._jsonpath_ready = False
        self._objectpath_ready = False

    def _choose_parser(self, name):
        name = self.alias.get(name, name)
        func_name = '%s_parser' % name
        if not hasattr(self, func_name):
            raise ValueError('BadParser name %s' % name)
        self._ensure_lib_ready(name)
        return getattr(self, func_name)

    def _ensure_lib_ready(self, parser_name):
        lib_name = self.parser_name_to_lib_name.get(parser_name, parser_name)
        if not getattr(self, '_%s_ready' % lib_name):
            # lazy import libs which are not ready, for performance...
            getattr(self, '_init_%s_lib' % lib_name)()

    def _init_lxml_lib(self):
        from lxml.html import HTMLParser, XHTMLParser, fromstring, tostring
        self._html_parser = HTMLParser()
        self._xml_parser = XHTMLParser()
        self._tostring = tostring
        self._fromstring = fromstring
        self._lxml_ready = True

    def _init_jsonpath_lib(self):
        from jsonpath_rw_ext import parse as jp_parser
        self._jsonpath_parser = jp_parser
        self._jsonpath_ready = True

    def _init_objectpath_lib(self):
        from objectpath import Tree
        self._objectpath_parser = Tree
        self._objectpath_ready = True

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
            r'^@|^\$\d+', args[1]), ValueError(r'args1 should match ^@|^\$\d+')
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
            self._fromstring(scode,
                             parser=self._html_parser).cssselect(css_path))
        if method.startswith('@'):
            result = [item.get(method[1:]) for item in result]
        else:
            result = [
                self._tostring(
                    item, method=method, with_tail=0, encoding='unicode')
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
            self._fromstring(scode,
                             parser=self._xml_parser).xpath(xpath_string))
        result = [
            self._tostring(
                item, method=method, with_tail=0, encoding='unicode')
            for item in result
        ]
        return result

    def jsonpath_parser(self, scode, jsonpath):
        scode = self.ensure_json(scode)
        # normalize jsonpath
        jsonpath = self._re.sub(
            r'\.$', '', self._re.sub(r'^JSON\.?|^\$?\.?', '$.', jsonpath))
        jp = self._jsonpath_parser(jsonpath)
        return [i.value for i in jp.find(scode)]

    def objectpath_parser(self, scode, objectpath):
        scode = self.ensure_json(scode)
        tree = self._objectpath_parser(scode)
        result = tree.execute(objectpath)
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
