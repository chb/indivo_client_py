import os
import sys
import inspect
import traceback

from django.test.client import Client

API_FILENAME = 'api'

try:
    from api import API
except ImportError:
    from create_api import CreateAPI
    if CreateAPI().write_api(API_FILENAME):
        # Hack
        import time; time.sleep(1)
        try:
            from api import API
        except ImportError:
            raise ImportError, "You need to run the create_api script. See README."

from iutils import IUtils

import hashlib, hmac, base64

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + '/..')

class CallRes:
    def __init__(self, *args, **kwargs): self.response = {}; pass
    def __call__(self, *args, **kwargs): return self.response

class DataStore:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.app_info    = {}
        self.user_info   = {}
        self.account_id  = ''
        self.record_id   = ''
        self.document_id = ''
        self.carenet_id  = ''
        self.app_id      = ''
    
    def values(self):
        return {'app_info': self.app_info,
               'user_info': self.user_info,
              'account_id': self.account_id,
               'record_id': self.record_id,
             'document_id': self.document_id,
              'carenet_id': self.carenet_id,
                  'app_id': self.app_id}

class APIConnectorError(RuntimeError):
    def __init__(self, msg='Unknown Error', include_traceback=True):
        self.msg = msg
        if include_traceback:
            self.traceback = traceback.extract_stack()

CONTENT, DATA, PARAMETERS, OAUTH_TOKEN, OAUTH_TOKEN_SECRET = ('content', 'data', 'parameters', 'oauth_token', 'oauth_token_secret')

