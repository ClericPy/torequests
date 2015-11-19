# torequests
####Using tomorrow to make requests async
## The only reason to use it is: nothing to learn & easy to use.

Source URL: https://github.com/ClericPy/torequests

>for python3.x, but tPool may not be fit for python2.x......

>Thanks to https://github.com/madisonmay/Tomorrow, requests could run fast in python3 and need to learn no more than requests-doc.

For first

>pip install torequests

Obviously, use it like :
```python
from torequests import tPool as Pool
requests = Pool(30)
```
or 
```python
import torequests
print(help(torequests))
```
then use requests.get/post/put/head/delete/ as usual.
so, this does support Session...

curio sames awosome and difficult，multiprocessing.dummy and pool.map is non-3rd-library but I don't like it even using it much time，requests said never support async（such like asyncio）， aiohttp not easy like requests, gevent hates Windows, twisted hard to study and no good for py3, grab seems good, scrapy seems to abandon py3, god ,I have try so much and deserve so many failures.........


一句话，就是给requests简单异步包装一下
####用法：
```python
from torequests import tPool as Pool
requests = Pool(30)
```
or 
```python
import torequests
print(help(torequests))
```
然后requests正常用就行了，支持Session什么的，就只是简单的requests.get加几个参数，可以命名成trequest，和原生requests分开混着用，原生的requests就用multiprocessing.dummy吧。。。（后来把tomorrow包装的叫tPool，multiprocessing.dummy包装的叫mPool，后者只是多线程处理下urls。。。)

#Example：

Try it yourself:

========================================
```python
from torequests import mPool
from torequests import tPool
import requests
import time

# requests in single thread
print('##### requests in single thread for 100 work')
aa = time.time()
ss = [requests.get(url)
      for url in ['http://p.3.cn/prices/mgets?skuIds=J_1273600'] * 100]
ss = [len(i.text) for i in ss]
print(ss[-10:],'\n')
print('>',time.time() - aa, 's\n')


# no Session multitreads
print('##### no Session multitreads for 1000 work')
aa = time.time()
mrequests = mPool(50)
ss = mrequests.get(['http://p.3.cn/prices/mgets?skuIds=J_1273600'] * 1000)
ss = [len(i.text) for i in ss]
print(ss[-10:],'\n')
print('>',time.time() - aa, 's\n')

# no Session tomorrow
print('##### no Session tomorrow for 1000 work')

aa = time.time()
trequests = tPool(50)
ss = [trequests.get(url) for url in [
    'http://p.3.cn/prices/mgets?skuIds=J_1273600'] * 1000]
ss = [len(i.text) for i in ss]
print(ss[-10:],'\n')
print('>',time.time() - aa, 's\n')


# with Session multitreads
print('##### with Session multitreads for 1000 work')

aa = time.time()
s = requests.Session()
mrequests = mPool(50, session=s)
ss = mrequests.get(['http://p.3.cn/prices/mgets?skuIds=J_1273600'] * 1000)
ss = [len(i.text) for i in ss]
print(ss[-10:],'\n')
print('>',time.time() - aa, 's\n')

# with Session tomorrow
print('##### with Session tomorrow for 1000 work')
aa = time.time()
s = requests.Session()
trequests = tPool(50, session=s)
ss = [trequests.get(url) for url in [
    'http://p.3.cn/prices/mgets?skuIds=J_1273600'] * 1000]
ss = [len(i.text) for i in ss]
print(ss[-10:],'\n')
print('>',time.time() - aa, 's\n')
```

=======
### no Session multitreads
[51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51]

1.1978464126586914 s

### no Session tomorrow
[51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51]

0.10907530784606934 s

### with Session multitreads
[51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51]

0.31622314453125 s

### with Session tomorrow
[51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51]

0.08806300163269043 s

===============================

##### requests in single thread for 100 work
[51, 51, 51, 51, 51, 51, 51, 51, 51, 51] 

> 1.8863472938537598 s

##### no Session multitreads for 1000 work
[51, 51, 51, 51, 51, 51, 51, 51, 51, 51] 

> 2.6028215885162354 s

##### no Session tomorrow for 1000 work
[51, 51, 51, 51, 51, 51, 51, 51, 51, 51] 

> 2.633859872817993 s

##### with Session multitreads for 1000 work
[51, 51, 51, 51, 51, 51, 51, 51, 51, 51] 

> 2.1975533962249756 s

##### with Session tomorrow for 1000 work
[51, 51, 51, 51, 51, 51, 51, 51, 51, 51] 

> 2.48775577545166 s

----
###For fix 'tomorrow' will return a Tomorrow object in python3.x ( but return true object in py2.x), torequests add an bad choice to check type, pPool.
>For now, autocheck only support:

>  字符串(str) 布尔类型(bool) 整数(int) 浮点数(float) 数字(number) 列表(list) 元组(tuple) 字典(dict) 日期(datetime)


####If you do not care about performance, you can use it by setting autocheck=1, else set autocheck=0. 
### pPool Usage:
```python
from torequests import pPool
import requests
import time


# get Tomorrow
def getint(url):
    r = requests.get(url)
    return r
pp = pPool(10)
ss = pp.map1(getint, [
    'http://p.3.cn/prices/mgets?skuIds=J_1273600'] * 3, autocheck=0)
print('Tomorrow:\n', ss)
# after using:
ss = [i.text for i in pp.map1(getint, [
    'http://p.3.cn/prices/mgets?skuIds=J_1273600'] * 3)]
print('use Tomorrow:\n', ss)


# get int
def getint(url):
    r = requests.get(url)
    return len(r.text)
pp = pPool(10)
ss = pp.map1(getint, [
    'http://p.3.cn/prices/mgets?skuIds=J_1273600'] * 3)
print('Int:\n', ss)


# get str
def getstr(url):
    r = requests.get(url)
    return r.text
pp = pPool(10)
ss = pp.map1(getstr, [
    'http://p.3.cn/prices/mgets?skuIds=J_1273600'] * 3)
print('String:\n', ss)




```
####result:
```
Tomorrow:
 [<torequests.Tomorrow object at 0x035316F0>, <torequests.Tomorrow object at 0x03531AF0>, <torequests.Tomorrow object at 0x03531ED0>]
use Tomorrow:
 ['[{"id":"J_1273600","p":"16999.00","m":"16999.00"}]\n', '[{"id":"J_1273600","p":"16999.00","m":"16999.00"}]\n', '[{"id":"J_1273600","p":"16999.00","m":"16999.00"}]\n']
Int:
 [51, 51, 51]
String:
 ['[{"id":"J_1273600","p":"16999.00","m":"16999.00"}]\n', '[{"id":"J_1273600","p":"16999.00","m":"16999.00"}]\n', '[{"id":"J_1273600","p":"16999.00","m":"16999.00"}]\n']
```
