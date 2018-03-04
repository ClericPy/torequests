#! coding:utf-8
import time
from torequests.utils import *
from torequests.parsers import *
import requests

# with capsys.disabled():


def test_curlparse_get():
    """  test_dummy_utils """
    cmd = """curl 'http://httpbin.org/get?test1=1&test2=2' -H 'Pragma: no-cache' -H 'DNT: 1' -H 'Accept-Encoding: gzip, deflate' -H 'Accept-Language: zh-CN,zh;q=0.8' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Cache-Control: no-cache' -H 'Connection: keep-alive' --compressed"""
    args = curlparse(cmd)
    resp = requests.request(**args)
    rj = resp.json()
    assert rj['url'] == 'http://httpbin.org/get?test1=1&test2=2' and rj['args']['test1'] == '1', 'test fail: curlparse get'


def test_curlparse_post():
    """  test_dummy_utils """
    cmd = """curl 'http://httpbin.org/post' -H 'Pragma: no-cache' -H 'Origin: null' -H 'Accept-Encoding: gzip, deflate' -H 'Accept-Language: zh-CN,zh;q=0.8' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36' -H 'Content-Type: application/x-www-form-urlencoded' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Cache-Control: no-cache' -H 'Connection: keep-alive' -H 'DNT: 1' --data 'test1=%E6%B5%8B%E8%AF%95&test2=%E4%B8%AD%E6%96%87' --compressed"""
    args = curlparse(cmd)
    resp = requests.request(**args)
    rj = resp.json()
    assert rj['form']['test1'] == u'测试', 'test fail: curlparse post & urlencode'


def test_slice_by_size():
    assert list(slice_by_size(range(10),
                              6)) == [(0, 1, 2, 3, 4, 5),
                                      (6, 7, 8, 9)], 'test fail: slice_by_size'


def test_slice_into_pieces():
    assert list(slice_into_pieces(
        range(10), 3)) == [(0, 1, 2, 3), (4, 5, 6, 7),
                           (8, 9)], 'test fail: slice_into_pieces'


def test_ttime_ptime():
    assert time.time() - ptime(
        ttime(tzone=0), tzone=0) < 2, 'fail: ttime / ptime'


def test_timeago():
    assert timeago(
        93245732.0032424, 5) == '1079 days, 05:35:32,003' and timeago(
            93245732.0032424, 4, 1) == '1079 days 5 hours 35 minutes 32 seconds'


def test_escape_unescape():
    assert escape('<>') == '&lt;&gt;' and unescape(
        '&lt;&gt;') == '<>', 'fail: escape'


def test_counts():
    c = Counts()
    [c.x for i in range(10)]
    assert c.c == 11, 'fail: test_counts'


def test_unique():
    assert list(
        unique(list(range(4, 0, -1)) + list(range(5)))) == [4, 3, 2, 1, 0]


def test_regex():
    reg = Regex()

    @reg.register_function('http.*cctv.*')
    def mock():
        pass

    reg.register('http.*HELLOWORLD', 'helloworld', flags=re.I)
    reg.register('http.*HELLOWORLD2', 'helloworld2', flags=re.I)

    assert (reg.search('http://cctv.com'))
    assert (reg.match('http://helloworld') == ['helloworld'])
    assert (reg.match('non-http://helloworld') == [])
    assert (reg.search('non-http://helloworld') == ['helloworld'])
    assert (len(reg.search('non-http://helloworld2')) == 2)


def test_clean_request():
    from torequests.crawlers import CleanRequest
    request = (
        """curl 'https://p.3.cn/prices/mgets?skuIds=J_1273600&nonsense=1&nonce=0' -H 'Pragma: no-cache' -H 'DNT: 1' -H 'Accept-Encoding: gzip, deflate' -H 'Accept-Language: zh-CN,zh;q=0.9' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Cache-Control: no-cache' -H 'Referer: https://p.3.cn/prices/mgets?skuIds=J_1273600&nonsense=1&nonce=0' -H 'Cookie: ASPSESSIONIDSQRRSADB=MLHDPOPCAMBDGPFGBEEJKLAF' -H 'Connection: keep-alive' --compressed"""
    )

    c = CleanRequest(request)
    assert (c.x == {
        'url': 'https://p.3.cn/prices/mgets?skuIds=J_1273600',
        'method': 'get'
    })


def test_failure():
    from torequests.exceptions import FailureException
    assert bool(FailureException(BaseException())) is False


def test_parsers():
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


def test_try_import():
    assert try_import('re')
    assert try_import('re', 'findall')
    assert not try_import('fake_re')
    assert not try_import('fake_re', 'findall')


def test_ensure_request():
    assert (ensure_request({
        'method': 'get',
        'url': 'http://github.com'
    }) == {
        'method': 'get',
        'url': 'http://github.com'
    })
    assert (ensure_request('http://github.com') == {
        'method': 'get',
        'url': 'http://github.com'
    })
    assert (ensure_request(
        '''curl 'https://github.com/' -H 'Pragma: no-cache' -H 'Accept-Encoding: gzip, deflate, br' -H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Cache-Control: no-cache' -H 'Cookie: logged_in=no; ' -H 'Connection: keep-alive' --compressed'''
    ) == {
        'url': 'https://github.com/',
        'headers': {
            'Pragma':
            'no-cache',
            'Accept-Encoding':
            'gzip, deflate, br',
            'Accept-Language':
            'zh-CN,zh;q=0.9,en;q=0.8',
            'Upgrade-Insecure-Requests':
            '1',
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
            'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Cache-Control':
            'no-cache',
            'Cookie':
            'logged_in=no;',
            'Connection':
            'keep-alive'
        },
        'method': 'get'
    })
