# trequests
####Using tomorrow to make requests async
https://github.com/madisonmay/Tomorrow

Obviously, use it like :
```python
from trequests import Pool

requests = Pool(30)
...
```
then use requests.get/post/put/head/delete/ as usual.
so, this does not support Session...

curio sames awosome and difficult，multiprocessing.dummy and pool.map is non-3rd but I don't like it even using it much time，requests said never support async（such like asyncio）， aiohttp not easy like requests, gevent hates Windows, twisted hard to study and no good for py3, grab seems good, scrapy seems to abandon py3, god ,I have try so much and deserve so many failures.........


##一句话，就是给requests简单异步包装一下
####用法：
```python
from trequests import Pool
requests = Pool(30)
```
然后requests正常用就行了，不过不支持Session什么的，就只是简单的requests.get加几个参数，可以命名成request1，和原生requests分开混着用，原生的requests就用multiprocessing.dummy吧。。。
