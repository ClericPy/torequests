# torequests

#### Using [tomorrow](https://github.com/madisonmay/Tomorrow) to make requests asynchronous.

The only reason to use is: nothing to learn & easy to use.(And it fits Windows.....Python 2/3 compatible)

[中文](#cn)

> To get the **Real Value**, use the **.x** property, but it will block the threads, so you can push the threads first but not use `.x` until really need the value.
> In other words, **`.x` should not be used until you need it**.

# Quick Start

```python
from torequests import tPool
import time


start_time = time.time()
trequests = tPool(30)  # you may use it without session either.
list1 = [trequests.get(url) for url in ['http://p.3.cn/prices/mgets?skuIds=J_1273600']*500]
# If failed, i.x may return False object by default, or you can reset the fail_return arg.
list2 = [len(i.x.content) if i.x else 'fail' for i in list1]
end_time = time.time()
print(list2[:10], '\ntimeused:%s s' % (end_time-start_time))

```

>result:[51, 51, 51, 51, 51, 51, 51, 51, 51, 51] 
timeused:0.929659366607666 s

# Tutorial

**first of all:**

>*pip install torequests -U*

## 1. tPool:
*make requests async(and retry/log)*

### The args:

num means Pool size; session is requests.Session; retry is the times when exception raised; retrylog is one bool object and determined whether show the log when retry occured; logging args will show what you want see when finished successfully; delay will run after some seconds, so it only fit float or int.

-------
#####Usage:

```python
from torequests import tPool
import requests

s = requests.Session()
trequests = tPool(30, session=s)  # you may use it without session either.
list1 = [trequests.get(url, timeout=1, retry=1, retrylog=1, fail_return=False, logging='finished') for url in ['http://127.0.0.1:8080/']*5]
list2 = [i.x.content if i.x else 'fail' for i in list1]
print(list2)
```

-------

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

-------
>PS:
http://127.0.0.1:8080/ is one server that route a function like:

```python
@app.get('/')
def function():
    aa=random.randint(0,1)
    if aa:
        print(aa)
        return 'success'
    time.sleep(5)
    return 'fail'
```

-------


As it's async, you can use print func as logging. 

## 2. threads & async:

>make functions asynchronous, no changing for original Tomorrow's threads.

#####Normal usage:

```python
# transform a function asynchronous

from torequests import async
async_function = async(old_function) # pool size is 30 for default, or set a new one async_function = async(old_function,40)
# this step will not block.
func_list = [async_function(i) for i in argvs] # or func_list = map(async_function, argvs)
# this step will block.
results = [i.x for i in func_list]


# original usage
from torequests import threads
newfunc = threads(10)(rawfunc)
# or Decorator, but it influences source function.

@threads(10)
def rawfunc():
    pass
```
> when you need the value returned by funtions, use `funtion().x`.

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
    html = [response.x.text for response in responses]
    end = time.time()
    print("Time: %f seconds" % (end - start))

# (time cost) Time: 2.321494 seconds

```

---------
<h2 id="cn">中文介绍</h2>
#### 借助 [tomorrow](https://github.com/madisonmay/Tomorrow) 使 [requests](https://github.com/kennethreitz/requests) 变得异步，并且加入更多功能（重试/默认错误返回值/log等）.

这个的唯一用处估计是比较无脑，并且还可以支持Windows吧。python2/3兼容。

>如果想返回 **真正的值（而不是Tomorrow对象）**, 通过使用 **.x** 属性即可, 但要注意的一点是，虽然函数执行是异步的，但通过.x得到返回值却会block住整个进程。所以简单的办法就是，一上来把所有函数都异步出去，用到谁再**点**谁。（我比较习惯用列表解析把函数全放进去，然后要用到谁了取出来.x，其他的还在继续跑，不耽误）。注：切忌一次异步出去七八万项，这每个都是个独立的线程，会悲剧的，先分段然后再执行比较妥当。

# 快速开始

```python
from torequests import tPool
import time


start_time = time.time()
trequests = tPool(30)  # you may use it without session either.
list1 = [trequests.get(url) for url in ['http://p.3.cn/prices/mgets?skuIds=J_1273600']*500]
# 如果函数执行失败（或超过重试次数）, i.x 默认会返回False对象, 除非你自定义去修改 fail_return 参数.
list2 = [len(i.x.content) if i.x else 'fail' for i in list1]
end_time = time.time()
print(list2[:10], '\ntimeused:%s s' % (end_time-start_time))

```

>result:[51, 51, 51, 51, 51, 51, 51, 51, 51, 51] 
timeused:0.929659366607666 s

# 简单使用

**当然是先** pip** 安装了:**

>*pip install torequests -U*

## 1. tPool:
*让原生的 requests 变的异步，并且支持重试等功能。*

### The args:

num 参数是指线程池大小（同时执行多少任务）; session 其实就是 requests.Session(); retry 参数指的是出错重试的次数; retrylog 是指当重试发生时是否打印出来; logging 参数就是完成时候打印出来; delay 参数很少使用，一般就是给个随机时间让它等待然后再执行（貌似没什么卵用）.

-------
#####用法:

```python
from torequests import tPool
import requests

s = requests.Session()
trequests = tPool(30, session=s)  # Session的好处是性能比每次都重新发送请求快，并且能保留Cookies等（但我基本从来没用过这参数）.
list1 = [trequests.get(url, timeout=1, retry=1, retrylog=1, fail_return=False, logging='finished') for url in ['http://127.0.0.1:8080/']*5]
list2 = [i.x.content if i.x else 'fail' for i in list1]
print(list2)
```

-------

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

-------
>PS:
http://127.0.0.1:8080/ 是我架的一个临时服务器，一般就是用来随机性地出错:

```python
@app.get('/')
def function():
    aa=random.randint(0,1)
    if aa:
        print(aa)
        return 'success'
    time.sleep(5)
    return 'fail'
```

-------

小贴士：由于这里的requests变成异步了，所以可以用 print 来查看进度。
注意：这里的异步只在请求的时候异步（因为这种I/O操作最费时），而取值的时候则不是，比如： 
```[trequests.get(url, timeout=1, retry=1, retrylog=1, fail_return=False, logging='finished').x for url in ['http://127.0.0.1:8080/']*5]```并不能异步来提高性能，换句话说，它变成串行执行了（所以平时我经常拿单个的代替原生的 requests …）。

## 2. threads & async:
 
>这两个就是 Tomorrow 的神奇之处了，用法和原生的没什么区别。简而言之就是把普通函数变成异步函数，你**把它撒出去它就是异步的非阻塞状态，直到你要取它的返回值**。

#####Normal usage:

```python
from torequests import async
async_function = async(old_function) # 线程池大小默认30，也可以设置个40 async_function = async(old_function,40)
# 这一步非阻塞.
func_list = [async_function(i) for i in argvs] # or func_list = map(async_function, argvs)
# 下一步开始阻塞.
results = [i.x for i in func_list]


# 原生用法
from torequests import threads
# 这个用法用的是新函数，不会影响到原来的函数
newfunc = threads(10)(rawfunc)

# 也可以用修饰器，但是会对原函数造成影响。
@threads(10)
def rawfunc():
    pass
```
> 函数执行时候非阻塞，会直接跳过去，直到你调用它的返回值 —— `funtion().x`.

##### demo:

```python
import time
import requests
import sys
from torequests import threads, async
s = requests.Session()
counting = 0
# @threads(10) # 这里可以用原生的修饰器方法
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
    dd = async(download)  # 其实就是 threads(30)(download)，但这样子更好看，虽然可能和python3.5关键词重名
    responses = [dd(url) for url in urls]
    html = [response.x.text for response in responses]
    end = time.time()
    print("Time: %f seconds" % (end - start))

# (耗费时间) Time: 2.321494 seconds

```