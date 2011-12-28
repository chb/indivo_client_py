"""
Testing Library for Indivo

Steve Zabak
steve.zabak@childrens.harvard.edu
"""

import os
import sys
import urllib
import socket
import httplib
import xml.parsers.expat
import xml_utils

from client_oauth import OAuth
try:
    from ..oauth import oauth
except:
    from oauth import oauth
from xml.dom import minidom
from urlparse import urlparse
from iaux import HTTP, Url, Reserved, Chars

class IUtilsError(Exception):
    
    def __init__(self, value, info=None):
        if info is not None:
            self.value = '%s: %s' % (value, info)
        else:
            self.value = value

    def __str__(self):
        return repr(self.value)


class IUtils(OAuth):

    def __init__(self, scheme, host, port, client):
        self.request_response_info = {}
        signature = {'call' : ['name', 'method', 'url'], 'response' : ['element', 'attribute']}

        self.HTTP = HTTP()
        self.res = Reserved()
        self.chars = Chars()

        path_home = os.path.abspath(os.path.abspath(os.path.dirname(__file__)) + \
                                        self.chars.slash + self.chars.period + self.chars.period)

        self.empty_string = ''
        self.wd = self.chars.slash.join(__file__.split(self.chars.slash)[0:-2])
        self.api, unused = xml_utils.xml2dict(path_home + '/config/api.xml', signature)
        self.url = Url(scheme, host, port)
        self.client = client

    def _http_request(self, method, oauth_header, parameters, content_type):
        retval = {}
        uri = self.url.path
        if isinstance(parameters, dict):
            parameters = urllib.urlencode(parameters)

        # temporary hack (Ben)
        if method == "GET":
            self.url.query = parameters
            parameters = None
        elif parameters == '':
            parameters = None

        # moved this here after query is regenerated (Ben)
        if len(self.url.query) > 0:
            uri = self.url.path + self.chars.qm + self.url.query

        # Make request, using Django's internal client instead of sending it over the wire
        client_method = method.lower()
        client_func = getattr(self.client, client_method)
        if method == 'get' or method == 'delete':
            resp = client_func(uri, **oauth_header)
        elif not parameters:
            resp = client_func(uri, content_type=content_type, data='', **oauth_header)
        else:
            resp = client_func(uri, content_type=content_type, data=parameters, **oauth_header) 

        if resp[self.HTTP.content_type_raw]:
            retval[self.HTTP.ContentTypes.content_type] = resp[self.HTTP.content_type_raw]
        else:
            retval[self.HTTP.ContentTypes.content_type] = self.empty_string
        self.request_response_info[self.res.Debug.status] = resp.status_code
        self.request_response_info[self.res.Debug.content_type] = retval[self.HTTP.ContentTypes.content_type]

        # Handle status
        if resp.status_code == self.HTTP.Status.ok:
            retval[self.HTTP.content] = resp.content.strip(self.chars.newline)
            return retval
        elif resp.status_code == self.HTTP.Status.permission_denied:
            return self.HTTP.Errors.permission_denied + \
                self.chars.colon + \
                resp.content.strip(self.chars.newline)
        elif resp.status_code == self.HTTP.Status.not_found:
            retval[self.HTTP.content] = resp.content.strip(self.chars.newline)
            return retval
        elif resp.status_code == self.HTTP.Status.redirect:
            retval[self.HTTP.content] = resp.content.strip(self.chars.newline)
            return retval
        elif resp.status_code == self.HTTP.Status.invalid_request:
            retval[self.HTTP.content] = resp.content.strip(self.chars.newline)
            return retval
        elif resp.status_code == self.HTTP.Status.server_error:
            raise IUtilsError('Server Error')
      # return self.HTTP.Errors.server_error
        else:
            raise IUtilsError(str(resp.status_code) + self.chars.colon + self.chars.space + uri)

    def http_conn(self, method, url, app_info, parameters=None, data=None):
        """ """
        data        = data or {}
        parameters  = parameters or {}

        content_type = self.get_content_type(parameters, data)
        if (url and self.set_url(url) and self.url_check(url)):
            if isinstance(method, str) \
                    or isinstance(method, unicode):
                method = method.upper()
            else:
                return None

            if app_info.__contains__(self.res.oauth_token) \
                    and app_info.__contains__(self.res.oauth_token_secret):
                self.set_token(app_info[self.res.oauth_token], app_info[self.res.oauth_token_secret])
            else:
                self.set_token(None, None)
            oauth_header = self.get_oauth_request_header(
                method,
                parameters,
                data,
                app_info['consumer_key'],
                app_info['consumer_secret'],
                content_type=content_type)
            self.request_response_info[self.res.Debug.oauth_header] = oauth_header
            self.request_response_info[self.res.Debug.data] = data
            
            return self._http_request(method, oauth_header, data, content_type)

        return None

    def get_content_type(self, parameters, data):
        if not self.is_binary(data):
            if (isinstance(data, str) \
                    or isinstance(data, unicode)) \
                    and len(data.strip()) > 0 \
                    and data.strip()[0] == self.chars.lt:
                content_type = self.HTTP.ContentTypes.xml
            elif len(data) > 0 or len(parameters) > 0:
                content_type = self.HTTP.ContentTypes.form_urlencoded
            else:
                content_type = self.HTTP.ContentTypes.plain
        else: 
            content_type = self.HTTP.ContentTypes.bzip2
        return content_type

    def is_binary(self, data):
        NULL_CHR = self.chars.hash
        count, null_count    = 1.0, 0.0
        threshold = 0.20
        if isinstance(data, str) or isinstance(data, unicode):
            printable = ''.join(["%s" % ((ord(x) <= 127 \
                                          and len(repr(chr(ord(x))))  == 3 \
                                          and chr(ord(x))) \
                                          or NULL_CHR) 
                                        for x in data])
            for char in printable:
                if char == NULL_CHR:
                    null_count += 1
                count += 1
            if null_count / count > threshold:
                return True
        return False
    
    def read_resp(self, response_data, data_loc):
        # SZ: Clean code!
        if response_data:
            if isinstance(response_data, str):
                return response_data
            
            elif isinstance(response_data, dict):
                if response_data.__contains__(self.HTTP.ContentTypes.content_type):
                    if self.is_binary(response_data[self.HTTP.content]):
                        return response_data
                    if response_data[self.HTTP.ContentTypes.content_type] == self.HTTP.ContentTypes.xml:
                        return self.read_xml(response_data[self.HTTP.content], data_loc)
                    elif response_data[self.HTTP.ContentTypes.content_type] == self.HTTP.ContentTypes.html:
                        return self.read_text(response_data[self.HTTP.content])
                    elif response_data[self.HTTP.ContentTypes.content_type] == self.HTTP.ContentTypes.plain:
                        return self.read_text(response_data[self.HTTP.content])
                    elif response_data[self.HTTP.ContentTypes.content_type] == self.HTTP.ContentTypes.html:
                        return self.read_text(response_data[self.HTTP.content])
                    else:
                        # Assume Plain
                        return self.read_text(response_data[self.HTTP.content])
                
                else:
                    # Assume Plain
                    return self.read_text(response_data[self.HTTP.content])
        return None
    
    def read_text(self, plaintext):
        retval = {}
        self.request_response_info[self.res.Debug.response_data] = plaintext
        if plaintext.find(self.chars.amp) > 0:
            for i in plaintext.split(self.chars.amp):
                tmp = i.split(self.chars.eq)
                retval[tmp[0]] = tmp[1]
            return retval
        
        return plaintext
    
    def read_xml(self, xml_string, data_loc):
        # SZ: 'error' is deprecated
        error = 'error'
        self.request_response_info[self.res.Debug.response_data] = xml_string
        try:
            req_ids = {}
            if xml_string[0:5].lower() != error and len(data_loc) > 1:
                for i in xrange(0, len(data_loc), 2):
                    xml_list_node, xml_id_node = data_loc[i], data_loc[i+1]
                    req_ids[xml_list_node] = []
                    if xml_string is not None and isinstance(xml_string, str):
                        xmldoc = minidom.parseString(xml_string.strip())
                        doc_elem = xmldoc.documentElement
                        if doc_elem.nodeName == xml_list_node \
                            and hasattr(doc_elem.getAttributeNode(xml_id_node), 'value') \
                            and doc_elem.getAttributeNode(xml_id_node).value:
                            req_ids[xml_list_node].append(doc_elem.getAttributeNode(xml_id_node).value)
                        # If there are child nodes examine them
                        if doc_elem.hasChildNodes():
                            for node in doc_elem.childNodes:
                                if node is not None \
                                    and node.nodeName == xml_list_node:
                                    req_ids[xml_list_node].append(node.getAttribute(xml_id_node))
                return req_ids
            else:
                return False
        
        except AttributeError, e:
            raise IUtilsError(e)
        except xml.parsers.expat.ExpatError:
            raise IUtilsError("Expat Error: " + xml_string)
    
    def set_url(self, url):
        try:
            purl = urlparse(url)
            
            # SZ: For now only set the path
            #self.url.scheme    = purl.scheme
            #self.url.host      = purl.hostname
            #self.url.port      = purl.port
            
            self.url.path = purl.path
            self.url.query = purl.query
            return True
        except:
            return False
    
    def url_check(self, url):
        # This is in case convert_api_url is not used
        # self.url.url is deprecated
        if not hasattr(self.url, 'url'):
            self.url.url = url
        if self.url \
            and self.url.url \
            and self.url_scheme_check() \
            and self.url.host:
            if not self.url.port:
                self.url.port = 80
            # SZ: Does not assume that path must be non-empty
            if hasattr(self.url, 'path'):
                return True
        else:       # PP: is this "else" correct here?
            return False
    
    def url_scheme_check(self):
        #We'll need to build this out
        if self.url.scheme == self.HTTP.http \
            or self.url.scheme == self.HTTP.https:
            return True
        else:
            return False
    
    def reformat(self, dict):
        return self.chars.amp.join('%s=%s' % (str(n), str(v)) for n, v in dict.iteritems())
    
    def convert_api_url(self, url_path, kwargs):
        
        # Rebuild kwargs
        # ikwargs - inherited kwargs
        ikwargs = self.rebuild_kwargs(kwargs)
        
        query = ''
        for name, val in ikwargs.items():
            if isinstance(val, str) or isinstance(val, unicode):
                url_path = url_path.replace(self.chars.openbracket + name.upper() + self.chars.closebracket, val)
        # Remove any unmatched brackets
        url_path = self.remove_unmatched_vars(url_path)
        
        # Set the path
        try:
            qm_marker = url_path.index(self.chars.qm)
            self.url.path = url_path[:qm_marker]
        except ValueError:
            self.url.path = url_path
        
        # Set the query
        if url_path.find(self.chars.qm) > 0:
            query = url_path[url_path.find(self.chars.qm)+1:]
            if not query:
                url_path = url_path[0:-1]
        self.url.query = query
        
        # Set the entire url
        self.url.url = self.url.base + url_path
        
        # Add to debug
        self.request_response_info[self.res.Debug.url] = self.url.url
        
        return self.url.url
    
    def remove_unmatched_vars(self, path):
        lst = []
        count = 0
        for i in path:
            if i == self.chars.openbracket or i == self.chars.closebracket:
                lst.append(count)
            count += 1
        lst.sort()
        if len(lst) % 2 == 0:
            while len(lst) > 0:
                b = lst.pop()
                a = lst.pop()
                path = path[0:a] + path[b+1:]
        return path
    
    def get_response(self, api_config_name, api_method, api_url, resp_data_loc, app_info, req_data=None, **kwargs):
        req_data = req_data or {}
        retval = None
        
        # Reset debug info
        self.request_response_info = {}
        parameters = {}
        
        # Include parameters
        if kwargs.has_key(self.res.parameters) \
            and kwargs[self.res.parameters] \
            and len(kwargs[self.res.parameters]) > 0:
            
            # SZ: parameters should remain a dict
            # transform to a string in IClient
            # transform to a string in request
            # transform to a string for convert_api_url()
            
            # Set the parameters
            parameters = kwargs[self.res.parameters]
            kwargs[self.res.parameters] = urllib.urlencode(parameters)
        
        # Call http_conn(...)
        if api_method and api_url:
            self.request_response_info[self.res.Debug.method] = api_method
            
            url = self.convert_api_url(api_url, kwargs)
            try:
                res = self.http_conn(api_method, url, app_info, parameters, req_data)
                if res is not None:
                    retval = self.read_resp(res, resp_data_loc)
                    # PRD - Processed Response Data
                    self.request_response_info['prd'] = retval
            except IUtilsError as e:
                self.request_response_info['response_status'] = 500                 # maybe also ship the error number via the exception?
                self.request_response_info['response_data'] = e.value
        
        if kwargs[self.res.Debug.debug]: 
            self.print_debug_info()
        
        return self.request_response_info
    
    def rebuild_kwargs(self, kwargs):
        tmp_kwargs = {}
        for name, value in kwargs.items():
            if value:
                tmp_kwargs[name] = value
        return tmp_kwargs
    
    def print_debug_info(self):
        for n,v in self.request_response_info.items():
            print(n, self.chars.hyphen*10 + self.chars.gt, v)
        print(self.chars.eq*40)
