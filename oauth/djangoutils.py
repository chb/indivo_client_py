"""
OAuth utilities for Django

Ben Adida
ben.adida@childrens.harvard.edu
"""

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.exceptions import *
import oauth

PARAMS = {'OAUTH_SERVER' : None}

def extract_request(request):
    """
    Extracts the implementation-independent HTTP request components from a Django HTTP request object.
    
    HTTP method, url, request body content type, request body content, headers (at least the authorization header)
    """

    if request.method == "GET":
        data = request.META['QUERY_STRING']
    else:
        data = request.raw_post_data

    if not data:
        data = ""

    # via straight django or via Apache
    content_type = None
    if request.META.has_key('CONTENT_TYPE'):
        content_type = request.META['CONTENT_TYPE']
    if not content_type and request.META.has_key('HTTP_CONTENT_TYPE'):
        content_type = request.META['HTTP_CONTENT_TYPE']

    if not content_type:
        content_type = oauth.HTTPRequest.FORM_URLENCODED_TYPE

    # we need the full path, including protocol, host, and relative path
    full_path = "%s://%s%s" % (request.is_secure() and 'https' or 'http', request.get_host(), request.path)

    return oauth.HTTPRequest(request.method, full_path, content_type, data, request.META)


def request_token(request):
    """
    the request-token request URL
    """

    # ask the oauth server to generate a request token given the HTTP request
    try:
        request_token = PARAMS['OAUTH_SERVER'].generate_request_token(extract_request(request))
        return HttpResponse(request_token.to_string())
    except oauth.OAuthError:
        # an exception can be raised if there is a bad signature (or no signature) in the request
        raise PermissionDenied()


def exchange_token(request):
    # ask the oauth server to exchange a request token into an access token
    # this will check proper oauth for this action

    access_token = PARAMS['OAUTH_SERVER'].exchange_request_token(extract_request(request))
    # an exception can be raised if there is a bad signature (or no signature) in the request

    return HttpResponse(access_token.to_string())
