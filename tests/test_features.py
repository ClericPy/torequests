#! coding:utf-8
import sys
import time

from torequests import *
from torequests.process import Process


def test_main_tPool():
    trequests = tPool()
    test_url = 'http://p.3.cn/prices/mgets?skuIds=J_1273500'
    ss = [trequests.get(test_url, retry=0, callback=lambda x:len(
        x.content)) for i in range(3)]
    [i.x for i in ss]
    ss = [i.cx for i in ss]
    assert all(ss), 'fail: test_main_tPool'

def proc_function():
    print('start')
    time.sleep(1.5)
    print('finish')
    return 'ok'

def test_process(capsys):
    '''  test_dummy_Requests_time_interval_sem_run_forever '''

    with capsys.disabled():

        f1 = Process(proc_function, timeout=0.5)
        f2 = Process(proc_function, timeout=2)
        f1_result = f1().x
        f2_result = f2().x
        print(f1_result, f2_result)
        assert isinstance(f1_result, Exception)
        assert bool(f2_result)


# ================================= PYTHON 3 only ========================


PY3 = (sys.version_info[0] == 3)
# tests for python3 only
if PY3:
    from .py3_features import *
