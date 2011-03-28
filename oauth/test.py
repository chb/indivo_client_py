"""
Tests for OAuth

How we really want to use OAuth

Ben Adida
ben.adida@childrens.harvard.edu

2009-02-13
"""

import oauth, djangoutils

CONSUMERS = {'test':oauth.OAuthConsumer('test','test')}
TOKENS = {'test': oauth.OAuthToken('test','test')}
REQUEST_TOKENS = {}

class OAuthStore(object):
    def __init__(self):
        pass

    def lookup_consumer(self, consumer_key):
        """
        returns on OAuthConsumer
        """
        return CONSUMERS[consumer_key]

    def create_request_token(self, consumer, request_token_str, request_token_secret):
        """
        take a RequestToken and store it.
        """
        REQUEST_TOKENS[request_token_str] = oauth.OAuthToken(request_token_str, request_token_secret)

    def lookup_request_token(self, consumer, request_token_str):
        """
        token is the token string
        returns a OAuthRequestToken

        consumer may be null.
        """
        return REQUEST_TOKENS.get(request_token_str, None)

    def authorize_request_token(self, request_token, user, **kwargs):
        """
        Mark a request token as authorized by the given user,
        with the given additional parameters.

        The user is whatever data structure was received by the OAuthServer.
        """
        raise NotImplementedError

    def mark_request_token_used(self, consumer, request_token):
        """
        Mark that this request token has been used.
        Should fail if it is already used
        """
        raise NotImplementedError

    def create_access_token(self, consumer, request_token, access_token_str, access_token_secret):
        """
        Store the newly created access token that is the exchanged version of this
        request token.
        
        IMPORTANT: does not need to check that the request token is still valid, 
        as the library will ensure that this method is never called twice on the same request token,
        as long as mark_request_token_used appropriately throws an error the second time it's called.
        """
        raise NotImplementedError

    def lookup_access_token(self, consumer, access_token_str):
        """
        token is the token string
        returns a OAuthAccessToken
        """
        return TOKENS[access_token_str]

    def check_and_store_nonce(self, nonce_str):
        """
        store the given nonce in some form to check for later duplicates
        
        IMPORTANT: raises an exception if the nonce has already been stored
        """
        pass

OAUTH_SERVER = oauth.OAuthServer(store=OAuthStore())


def django_request_token(request):
    """
    the request-token request URL
    """
    # ask the oauth server to generate a request token given the HTTP request
    try:
        request_token = OAUTH_SERVER.generate_request_token(djangoutils.extract_request(request))
    except OAuthError:
        # an exception can be raised if there is a bad signature (or no signature) in the request
        pass

    return HttpResponse(request_token.to_string())

def django_authorize(request):
    """
    Authorize a request token
    """
    request_token_str = request.POST['token']
    user = request.user
    permission_level = request.POST['permission_level']

    # does not take the HTTP request, since there's no HTTP oauth request here
    OAUTH_SERVER.authorize_request_token(request_token_str, user=user, permission_level = permission_level)
    

def django_exchange_token(request):
    # ask the oauth server to exchange a request token into an access token
    # this will check proper oauth for this action
    try:
        access_token = OAUTH_SERVER.exchange_request_token(djangoutils.extract_request(request))
    except OAuthError:
        # an exception can be raised if there is a bad signature (or no signature) in the request
        pass

    return HttpResponse(access_token.to_string())

def django_protected_view(request):
    """
    A Django view that is oauth authenticated
    """

    try:
        # oauth_parameters will be all of the oauth parameters, including core (timestamp) and non-core (sudo).
        consumer, token, oauth_parameters = OAUTH_SERVER.check_resource_access(djangoutils.extract_request(request))
    except OAuthError:
        # a permission error
        pass

    # return the actual resource.
