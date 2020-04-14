
---

later (4.9.10+) changes view: https://github.com/ClericPy/torequests/releases

- 4.9.9
    - fix catch_exception error

- 4.9.6 ~ 4.9.8
    - fix python3.8 contend generator
    - use asend instead of async for
    - fix default_host_frequency strategy
    - new faster and tiny frequency controller

- 4.9.5
    - fix aiohttp verify param compatible

- 4.9.4
    - fix aiohttp 4 Compatible issue
    - update readme and benchmark

- 4.9.3
    - hotfix setup.py

- 4.9.2
    - fix bugs

- 4.9.1
    - add new Frequency implementation
    - fix python2 queue import error
    - remove useless parsers, uniparser is the new choice
    - update benchmarks
    - cancel frequency put_tasks if `del`
    - 

- 4.9.0
    - fix dummy Requests task.cx not return callback result #36
    - add `__aenter__` for dummy
    - fix frequency
    - fix task_cost_time

- 4.8.21
    - remove nonsense semphore for performance lost
    - add some extras_requires

- 4.8.20
    - fix runtime error for running loop

- 4.8.19
    - Fix curlparse encoding error
    - add test 3.8
    - fix aiohttp unclosed connection

- 4.8.18
    - hotfix curlparse issue by backslash string.

- 4.8.17
    - hotfix version crash of 4.8.16

- 4.8.16 - [deleted]
    - upgrade aiohttp 3.6.2 for deprecation warning

- 4.8.15
    - update setup.py requirements

- 4.8.14
    - use ssl args for newest aiohttp

- 4.8.13
    - fix dummy unclosed connection

- 4.8.12
    - fix utils.curlparse post form encoding issue

- 4.8.10
    - fix dummy.Requests "Unclosed connector"
    - add sort_url_query

- 4.8.9
    - fix issue: close aiohttp.ClientSession as coroutine

- 4.8.8
    - remove useless arg of torequests.dummy.Requests: reuse_running_loop

- 4.8.7
    - support tuple type timeout for dummy, like
        - `req.get(url, timeout=(1, 3))`

- 4.8.6 and before
    - ignore
