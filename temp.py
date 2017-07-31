import asyncio
import time
from torequests import Pool, NewFuture
from torequests.dummy import Loop, NewTask

now = lambda: time.time()
 
aaaa = (lambda : (time.sleep(1),11231))

'''
需要重写 run_coroutine_threadsafe
Loop 带上run_coroutine_threadsafe , run_in_executor
async_run_forever 以后要带上状态表明thread, 以后submit都改成threadsafe的

'''



async def do_some_work(x):
    print('Waiting: ', x)
    # await asyncio.sleep(x)
    ss = await loop.run_in_executor(None, aaaa)
    print(ss,1111,flush=1)
    return 'Done after {} s'.format(x)

start = now()

# coroutine = do_some_work(2)
loop = Loop()
loop.async_run_forever()
# aa = do_some_work(2)
# dd = loop.submit(aa)
dd = [loop.submit(do_some_work(i)) for i in range(3)]
print(dd[1].x)

# print('Task ret: ', task.result())
print('TIME: ', now() - start)
time.sleep(5)
print('to stop')

loop.stop()
print('stoped')
# loop.loop.close()