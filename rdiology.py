CONSUMER_TOKEN='vrun8954fry59w7297mr5ux5'
CONSUMER_SECRET='MEsUjbamFt'


import os


from google.appengine.ext import webapp
from google.appengine.ext.webapp import template as _template

import wsgiref, urllib

import cookies
from django.utils import simplejson as json

from rdio import Rdio


class Cookies(cookies.Cookies):
    def __getitem__(self, key):
        return json.loads(urllib.unquote(cookies.Cookies.__getitem__(self, key)))
    def __setitem__(self, key, item):
        cookies.Cookies.__setitem__(self, key, urllib.quote(json.dumps(item)))



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