class APIConnector:
    def __init__(self, consumer_key, consumer_secret, connection_params=None):

        self.scheme = 'http'
        self.host = 'testserver'
        #self.host = 'indivo.genepartnership.org'
        #self.host = 'indivo-staging.informedcohort.org'
        #self.host = 'indivobig.genepartnership.org'
        #self.host = 'x-staging.indivo.org'
        self.port = '80'

        if connection_params:
            if connection_params.has_key('scheme'): self.scheme = connection_params['scheme']
            if connection_params.has_key('host'):   self.host = connection_params['host']
            if connection_params.has_key('port'):   self.port = connection_params['port']

        django_client = Client()
        if self.scheme and self.host and self.port:
            self.utils_obj = IUtils(self.scheme, self.host, self.port, django_client)
        else:
            raise APIConnectorError("Scheme, host, port needed")
        
        self.api = API(self.utils_obj)
        self.ds = DataStore()
        self.ds.reset()
        self.ds.app_info['consumer_key'] = consumer_key
        self.ds.app_info['consumer_secret'] = consumer_secret 
        self.count = 0
    
    def call(self, method, url, options=None):
        options = options or {}
        
        data = {}
        oauth_token = {}
        parameters = {}
        if options.has_key(DATA): data = options[DATA]
        if options.has_key(PARAMETERS): parameters = options[PARAMETERS]
        #if options.has_key(OAUTH_TOKEN): oauth_token = options[OAUTH_TOKEN]
        #if options.has_key(OAUTH_TOKEN_SECRET): oauth_token_secret = options[OAUTH_TOKEN_SECRET]
        if self.ds.app_info:
            try:
                retval = self.utils_obj.http_conn(method, url, self.ds.app_info, parameters=parameters, data=data)
            except:
                return False
            
            if retval:
                if isinstance(retval, dict) and retval.has_key(CONTENT):
                    return retval[CONTENT]
                else:
                    return retval
        return False

    def _handle_response(self, response):
        PRD  = 'prd'
        # SZ: Abstarct this out
        prd_vals = {'Account' : 'account_id', 'Document' : 'document_id', 'Record' : 'record_id'}
        for prd_name, attr in prd_vals.items():
            if response \
                    and response.has_key(PRD) \
                    and isinstance(response[PRD], dict) \
                    and response[PRD].has_key(prd_name):
                id = response[PRD][prd_name]
                if len(id) > 0 and attr:
                    setattr(self.ds, attr, id[0])
        return True

    
    def __getattr__(self, func_name):
        cr = CallRes()
        
        def internal_getattr(*args, **kwargs):
            if hasattr(self.api, func_name):
                _args, _, _, _defaults = inspect.getargspec(getattr(self.api, func_name))
                kw = {}
                count = 0
                for arg in _args[1:]:
                    if kwargs.has_key(arg):
                        kw[arg] = kwargs[arg]    
                    elif hasattr(self.ds, arg) \
                        and not (getattr(self.ds, arg) is None or getattr(self.ds, arg) == ''):
                            kw[arg] = getattr(self.ds, arg)
                    else:
                        kw[arg] = _defaults[_args.index(arg) - (len(_args) - len(_defaults))]
                    count += 1
                cr.response = getattr(self.api, func_name)(**kw)
                self._handle_response(cr.response)
                return cr
            return False
        return internal_getattr
    
    def __call__(self, func_name, *args, **kwargs):
        if hasattr(self.api, func_name):
            self.count += 1
            kw = self._get_kwargs(func_name, args, kwargs)
            call_res = getattr(self.api, func_name)(**kw)
            return self.post_call(call_res)
        else:
            raise APIConnectorError("No such API call " + func_name)
    
    def _get_kwargs(self, func_name, args, kwargs):
        SELF = 'self'
        _kw = {}
        _args, _, _, _defaults = inspect.getargspec(getattr(self.api, func_name))
        for arg in _args:
            # Get passed in kwarg
            if len(kwargs) > 0 and kwargs.has_key(arg):
                _kw[arg] = kwargs[arg]
            # If it is an arg it is required, therefore must be non-empty
            elif hasattr(self.ds, arg):
                if not (getattr(self.ds, arg) is None or getattr(self.ds, arg) == ''):
                    _kw[arg] = getattr(self.ds, arg)
                else:
                    raise APIConnectorError(arg + ' is missing')
            # Get passed in arg
            elif len(args) > 1 and args[1].has_key(arg):
                _kw[arg] = args[1][arg]
            # Get defaults
            else:
                _kw[arg] = _defaults[_args.index(arg) - (len(_args) - len(_defaults))]
        if _kw.has_key(SELF):
            del _kw[SELF]
        return _kw

    # SZ: Remove this from IndivoClient
    def post_call(self, call_res):
        PRD  = 'prd'
        CONTENT = 'content'
        prd_vals = {'Account': 'account_id',
                   'Document': 'document_id',
                      'Entry': None,
               'Measurements': None,
                     'Record': 'record_id',
                     'Result': None}
        if call_res['response_content_type'] == 'text/plain':
            return call_res[PRD]
        elif call_res.has_key(PRD) and isinstance(call_res[PRD], dict):
            for prd_name, attr in prd_vals.items():
                if call_res[PRD].has_key(prd_name):
                    id = call_res[PRD][prd_name]
                    if len(id) > 0:
                        if attr:
                            setattr(self.ds, attr, id[0])
                            #return getattr(self.ds, attr)
                        #else:
                        #    return True
                    #else:
                    #    return False
            #if call_res[PRD].has_key(CONTENT):
            #    return call_res[PRD][CONTENT]
            return call_res
        else:
            return call_res
            #if call_res.has_key(PRD):
            #    raise APIConnectorError(call_res[PRD], include_traceback=True)
        raise APIConnectorError()








# SZ: Indivo Client

OAUTH_TOKEN = 'oauth_token'
OAUTH_TOKEN_SECRET = 'oauth_token_secret'

class IndivoClientError(RuntimeError):
    def __init__(self, msg='Unknown Error', include_traceback=True):
        self.msg = msg
        if include_traceback:
            self.traceback = traceback.extract_stack()

