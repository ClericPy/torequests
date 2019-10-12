# [torequests](https://github.com/ClericPy/torequests)

Briefly speaking, requests / aiohttp wrapper for asynchronous programming rookie, to shorten the code quantity. 

## To install:

> pip install torequests -U

**requirements:**

    | requests
    | futures # python2
    | aiohttp >= 3.0.5 # python3
    | uvloop  # python3
    | jsonpath_rw_ext
    | lxml
    | cssselect
    | objectpath

**optional:**

    | psutil
    | fuzzywuzzy
    | python-Levenshtein
    | pyperclip

## Features

Inspired by [tomorrow](https://github.com/madisonmay/Tomorrow), to make async-coding brief & smooth, compatible for win32 / python 2&3.

* convert any funtions into async-mode with concurrent.futures
* wrap requests module in future...
* simplify aiohttp, make it `requests-like`.
* some crawler toolkits.

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

#### 2.1 Test the performance (win32+python3.7).

```python
from torequests import tPool
import time

start_time = time.time()
trequests = tPool()
list1 = [
    trequests.get('http://127.0.0.1:5000/test/%s' % num) for num in range(5000)
]
# If failed, i.x may return False by default,
# or you can reset the fail_return arg.
list2 = [i.x.text if i.x else 'fail' for i in list1]
end_time = time.time()
print(list2[:5], '\n5000 requests time cost: %s s' % (end_time - start_time))
# output:
# ['test ok 0', 'test ok 1', 'test ok 2', 'test ok 3', 'test ok 4'] 
# 5000 requests time cost: 5.906721591949463 s
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

#### 3.1 win32+python3.7 cost 3.9s per 5000 requests, which may be much faster with uvloop.

```python
from torequests.dummy import Requests
import time

start_time = time.time()
trequests = Requests()
list1 = [
    trequests.get('http://127.0.0.1:5000/test/%s' % num) for num in range(5000)
]
# If failed, i.x may return False by default,
# or you can reset the fail_return arg.
list2 = [i.x.text if i.x else 'fail' for i in list1]
end_time = time.time()
print(list2[:5], '\n5000 requests time cost:%s s' % (end_time - start_time))
# output:
# win32, without uvloop;
# ['test ok 0', 'test ok 1', 'test ok 2', 'test ok 3', 'test ok 4'] 
# 5000 requests time cost:3.909820079803467 s
```

#### 3.2 using torequests.dummy.Requests in async environment.

```python
import asyncio

from responder import API
from torequests.dummy import Requests

loop = asyncio.get_event_loop()
api = API()


@api.route('/')
async def index(req, resp):
    # await for request or FailureException
    r = await api.req.get('http://p.3.cn', timeout=(1, 1))
    print(r)
    if r:
        # including good request with status_code between 200 and 299
        resp.text = 'ok' if 'Welcome to nginx!' in r.text else 'bad'
    else:
        resp.text = 'fail'


if __name__ == "__main__":
    api.req = Requests(loop=loop)
    api.run(port=5000, loop=loop)
```

#### 3.3 mock server source code

```python
from gevent.monkey import patch_all
patch_all()
import bottle
app = bottle.Bottle()
@app.get('/test/<num>')
def test(num):
    return 'ok %s' % num
app.run(server='gevent', port=5000)
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
