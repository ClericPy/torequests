# ====================== sync environment ======================
from torequests.dummy import Requests
from torequests.logs import print_info
req = Requests(frequencies={'p.3.cn': (2, .1)})
tasks = [
    req.get(
        'http://p.3.cn',
        retry=1,
        timeout=5,
        callback=lambda x: (len(x.content), print_info(req.frequencies)))
    for i in range(1)
]
req.x
results = [i.cx for i in tasks]
print_info(results)
# print(req.loop)
# [2020-02-11 13:32:15] temp_code.py(10): {'p.3.cn': Frequency(2 / 2, pending: 2, interval: 1s)}
# [2020-02-11 13:32:15] temp_code.py(10): {'p.3.cn': Frequency(2 / 2, pending: 2, interval: 1s)}
# [2020-02-11 13:32:16] temp_code.py(10): {'p.3.cn': Frequency(2 / 2, pending: 0, interval: 1s)}
# [2020-02-11 13:32:16] temp_code.py(10): {'p.3.cn': Frequency(2 / 2, pending: 0, interval: 1s)}
# [2020-02-11 13:32:16] temp_code.py(15): [(612, None), (612, None), (612, None), (612, None)]

# ====================== async with ======================
from torequests.dummy import Requests
from torequests.logs import print_info
import asyncio
from torequests.main import threads


async def main():
    async with Requests(frequencies={'p.3.cn': (2, .1)}) as req:
        tasks = [
            req.get(
                'http://p.3.cn',
                retry=1,
                timeout=5,
                callback=lambda x: (len(x.content), print_info(req.frequencies))
            ) for i in range(1)
        ]
        # print(req.loop)
        await req.wait(tasks)
        results = [task.cx for task in tasks]
        print_info(results)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
# [2020-02-11 13:32:16] temp_code.py(35): {'p.3.cn': Frequency(2 / 2, pending: 2, interval: 1s)}
# [2020-02-11 13:32:16] temp_code.py(35): {'p.3.cn': Frequency(2 / 2, pending: 2, interval: 1s)}
# [2020-02-11 13:32:17] temp_code.py(35): {'p.3.cn': Frequency(2 / 2, pending: 0, interval: 1s)}
# [2020-02-11 13:32:17] temp_code.py(35): {'p.3.cn': Frequency(2 / 2, pending: 0, interval: 1s)}
# [2020-02-11 13:32:17] temp_code.py(41): [(612, None), (612, None), (612, None), (612, None)]
from torequests.dummy import coros, Loop
import time
loop = Loop()


@threads()
def sleep(n):
    time.sleep(n)
    return n


async def test():
    result = await sleep(1.5)
    return result


coro = test()
task = loop.submit(coro)
loop.x
assert task.x == 1.5


@coros(2, 1)
async def testcoro():
    print("testcoro 2 ops/s")
    await asyncio.sleep(0)
    return "testcoro result"


print("\n")
task = [testcoro() for i in range(4)]
tasks = [i.x for i in task]
assert tasks == [
    "testcoro result",
    "testcoro result",
    "testcoro result",
    "testcoro result",
]
