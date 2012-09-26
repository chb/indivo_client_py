import oauth2 as oauth
import urllib
import urlparse
import re
import os
import base64
import hmac
import hashlib
from xml.dom import minidom as XML # Use the built-in to avoid requiring an lxml install

# OAuth relative URLs
REQUEST_TOKEN_URL = '/oauth/request_token'
ACCESS_TOKEN_URL = '/oauth/access_token'
AUTHORIZATION_URL = '/oauth/authorize?oauth_token=%s'

# Configuration file defining valid Indivo API calls
CONFIG_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'api.xml')

# Dictionary to hold API calls defined in the config file
API_CALLS = {}

class IndivoClientError(Exception):
    pass

class IndivoClient(oauth.Client):
    """ Establishes OAuth communication with an Indivo Container, and provides access to the API. """

    def __init__(self, server_params, consumer_params, resource_token=None, **state_vars):
        consumer = oauth.Consumer(consumer_params['consumer_key'], consumer_params['consumer_secret'])
        super(IndivoClient, self).__init__(consumer)
        if resource_token:
            self.update_token(resource_token)
                               
        self.api_base = server_params['api_base']
        self.authorization_url = server_params['authorization_base'] + AUTHORIZATION_URL
        
        # Set extra state that was passed in (i.e. record_id, app_email, etc.)
        for var_name, value in state_vars.iteritems():
            setattr(self, var_name, value)

    def get(self, uri, body={}, headers={}, **uri_params):
        """ Make an OAuth-signed GET request to Indivo Server. """

        # append the body data to the querystring
        if isinstance(body, dict):
            body = urllib.urlencode(body)
            uri = "%s?%s"%(uri, body) if body else uri

        return self.request(self.api_base+uri, uri_params, method="GET", body='', headers=headers)

    def put(self, uri, body='', headers={}, content_type=None, **uri_params):
        """ Make an OAuth-signed PUT request to Indivo Server. """
        if content_type:
            headers['Content-Type'] = content_type
        if isinstance(body, dict):
            body = urllib.urlencode(body)
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        return self.request(self.api_base+uri, uri_params, method="PUT", body=body, headers=headers)

    def post(self, uri, body='', headers={}, content_type=None, **uri_params):
        """ Make an OAuth-signed POST request to Indivo Server. """
        if content_type:
            headers['Content-Type'] = content_type
        if isinstance(body, dict):
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            body = urllib.urlencode(body)
        return self.request(self.api_base+uri, uri_params, method="POST", body=body, headers=headers)

    def delete(self, uri, headers={}, **uri_params):
        """ Make an OAuth-signed DELETE request to Indivo Server. """
        return self.request(self.api_base+uri, uri_params, method="DELETE", headers=headers)

    def update_token(self, resource_token):
        """ Update the resource token used by the client to sign requests. """
        token = oauth.Token(resource_token['oauth_token'], resource_token['oauth_token_secret'])
        self.token = token

    def fetch_request_token(self, params={}):
        """ Get a request token from the server. """
        if self.token:
            raise IndivoClientError("Client already has a resource token.")
        resp, content = self.post(REQUEST_TOKEN_URL, body=params)
        if resp['status'] != '200':
            raise IndivoClientError("%s response fetching request token: %s"%(resp['status'], content))
        req_token = dict(urlparse.parse_qsl(content))
        self.update_token(req_token)
        return req_token

    @property
    def auth_redirect_url(self):
        if not self.token:
            raise IndivoClientError("Client must have a token to get a redirect url")
        return self.authorization_url%self.token.key
        
    def exchange_token(self, verifier):
        """ Exchange the client's current token (should be a request token) for an access token. """
        if not self.token:
            raise IndivoClientError("Client must have a token to exchange.")
        self.token.set_verifier(verifier)
        resp, content = self.post(ACCESS_TOKEN_URL)
        if resp['status'] != '200':
            raise IndivoClientError("%s response fetching access token: %s"%(resp['status'], content))
        access_token = dict(urlparse.parse_qsl(content))
        self.update_token(access_token)
        return access_token

    def get_surl_credentials(self):
        """ Produces a token and secret for signing URLs."""
        if not self.token:
            raise IndivoClientError("Client must have a token to generate SURL credentials.")
        secret = base64.b64encode(hmac.new(self.token.secret, "SURL-SECRET", hashlib.sha1).digest())
        return {'token': self.token.key, 'secret': secret}

    def _fill_url_template(self, url, **kwargs):
        for param_name in re.findall("{(.*?)}", str(url)):
            arg_name = param_name.lower()
            try:
                v = kwargs[arg_name]
            except KeyError as e:
                # Is it a direct attribute of the client? i.e. client.record_id
                try:
                    v = getattr(self, arg_name)
                except AttributeError:
                    raise KeyError("Expected argument %s"%arg_name)

            url = url.replace("{%s}"%param_name, v)
        return url

    def request(self, uri, uri_params, *args, **kwargs):
        uri = self._fill_url_template(uri, **uri_params)
        return super(IndivoClient, self).request(uri, *args, **kwargs)
            
    def __getattr__(self, call_name):
        """ Lookup additional API calls defined in the config file."""
        call = API_CALLS.get(call_name)
        if call:
            call.set_client(self)
            return call
        else:
            raise AttributeError("API Call doesn't exist: %s"%call_name)

class APICall(object):
    def __init__(self, method, url, client=None):
        self.method = method.lower()
        self.url = url
        self.client = client

    def set_client(self, client):
        self.client = client
        
    def __call__(self, *args, **kwargs):
        func = getattr(self.client, self.method)
        return func(self.url, *args, **kwargs)
        
# Load the API Methods
config_dom = XML.parse(CONFIG_FILE)
for call in config_dom.getElementsByTagName('call'):
    name = call.getAttribute('name')
    method = call.getAttribute('method')
    url = call.getAttribute('url')
    API_CALLS[name] = APICall(method, url)
