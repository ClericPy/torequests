# trequests
####Using tomorrow to make requests async
>for python3.x, but tPool may not be fit for python2.x......
Thanks https://github.com/madisonmay/Tomorrow very much.

for first

>pip install requests

Obviously, use it like :
```python
from trequests import tPool as Pool
requests = Pool(30)
```
or 
```python
import requests
print(help(trequests))
```
then use requests.get/post/put/head/delete/ as usual.
so, this does support Session...

curio sames awosome and difficult，multiprocessing.dummy and pool.map is non-3rd-library but I don't like it even using it much time，requests said never support async（such like asyncio）， aiohttp not easy like requests, gevent hates Windows, twisted hard to study and no good for py3, grab seems good, scrapy seems to abandon py3, god ,I have try so much and deserve so many failures.........


一句话，就是给requests简单异步包装一下
####用法：
```python
from trequests import tPool as Pool
requests = Pool(30)
```
or 
```python
import requests
print(help(trequests))
```
然后requests正常用就行了，支持Session什么的，就只是简单的requests.get加几个参数，可以命名成trequest，和原生requests分开混着用，原生的requests就用multiprocessing.dummy吧。。。（后来把tomorrow包装的叫tPool，multiprocessing.dummy包装的叫mPool，后者只是多线程处理下urls。。。)

#Example：

```python
from trequests import mPool
from trequests import tPool
import requests
import time

# no Session multitreads
print('# no Session multitreads')
aa = time.time()
mrequests = mPool(50)
ss = mrequests.get(['http://p.3.cn/prices/mgets?skuIds=J_1273600'] * 100)
print([len(i.text) for i in ss])
print(time.time() - aa, 's')

# no Session tomorrow
print('# no Session tomorrow')

aa = time.time()
trequests = tPool(50)
ss = [requests.get('http://p.3.cn/prices/mgets?skuIds=J_1273600')] * 5000
ss = [len(i.text) for i in ss]
print(ss[-50:])
print(time.time() - aa, 's')


# with Session multitreads
print('# with Session multitreads')

aa = time.time()
s = requests.Session()
mrequests = mPool(50, session=s)
ss = mrequests.get(['http://p.3.cn/prices/mgets?skuIds=J_1273600'] * 100)
print([len(i.text) for i in ss])
print(time.time() - aa, 's')

# with Session tomorrow
print('# with Session tomorrow')
aa = time.time()
s = requests.Session()
trequests = tPool(50, session=s)
ss = [requests.get('http://p.3.cn/prices/mgets?skuIds=J_1273600')] * 5000
ss = [len(i.text) for i in ss]
print(ss[-50:])
print(time.time() - aa, 's')
```
># no Session multitreads
[51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51]
1.1978464126586914 s
# no Session tomorrow
[51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51]
0.10907530784606934 s
# with Session multitreads
[51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51]
0.31622314453125 s
# with Session tomorrow
[51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51, 51]
0.08806300163269043 s

