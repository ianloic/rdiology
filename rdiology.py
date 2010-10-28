CONSUMER_TOKEN='vrun8954fry59w7297mr5ux5'
CONSUMER_SECRET='MEsUjbamFt'


import sys, os, urlparse, logging

sys.path.append(os.path.join(os.path.dirname(__file__), 'python-oauth2'))

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template as _template

import oauth2 as oauth
import wsgiref, urllib

import cookies
from django.utils import simplejson as json

from cgi import parse_qsl

class Cookies(cookies.Cookies):
    def __getitem__(self, key):
        return json.loads(urllib.unquote(cookies.Cookies.__getitem__(self, key)))
    def __setitem__(self, key, item):
        cookies.Cookies.__setitem__(self, key, urllib.quote(json.dumps(item)))

consumer = oauth.Consumer(CONSUMER_TOKEN, CONSUMER_SECRET)
client = oauth.Client(consumer)

import httplib2
httplib2.debuglevel = 666

class Rdio(object):
    REQUEST_TOKEN='http://rdio.api.mashery.com/oauth/request_token'
    ACCESS_TOKEN='http://rdio.api.mashery.com/oauth/access_token'
    API='http://rdio.api.mashery.com/api/1/'
    def __init__(self, consumer_token, consumer_secret, data_store):
        self.__consumer = oauth.Consumer(consumer_token, consumer_secret)
        self.__data_store = data_store


    def authenticating(self):
        return self.__data_store.has_key('request_token')


    def authenticated(self):
        return self.__data_store.has_key('access_token')


    def begin_authentication(self, callback_url):
        assert not self.authenticating() and not self.authenticated()
        
        resp, content = self.__client().request(Rdio.REQUEST_TOKEN, 'POST',
                                       urllib.urlencode({'oauth_callback':callback_url}))
        if resp['status'] != '200':
            raise Exception("Invalid response %s." % resp['status'])
        request_token = dict(parse_qsl(content))
        self.__data_store['request_token'] = request_token
        return (request_token['login_url']+'?oauth_token='+request_token['oauth_token'])


    def complete_authentication(self, oauth_verifier):
        assert self.authenticating() and not self.authenticated()

        client = self.__client(oauth_verifier)
        resp, content = client.request(Rdio.ACCESS_TOKEN, "POST")
        if resp['status'] != '200':
            raise Exception("Invalid response %s." % resp['status'])
        access_token = dict(parse_qsl(content))
        self.__data_store['access_token'] = access_token
        del self.__data_store['request_token']

        
    def logout(self):
        if self.authenticating():
            del self.__data_store['request_token']
        if self.authenticated():
            del self.__data_store['access_token']


    def __client(self, oauth_verifier=None):
        token = None
        if self.authenticated():
            at = self.__data_store['access_token']
            token = oauth.Token(at['oauth_token'], at['oauth_token_secret'])
        elif self.authenticating():
            rt = self.__data_store['request_token']
            token = oauth.Token(rt['oauth_token'], rt['oauth_token_secret'])
        if token is not None and oauth_verifier is not None:
            token.set_verifier(oauth_verifier)
        return oauth.Client(self.__consumer, token)

    def call(self, method, **args):
        args['method'] = method
        client = self.__client()
        resp, content = client.request(Rdio.API, 'POST', urllib.urlencode(args))
        if resp['status'] != '200':
            raise Exception("Invalid response %s." % resp['status'])
        return json.loads(content)


def template(name, template_values={}):
    return _template.render(os.path.join(os.path.dirname(__file__), 'templates', name), template_values)


class RdioRequestHandler(webapp.RequestHandler):
    __cached_rdio = None
    def rdio(self):
        if (self.__cached_rdio is None):
            self.__cached_rdio = Rdio(CONSUMER_TOKEN, CONSUMER_SECRET, Cookies(self))
        return self.__cached_rdio


class MainPage(RdioRequestHandler):
    def get(self):
        rdio = self.rdio()
        self.response.out.write(template('index.html', {
            'authenticated': rdio.authenticated(),
        }))


class AuthPage(RdioRequestHandler):
    def get(self):
        rdio = self.rdio()

        assert not rdio.authenticated()

        if not rdio.authenticating():
            # obtain a request token
            callback_url = wsgiref.util.request_uri(self.request.environ)
            #callback_url = callback_url.replace('/authrequest', '/authcallback')
            self.redirect(self.rdio().begin_authentication(callback_url))
        else:
            self.rdio().complete_authentication(self.request.get('oauth_verifier'))
            self.redirect('/')


class LogoutPage(RdioRequestHandler):
    def get(self):
        self.rdio().logout()
        self.redirect('/')


class HeavyRotationPage(RdioRequestHandler):
    def get(self):
        heavy_rotation = self.rdio().call('getHeavyRotationForUser', id= 13, type = 'albums', scope = 'friends', timeframe = 'weighted', attempt_everyone = 'true')

        self.response.out.write(template('heavy.html', {
            'albums': heavy_rotation['result']['items']
        }))
        from pprint import pprint
        pprint(heavy_rotation, self.response.out)


if __name__ == '__main__':
    from google.appengine.ext.webapp.util import run_wsgi_app
    app = webapp.WSGIApplication([
                ('/auth', AuthPage),
                ('/logout', LogoutPage),
                ('/heavy', HeavyRotationPage),
                ('/', MainPage),
        ],
        debug=True)
    run_wsgi_app(app)