class IndivoClient(APIConnector):
    
    def create_account(self, user):
        
        # set an account_id
        account_id = user.get('account_id') or user.get('user_email') or user.get('contact_email')
        if account_id is None:
            raise APIConnectorError("No user email or account id when posting account")
        
        user['account_id'] = account_id
        user['contact_email'] = user.get('contact_email') or account_id
        
        # There is a difference between app_type chrome without auth and admin
        return self.api.call(self.ds.app_info, user)
    
    def create_record(self, data=None):
        """
        A contact document is required when creating a record. UI for now only provides given- and family-name and an
        email address, so create a very limited document XML for now:
        <Contact xmlns="http://indivo.org/vocab/xml/documents#">
            <name>
                <fullName>record.fullName OR record.givenName record.familyName</fullName>
                <givenName>record.givenName</givenName>
                <familyName>record.familyName</familyName>
            </name>
            <email type="personal">record.email</email>
        </Contact>
        """
        
        # generate contact XML, if we were passed a data dictionary
        if hasattr(data, 'get'):
            givenName = data.get('givenName', '')
            familyName = data.get('familyName', '')
            spacer = ' ' if givenName and familyName else ''
            fullName = data.get('fullName', '%s%s%s' % (givenName, spacer, familyName))
            email = data.get('email', '')
        
            if not fullName and not givenName and not familyName:
                raise IOError(400, 'A name is needed to create a new record')
        
            xml = '''<Contact xmlns="http://indivo.org/vocab/xml/documents#">
                       <name>
                         <fullName>%s</fullName>
                         <givenName>%s</givenName>
                         <familyName>%s</familyName>
                       </name>
                       <email type="personal">%s</email>
                     </Contact>''' % (fullName, givenName, familyName, email)

            old_style = False

        # Assume we were passed a valid contact xml string. If not, this will fail lower down.
        else:
            xml = data
            old_style = True

        ret = self.api.call(self.ds.app_info, xml)
        if old_style:
            cr = CallRes()
            cr.response = ret
            self._handle_response(cr.response)
            return cr
        
        return ret
    
    def set_record_id(self, id):
        self.record_id, self.ds.record_id = id, id

    def set_app_id(self, id):
        self.app_id, self.ds.app_id = id, id

    def create_session(self, user):
        chrome_auth = {}
        if user.has_key('username'):
            chrome_auth['username'] = user['username']
            if user.has_key('user_pass'):
                chrome_auth['password'] = user['user_pass']
            elif user.has_key('system'):
                chrome_auth['system'] = user['system']
            else:
                raise IOError(400, 'Neither a password nor an alternate authentication system supplied')
            
            res = self.api.call(self.ds.app_info, chrome_auth)
            chrome_token = res.get('prd', None)
            status = res.get('response_status', 500)
            if 200 != status:
                raise IOError(status, chrome_token or res.get('response_data', 'Unknown Server Error'))
            
            # we got something after a 200, pass it on
            if isinstance(chrome_token, dict):
                self.ds.app_info.update(chrome_token)
                return chrome_token
        
        # this previously simply returned False
        raise IOError(400, 'No username supplied')

    def update_token(self, oauth_token={}):
        if oauth_token \
            and isinstance(oauth_token, dict) \
            and oauth_token.has_key(OAUTH_TOKEN) \
            and oauth_token.has_key(OAUTH_TOKEN_SECRET):
            self.ds.app_info[OAUTH_TOKEN] = oauth_token[OAUTH_TOKEN]
            self.ds.app_info[OAUTH_TOKEN_SECRET] = oauth_token[OAUTH_TOKEN_SECRET]

    def get_surl_credentials(self):
        """
        Requires there to be a token and secret set
        produces a token and secret dictionary for SURL (signing URLs).
        """
        
        if self.ds.app_info.has_key(OAUTH_TOKEN) \
            and self.ds.app_info.has_key(OAUTH_TOKEN_SECRET):
            token = self.ds.app_info[OAUTH_TOKEN]
            secret = base64.b64encode(hmac.new(self.ds.app_info[OAUTH_TOKEN_SECRET], "SURL-SECRET", hashlib.sha1).digest())
            return {'token' : token, 'secret' : secret}
        return False
