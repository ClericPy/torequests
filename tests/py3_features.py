#! coding:utf-8
import sys
import time

from torequests import *
from torequests.dummy import *

# with capsys.disabled():


def test_dummy_Requests():
    '''use default event loop'''
    trequests = Requests()
    test_url = 'http://p.3.cn/prices/mgets?skuIds=J_1273500'
    ss = [trequests.get(test_url, retry=0, callback=lambda x:len(
        x.content)) for i in range(3)]
    trequests.x
    ss = [i.cx for i in ss]
    assert all(ss), 'fail: test_dummy_Requests'


def test_dummy_Requests_time_interval_sem_run_forever(capsys):
    '''  test_dummy_Requests_time_interval_sem_run_forever '''
    with capsys.disabled():
        trequests = Requests(frequencies={'p.3.cn': (2, 1)})
        trequests.async_run_forever()
        print()
        ss = [trequests.get('http://p.3.cn/prices/mgets?skuIds=J_1273500',
                            callback=lambda x: (len(x.content), print(trequests.frequencies)))
              for i in range(4)]
        trequests.x
        ss = [i.cx for i in ss]
        assert all(ss), 'fail: test_dummy_Requests_time_interval_sem_run_forever'


def test_new_future_await():
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
            print('testcoro 2 ops/s')
            await asyncio.sleep(0)
            return 'testcoro result'

        print()
        task = [testcoro() for i in range(4)]
        tasks = [i.x for i in task]
        assert tasks == ['testcoro result', 'testcoro result',
                         'testcoro result', 'testcoro result']


def test_asyncme(capsys):
    with capsys.disabled():

        async def test():
            print('testAsyncme 2 ops/s')
            await asyncio.sleep(0)
            return 'testAsyncme result'
        print()
        testAsyncme = Asyncme(test, 2, 1)
        task = [testAsyncme() for i in range(4)]
        tasks = [i.x for i in task]
        assert tasks == ['testAsyncme result', 'testAsyncme result',
                         'testAsyncme result', 'testAsyncme result']
