# torequests

#### Using [tomorrow](https://github.com/madisonmay/Tomorrow) to make requests async, but not fit python2.x any more( by intention ).

The only reason to use it is: nothing to learn & easy to use.(And it can run on windows.....)

By the way, if you want to get the true value instead of "Tomorrow" class, sometimes you can use __rmul__(1) method.Then, <torequests.Tomorrow object at 0x03922F70> can be transform to the real value.

# Tutorial

first of all:
>pip install torequests -U

## tPool:

>make requests async(and retry/log)

### The args:
num means Pool size; session is requests.Session; retry is the times when exception raised; retrylog is one bool object and determined whether show the log when retry occured; logging args will show what you want see when finished successfully; delay will run after some seconds, so it only fit float or int.

========================
#####Usage:

```python
from torequests import tPool
import requests
s = requests.Session()
trequests = tPool(30, session = s) # you may use it without session either.
list1 = [trequests.get(url, timeout=1, retry=1, retrylog=1, logging='finished') for url in ['http://127.0.0.1:8080/']*5]
list2 = [i.content if i.__bool__() else 'fail' for i in list1]
print(list2)
```

========================

result:

```
http://127.0.0.1:8080/ finished
http://127.0.0.1:8080/ finished
http://127.0.0.1:8080/ finished
retry http://127.0.0.1:8080/ for the 1 time, as the Exception: HTTPConnectionPool(host='127.0.0.1', port=8080): Read timed out. (read timeout=1)
retry http://127.0.0.1:8080/ for the 1 time, as the Exception: HTTPConnectionPool(host='127.0.0.1', port=8080): Read timed out. (read timeout=1)
http://127.0.0.1:8080/ finished
retry http://127.0.0.1:8080/ for the 2 time, as the Exception: HTTPConnectionPool(host='127.0.0.1', port=8080): Read timed out. (read timeout=1)
[b'success', b'success', b'success', b'success', 'fail']
```

========================
>PS:
http://127.0.0.1:8080/ is one server that route a function like:

```python
    aa=random.randint(0,1)
    if aa:
        print(aa)
        return 'success'
    time.sleep(5)
    return 'fail'
```

========================
as you see, only the requests.get is async.


## pPool:

> tomorrow style multiprocessing.dummy.Pool

Using tomorrow to generate an async Pool like gevent.pool.Pool or multiprocessing.dummy.Pool, no need for close.

```python
from torequests import pPool
pp=pPool(30)
ss=list(pp.map(func, argvs,autocheck=1))
```

========================

Autocheck means return the real response instead of Tomorrow Class.
As it's async, you can use print func as logging. 

## threads:

>make any functions asynchronous

no changing for original Tomorrow's threads

#####Normal usage:

```python

# transform a function asynchronous
from torequests import async
async_function = async(old_function) 
# pool size is 30 for default, or set a new one like
# async_function = async(old_function,40) # or async_function = async(old_function, n=40)


# original usage
from torequests import threads

newfunc = threads(10)(rawfunc)

# or Decorator, but it influenced raw func.

@threads(10)
def rawfunc():
	pass


```

##### demo:

```python
import time
import requests
import sys
from torequests import threads, async
s = requests.Session()
counting = 0

# @threads(10) # the Decorator style
def download(url):
    global counting
    for _ in range(5):
        try:
            aa = s.get(url)
            counting += 1
            sys.stderr.write('%s  \r' % counting) 
            break
        except:
            pass
    return aa
urls = ['http://p.3.cn/prices/mgets?skuIds=J_1273600']*1000
if __name__ == "__main__":
    start = time.time()
    dd = async(download)  # no difference to threads(30)(download)
    responses = [dd(url) for url in urls]
    html = [response.text for response in responses]
    end = time.time()
    print("Time: %f seconds" % (end - start))

# (time cost) Time: 2.321494 seconds

```

========================



========================


[More readme](README1.md)



