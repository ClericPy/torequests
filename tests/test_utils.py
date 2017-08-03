#! coding:utf-8
import time
from torequests.utils import *
import requests

### with capsys.disabled():

def test_curlparse_get():
    '''  test_dummy_utils '''
    cmd = '''curl 'http://httpbin.org/get?test1=1&test2=2' -H 'Pragma: no-cache' -H 'DNT: 1' -H 'Accept-Encoding: gzip, deflate' -H 'Accept-Language: zh-CN,zh;q=0.8' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Cache-Control: no-cache' -H 'Connection: keep-alive' --compressed'''
    args = curlparse(cmd)
    resp = requests.request(**args)
    rj = resp.json()
    assert rj['url'] == 'http://httpbin.org/get?test1=1&test2=2' and rj['args']['test1'] == '1', 'test fail: curlparse get'


def test_curlparse_post():
    '''  test_dummy_utils '''
    cmd = '''curl 'http://httpbin.org/post' -H 'Pragma: no-cache' -H 'Origin: null' -H 'Accept-Encoding: gzip, deflate' -H 'Accept-Language: zh-CN,zh;q=0.8' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36' -H 'Content-Type: application/x-www-form-urlencoded' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Cache-Control: no-cache' -H 'Connection: keep-alive' -H 'DNT: 1' --data 'test1=%E6%B5%8B%E8%AF%95&test2=%E4%B8%AD%E6%96%87' --compressed'''
    args = curlparse(cmd)
    resp = requests.request(**args)
    rj = resp.json()
    assert rj['form']['test1'] == u'测试', 'test fail: curlparse post & urlencode'


def test_slice_by_size():
    assert list(slice_by_size(range(10), 6)) == [(0, 1, 2, 3, 4, 5), (6, 7, 8, 9)], 'test fail: slice_by_size'

def test_slice_into_pieces():
    assert list(slice_into_pieces(range(10),3))==[(0, 1, 2, 3), (4, 5, 6, 7), (8, 9)], 'test fail: slice_into_pieces'

def test_ttime_ptime():
    assert time.time() - ptime(ttime(tzone=0),tzone=0) < 2, 'fail: ttime / ptime'

def test_escape_unescape():
    assert escape('<>')=='&lt;&gt;' and unescape('&lt;&gt;')=='<>', 'fail: escape'