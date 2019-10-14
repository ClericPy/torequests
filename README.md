# [torequests](https://github.com/ClericPy/torequests) [![Build Status](https://travis-ci.org/ClericPy/torequests.svg?branch=master)](https://travis-ci.org/ClericPy/torequests)[![PyPI version](https://badge.fury.io/py/torequests.svg)](https://badge.fury.io/py/torequests)

Briefly speaking, requests & aiohttp wrapper for asynchronous programming rookie, to shorten the code quantity. 

## Install:

> pip install torequests -U

#### requirements

##### python2.7 / python3.6+

    | requests
    | futures # python2
    | aiohttp >= 3.0.5 # python3
    | uvloop  # python3

**optional:**

    | jsonpath_rw_ext
    | lxml
    | cssselect
    | objectpath
    | psutil
    | fuzzywuzzy
    | python-Levenshtein
    | pyperclip

## Features

Inspired by [tomorrow](https://github.com/madisonmay/Tomorrow), to make async-coding brief & smooth, compatible for win32 / python 2&3.

* convert any funtions into async-mode with concurrent.futures.
* wrap requests lib with concurrent.futures.
* simplify aiohttp, make it `requests-like`.
* add failure request class, add frequency control.
* plenty of crawler utils.

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

req = tPool()
test_url = 'http://p.3.cn'
ss = [
    req.get(
        test_url,
        retry=2,
        callback=lambda x: (len(x.content), print_info(len(x.content))))
    for i in range(3)
]
# or [i.x for i in ss]
req.x
ss = [i.cx for i in ss]
print_info(ss)

# [2019-04-01 00:19:07] temp_code.py(10): 612
# [2019-04-01 00:19:07] temp_code.py(10): 612
# [2019-04-01 00:19:07] temp_code.py(10): 612
# [2019-04-01 00:19:07] temp_code.py(16): [(612, None), (612, None), (612, None)]

```

#### 2.1 Performance.

```verilog
[3.7.1 (v3.7.1:260ec2c36a, Oct 20 2018, 14:57:15) [MSC v.1915 64 bit (AMD64)]]: 2000 / 2000, 100.0%, cost 4.5911 seconds, 436.0 qps.
[2.7.15 (v2.7.15:ca079a3ea3, Apr 30 2018, 16:30:26) [MSC v.1500 64 bit (AMD64)]]: 2000 / 2000, 100%, cost 9.3587 seconds, 214.0 qps.
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
tasks = [req.get('http://127.0.0.1:9090') for num in range(total)]
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
trequests = Requests(frequencies={'p.3.cn': (2, 2)})
ss = [
    trequests.get(
        'http://p.3.cn', retry=1, timeout=5,
        callback=lambda x: (len(x.content), print_info(trequests.frequencies)))
    for i in range(4)
]
trequests.x
ss = [i.cx for i in ss]
print_info(ss)

# [2019-04-01 00:16:35] temp_code.py(7): {'p.3.cn': Frequency(sem=<1/2>, interval=2)}
# [2019-04-01 00:16:35] temp_code.py(7): {'p.3.cn': Frequency(sem=<0/2>, interval=2)}
# [2019-04-01 00:16:37] temp_code.py(7): {'p.3.cn': Frequency(sem=<2/2>, interval=2)}
# [2019-04-01 00:16:37] temp_code.py(7): {'p.3.cn': Frequency(sem=<2/2>, interval=2)}
# [2019-04-01 00:16:37] temp_code.py(12): [<NewResponse [200]>, <NewResponse [200]>, <NewResponse [200]>, <NewResponse [200]>]

```

#### 3.1 Performance.

>  aiohttp is almostly 3 times faster than requests + ThreadPoolExecutor, even without uvloop on windows10.

```verilog
3.7.1 (v3.7.1:260ec2c36a, Oct 20 2018, 14:57:15) [MSC v.1915 64 bit (AMD64)]
sync_test: 2000 / 2000, 100.0%, cost 1.7625 seconds, 1135.0 qps.
async_test: 2000 / 2000, 100.0%, cost 1.7321 seconds, 1155.0 qps.
```

```python
import asyncio
import sys
import timeit

from torequests.dummy import Requests


def sync_test():
    req = Requests()
    start_time = timeit.default_timer()
    oks = 0
    total = 2000
    # concurrent all the tasks
    tasks = [req.get('http://127.0.0.1:9090') for num in range(total)]
    for task in tasks:
        r = task.x
        if r.text == 'ok':
            oks += 1
    end_time = timeit.default_timer()
    succ_rate = oks * 100 / total
    cost_time = round(end_time - start_time, 4)
    qps = round(total / cost_time, 0)
    print(
        'sync_test: {oks} / {total}, {succ_rate}%, cost {cost_time} seconds, {qps} qps.'
        .format(**vars()))


async def async_test():
    req = Requests()
    start_time = timeit.default_timer()
    oks = 0
    total = 2000
    # concurrent all the tasks
    tasks = [req.get('http://127.0.0.1:9090') for num in range(total)]
    for task in tasks:
        r = await task
        if r.text == 'ok':
            oks += 1
    end_time = timeit.default_timer()
    succ_rate = oks * 100 / total
    cost_time = round(end_time - start_time, 4)
    qps = round(total / cost_time, 0)
    print(
        'async_test: {oks} / {total}, {succ_rate}%, cost {cost_time} seconds, {qps} qps.'
        .format(**vars()))


if __name__ == "__main__":
    print(sys.version)
    sync_test()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_test())

```

#### 3.2 using torequests.dummy.Requests in async environment.

> ensure the loop is unique.

```python
import asyncio

import uvicorn
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from torequests.dummy import Requests

loop = asyncio.get_event_loop()
api = Starlette()


@api.route('/')
async def index(req):
    if not hasattr(api, 'req'):
        # or use `loop` arg to init Requests in globals
        api.req = Requests()
    # await for request or FailureException
    r = await api.req.get('http://p.3.cn', timeout=(1, 1))
    print(r)
    if r:
        # including good request with status_code between 200 and 299
        text = 'ok' if 'Welcome to nginx!' in r.text else 'bad'
    else:
        text = 'fail'
    return PlainTextResponse(text)

if __name__ == "__main__":
    uvicorn.run(api)
```

#### 3.3 mock server source code

```python
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse

app = Starlette()


@app.route("/")
async def source_redirect(req):
    return PlainTextResponse('ok')


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=9090)
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


## Documentation
> [Document & Usage](https://torequests.readthedocs.io/en/latest/)

## License
> [MIT license](LICENSE)

## Benchmarks
> to be continued......
