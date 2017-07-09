#! coding:utf-8
import time
from torequests.dummy import Requests
from torequests import tPool
import asyncio


def test_dummy_Requests_speed(capsys):
    '''use default event loop'''
    with capsys.disabled():
        start = time.time()
        trequests = Requests()
        test_url = 'http://127.0.0.1:5000/test/%s'
        ss = [trequests.get(test_url % i, retry=0)
            for i in range(1000)]
        trequests.x
        ss = [i.x for i in ss]
        cost = round(time.time() - start, 2)
        print('test_dummy_Requests_speed[ ', cost, ' ]seconds.')

def test_main_tPool_speed(capsys):
    '''use default event loop'''
    with capsys.disabled():
        start = time.time()
        trequests = tPool()
        test_url = 'http://127.0.0.1:5000/test/%s'
        ss = [trequests.get(test_url % i, retry=0)
            for i in range(1000)]
        ss = [i.x for i in ss]
        cost = round(time.time() - start, 2)
        print('test_main_tPool_speed[ ', cost, ' ]seconds.')

def test_dummy_Requests_time_interval_sem_run_forever(capsys):
    '''  test_dummy_Requests_time_interval_sem_run_forever '''
    with capsys.disabled():
        req = Requests(time_interval=1, n=2)
        ss = [req.get('http://localhost:5000/sleep/0', callback=lambda x: print((x.text)))
            for i in range(3)]
        req.async_run_forever()
        for i in range(3):
            req.get('http://localhost:5000/sleep/0', callback=lambda x: print((x.text)))
            time.sleep(1)
        time.sleep(3)
        req.stop()

