import os
import sys
import inspect
import traceback

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

class APIConnectorError(RuntimeError):
  pass

class DataStore:

  def __init__(self):
    self.reset()

  def reset(self):
    self.app_info     = {}
    self.user_info    = {}
    self.account_id   = ''
    self.record_id    = ''
    self.document_id  = ''
    self.carenet_id   = ''
    self.app_id       = ''

  def values(self):
    return {  'app_info'    : self.app_info,
              'user_info'   : self.user_info,
              'account_id'  : self.account_id,
              'record_id'   : self.record_id,
              'document_id' : self.document_id,
              'carenet_id'  : self.carenet_id,
              'app_id'      : self.app_id}

class APIConnectorError(RuntimeError):
  def __init__(self, msg='Unknown Error', include_traceback=True):
    self.msg = msg
    if include_traceback:
      self.traceback = traceback.extract_stack()

CONTENT, DATA, PARAMETERS, OAUTH_TOKEN, OAUTH_TOKEN_SECRET = ('content', 'data', 'parameters', 
                                                              'oauth_token', 'oauth_token_secret')

class APIConnector:

  def __init__(self, consumer_key, consumer_secret, connection_params=None):

    self.scheme = 'http'
    self.host = 'localhost'
    #self.host = 'indivo.genepartnership.org'
    #self.host = 'indivo-staging.informedcohort.org'
    #self.host = 'indivobig.genepartnership.org'
    #self.host = 'x-staging.indivo.org'
    self.port = '8000'

    if connection_params:
      if connection_params.has_key('scheme'): self.scheme = connection_params['scheme']
      if connection_params.has_key('host'):   self.host = connection_params['host']
      if connection_params.has_key('port'):   self.port = connection_params['port']

    if self.scheme and self.host and self.port:
      self.utils_obj = IUtils(self.scheme, self.host, self.port)
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
      retval = self.utils_obj.http_conn(method, url, self.ds.app_info, parameters=parameters, data=data)
      if retval:
        if isinstance(retval, dict) and retval.has_key(CONTENT):
          return retval[CONTENT]
        else:
          return retval
    return False

  def __getattr__(self, func_name):
    cr = CallRes()

    def handle_response(response):
      PRD  = 'prd'
      # SZ: Abstarct this out
      prd_vals = {'Account' : 'account_id', 'Document' : 'document_id', 'Record' : 'record_id'}
      for prd_name, attr in prd_vals.items():
        if response.has_key(PRD) and \
          isinstance(cr.response[PRD], dict) and \
          response[PRD].has_key(prd_name):
          id = response[PRD][prd_name]
          if len(id) > 0 and attr:
            setattr(self.ds, attr, id[0])
      return True

    def internal_getattr(*args, **kwargs):
      if hasattr(self.api, func_name):
        _args, _, _, _defaults = inspect.getargspec(getattr(self.api, func_name))
        kw = {}
        count = 0
        for arg in _args[1:]:
          if kwargs.has_key(arg):
            kw[arg] = kwargs[arg]  
          elif hasattr(self.ds, arg) and \
            not (getattr(self.ds, arg) is None or getattr(self.ds, arg) == ''):
              kw[arg] = getattr(self.ds, arg)
          else:
            kw[arg] = _defaults[_args.index(arg) - (len(_args) - len(_defaults))]
          count += 1
        cr.response = getattr(self.api, func_name)(**kw)
        handle_response(cr.response)
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
    prd_vals = {  'Account'       : 'account_id',
                  'Document'      : 'document_id',
                  'Entry'         : None,
                  'Measurements'  : None,
                  'Record'        : 'record_id',
                  'Result'        : None}
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
            #  return True
          #else:
          #  return False
      #if call_res[PRD].has_key(CONTENT):
      #  return call_res[PRD][CONTENT]
      return call_res
    else:
      return call_res
      #if call_res.has_key(PRD):
      #  raise APIConnectorError(call_res[PRD], include_traceback=True)
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
    USER_EMAIL = 'user_email'
    ACCOUNT_ID = 'account_id'
    if not (user.has_key(USER_EMAIL) or user.has_key(ACCOUNT_ID)):
      raise APIConnectorError("No user email or account id when posting account")

    account_id = None
    if user.has_key(USER_EMAIL):
      account_id = user[USER_EMAIL]
    elif user.has_key(ACCOUNT_ID):
      account_id = user[ACCOUNT_ID]

    if account_id:
      primary_secret = user.get('primary_secret_p', 0)
      secondary_secret = user.get('secondary_secret_p', 0)
      password = user.get('user_pass', '')

      # There is a difference between app_type chrome without auth and admin
      return self.api.call(  self.ds.app_info,
                            { 'account_id'          : account_id,
                              'primary_secret_p'    : primary_secret,
                              'secondary_secret_p'  : secondary_secret,
                              'password'            : password})
    return False

  def set_record_id(self, id):
    self.record_id, self.ds.record_id = id, id

  def set_app_id(self, id):
    self.app_id, self.ds.app_id = id, id

  def create_session(self, user):
    if user.has_key('username') and user.has_key('user_pass'):
      chrome_auth   = {'username' : user['username'], 'password' : user['user_pass']}
      chrome_token = self.api.call(self.ds.app_info, chrome_auth)['prd']
      if isinstance(chrome_token, dict):
        self.ds.app_info.update(chrome_token)
        return chrome_token
    return False

  def update_token(self, oauth_token={}):
    if oauth_token and \
        isinstance(oauth_token, dict) and \
        oauth_token.has_key(OAUTH_TOKEN) and \
        oauth_token.has_key(OAUTH_TOKEN_SECRET):
      self.ds.app_info[OAUTH_TOKEN] = oauth_token[OAUTH_TOKEN]
      self.ds.app_info[OAUTH_TOKEN_SECRET] = oauth_token[OAUTH_TOKEN_SECRET]

  def get_surl_credentials(self):
    """Requires there to be a token and secret set

    produces a token and secret dictionary for SURL (signing URLs).
    """

    if self.ds.app_info.has_key(OAUTH_TOKEN) and \
        self.ds.app_info.has_key(OAUTH_TOKEN_SECRET):
      token = self.ds.app_info[OAUTH_TOKEN]
      secret = base64.b64encode(hmac.new(self.ds.app_info[OAUTH_TOKEN_SECRET], "SURL-SECRET", hashlib.sha1).digest())
      return {'token' : token, 'secret' : secret}
    return False
