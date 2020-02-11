#! coding:utf-8
import re
import time

import requests
from torequests.utils import *

# with capsys.disabled():


def test_curlparse_get():
    """  test_dummy_utils """
    cmd = """curl 'http://httpbin.org/get?test1=1&test2=2' -H 'Pragma: no-cache' -H 'DNT: 1' -H 'Accept-Encoding: gzip, deflate' -H 'Accept-Language: zh-CN,zh;q=0.8' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Cache-Control: no-cache' -H 'Connection: keep-alive' --compressed"""
    args = curlparse(cmd)
    resp = requests.request(**args)
    rj = resp.json()
    assert ('httpbin.org/get?test1=1&test2=2' in rj["url"] and
            rj["args"]["test1"] == "1"), "test fail: curlparse get"


def test_curlparse_post():
    """  test_dummy_utils """
    cmd = """curl 'http://httpbin.org/post' -H 'Pragma: no-cache' -H 'Origin: null' -H 'Accept-Encoding: gzip, deflate' -H 'Accept-Language: zh-CN,zh;q=0.8' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36' -H 'Content-Type: application/x-www-form-urlencoded' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Cache-Control: no-cache' -H 'Connection: keep-alive' -H 'DNT: 1' --data 'test1=%E6%B5%8B%E8%AF%95&test2=%E4%B8%AD%E6%96%87' --compressed"""
    args = curlparse(cmd)
    resp = requests.request(**args)
    rj = resp.json()
    assert rj["form"]["test1"] == u"测试", "test fail: curlparse post & urlencode"


def test_curlparse_post2():
    """  test_dummy_utils """
    cmd = """curl 'http://httpbin.org/post' -H 'Pragma: no-cache' -H 'Origin: null' -H 'Accept-Encoding: gzip, deflate' -H 'Accept-Language: zh-CN,zh;q=0.8' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Cache-Control: no-cache' -H 'Connection: keep-alive' -H 'DNT: 1' --data-binary $'中文' --compressed"""
    args = curlparse(cmd)
    resp = requests.request(**args)
    rj = resp.json()
    assert rj["data"] == u"中文"


def test_slice_by_size():
    assert list(slice_by_size(range(10), 6)) == [
        (0, 1, 2, 3, 4, 5),
        (6, 7, 8, 9),
    ], "test fail: slice_by_size"


def test_slice_into_pieces():
    assert list(slice_into_pieces(range(10), 3)) == [
        (0, 1, 2, 3),
        (4, 5, 6, 7),
        (8, 9),
    ], "test fail: slice_into_pieces"


def test_ttime_ptime():
    assert time.time() - ptime(
        ttime(tzone=0), tzone=0) < 2, "fail: ttime / ptime"
    assert ttime(1542099747428) == ttime(1542099747428 / 1000)


