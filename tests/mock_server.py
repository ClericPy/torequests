import asyncio
import time

from responder import API

api = API()


@api.route('/test/{num}')
async def test(_, resp, *, num):
    resp.text = 'test ok %s' % num


@api.route('/sleep/<num:int>')
async def sleep(_, resp, *, num):
    await asyncio.sleep(num)
    resp.text = 'sleep ok %s; %s' % (num, time.ctime())


@api.route('/')
async def index(req, resp):
    resp.text = '<a href="http://localhost:5000/sleep/3">%s</a>' % 'a' * 100


if __name__ == "__main__":
    api.run(port=5000)
