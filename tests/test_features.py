#! coding:utf-8
import sys

import torequests
from torequests.logs import print_info


def test_main_tPool():
    trequests = torequests.tPool(2, 1)
    test_url = "http://p.3.cn"
    tasks = [
        trequests.get(test_url,
                      retry=2,
                      callback=lambda x: print_info(i) or len(x.content),
                      retry_interval=1,
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
    assert not trequests.get(
        'http://httpbin.org/status/206',
        response_validator=lambda r: r.status_code == 200).x


def test_sync_frequency():
    from torequests.frequency_controller.sync_tools import Frequency
    from concurrent.futures import ThreadPoolExecutor
    from time import time

    # limit to 2 concurrent tasks each 1 second
    frequency = Frequency(2, 1)

    def test():
        with frequency:
            return time()

    now = time()
    pool = ThreadPoolExecutor()
    tasks = []
    for _ in range(5):
        tasks.append(pool.submit(test))
    result = [task.result() for task in tasks]
    assert result[0] - now <= 1
    assert result[1] - now <= 1
    assert result[2] - now >= 1
    assert result[3] - now >= 1
    assert result[4] - now >= 2
    assert frequency.to_dict() == {'n': 2, 'interval': 1}
    assert frequency.to_list() == [2, 1]


def test_workshop():
    import time
    from torequests.main import Workshop

    def callback(todo, worker_arg):
        if worker_arg == 'worker1':
            return None
        time.sleep(todo / 10)
        return todo

    fc = Workshop(range(1, 10), ['worker1', 'worker2', 'worker3'], callback)

    assert fc.run() == list(range(1, 10))
    assert fc.run(as_completed=True) != list(range(1, 10))


# ================================= PYTHON 3 only ========================

PY3 = sys.version_info[0] == 3
# tests for python3 only
if PY3:
    from ._test_py3_features import *
