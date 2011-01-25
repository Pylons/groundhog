from groundhog import Groundhog
from groundhog import NotFound
from groundhog import request
from groundhog import application
from groundhog import g

import webob.exc

# application

app = Groundhog(__name__, 'seekrit')

@app.errorhandler(404)
def notfound(exc):
    return 'Not found yo'

@app.route('/')
def root():
    return 'root'

@app.route('/miss_webob')
def miss_webob():
    raise webob.exc.HTTPNotFound('holy crap')

@app.route('/miss_internal')
def miss_internal():
    raise NotFound('holy crap')

@app.route('/redirect')
def redirect():
    app.redirect('/')

@app.route('/abort500')
def abort500():
    app.abort(500, 'its broke')

@app.listen()
def listener(event):
    print event

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

class MyEvent(object):
    def __init__(self, param):
        self.param = param

if __name__ == '__main__':
    app.run(debug=True)
