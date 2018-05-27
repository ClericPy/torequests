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
    return 'sleep ok %s; %s' % (num, time.ctime())


@app.get('/')
def index():
    return '<a href="http://localhost:5000/sleep/3">%s</a>' % 'a' * 100


app.run(server='gevent', port=5000, reloader=True, debug=True)