def test_timeago():
    assert timeago(93245732.0032424, 5) == "1079 days, 05:35:32,003"
    assert timeago(93245732.0032424, 4,
                   1) == "1079 days 5 hours 35 minutes 32 seconds"
    seconds = [60, 61, 62, 120, 121, 122, 3600, 3601, 86400, 864111, 0, 0.1, 60.1]
    accuracies = range(1, 6)
    formats = range(2)
    cases = {
        (60, 1, 0): '00:01:00',
        (60, 1, 1): '1 min',
        (60, 2, 0): '00:01:00',
        (60, 2, 1): '1 min',
        (60, 3, 0): '00:01:00',
        (60, 3, 1): '1 min',
        (60, 4, 0): '00:01:00',
        (60, 4, 1): '1 min',
        (60, 5, 0): '00:01:00,000',
        (60, 5, 1): '1 min',
        (61, 1, 0): '00:01:01',
        (61, 1, 1): '1 min',
        (61, 2, 0): '00:01:01',
        (61, 2, 1): '1 min 1 sec',
        (61, 3, 0): '00:01:01',
        (61, 3, 1): '1 min 1 sec',
        (61, 4, 0): '00:01:01',
        (61, 4, 1): '1 min 1 sec',
        (61, 5, 0): '00:01:01,000',
        (61, 5, 1): '1 min 1 sec',
        (62, 1, 0): '00:01:02',
        (62, 1, 1): '1 min',
        (62, 2, 0): '00:01:02',
        (62, 2, 1): '1 min 2 secs',
        (62, 3, 0): '00:01:02',
        (62, 3, 1): '1 min 2 secs',
        (62, 4, 0): '00:01:02',
        (62, 4, 1): '1 min 2 secs',
        (62, 5, 0): '00:01:02,000',
        (62, 5, 1): '1 min 2 secs',
        (120, 1, 0): '00:02:00',
        (120, 1, 1): '2 mins',
        (120, 2, 0): '00:02:00',
        (120, 2, 1): '2 mins',
        (120, 3, 0): '00:02:00',
        (120, 3, 1): '2 mins',
        (120, 4, 0): '00:02:00',
        (120, 4, 1): '2 mins',
        (120, 5, 0): '00:02:00,000',
        (120, 5, 1): '2 mins',
        (121, 1, 0): '00:02:01',
        (121, 1, 1): '2 mins',
        (121, 2, 0): '00:02:01',
        (121, 2, 1): '2 mins 1 sec',
        (121, 3, 0): '00:02:01',
        (121, 3, 1): '2 mins 1 sec',
        (121, 4, 0): '00:02:01',
        (121, 4, 1): '2 mins 1 sec',
        (121, 5, 0): '00:02:01,000',
        (121, 5, 1): '2 mins 1 sec',
        (122, 1, 0): '00:02:02',
        (122, 1, 1): '2 mins',
        (122, 2, 0): '00:02:02',
        (122, 2, 1): '2 mins 2 secs',
        (122, 3, 0): '00:02:02',
        (122, 3, 1): '2 mins 2 secs',
        (122, 4, 0): '00:02:02',
        (122, 4, 1): '2 mins 2 secs',
        (122, 5, 0): '00:02:02,000',
        (122, 5, 1): '2 mins 2 secs',
        (3600, 1, 0): '01:00:00',
        (3600, 1, 1): '1 hr',
        (3600, 2, 0): '01:00:00',
        (3600, 2, 1): '1 hr',
        (3600, 3, 0): '01:00:00',
        (3600, 3, 1): '1 hr',
        (3600, 4, 0): '01:00:00',
        (3600, 4, 1): '1 hr',
        (3600, 5, 0): '01:00:00,000',
        (3600, 5, 1): '1 hr',
        (3601, 1, 0): '01:00:01',
        (3601, 1, 1): '1 hr',
        (3601, 2, 0): '01:00:01',
        (3601, 2, 1): '1 hr 0 min',
        (3601, 3, 0): '01:00:01',
        (3601, 3, 1): '1 hr 0 min 1 sec',
        (3601, 4, 0): '01:00:01',
        (3601, 4, 1): '1 hr 0 min 1 sec',
        (3601, 5, 0): '01:00:01,000',
        (3601, 5, 1): '1 hr 0 min 1 sec',
        (86400, 1, 0): '1 day, 00:00:00',
        (86400, 1, 1): '1 day',
        (86400, 2, 0): '1 day, 00:00:00',
        (86400, 2, 1): '1 day',
        (86400, 3, 0): '1 day, 00:00:00',
        (86400, 3, 1): '1 day',
        (86400, 4, 0): '1 day, 00:00:00',
        (86400, 4, 1): '1 day',
        (86400, 5, 0): '1 day, 00:00:00,000',
        (86400, 5, 1): '1 day',
        (864111, 1, 0): '10 days, 00:01:51',
        (864111, 1, 1): '10 days',
        (864111, 2, 0): '10 days, 00:01:51',
        (864111, 2, 1): '10 days 0 hr',
        (864111, 3, 0): '10 days, 00:01:51',
        (864111, 3, 1): '10 days 0 hr 1 min',
        (864111, 4, 0): '10 days, 00:01:51',
        (864111, 4, 1): '10 days 0 hr 1 min 51 secs',
        (864111, 5, 0): '10 days, 00:01:51,000',
        (864111, 5, 1): '10 days 0 hr 1 min 51 secs',
        (0, 1, 0): '00:00:00',
        (0, 1, 1): '0 ms',
        (0, 2, 0): '00:00:00',
        (0, 2, 1): '0 ms',
        (0, 3, 0): '00:00:00',
        (0, 3, 1): '0 ms',
        (0, 4, 0): '00:00:00',
        (0, 4, 1): '0 ms',
        (0, 5, 0): '00:00:00,000',
        (0, 5, 1): '0 ms',
        (0.1, 1, 0): '00:00:00',
        (0.1, 1, 1): '100 ms',
        (0.1, 2, 0): '00:00:00',
        (0.1, 2, 1): '100 ms',
        (0.1, 3, 0): '00:00:00',
        (0.1, 3, 1): '100 ms',
        (0.1, 4, 0): '00:00:00',
        (0.1, 4, 1): '100 ms',
        (0.1, 5, 0): '00:00:00,100',
        (0.1, 5, 1): '100 ms',
        (60.1, 1, 0): '00:01:00',
        (60.1, 1, 1): '1 min',
        (60.1, 2, 0): '00:01:00',
        (60.1, 2, 1): '1 min 0 sec',
        (60.1, 3, 0): '00:01:00',
        (60.1, 3, 1): '1 min 0 sec 100 ms',
        (60.1, 4, 0): '00:01:00',
        (60.1, 4, 1): '1 min 0 sec 100 ms',
        (60.1, 5, 0): '00:01:00,100',
        (60.1, 5, 1): '1 min 0 sec 100 ms'
    }
    for sec in seconds:
        for acc in accuracies:
            for f in formats:
                args = (sec, acc, f)
                result = timeago(
                    seconds=sec, accuracy=acc, format=f, short_name=True)
                assert cases[args] == result


