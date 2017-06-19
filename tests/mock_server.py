from gevent.monkey import patch_all
patch_all()
import bottle

app = bottle.Bottle()

@app.get('/test/<num>')
def test(num):
    return 'ok %s' % num

app.run(server='gevent', port=5000)