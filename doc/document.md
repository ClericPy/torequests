# torequests.main

> compatible for python 2 & 3


## Pool 

> subclass of concurrent.futures.ThreadPoolExecutor

```python
__init__(self, n=None, timeout=None)
    - n for max_size of pool
    - timeout will be passed to NewFuture

async_func(self, function)
    - function decorator. Major worker for submitting called-function into Pool obj.
    - `function` here will support kwargs: `callback`.

submit(self, func, *args, **kwargs)
    - submmit function with its args&kwargs into the Pool obj.
        kwargs may contains the callback param:
            callback will accept only one arg: NewFuture obj.
            callback can be set as function / tuple(list) of functions.
            callback's returned value will be set to future's attribute: callback_result.
```

## NewFuture

> subclass of concurrent.futures.Future

```python
__init__(self, timeout=None, args=None, kwargs=None)
    - timeout is for getting (NewFuture class does not have) attribute from future.result(timeout), or raise concurrent.futures.TimeoutError

__getattr__(self, name)
    - same as `Tomorrow` module's magic method
        get attribute from NewFuture obj will call result and return value of the `result` if future lack of it.

wrap_callback(function)
    - callback function will add callback_result attribute for NewFuture obj with the returned value of callback.

x(self)
    - return self.result(self._timeout) of raise TimeoutError
        this version will not catch TimeoutError an return None
```
## Async / threads

> to convert a function asynchronous 

```python
Async(f, n=None, timeout=None)
    - Initial a Pool obj, and submit function with params while being called.
        It will return a new async function, so it does't reset the origin function.

@threads(n=None, timeout=None)
    - Decorator function
        It will wrap the function in future, it will change the origin function.

get_results_generator(future_list, timeout=None, sort_by_completed=False)
    - future_list as the input, return a generator order by sort_by_completed or not:
        sort_by_completed=False: return as the origin sequence
        sort_by_completed=True: return as the completed sequence
```

## tPool
> utils for wrap requests module asynchronous by Pool

```python
__init__(self, n=None, session=None, timeout=None, time_interval=0, catch_exception=False)
    - n, the max_size of Pool obj
    - session should be requests.Session obj, or None
    - timeout arg for Pool, but not very necessary here, requests's timeout will be more useful
    - time_interval: seconds waiting for request interval between 2 request
                    n + time_interval will be used for frequency control
    - catch_exception: when raise an error, 
                    if True, return RequestsException obj (__bool__ is always False)
                    if False, raise the origin Exception
                    the RequestsException obj or origin Exception will contains all request-arg in args attribute.

close(self, wait=True)
    - close the session and pool

__enter__ & __exit__
    - for with context control

request(self, url, mode, retry=0, **kwargs)
    - retry: max_retries
    - `callback` can be accepted from kwargs
    - timeout + tPool's `catch_exception`, will save time and avoid crashing from Exceptions
```


#### More doc from [Requests: HTTP for Humans](http://docs.python-requests.org/en/master/)



-------------------



# torequests.dummy

> for python3.5+ only



#### More doc from [aiohttp: Asynchronous HTTP Client/Server](http://aiohttp.readthedocs.io/en/latest/)