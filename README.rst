Welcome to torequests's documentation!
======================================


`Github <https://github.com/ClericPy/torequests>`_


`Document <https://torequests.readthedocs.io/en/latest/>`_


Quickstart
==================

To start:
----------

    | ``pip install torequests -U``

    **requirements:**

        | requests
        | futures # python2
        | aiohttp >= 3.0.5 # python3
        | uvloop  # python3

    **optional:**

        | psutil
        | fuzzywuzzy
        | python-Levenshtein
        | pyperclip

Examples:
----------

**1. Async, threads - make functions asynchronous**

    ::

        from torequests.main import Async, threads
        import time


        def use_submit(i):
            time.sleep(i)
            result = 'use_submit: %s' % i
            print(result)
            return result


        @threads()
        def use_decorator(i):
            time.sleep(i)
            result = 'use_decorator: %s' % i
            print(result)
            return result


        new_use_submit = Async(use_submit)
        tasks = [new_use_submit(i) for i in (2, 1, 0)
                ] + [use_decorator(i) for i in (2, 1, 0)]
        print([type(i) for i in tasks])
        results = [i.x for i in tasks]
        print(results)

        # use_submit: 0
        # use_decorator: 0[<class 'torequests.main.NewFuture'>, <class 'torequests.main.NewFuture'>, <class 'torequests.main.NewFuture'>, <class 'torequests.main.NewFuture'>, <class 'torequests.main.NewFuture'>, <class 'torequests.main.NewFuture'>]

        # use_submit: 1
        # use_decorator: 1
        # use_submit: 2
        # use_decorator: 2
        # ['use_submit: 2', 'use_submit: 1', 'use_submit: 0', 'use_decorator: 2', 'use_decorator: 1', 'use_decorator: 0']
        
**2. tPool - thread pool for async-requests**

    ::

        from torequests.main import tPool
        from torequests.logs import print_info

        trequests = tPool()
        test_url = 'http://p.3.cn'
        ss = [
            trequests.get(
                test_url,
                retry=2,
                callback=lambda x: (len(x.content), print_info(len(x.content))))
            for i in range(3)
        ]
        # or [i.x for i in ss]
        trequests.x
        ss = [i.cx for i in ss]
        print_info(ss)

        # [2019-04-01 00:22:22] temp_code.py(10): 612
        # [2019-04-01 00:22:22] temp_code.py(10): 612
        # [2019-04-01 00:22:22] temp_code.py(10): 612
        # [2019-04-01 00:22:22] temp_code.py(16): [(612, None), (612, None), (612, None)]


**3. Requests - aiohttp-wrapper**

    ::

        from torequests.dummy import Requests
        from torequests.logs import print_info
        trequests = Requests(frequencies={'p.3.cn': (2, 2)})
        ss = [
            trequests.get(
                'http://p.3.cn',
                retry=1,
                timeout=5,
                callback=lambda x: (len(x.content), print_info(trequests.frequencies)))
            for i in range(4)
        ]
        trequests.x
        ss = [i.cx for i in ss]
        print_info(ss)

        # [2019-04-01 00:22:51] temp_code.py(9): {'p.3.cn': Frequency(sem=<1/2>, interval=2)}
        # [2019-04-01 00:22:51] temp_code.py(9): {'p.3.cn': Frequency(sem=<0/2>, interval=2)}
        # [2019-04-01 00:22:53] temp_code.py(9): {'p.3.cn': Frequency(sem=<1/2>, interval=2)}
        # [2019-04-01 00:22:53] temp_code.py(9): {'p.3.cn': Frequency(sem=<2/2>, interval=2)}
        # [2019-04-01 00:22:53] temp_code.py(14): [<NewResponse [200]>, <NewResponse [200]>, <NewResponse [200]>, <NewResponse [200]>]

    or using torequests.dummy.Requests in async environment.
    ::
        import asyncio

        from responder import API
        from torequests.dummy import Requests

        loop = asyncio.get_event_loop()
        api = API()


        @api.route('/')
        async def index(req, resp):
            # await for request or FailureException
            r = await api.req.get('http://p.3.cn', timeout=(1, 1))
            print(r)
            if r:
                # including good request with status_code between 200 and 299
                resp.text = 'ok' if 'Welcome to nginx!' in r.text else 'bad'
            else:
                resp.text = 'fail'


        if __name__ == "__main__":
            api.req = Requests(loop=loop)
            api.run(port=5000, loop=loop)


**4. utils: some useful crawler toolkits**

        | **ClipboardWatcher**: watch your clipboard changing.
        | **Counts**: counter while every time being called.
        | **Null**: will return self when be called, and alway be False.
        | **Regex**: Regex Mapper for string -> regex -> object.
        | **Saver**: simple object persistent toolkit with pickle/json.
        | **Timer**: timing tool.
        | **UA**: some common User-Agents for crawler.
        | **curlparse**: translate curl-string into dict of request.
        | **md5**: str(obj) -> md5_string.
        | **print_mem**: show the proc-mem-cost with psutil, use this only for lazinesssss.
        | **ptime**: %Y-%m-%d %H:%M:%S -> timestamp.
        | **ttime**: timestamp -> %Y-%m-%d %H:%M:%S
        | **slice_by_size**: slice a sequence into chunks, return as a generation of chunks with size.
        | **slice_into_pieces**: slice a sequence into n pieces, return a generation of n pieces.
        | **timeago**: show the seconds as human-readable.
        | **unique**: unique one sequence.


`Read More <https://torequests.readthedocs.io/en/latest/>`_
