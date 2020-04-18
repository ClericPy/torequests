import asyncio
import timeit

import aiohttp
import httpx
import requests
import torequests

result: dict = {}


def print_msg(name, cost, ok):
    qps = round(TOTAL_REQUEST_COUNTS / cost)
    msg = f'{name: <25}: {ok} / {TOTAL_REQUEST_COUNTS} = {ok * 100 / (TOTAL_REQUEST_COUNTS)}%, cost {round(cost, 3):0>5}s, {qps: >4} qps, {(round(qps*100/AIOHTTP_QPS) if AIOHTTP_QPS else 100): >3}% standard.'
    print(msg)


async def test_aiohttp():
    global AIOHTTP_QPS
    from aiohttp import ClientSession

    async def test(req, url):
        async with req.get(url) as resp:
            await resp.read()
            return resp._body

    async with ClientSession() as req:
        ok = 0
        start = timeit.default_timer()
        tasks = [
            asyncio.ensure_future(test(req, url))
            for _ in range(TOTAL_REQUEST_COUNTS)
        ]
        for task in tasks:
            r = await task
            if r == b'ok':
                ok += 1
    name = 'test_aiohttp'
    cost = timeit.default_timer() - start
    if cost < result.get(name, 999):
        result[name] = cost
        AIOHTTP_QPS = round(TOTAL_REQUEST_COUNTS / cost)
    else:
        cost = result[name]
    print_msg(name, cost, ok)


async def test_dummy():
    from torequests.dummy import Requests

    async with Requests() as req:
        start = timeit.default_timer()
        ok = 0
        tasks = [
            asyncio.ensure_future(req.get(url))
            for _ in range(TOTAL_REQUEST_COUNTS)
        ]
        for task in tasks:
            r = await task
            if r.content == b'ok':
                ok += 1
    name = 'test_dummy'
    cost = timeit.default_timer() - start
    if cost < result.get(name, 999):
        result[name] = cost
    else:
        cost = result[name]
    result[name] = cost
    print_msg(name, cost, ok)


async def test_aiohttp_dummy():
    from torequests.aiohttp_dummy import Requests

    async with Requests() as req:
        start = timeit.default_timer()
        ok = 0
        tasks = [
            asyncio.ensure_future(req.get(url))
            for _ in range(TOTAL_REQUEST_COUNTS)
        ]
        for task in tasks:
            r = await task
            if r.content == b'ok':
                ok += 1
    name = 'test_aiohttp_dummy'
    cost = timeit.default_timer() - start
    if cost < result.get(name, 999):
        result[name] = cost
    else:
        cost = result[name]
    result[name] = cost
    print_msg(name, cost, ok)


def test_tPool():
    from torequests.main import tPool

    req = tPool()
    start = timeit.default_timer()
    ok = 0
    tasks = [req.get(url) for _ in range(TOTAL_REQUEST_COUNTS)]
    req.x
    for task in tasks:
        r = task.x
        if r.text == 'ok':
            ok += 1
    name = 'test_tPool'
    cost = timeit.default_timer() - start
    if cost < result.get(name, 999):
        result[name] = cost
    else:
        cost = result[name]
    result[name] = cost
    print_msg(name, cost, ok)


async def test_httpx():
    from httpx import AsyncClient
    start = timeit.default_timer()
    ok = 0
    async with AsyncClient() as req:
        tasks = [
            asyncio.create_task(req.get(url))
            for _ in range(TOTAL_REQUEST_COUNTS)
        ]
        for task in tasks:
            r = await task
            if r.text == 'ok':
                ok += 1
    name = 'test_httpx'
    cost = timeit.default_timer() - start
    if cost < result.get(name, 999):
        result[name] = cost
    else:
        cost = result[name]
    result[name] = cost
    print_msg(name, cost, ok)


if __name__ == "__main__":
    import platform
    import sys
    if sys.platform == 'win32':  # use IOCP in windows
        if sys.version_info.major >= 3 and sys.version_info.minor >= 7:
            asyncio.set_event_loop_policy(
                asyncio.WindowsProactorEventLoopPolicy())
        else:
            asyncio.set_event_loop(asyncio.ProactorEventLoop())
    else:  # try to use uvloop
        try:
            import uvloop
            uvloop.install()
        except ImportError:
            pass
    url = 'http://127.0.0.1:8080'
    TOTAL_REQUEST_COUNTS = 2000
    # use aiohttp as the standard qps
    AIOHTTP_QPS = None
    if len(sys.argv) > 1:
        n = int(sys.argv[1])
    else:
        n = 10
    for _ in range(n):
        asyncio.run(test_aiohttp())
        asyncio.run(test_dummy())
        asyncio.run(test_aiohttp_dummy())
        print('=' * 80)
    # show final result
    print(platform.platform())
    print(sys.version)
    print([
        f'{mod.__name__}({mod.__version__})'
        for mod in [aiohttp, torequests, requests, httpx]
    ])
    print('=' * 80)
    asyncio.run(test_aiohttp())
    asyncio.run(test_dummy())
    asyncio.run(test_aiohttp_dummy())
    asyncio.run(test_httpx())
    test_tPool()
