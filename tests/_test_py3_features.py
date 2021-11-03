#! coding:utf-8
import asyncio
import time

from torequests import *
from torequests.dummy import *
from torequests.utils import retry


def test_dummy_Requests():
    """use default event loop"""
    req = Requests()
    test_url = "https://httpbin.org/json"
    tasks = [
        req.get(test_url,
                retry=1,
                verify=True,
                callback=lambda r: len(r.content),
                timeout=(2, 5),
                referer_info=i) for i in range(3)
    ]
    req.x
    cb_results = [i.cx for i in tasks]
    # test and ensure task.cx is callback result
    assert all([isinstance(i, int) for i in cb_results
               ]), "fail: test_dummy_Requests"
    r = tasks[0]
    assert isinstance(r.content, bytes)
    assert isinstance(r.text, str)
    assert isinstance(r.json(), dict)
    assert not r.is_redirect
    assert r.ok
    assert r.status_code == 200
    print(r.url, type(r.url))
    assert isinstance(r.url, str)
    assert r.referer_info == 0


def test_dummy_Requests_async():
    """use default event loop"""

    async def async_validator(r):
        await asyncio.sleep(0.001)
        return r.status_code == 206

    async def test_async():
        async with Requests() as req:
            test_url = "https://httpbin.org/json"
            tasks = [
                req.get(test_url,
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
            assert await req.get(
                'http://httpbin.org/status/206',
                response_validator=lambda r: r.status_code == 206)
            assert not await req.get(
                'http://httpbin.org/status/206',
                response_validator=lambda r: r.status_code == 200)
            assert await req.get('http://httpbin.org/status/206',
                                 response_validator=async_validator)
            assert not await req.get('http://httpbin.org/status/201',
                                     response_validator=async_validator)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_async())


def test_dummy_Requests_time_interval_frequency(capsys):
    """  test_dummy_Requests_time_interval_frequency"""
    with capsys.disabled():
        req = Requests(frequencies={"p.3.cn": (2, 1)})
        print("\n")
        ss = [
            req.get(
                "http://p.3.cn",
                callback=lambda x: (len(x.content), print(req.frequencies)),
            ) for i in range(4)
        ]
        req.x
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


def test_retry():
    # python2
    nums = {'num': 0}

    @retry(2, (ValueError,), True)
    def test_sync():
        nums['num'] += 1
        if nums['num'] > 1:
            raise ValueError()
        return 1

    result = test_sync()
    assert isinstance(result, int)
    result = test_sync()
    assert isinstance(result, ValueError)
    try:
        test_sync()
    except Exception as err:
        assert isinstance(err, ValueError)


def test_retry_async():

    async def async_test_func():
        nums = {'num': 0}

        @retry(2, (ValueError,), True)
        async def test_async():
            nums['num'] += 1
            if nums['num'] > 1:
                raise ValueError()
            return 1

        result = await test_async()
        assert isinstance(result, int)
        result = await test_async()
        assert isinstance(result, ValueError)
        try:
            await test_async()
        except Exception as err:
            assert isinstance(err, ValueError)

    asyncio.get_event_loop().run_until_complete(async_test_func())


def test_async_frequency():
    # for python3.6+ only
    from torequests.frequency_controller.async_tools import AsyncFrequency
    from asyncio import ensure_future, get_event_loop
    from time import time

    async def test_async():
        frequency = AsyncFrequency(2, 1)

        async def task():
            async with frequency:
                return time()

        now = time()
        tasks = [ensure_future(task()) for _ in range(5)]
        result = [await task for task in tasks]
        assert result[0] - now <= 1
        assert result[1] - now <= 1
        assert result[2] - now >= 1
        assert result[3] - now >= 1
        assert result[4] - now >= 2
        assert frequency.to_dict() == {'n': 2, 'interval': 1}
        assert frequency.to_list() == [2, 1]

    get_event_loop().run_until_complete(test_async())


def test_aiohttp_dummy():
    # for python3.6+ only
    from torequests.aiohttp_dummy import Requests
    from asyncio import get_event_loop

    async def async_validator(r):
        await asyncio.sleep(0.001)
        return r.status_code == 206

    async def test1():
        url = 'http://httpbin.org/get'
        req = Requests()
        r = await req.get(url, retry=1)
        assert r.json()['url'] == url
        r = await req.get('http://', retry=1, retry_interval=1)
        assert isinstance(r, Exception)
        r = await req.get('http://', retry=1, callback=lambda r: r.text)
        assert r.startswith('FailureException')
        async with Requests() as req:
            r = await req.get(url)
            assert r.json()['url'] == url
        # ==================
        test_url = "https://httpbin.org/json"
        req = Requests()
        r = await req.get(test_url,
                          retry=1,
                          ssl=True,
                          timeout=2,
                          referer_info=0)
        assert isinstance(r.content, bytes)
        assert isinstance(r.text, str)
        assert isinstance(r.json(), dict)
        assert not r.is_redirect
        assert r.ok
        assert r.status_code == 200
        assert isinstance(r.url, str)
        assert r.referer_info == 0
        assert await req.get('http://httpbin.org/status/206',
                             response_validator=lambda r: r.status_code == 206)
        assert not await req.get(
            'http://httpbin.org/status/206',
            response_validator=lambda r: r.status_code == 200)
        assert await req.get('http://httpbin.org/status/206',
                             response_validator=async_validator)
        assert not await req.get('http://httpbin.org/status/201',
                                 response_validator=async_validator)

    get_event_loop().run_until_complete(test1())


def test_workshop():
    import asyncio
    from torequests.dummy import Workshop

    async def _test():

        async def callback(todo, worker_arg):
            await asyncio.sleep(todo / 10)
            if worker_arg == 'worker1':
                return None
            return todo

        fc = Workshop(range(1, 10), ['worker1', 'worker2', 'worker3'], callback)

        assert await fc.run() == list(range(1, 10))
        assert await fc.run(as_completed=True) != list(range(1, 10))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(_test())
