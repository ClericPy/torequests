#! coding:utf-8
import sys
import time

from torequests import *


def test_main_tPool():
    trequests = tPool()
    test_url = 'http://p.3.cn/prices/mgets?skuIds=J_1273500'
    ss = [trequests.get(test_url, retry=0, callback=lambda x:len(
        x.content)) for i in range(3)] 
    [i.x for i in ss]
    ss = [i.cx for i in ss]
    assert all(ss), 'fail: test_main_tPool'

# def test_main_ProcessPool():
#     def test(arg):
#         return arg**2
#     ppool = ProcessPool(2)
#     task = ppool.submit(test, 2)
#     assert task.x==4


# if __name__ == '__main__':
#     test_main_ProcessPool()







# ================================= PYTHON 3 only ========================


PY3 = (sys.version_info[0] == 3)
# tests for python3 only
if PY3:
    from .py3_features import *
