#! coding:utf-8
import sys
import time

import torequests


def test_main_tPool():
    trequests = torequests.tPool()
    test_url = 'http://p.3.cn'
    ss = [
        trequests.get(test_url, retry=2, callback=lambda x: len(x.content))
        for i in range(3)
    ]
    # [i.x for i in ss]
    trequests.x
    ss = [i.cx for i in ss]
    assert all(ss), 'fail: test_main_tPool'
    r = torequests.get(test_url, retry=1, timeout=3)
    assert 'Welcome to nginx!' in r.text


# ================================= PYTHON 3 only ========================

PY3 = (sys.version_info[0] == 3)
# tests for python3 only
if PY3:
    from .py3_features import *
