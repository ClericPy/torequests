#! coding:utf-8
import asyncio
import time

from torequests import *
from torequests.dummy import *


def test_dummy_Requests():
    """use default event loop"""
    trequests = Requests()
    test_url = "https://httpbin.org/json"
    tasks = [
        trequests.get(
            test_url,
            retry=1,
            verify=True,
            callback=lambda r: len(r.content),
            timeout=(2, 5),
            referer_info=i) for i in range(3)
    ]
    trequests.x
    cb_results = [i.cx for i in tasks]
    # test and ensure task.cx is callback result
    assert all(
        [isinstance(i, int) for i in cb_results]), "fail: test_dummy_Requests"
    r = tasks[0]
    assert isinstance(r.content, bytes)
    assert isinstance(r.text, str)
    assert isinstance(r.json(), dict)
    assert not r.is_redirect
    assert r.ok
    assert r.status_code == 200
    assert isinstance(r.url, str)
    assert r.referer_info == 0


def test_dummy_Requests_async():
    """use default event loop"""

    async def test_async():
        async with Requests() as trequests:
            test_url = "https://httpbin.org/json"
            tasks = [
                trequests.get(
                    test_url,
                    retry=1,
                    callback=lambda r: len(r.content),
                    timeout=(2, 5),
                    referer_info=i) for i in range(3)
            ]
            result = [(await task).text for task in tasks]
            assert all(result), "fail: test_dummy_Requests_async"
            r = tasks[0]
            assert isinstance(r.content, bytes)
            assert isinstance(r.text, str)
            assert isinstance(r.json(), dict)
            assert not r.is_redirect
            assert r.ok
            assert r.status_code == 200
            assert isinstance(r.url, str)
            assert r.referer_info == 0

    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_async())


def test_dummy_Requests_time_interval_frequency(capsys):
    """  test_dummy_Requests_time_interval_frequency"""
    with capsys.disabled():
        trequests = Requests(frequencies={"p.3.cn": (2, 1)})
        print("\n")
        ss = [
            trequests.get(
                "http://p.3.cn",
                callback=
                lambda x: (len(x.content), print(trequests.frequencies)),
            ) for i in range(4)
        ]
        trequests.x
        assert ss[-1].task_cost_time >= 1, 'fail test task_cost_time'
        ss = [i.cx for i in ss]
        assert all(ss), "fail: test_dummy_Requests_time_interval_frequency"


def test_new_future_awaitable():
    loop = Loop()

    @threads()
    def sleep(n):
        time.sleep(n)
        return n

    async def test():
        result = await sleep(1.5)
        return result

    coro = test()
    task = loop.submit(coro)
    loop.x
    assert task.x == 1.5


def test_coros(capsys):
    with capsys.disabled():

        @coros(2, 1)
        async def testcoro():
            print("testcoro 2 ops/s")
            await asyncio.sleep(0)
            return "testcoro result"

        print("\n")
        task = [testcoro() for i in range(4)]
        tasks = [i.x for i in task]
        assert tasks == [
            "testcoro result",
            "testcoro result",
            "testcoro result",
            "testcoro result",
        ]


def test_asyncme(capsys):
    with capsys.disabled():

        async def test():
            print("testAsyncme 2 ops/s")
            await asyncio.sleep(0)
            return "testAsyncme result"

        print("\n")
        testAsyncme = Asyncme(test, 2, 1)
        task = [testAsyncme() for i in range(4)]
        tasks = [i.x for i in task]
        assert tasks == [
            "testAsyncme result",
            "testAsyncme result",
            "testAsyncme result",
            "testAsyncme result",
        ]
