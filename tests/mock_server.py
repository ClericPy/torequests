from gevent.monkey import patch_all
patch_all()
import bottle
import time

app = bottle.Bottle()

@app.get('/test/<num>')
def test(num):
    return 'test ok %s' % num

@app.get('/sleep/<num:int>')
def sleep(num):
    time.sleep(num)
    return 'sleep ok %s' % num


app.run(server='gevent', port=5000)