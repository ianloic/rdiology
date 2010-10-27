CONSUMER_TOKEN='vrun8954fry59w7297mr5ux5'
CONSUMER_SECRET='MEsUjbamFt'
REQUEST_TOKEN='http://rdio.api.mashery.com/oauth/request_token'
ACCESS_TOKEN='http://rdio.api.mashery.com/oauth/access_token'
API='http://rdio.api.mashery.com/api/1/'


import sys, os, urlparse, logging

sys.path.append(os.path.join(os.path.dirname(__file__), 'python-oauth2'))

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template as _template

import oauth2 as oauth
import wsgiref, urllib

import cookies
import json

class Cookies(cookies.Cookies):
    def __getitem__(self, key):
        return json.loads(urllib.unquote(cookies.Cookies.__getitem__(self, key)))
    def __setitem__(self, key, item):
        cookies.Cookies.__setitem__(self, key, urllib.quote(json.dumps(item)))

class RdioClient(oauth.Client):
    def __init__(self, consumer):
        oauth.Client.__init__(self, consumer)

consumer = oauth.Consumer(CONSUMER_TOKEN, CONSUMER_SECRET)
client = RdioClient(consumer)

import httplib2
httplib2.debuglevel = 666


def template(name, template_values={}):
    return _template.render(os.path.join(os.path.dirname(__file__), 'templates', name), template_values)

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.out.write(template('index.html'))


class AuthRequest(webapp.RequestHandler):
    def get(self):
        # obtain a request token
        callback_url = wsgiref.util.request_uri(self.request.environ)
        callback_url = callback_url.replace('/authrequest', '/authcallback')

        logging.info(callback_url)

        resp, content = client.request(REQUEST_TOKEN, 'POST',
                                       urllib.urlencode({'oauth_callback':callback_url}))

        if resp['status'] != '200':
            raise Exception("Invalid response %s." % resp['status'])
        request_token = dict(urlparse.parse_qsl(content))

        cookies = Cookies(self)
        cookies['request_token'] = request_token
        self.redirect(request_token['login_url']+'?oauth_token='+request_token['oauth_token'])


class AuthCallback(webapp.RequestHandler):
    def get(self):
        self.response.out.write('word up')
        verifier = self.request.get('oauth_verifier')
        cookies = Cookies(self)
        request_token = cookies['request_token']
        token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
        token.set_verifier(verifier)

        client = oauth.Client(consumer, token)
        resp, content = client.request(ACCESS_TOKEN, "POST")
        access_token = dict(urlparse.parse_qsl(content))
        cookies['access_token'] = access_token

        client = oauth.Client(consumer, oauth.Token(access_token['oauth_token'], access_token['oauth_token_secret']))


        apicall = {
            'method': 'getHeavyRotationForUser',
            'id': 13,
            'type': 'albums',
            'scope': 'friends',
            'timeframe': 'weighted',
            'attempt_everyone': 'true'
        }

        resp, content = client.request(API, 'POST', urllib.urlencode(apicall))
        self.response.out.write(`resp`)
        self.response.out.write(`content`)

if __name__ == '__main__':
    from google.appengine.ext.webapp.util import run_wsgi_app
    app = webapp.WSGIApplication([
                ('/authrequest', AuthRequest),
                ('/authcallback', AuthCallback),
                ('/', MainPage),
        ],
        debug=True)
    run_wsgi_app(app)