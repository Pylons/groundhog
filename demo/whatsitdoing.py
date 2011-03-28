from groundhog import Groundhog
from repoze.profile.profiler import AccumulatingProfileMiddleware
from paste.httpserver import serve

# application

app = Groundhog(__name__, 'seekrit')

@app.route('/')
def root():
    return 'hello'

if __name__ == '__main__':
    wsgiapp = app.get_wsgiapp()
    wrapped = AccumulatingProfileMiddleware(wsgiapp)
    serve(wrapped)
    
