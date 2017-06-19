import time
from torequests.dummy import Requests

def test_speed(capsys):
    '''to do'''
    start = time.time()
    # loop = asyncio.ProactorEventLoop()
    # asyncio.set_event_loop(loop)
    # trequests = Requests(loop=loop)
    trequests = Requests()
    test_url = 'http://127.0.0.1:5000/test/%s'
    ss = [trequests.get(test_url%i, retry=0)
          for i in range(1000)]
    ss = [i.x for i in ss]
    cost = time.time() - start
    with capsys.disabled():
        print(cost)
