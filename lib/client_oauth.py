"""
Testing Class for Chrome Apps against Indivo

Ben Adida
ben.adida@childrens.harvard.edu

Steve Zabak
steve.zabak@childrens.harvard.edu
"""

import urllib
try:
  from ..oauth import oauth
except:
  from oauth import oauth

class OAuth(object):


  def get_oauth_request_header(self, 
                                method, 
                                parameters,
                                data,
                                consumer_key,
                                consumer_secret,
                                content_type = oauth.HTTPRequest.FORM_URLENCODED_TYPE):

    if isinstance(data, dict) and isinstance(parameters, dict):
      data.update(parameters)
      data = urllib.urlencode(data)

    http_request = oauth.HTTPRequest(method, self.url.base + self.url.path, content_type, data, {})
    oauth_request = oauth.OAuthRequest( self.get_consumer(consumer_key, consumer_secret), 
                                        self.get_token(), 
                                        http_request, 
                                        {})

    # Sign the request
    oauth_request.sign(oauth.OAuthSignatureMethod_HMAC_SHA1())
    return oauth_request.to_header(with_content_type=True)

  def get_consumer(self, consumer_key, consumer_secret):
    return oauth.OAuthConsumer(consumer_key, consumer_secret)

  def set_token(self, token, token_secret):
    self.token = None
    if token and token_secret:
      self.token = oauth.OAuthToken(token, token_secret)

  def get_token(self):
    if hasattr(self, 'token'):
      return self.token
    return None
      
