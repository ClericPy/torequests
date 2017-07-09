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
        It will return a new async function, so it does't overwrite the origin function.

@threads(n=None, timeout=None)
    - Decorator function
        It will wrap the function in future, it will change the origin function.

get_results_generator(future_list, timeout=None, sort_by_completed=False)
    - future_list as the input, return a generator order by sort_by_completed or not:
        sort_by_completed=False: return as the origin sequence
        sort_by_completed=True: return as the completed sequence
```

## tPool

> utils for wrap requests module asynchronous with Pool obj.

```python
__init__(self, n=None, session=None, timeout=None, time_interval=0, catch_exception=False)
    - n, the max_size of Pool obj
    - session should be requests.Session obj, or None
    - timeout arg for Pool, but not very necessary here, requests's timeout will be more useful
    - time_interval: seconds waiting for request interval between 2 requests;
                    n + time_interval params will be used for the frequency control.
    - catch_exception: when raise an error, 
                    if be set with True (by default), return RequestsException obj (__bool__ is always False)
                    else if False, raise the origin Exception
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

## NewTask

> subclass of asyncio.tasks.Task, input coroutine return NewTask

```python
__init__(self, coro, *, loop=None)
    - same as asyncio.tasks.Task

wrap_callback(function)
    - be used to wrap a callback function, to bind callback_result attribute for the task / future.

x(self)
    - fetch the future's result, may run in loop if not finished.

__getattr__(self, name)
    - tomorrow-like magic method, return result.getattr(name) if name is not included in the task.

__setattr__(self, name, value)
    - only used for 

__getattr__(self, name)
    - tomorrow-like magic method, return result.getattr(name) if name is not included in the task.

__setattr__(self, name, value)
    - only used for ('encoding', 'content') as requests-like usage.
```

## Loop

> Default event loop as the other class need, use uvloop if supported.

```python
__init__(self, n=100, loop=None, default_callback=None)
    - maximum concurrent number for the event loop.
    - loop can be specified if necessary.
    - if one task obj does'nt have callback params, with run default_callback(task) while finished.

wrap_sem(self, coro_func)
    - make a task run under the concurrent limitation.

apply(self, function, args=None, kwargs=None)
    - apply a function to loop with args(tuple) and kwargs(dict), kwargs may contain callback param.

submit(self, coro, callback=None)
    - coro is a called coroutine function
        - because coro has been called, so it only can be set sem with loop.wrap_sem before coro function was called.
    - callback may be a function with one param(NewTask obj), or tuple(list) of functions.

submitter(self, f)
    - decorator for coroutine function

todo_tasks(self)
    - return self.tasks only remain the _PENDING tasks

x(self)
    - loop.x == loop.run()

run(self)
    - loop.run_until_complete for all the todo_tasks

run_forever(self)
    - loop.run_forever()

async def done(self)
    -  be used in coroutine context like `await loop.done`.
```

## Async / threads

> to convert a function asynchronous 

```python
Async(func, n=None, timeout=None)
    - Initial a Loop obj, and apply a coro-function with params while being called.
        It will return a new async function, so it does't overwrite the origin function.

@threads(n=None, timeout=None)
    - Decorator function
        It will wrap the function in future, it will change the origin function.
```

## Requests

> utils for wrap aiohttp module like requests module, subclass of Loop.

```python
__init__(self, n=100, session=None, time_interval=0, catch_exception=True,
                 default_callback=None, **kwargs)
    - n, the maximum concurrent number of Pool obj
    - session: aiohttp.ClientSession, or None
    - time_interval: seconds waiting for request interval between 2 requests;
                    n + time_interval params will be used for the frequency control.
    - catch_exception: when raise an error, 
                    if be set with True (by default), return RequestsException obj (__bool__ is always False);
                    else if False, raise the origin Exception;
                    the RequestsException obj or origin Exception will contains all request-arg in args attribute.

_initial_request(self)
    - to pack origin aiohttp request method(get/post/...) in Loop

_mock_request_method(self, method)
    - work for _initial_request, packing request in default_callback/sem/... 

async def _request(self, method, url, retry=0, **kwargs)
    work for _initial_request
    - retry: max_retries num
    - callback: will take place of default_callback

close(self)
    - close self.session avoid warning for unclosed session.
    no need for close loop here.
```

#### More doc from [aiohttp: Asynchronous HTTP Client/Server](http://aiohttp.readthedocs.io/en/latest/)



----------------



# USAGE / EXAMPLES

> TODO