def test_escape_unescape():
    assert escape("<>") == "&lt;&gt;" and unescape(
        "&lt;&gt;") == "<>", "fail: escape"


def test_counts():
    c = Counts()
    [c.x for i in range(10)]
    assert c.c == 11, "fail: test_counts"


def test_unique():
    assert list(
        unique(list(range(4, 0, -1)) + list(range(5)))) == [4, 3, 2, 1, 0]


def test_regex():
    reg = Regex()

    @reg.register_function("http.*cctv.*")
    def mock():
        pass

    reg.register("http.*HELLOWORLD", "helloworld", flags=re.I)
    reg.register("http.*HELLOWORLD2", "helloworld2", flags=re.I)

    assert reg.search("http://cctv.com")
    assert reg.match("http://helloworld") == ["helloworld"]
    assert reg.match("non-http://helloworld") == []
    assert reg.search("non-http://helloworld") == ["helloworld"]
    assert len(reg.search("non-http://helloworld2")) == 2


def test_clean_request():
    from torequests.crawlers import CleanRequest

    request = """curl 'https://p.3.cn?skuIds=1&nonsense=1&nonce=0' -H 'Pragma: no-cache' -H 'DNT: 1' -H 'Accept-Encoding: gzip, deflate' -H 'Accept-Language: zh-CN,zh;q=0.9' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Cache-Control: no-cache' -H 'Referer: https://p.3.cn?skuIds=1&nonsense=1&nonce=0' -H 'Cookie: ASPSESSIONIDSQRRSADB=MLHDPOPCAMBDGPFGBEEJKLAF' -H 'Connection: keep-alive' --compressed"""

    c = CleanRequest(request)
    assert c.x == {"url": "https://p.3.cn", "method": "get"}


def test_failure():
    from torequests.exceptions import FailureException

    assert bool(FailureException(BaseException())) is False


def test_try_import():
    assert try_import("re")
    assert try_import("re", "findall")
    assert not try_import("fake_re")
    assert not try_import("fake_re", "findall")


