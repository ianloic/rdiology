CONSUMER_TOKEN='vrun8954fry59w7297mr5ux5'
CONSUMER_SECRET='MEsUjbamFt'


import os, wsgiref, logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from rdio import Rdio
from cookies import JSONCookies as Cookies



class RdioRequestHandler(webapp.RequestHandler):
    __cached_rdio = None
    @property
    def rdio(self):
        if (self.__cached_rdio is None):
            self.__cached_rdio = Rdio(CONSUMER_TOKEN, CONSUMER_SECRET, Cookies(self))
        return self.__cached_rdio

    def template(self, name, template_values={}):
        self.response.out.write(template.render(os.path.join(os.path.dirname(__file__),
                                                             'templates', name),
                                                template_values))


class MainPage(RdioRequestHandler):
    def get(self):
        self.template('index.html', {
            'authenticated': self.rdio.authenticated,
        })


class AuthPage(RdioRequestHandler):
    def get(self):
        assert not self.rdio.authenticated

        if not self.rdio.authenticating:
            # obtain a request token
            callback_url = wsgiref.util.request_uri(self.request.environ)
            self.redirect(self.rdio.begin_authentication(callback_url))
        else:
            self.rdio.complete_authentication(self.request.get('oauth_verifier'))
            self.redirect('/')


class LogoutPage(RdioRequestHandler):
    def get(self):
        self.rdio.logout()
        self.redirect('/')


class HeavyRotationPage(RdioRequestHandler):
    def get(self):
        heavy_rotation = self.rdio.getHeavyRotationForUser(id= 13, type = 'albums', scope = 'friends', timeframe = 'weighted', attempt_everyone = 'true')

        self.template('heavy.html', {
            'albums': heavy_rotation['result']['items']
        })
        from pprint import pprint
        pprint(heavy_rotation, self.response.out)


class SearchPage(RdioRequestHandler):
    def post(self):
        results = self.rdio.search_v2(query=self.request.get('q'), filter="albums")
        self.template('search.html', {'results': results})


if __name__ == '__main__':
    from google.appengine.ext.webapp.util import run_wsgi_app
    app = webapp.WSGIApplication([
                ('/auth', AuthPage),
                ('/logout', LogoutPage),
                ('/heavy', HeavyRotationPage),
                ('/search', SearchPage),
                ('/', MainPage),
        ],
        debug=True)
    run_wsgi_app(app)