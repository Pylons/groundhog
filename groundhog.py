from paste.httpserver import serve
from paste.registry import StackedObjectProxy
from paste.registry import RegistryManager

from weberror.evalexception import EvalException

from pyramid.config import Configurator
from pyramid.events import NewRequest
from pyramid.exceptions import NotFound
from pyramid.url import route_url
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.threadlocal import get_current_request
from pyramid.view import AppendSlashNotFoundViewFactory
from pyramid import httpexceptions # API

from pyramid_jinja2 import renderer_factory as j2_renderer_factory

class Namespace(object):
    pass

request = StackedObjectProxy()
application = StackedObjectProxy()
g = StackedObjectProxy()

class Groundhog(object):

    def __init__(self, package, session_key=None, authn_policy=None,
                 authz_policy=None, **settings):
        self.package = package
        self.session_key = session_key
        self.g = Namespace()
        session_factory = UnencryptedCookieSessionFactoryConfig(
            session_key,
            )
        settings['jinja2.directories'] = ['%s:templates' % package]
        self.config = Configurator(session_factory=session_factory,
                                   settings=settings,
                                   authentication_policy=authn_policy,
                                   authorization_policy=authz_policy)
        self.config.begin()
        self.config.add_renderer(None, self.renderer_factory)
        self.config.add_renderer('.html', j2_renderer_factory)
        self.config.set_renderer_globals_factory(self.renderer_globals_factory)
        notfound_view = AppendSlashNotFoundViewFactory()
        self.config.add_view(notfound_view, context=NotFound)
        self.config.add_view(self.exc_handler,
                             context=httpexceptions.WSGIHTTPException)
        self.config.add_static_view('static', '%s:static' % self.package)
        self.config.add_subscriber(self.start_request, NewRequest)
        self.config.commit()

    def start_request(self, event):
        req = event.request
        environ = req.environ
        reg = environ.get('paste.registry')
        if reg is not None:
            reg.register(request, req)
            reg.register(application, self)
            reg.register(g, self.g)

    def exc_handler(self, exc, request):
        return request.get_response(exc)

    def renderer_factory(self, name):
        def render_(value, system):
            request = system.get('request')
            if request is not None:
                request.response.content_type = 'text/html'
            return value
        return render_

    def renderer_globals_factory(self, system):
        return {'g':self.g, 'app':self}

    def mapply(self, func):
        def mapplied(request):
            return func(**request.matchdict)
        return mapplied

    def route(self, pattern, methods=('GET', 'HEAD'), **kw):
        if not hasattr(methods, '__iter__'):
            methods = (methods,)
        def decorator(func):
            endpoint = func.__name__
            
            self.config.add_route(endpoint, pattern,
                                  custom_predicates=(lambda *arg: False,))
            for method in methods:
                route_name = '%s_%s' % (endpoint, method)
                self.config.add_route(route_name, pattern,request_method=method)
                view = self.mapply(func)
                self.config.add_view(view, route_name=route_name, **kw)
            return func
        return decorator

    def get_wsgiapp(self):
        self.config.end()
        return self.config.make_wsgi_app()

    def run(self, host=None, port=8080, debug=False):
        self.config.end()
        app = self.config.make_wsgi_app()
        if debug:
            app = EvalException(app)
        app = RegistryManager(app)
        serve(app, host, port)

    def url_for(self, endpoint, *arg, **options):
        if not isinstance(endpoint, basestring):
            endpoint = endpoint.__name__
        request = self.request
        return route_url(endpoint, request, *arg, **options)

    @property
    def request(self):
        return get_current_request()

    def abort(self, code, message=''):
        raise httpexceptions.status_map[code](message)

    def redirect(self, url):
        raise httpexceptions.HTTPFound(location=url)

    def listen(self, event_type=None):
        def decorator(func):
            self.config.add_subscriber(func, event_type)
        return decorator

    def notify(self, event):
        self.config.registry.notify(event)

    def errorhandler(self, code):
        def decorator(func):
            def errfunc(exc, request):
                request.response.status = exc.status
                return func(exc)

            exc = httpexceptions.status_map.get(code)

            if exc is not None:
                view = errfunc
                if exc is NotFound:
                    view = AppendSlashNotFoundViewFactory(errfunc)
                self.config.add_view(view,context=exc)

            return func

        return decorator