def test_ensure_request():
    assert ensure_request({
        "method": "get",
        "url": "http://github.com"
    }) == {
        "method": "get",
        "url": "http://github.com",
    }
    assert ensure_request("http://github.com") == {
        "method": "get",
        "url": "http://github.com",
    }
    assert ensure_request(
        """curl 'https://github.com/' -H 'Pragma: no-cache' -H 'Accept-Encoding: gzip, deflate, br' -H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' -H 'Cache-Control: no-cache' -H 'Cookie: logged_in=no; ' -H 'Connection: keep-alive' --compressed"""
    ) == {
        "url": "https://github.com/",
        "headers": {
            "Pragma": "no-cache",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Cache-Control": "no-cache",
            "Cookie": "logged_in=no;",
            "Connection": "keep-alive",
        },
        "method": "get",
    }

    def test_split_n():
        ss = """a b c  d e f  1 2 3  4 5 6
        a b c  d e f  1 2 3  4 5 6
        a b c  d e f  1 2 3  4 5 6"""
        assert split_n(ss,
                       ("\n", "  ", " ")) == [
                           [["a", "b", "c"], ["d", "e", "f"], ["1", "2", "3"],
                            ["4", "5", "6"]],
                           [["a", "b", "c"], ["d", "e", "f"], ["1", "2", "3"],
                            ["4", "5", "6"]],
                           [["a", "b", "c"], ["d", "e", "f"], ["1", "2", "3"],
                            ["4", "5", "6"]],
                       ]
        assert split_n(
            ss, ["\\s+"], reg=1) == [
                "a",
                "b",
                "c",
                "d",
                "e",
                "f",
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "a",
                "b",
                "c",
                "d",
                "e",
                "f",
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "a",
                "b",
                "c",
                "d",
                "e",
                "f",
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
            ]

    def test_saver():
        ss = Saver("test.json", auto_backup=1)
        try:
            ss.a = 1
            assert ss.a == ss["a"] == ss._get("a")
            assert ss._get("not_exist") is None
            assert ss.not_exist is None
            ss._update({"b": 2})
            ss._update(**{"c": 3})
            ss._set("d", 4)
            assert ss.b == 2
            assert ss.c == 3
            assert ss._cache == {u"a": 1, u"c": 3, u"b": 2, u"d": 4}
            assert len(ss) == 4
            assert ss
            del ss.a
            del ss["b"]
            assert ss._pop("c", 0) == 3
            assert ss._pop("c", 0) == 0
            assert "a" not in ss
            assert "b" not in ss
            assert "c" not in ss
            assert ss._popitem() == ("d", 4)
            ss._clear()
            assert not ss
        finally:
            ss._shutdown()


def test_find_one():
    string = "abcd"
    assert find_one("a.*", string)[0] == "abcd"
    assert find_one("a(.)", string)[0] == "ab"
    assert find_one("a(.)", string)[1] == "b"
    assert find_one("a(B)", string, flags=re.I | re.DOTALL)[1] == "b"
    assert (find_one("a(B)", string)[1] or "default") == "default"
    assert (find_one("a(B)", string)[1]) == ""
    register_re_findone()
    assert re.findone("a(.)", string)[1] == "b"


def test_cooldown():
    cd = Cooldown(range(1, 2), 3)
    cd.add_item(2)
    cd.add_items([3, 4])
    item_types = [True, True, True, True, False, False]
    for _ in range(5):
        item = cd.get(1, 0)
        assert (item > 0) == item_types[_]
    # remove items
    for _ in range(cd.size):
        item = cd.get(6, 0)
        if item > 2:
            cd.remove_item(item)
    assert cd.all_items == [1, 2]


def test_curlrequests():
    r = curlrequests(
        '''curl 'https://httpbin.org/get' -H 'Connection: keep-alive' -H 'Cache-Control: max-age=0' -H 'DNT: 1' -H 'Upgrade-Insecure-Requests: 1' -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36' -H 'Sec-Fetch-Mode: navigate' -H 'Sec-Fetch-User: ?1' -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3' -H 'Sec-Fetch-Site: none' -H 'Accept-Encoding: gzip, deflate, br' -H 'Accept-Language: zh-CN,zh;q=0.9' --compressed''',
        retry=1)
    assert '"args": {}' in r.text


def test_sort_url_query():
    url = 'http://www.google.com?b=2&z=26&a=1'
    default_sorted = sort_url_query(url)
    reversed_sorted = sort_url_query(url, reverse=True)
    update_https_default_sorted = sort_url_query(
        url, _replace_kwargs={'scheme': 'https'})
    assert default_sorted == 'http://www.google.com?a=1&b=2&z=26'
    assert reversed_sorted == 'http://www.google.com?z=26&b=2&a=1'
    assert update_https_default_sorted == 'https://www.google.com?a=1&b=2&z=26'
