
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'python-oauth2'))
import oauth2 as oauth
from cgi import parse_qsl
import urllib
from django.utils import simplejson as json


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
