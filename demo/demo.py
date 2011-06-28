from groundhog import httpexceptions
from groundhog import Groundhog
from groundhog import request
from groundhog import application
from groundhog import g

# application

app = Groundhog(__name__, 'seekrit')

@app.route('/')
def root():
    return 'root'

@app.route('/miss')
def miss():
    raise httpexceptions.HTTPNotFound()

@app.route('/redirect')
def redirect():
    app.redirect('/')

@app.route('/abort500')
def abort500():
    app.abort(500, 'its broke')

@app.route('/showrequest')
def showrequest():
    import cgi
    print request
    print application
    print g
    return cgi.escape('%s, %s, %s' % (request, application, g))

@app.route('/notify/{param}')
def notify(param=None):
    app.notify(MyEvent(param))
    return 'notified'

@app.listen()
def listener(event):
    print event

@app.errorhandler(404)
def notfound(exc):
    return 'Not found yo'

class MyEvent(object):
    def __init__(self, param):
        self.param = param

if __name__ == '__main__':
    app.run(debug=True)
