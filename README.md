# torequests  - v4.1.0

Briefly speaking, requests / aiohttp wrapper for asynchronous programming rookie, to shorten the code quantity. 

> warn: v4.1.0 is not backwardly compatible with old version in about some args and function name.

### Features

Inspired by [tomorrow](https://github.com/madisonmay/Tomorrow), to make async-coding brief & smooth, compatible for win32, python 2/3.

* convert funtions into async-mode with concurrent.futures
* convert requests module too...
* simplify aiohttp and make it requests-like

### Getting started

#### Async, threads - make functions asynchronous

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
#### tPool - thread pool for requests
```python
from torequests import tPool
import time

start_time = time.time()
trequests = tPool()
list1 = [trequests.get('http://127.0.0.1:5000/test/%s'%num) for num in range(5000)]
# If failed, i.x may return False by default,
# or you can reset the fail_return arg.
list2 = [i.x.text if i.x else 'fail' for i in list1]
end_time = time.time()
print(list2[:5], '\n5000 requests time cost:%s s' % (end_time - start_time))
# output:
# ['ok 0', 'ok 1', 'ok 2', 'ok 3', 'ok 4'] 
# 5000 requests time cost:10.918817281723022 s
```

#### Requests - aiohttp-wrapper
> uvloop cost about 3.8s per 5000 requests; win32 5.78s per 5000 requests.
```python
from torequests.dummy import Requests
import time

start_time = time.time()
trequests = Requests()
list1 = [trequests.get('http://127.0.0.1:5000/test/%s'%num) for num in range(5000)]
# If failed, i.x may return False by default,
# or you can reset the fail_return arg.
list2 = [i.x.text if i.x else 'fail' for i in list1]
end_time = time.time()
print(list2[:5], '\n5000 requests time cost:%s s' % (end_time - start_time))
# output:
# win32, without uvloop; 
# ['ok 0', 'ok 1', 'ok 2', 'ok 3', 'ok 4'] 
# 5000 requests time cost:5.776089191436768 s
```

> mock server

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

### Requirement
> pip install torequests -U
- requests
- future(python2.x only)
- aiohttp(python3.5+ only)

### Documentation
> To be continued...

### License
> do I need one?

### Benchmarks
> What's this......