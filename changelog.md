


---

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
