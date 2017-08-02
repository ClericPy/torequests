#! coding:utf-8
import time
from torequests.dummy import *
from torequests import *
from torequests.utils import *
import requests
import asyncio


def test_dummy_Requests(capsys):
    '''use default event loop'''
    with capsys.disabled():
        start = time.time()
        trequests = Requests()
        test_url = 'http://baidu.com'
        ss = [trequests.get(test_url, retry=0, callback=lambda x:len(x.content)) for i in range(3)]
        trequests.x
        ss = [i.cx for i in ss]
        cost = round(time.time() - start, 2)
        print('test_dummy_Requests [ ', cost, ' ]seconds.', ss)
        assert all(ss), 'fail: test_dummy_Requests'

def test_main_tPool(capsys):
    '''use default event loop'''
    with capsys.disabled():
        start = time.time()
        trequests = tPool()
        test_url = 'http://baidu.com'
        ss = [trequests.get(test_url, retry=0, callback=lambda x:len(x.content)) for i in range(3)]
        [i.x for i in ss]
        ss = [i.cx for i in ss]
        cost = round(time.time() - start, 2)
        print('test_main_tPool [ ', cost, ' ]seconds.', ss)
        assert all(ss), 'fail: test_main_tPool'

def test_dummy_Requests_time_interval_sem_run_forever(capsys):
    '''  test_dummy_Requests_time_interval_sem_run_forever '''
    with capsys.disabled():
        req = Requests(time_interval=1, n=2)
        req.async_run_forever()
        ss = [req.get('http://baidu.com', callback=lambda x: (len(x.content), 'ok'))
            for i in range(3)]
        time.sleep(2)
        ss = [i.cx for i in ss]
        print(ss)
        assert all(ss), 'fail: test_main_tPool'
