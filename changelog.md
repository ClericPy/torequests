


---

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
