import asyncio
import timeit


async def test_aiohttp():
    global AIOHTTP_QPS
    from aiohttp import ClientSession, __version__

    async with ClientSession() as req:
        ok = 0
        bad = 0
        start = timeit.default_timer()
        tasks = [
            asyncio.ensure_future(req.get(url))
            for _ in range(TOTAL_REQUEST_COUNTS)
        ]
        for task in tasks:
            r = await task
            text = await r.text()
            if text == 'ok':
                ok += 1
            else:
                bad += 1
        cost = timeit.default_timer() - start
        name = f'test_aiohttp({__version__})'
        AIOHTTP_QPS = qps = round(TOTAL_REQUEST_COUNTS / cost)
        print(
            f'{name: <25}: {ok} / {ok + bad} = {ok * 100 / (ok + bad)}%, cost {round(cost, 3): >5}s, {qps} qps, {round(qps*100/AIOHTTP_QPS, 2)}% standard.'
        )


async def test_dummy():
    from torequests.dummy import Requests
    from torequests import __version__

    async with Requests() as req:
        start = timeit.default_timer()
        ok = 0
        bad = 0
        tasks = [req.get(url) for _ in range(TOTAL_REQUEST_COUNTS)]
        for task in tasks:
            r = await task
            if r.text == 'ok':
                ok += 1
            else:
                bad += 1
        cost = timeit.default_timer() - start
        name = f'test_dummy({__version__})'
        qps = round(TOTAL_REQUEST_COUNTS / cost)
        print(
            f'{name: <25}: {ok} / {ok + bad} = {ok * 100 / (ok + bad)}%, cost {round(cost, 3): >5}s, {qps} qps, {round(qps*100/AIOHTTP_QPS, 2)}% standard.'
        )


def test_tPool():
    from torequests.main import tPool
    from torequests import __version__

    req = tPool()
    start = timeit.default_timer()
    ok = 0
    bad = 0
    tasks = [req.get(url) for _ in range(TOTAL_REQUEST_COUNTS)]
    req.x
    for task in tasks:
        r = task.x
        if r.text == 'ok':
            ok += 1
        else:
            bad += 1
    cost = timeit.default_timer() - start
    name = f'test_tPool({__version__})'
    qps = round(TOTAL_REQUEST_COUNTS / cost)
    print(
        f'{name: <25}: {ok} / {ok + bad} = {ok * 100 / (ok + bad)}%, cost {round(cost, 3): >5}s, {qps} qps, {round(qps*100/AIOHTTP_QPS, 2)}% standard.'
    )


async def test_httpx():
    from httpx import AsyncClient, __version__
    start = timeit.default_timer()
    ok = 0
    bad = 0
    async with AsyncClient() as req:
        tasks = [
            asyncio.create_task(req.get(url))
            for _ in range(TOTAL_REQUEST_COUNTS)
        ]
        for task in tasks:
            r = await task
            if r.text == 'ok':
                ok += 1
            else:
                bad += 1
    cost = timeit.default_timer() - start
    name = f'test_httpx({__version__})'
    qps = round(TOTAL_REQUEST_COUNTS / cost)
    print(
        f'{name: <25}: {ok} / {ok + bad} = {ok * 100 / (ok + bad)}%, cost {round(cost, 3): >5}s, {qps} qps, {round(qps*100/AIOHTTP_QPS, 2)}% standard.'
    )


if __name__ == "__main__":
    import platform
    import sys
    import os
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        print('Test with uvloop,', os.cpu_count(), 'logical CPUs.')
    except ImportError:
        print('Test without uvloop,', os.cpu_count(), 'logical CPUs.')
    url = 'http://127.0.0.1:8080'
    TOTAL_REQUEST_COUNTS = 2000
    # use aiohttp as the standard qps
    AIOHTTP_QPS = None
    print(platform.platform())
    print(sys.version)
    print('=' * 80)
    if len(sys.argv) > 1:
        n = int(sys.argv[1])
    else:
        n = 10
    for _ in range(n):
        asyncio.run(test_aiohttp())
        asyncio.run(test_dummy())
        asyncio.run(test_httpx())
        test_tPool()
