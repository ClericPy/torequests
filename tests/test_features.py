#! coding:utf-8
import sys

import torequests
from torequests.logs import print_info


def test_main_tPool():
    trequests = torequests.tPool(2, 1)
    test_url = "http://p.3.cn"
    tasks = [
        trequests.get(
            test_url,
            retry=2,
            callback=lambda x: print_info(i) or len(x.content),
            referer_info=i) for i in range(3)
    ]
    # [i.x for i in ss]
    trequests.x
    cb_results = [i.cx for i in tasks]
    assert tasks[-1].task_cost_time > 1
    assert all(cb_results), "fail: test_main_tPool"
    assert tasks[0].referer_info == 0
    r = torequests.get(test_url, retry=1, timeout=3)
    assert "Welcome to nginx!" in r.text


# ================================= PYTHON 3 only ========================

PY3 = sys.version_info[0] == 3
# tests for python3 only
if PY3:
    from .py3_features import *
