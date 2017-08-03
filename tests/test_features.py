#! coding:utf-8
import time
from torequests.dummy import *
from torequests import *


def test_dummy_Requests():
    '''use default event loop'''
    trequests = Requests()
    test_url = 'http://p.3.cn/prices/mgets?skuIds=J_1273500'
    ss = [trequests.get(test_url, retry=0, callback=lambda x:len(x.content)) for i in range(3)]
    trequests.x
    ss = [i.cx for i in ss]
    assert all(ss), 'fail: test_dummy_Requests'

def test_main_tPool():
    '''use default event loop'''
    trequests = tPool()
    test_url = 'http://p.3.cn/prices/mgets?skuIds=J_1273500'
    ss = [trequests.get(test_url, retry=0, callback=lambda x:len(x.content)) for i in range(3)]
    [i.x for i in ss]
    ss = [i.cx for i in ss]
    assert all(ss), 'fail: test_main_tPool'

def test_dummy_Requests_time_interval_sem_run_forever():
    '''  test_dummy_Requests_time_interval_sem_run_forever '''
    trequests = Requests(time_interval=1, n=2)
    trequests.async_run_forever()
    ss = [trequests.get('http://p.3.cn/prices/mgets?skuIds=J_1273500', callback=lambda x: (len(x.content), 'ok'))
        for i in range(3)]
    ss = [i.cx for i in ss]
    assert all(ss), 'fail: test_main_tPool'
