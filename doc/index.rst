.. torequests documentation master file, created by
   sphinx-quickstart on Sat Mar 17 02:18:11 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to torequests's documentation!
======================================
`https://github.com/ClericPy/torequests <https://github.com/ClericPy/torequests>`_

Indices and tables
==================

* :ref:`modindex`
* :ref:`genindex`


Quickstart
==================

To start:
----------

    | ``pip install torequests -U``

    **requirements:**

        | requests
        | futures # python2
        | aiohttp >= 3.6.2 # python3
        | uvloop  # python3

    **optional:**

        | psutil
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
        # use_decorator: 0
        # [<class 'torequests.main.NewFuture'>, <class 'torequests.main.NewFuture'>, <class 'torequests.main.NewFuture'>, <class 'torequests.main.NewFuture'>, <class 'torequests.main.NewFuture'>, <class 'torequests.main.NewFuture'>]
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

        # [2018-03-18 21:18:09]: 612
        # [2018-03-18 21:18:09]: 612
        # [2018-03-18 21:18:09]: 612
        # [2018-03-18 21:18:09]: [(612, None), (612, None), (612, None)]

**3. Requests - aiohttp-wrapper**

    ::

        # ====================== sync environment ======================
        from torequests.dummy import Requests
        from torequests.logs import print_info
        req = Requests(frequencies={'p.3.cn': (2, 1)})
        tasks = [
            req.get(
                'http://p.3.cn',
                retry=1,
                timeout=5,
                callback=lambda x: (len(x.content), print_info(x.status_code)))
            for i in range(4)
        ]
        req.x
        results = [i.cx for i in tasks]
        print_info(results)
        # [2020-02-11 15:30:54] temp_code.py(11): 200
        # [2020-02-11 15:30:54] temp_code.py(11): 200
        # [2020-02-11 15:30:55] temp_code.py(11): 200
        # [2020-02-11 15:30:55] temp_code.py(11): 200
        # [2020-02-11 15:30:55] temp_code.py(16): [(612, None), (612, None), (612, None), (612, None)]

        # ====================== async with ======================
        from torequests.dummy import Requests
        from torequests.logs import print_info
        import asyncio


        async def main():
            async with Requests(frequencies={'p.3.cn': (2, 1)}) as req:
                tasks = [
                    req.get(
                        'http://p.3.cn',
                        retry=1,
                        timeout=5,
                        callback=lambda x: (len(x.content), print_info(x.status_code))
                    ) for i in range(4)
                ]
                await req.wait(tasks)
                results = [task.cx for task in tasks]
                print_info(results)


        if __name__ == "__main__":
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
            loop.close()
        # [2020-02-11 15:30:55] temp_code.py(36): 200
        # [2020-02-11 15:30:55] temp_code.py(36): 200
        # [2020-02-11 15:30:56] temp_code.py(36): 200
        # [2020-02-11 15:30:56] temp_code.py(36): 200
        # [2020-02-11 15:30:56] temp_code.py(41): [(612, None), (612, None), (612, None), (612, None)]


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


Read More
=================

* :ref:`modindex`
