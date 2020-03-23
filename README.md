# [torequests](https://github.com/ClericPy/torequests) [![PyPI](https://img.shields.io/pypi/v/torequests?style=plastic)](https://pypi.org/project/torequests/)[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/clericpy/torequests/Python%20package?style=plastic)](https://github.com/ClericPy/torequests/actions?query=workflow%3A%22Python+package%22)![PyPI - Wheel](https://img.shields.io/pypi/wheel/torequests?style=plastic)![PyPI - Python Version](https://img.shields.io/pypi/pyversions/torequests?style=plastic)![PyPI - Downloads](https://img.shields.io/pypi/dm/torequests?style=plastic)![PyPI - License](https://img.shields.io/pypi/l/torequests?style=plastic)

<!-- [![Downloads](https://pepy.tech/badge/torequests)](https://pepy.tech/project/torequests) -->

Briefly speaking, requests & aiohttp wrapper for asynchronous programming rookie, to shorten the code quantity. 

## Install:

> pip install torequests -U

#### requirements

##### python2.7 / python3.6+

    | requests			# python
    | futures 			# python2
    | aiohttp >= 3.0.5 	# python3
    | uvloop  			# python3

**optional:**

    | psutil
    | rapidfuzz
    | pyperclip

## Features

Inspired by [tomorrow](https://github.com/madisonmay/Tomorrow), to make async-coding brief & smooth, compatible for win32 / python 2&3.

* Convert any funtions into async-mode with concurrent.futures.
* Wrap requests lib with concurrent.futures to enjoy the concurrent performance.
* Simplify aiohttp, make it `requests-like`.
* Add FailureException to check the context of request failure.
* Add frequency control, prevent from anti-spider based on frequency check.
* Add retry for request.
* Alenty of common crawler utils.
* Compatible with [uniparser]( https://github.com/ClericPy/uniparser )

## Getting started

### 1. Async, threads - make functions asynchronous

```python
from torequests import threads, Async
import time


@threads(5)
def test1(n):
    time.sleep(n)
    return 'test1 ok'


def test2(n):
    time.sleep(n)
    return 'test1 ok'


start = int(time.time())
# here async_test2 is same as test1
async_test2 = Async(test2)
future = test1(1)
# future run in non blocking thread pool
print(future, ', %s s passed' % (int(time.time() - start)))
# call future.x will block main thread and get the future.result()
print(future.x, ', %s s passed' % (int(time.time() - start)))
# output:
# <NewFuture at 0x34b1d30 state=running> , 0 s passed
# test1 ok , 1 s passed
```
### 2. tPool - thread pool for async-requests

```python
from torequests.main import tPool
from torequests.logs import print_info
from torequests.utils import ttime

req = tPool()
test_url = 'http://p.3.cn'


def callback(task):
    return (len(task.content),
            print_info(
                ttime(task.task_start_time), '-> ', ttime(task.task_end_time),
                ',', round(task.task_cost_time * 1000), 'ms'))


ss = [req.get(test_url, retry=2, callback=callback) for i in range(3)]
# or [i.x for i in ss]
req.x
# task.cx returns the callback_result
ss = [i.cx for i in ss]
print_info(ss)
# [2020-01-21 16:56:23] temp_code.py(11): 2020-01-21 16:56:23 ->  2020-01-21 16:56:23 , 54 ms
# [2020-01-21 16:56:23] temp_code.py(11): 2020-01-21 16:56:23 ->  2020-01-21 16:56:23 , 55 ms
# [2020-01-21 16:56:23] temp_code.py(11): 2020-01-21 16:56:23 ->  2020-01-21 16:56:23 , 57 ms
# [2020-01-21 16:56:23] temp_code.py(18): [(612, None), (612, None), (612, None)]

```

#### 2.1 Performance.

```verilog
[3.7.1 (v3.7.1:260ec2c36a, Oct 20 2018, 14:57:15) [MSC v.1915 64 bit (AMD64)]]: 2000 / 2000, 100.0%, cost 4.2121 seconds, 475.0 qps.
[2.7.15 (v2.7.15:ca079a3ea3, Apr 30 2018, 16:30:26) [MSC v.1500 64 bit (AMD64)]]: 2000 / 2000, 100%, cost 9.4462 seconds, 212.0 qps.
```

```python
import timeit
from torequests import tPool
import sys

req = tPool()
start_time = timeit.default_timer()
oks = 0
total = 2000
# concurrent all the tasks
tasks = [req.get('http://127.0.0.1:8080') for num in range(total)]
for task in tasks:
    r = task.x
    if r.text == 'ok':
        oks += 1
end_time = timeit.default_timer()
succ_rate = oks * 100 / total
cost_time = round(end_time - start_time, 4)
version = sys.version
qps = round(total / cost_time, 0)
print(
    '[{version}]: {oks} / {total}, {succ_rate}%, cost {cost_time} seconds, {qps} qps.'
    .format(**vars()))
```

### 3. Requests - aiohttp-wrapper

```python
from torequests.dummy import Requests
from torequests.logs import print_info
from torequests.utils import ttime
req = Requests(frequencies={'p.3.cn': (2, 1)})


def callback(task):
    return (len(task.content),
            print_info(
                ttime(task.task_start_time), '->', ttime(task.task_end_time),
                ',', round(task.task_cost_time * 1000), 'ms'))


ss = [
    req.get('http://p.3.cn', retry=1, timeout=5, callback=callback)
    for i in range(4)
]
req.x  # this line can be removed
ss = [i.cx for i in ss]
print_info(ss)
# [2020-01-21 18:15:33] temp_code.py(11): 2020-01-21 18:15:32 -> 2020-01-21 18:15:33 , 1060 ms
# [2020-01-21 18:15:33] temp_code.py(11): 2020-01-21 18:15:32 -> 2020-01-21 18:15:33 , 1061 ms
# [2020-01-21 18:15:34] temp_code.py(11): 2020-01-21 18:15:32 -> 2020-01-21 18:15:34 , 2081 ms
# [2020-01-21 18:15:34] temp_code.py(11): 2020-01-21 18:15:32 -> 2020-01-21 18:15:34 , 2081 ms
# [2020-01-21 18:15:34] temp_code.py(20): [(612, None), (612, None), (612, None), (612, None)]
```

#### 3.1 Performance.

>  aiohttp is almostly 3 times faster than requests + ThreadPoolExecutor, even without uvloop on windows10.

```verilog
3.7.1 (v3.7.1:260ec2c36a, Oct 20 2018, 14:57:15) [MSC v.1915 64 bit (AMD64)]
sync_test: 2000 / 2000, 100.0%, cost 1.2965 seconds, 1543.0 qps.
async_test: 2000 / 2000, 100.0%, cost 1.2834 seconds, 1558.0 qps.

Sync usage has little performance lost.
```

```python
import asyncio
import sys
import timeit

from torequests.dummy import Requests


def sync_test():
    with Requests() as req:
        start_time = timeit.default_timer()
        oks = 0
        total = 2000
        # concurrent all the tasks
        tasks = [req.get('http://127.0.0.1:8080') for num in range(total)]
        req.x
        for task in tasks:
            if task.text == 'ok':
                oks += 1
        end_time = timeit.default_timer()
        succ_rate = oks * 100 / total
        cost_time = round(end_time - start_time, 4)
        qps = round(total / cost_time, 0)
        print(
            f'sync_test: {oks} / {total}, {succ_rate}%, cost {cost_time} seconds, {qps} qps.'
        )


async def async_test():
    req = Requests()
    async with Requests() as req:
        start_time = timeit.default_timer()
        oks = 0
        total = 2000
        # concurrent all the tasks
        tasks = [req.get('http://127.0.0.1:8080') for num in range(total)]
        for task in tasks:
            r = await task
            if r.text == 'ok':
                oks += 1
        end_time = timeit.default_timer()
        succ_rate = oks * 100 / total
        cost_time = round(end_time - start_time, 4)
        qps = round(total / cost_time, 0)
        print(
            f'async_test: {oks} / {total}, {succ_rate}%, cost {cost_time} seconds, {qps} qps.'
        )


if __name__ == "__main__":
    print(sys.version)
    sync_test()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_test())

```

#### 3.2 using torequests.dummy.Requests in async environment.

```python
import asyncio

import uvicorn
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from torequests.dummy import Requests

api = Starlette()
api.req = Requests()


@api.route('/')
async def index(req):
    # await for Response or FailureException
    r = await api.req.get('http://p.3.cn', timeout=(1, 1))
    return PlainTextResponse(r.content)


if __name__ == "__main__":
    uvicorn.run(api)

```

### 4. utils: some useful crawler toolkits

    ClipboardWatcher: watch your clipboard changing.
    Counts: counter while every time being called.
    Null: will return self when be called, and alway be False.
    Regex: Regex Mapper for string -> regex -> object.
    Saver: simple object persistent toolkit with pickle/json.
    Timer: timing tool.
    UA: some common User-Agents for crawler.
    curlparse: translate curl-string into dict of request.
    md5: str(obj) -> md5_string.
    print_mem: show the proc-mem-cost with psutil, use this only for lazinesssss.
    ptime: %Y-%m-%d %H:%M:%S -> timestamp.
    ttime: timestamp -> %Y-%m-%d %H:%M:%S
    slice_by_size: slice a sequence into chunks, return as a generation of chunks with size.
    slice_into_pieces: slice a sequence into n pieces, return a generation of n pieces.
    timeago: show the seconds as human-readable.
    unique: unique one sequence.
    find_one: use regex like Javascript to find one string with index(like [0], [1]).
    ...


## Benchmarks
> Benchmark of concurrent is not very necessary and accurate, just take a look.

### Test Server: golang net/http

Source code: [go_test_server.go](https://github.com/ClericPy/torequests/blob/master/benchmarks/go_test_server.go)

### Client Testing Code

Source code: [py_test_client.py](https://github.com/ClericPy/torequests/blob/master/benchmarks/py_test_client.py)

### Test Result on Windows

```verilog
Test without uvloop, 12 logical CPUs.
Windows-10-10.0.18362-SP0
3.7.1 (v3.7.1:260ec2c36a, Oct 20 2018, 14:57:15) [MSC v.1915 64 bit (AMD64)]
================================================================================
test_aiohttp(3.6.2)      : 2000 / 2000 = 100.0%, cost 1.158s, 1727 qps, 100.0% standard.
test_dummy(4.9.4)        : 2000 / 2000 = 100.0%, cost  1.25s, 1600 qps, 92.65% standard.
test_httpx(0.11.1)       : 2000 / 2000 = 100.0%, cost 3.927s, 509 qps, 29.47% standard.
test_tPool(4.9.4)        : 2000 / 2000 = 100.0%, cost 4.754s, 421 qps, 24.38% standard.
```

### Test Result on Linux

```verilog
Test with uvloop, 1 logical CPUs.
Linux-4.15.0-13-generic-x86_64-with-Ubuntu-18.04-bionic
3.7.3 (default, Apr  3 2019, 19:16:38)
[GCC 8.0.1 20180414 (experimental) [trunk revision 259383]]
================================================================================
test_aiohttp(3.6.2)      : 2000 / 2000 = 100.0%, cost 0.698s, 2866 qps, 100.0% standard.
test_dummy(4.8.21)       : 2000 / 2000 = 100.0%, cost 0.874s, 2288 qps, 79.83% standard.
test_httpx(0.11.1)       : 2000 / 2000 = 100.0%, cost 2.337s, 856 qps, 29.87% standard.
test_tPool(4.8.21)       : 2000 / 2000 = 100.0%, cost 3.029s, 660 qps, 23.03% standard.
```

### Conclusion

1. **aiohttp** is the fastest, for the cython utils
   1. aiohttp's qps is 2866 on 1 cpu linux with uvloop, near to golang's 3300.
2. **torequests.dummy.Requests** based on **aiohttp**.
   1. about **2~10%** performance lost **without** uvloop.
   2. about **20%** performance lost with uvloop.
3. **httpx** is faster than **requests + Thread,** but not very obviously.

#### PS

**golang - net/http** 's performance

```
`2000 / 2000, 100.00 %, cost 0.26 seconds, 7567.38 qps` on windows (12 cpus)
`2000 / 2000, 100.00 %, cost 0.61 seconds, 3302.48 qps` on linux (1 cpu)
   1. slower than windows, because golang benefit from multiple CPU count
   2. linux 1 cpu, but windows is 12
```

**golang http client testing code:**

[go_test_client.go](https://github.com/ClericPy/torequests/blob/master/benchmarks/go_test_client.go)

## Documentation
> [Document & Usage](https://torequests.readthedocs.io/en/latest/)

## License
> [MIT license](LICENSE)
