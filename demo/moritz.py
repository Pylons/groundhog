# tests:
#
# GET:
#
# curl -i http://127.0.0.1:8080/entries/1 
# 
# PUT:
#
# curl -i -H "Accept: application/json" -X PUT -d '{"foo":1}' \
#            http://127.0.0.1:8080/entries/1
#
# DELETE:
#
# curl -i -X DELETE http://127.0.0.1:8080/entries/1


import json

from webob.exc import HTTPNoContent

from groundhog import Groundhog
from groundhog import request

from pyramid.authentication import RemoteUserAuthenticationPolicy

authn_policy = RemoteUserAuthenticationPolicy()

class DummyRiakAuthorizationPolicy(object):
    def permits(self, context, principals, permission):
        print ('checked security policy with principals %r and permission %s' %
               (principals, permission))
        return True

authz_policy = DummyRiakAuthorizationPolicy()

class DummyRiakObject(object):
    def delete(self):
        pass

    def store(self):
        pass

    def get_data(self):
        return {'data':'foo'}

class DummyRiakBucket(object):
    def new(self, slug, data=None):
        return DummyRiakObject()

    def get(self, slug):
        return DummyRiakObject()

class DummyRiak(object):
    def __init__(self):
        self.buckets = {}

    def bucket(self, name):
        bucket = self.buckets.setdefault(name, DummyRiakBucket())
        return bucket

riak = DummyRiak()

app = Groundhog(
    __name__,
    'seekr1t',
    authn_policy=authn_policy,
    authz_policy=authz_policy,
    riak_host='localhost',
    riak_port='8881',
    solr_url='http://my_solr_url'
    )

@app.route('/entries/{slug}', methods='DELETE', permission='delete')
def entry_delete(slug):
    bucket = riak.bucket("entries")
    obj = bucket.new(slug)
    obj.delete()
    return HTTPNoContent()

@app.route('/entries/{slug}', methods='PUT', accept='application/json',
           permission='update')
def entry_update(slug):
    bucket = riak.bucket("entries")
    username = request.remote_user

    data = json.loads(request.body)
    # validate in someway
    data['author'] = username

    obj = bucket.new(slug, data=data)
    obj.store()
    return HTTPNoContent()

@app.route("/entries/{slug}", methods="GET", renderer='details.html')
def entry_detail(slug):
    bucket = riak.bucket("entries")
    obj = bucket.get(slug)
    return obj.get_data()

if __name__ == '__main__':
    app.run(debug=False)

