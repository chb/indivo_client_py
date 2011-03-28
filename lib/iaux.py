
class Reserved:

  port          = 'port'
  host          = 'host'
  scheme        = 'scheme'
  default_port  = 'default_port'

  consumer_key    = 'consumer_key'
  consumer_secret = 'consumer_secret'

  oauth_token         = 'oauth_token'
  oauth_token_secret  = 'oauth_token_secret'

  parameters    = 'parameters'

  app_type    = 'app_type'

  class Debug:
    debug         = 'debug'
    response_data = 'response_data'
    oauth_header  = 'oauth_header'
    method        = 'request_method'
    data          = 'request_data'
    url           = 'request_url'
    status        = 'response_status'
    content_type  = 'response_content_type'

  class Dir:
    lib     = 'lib'
    config  = 'config'

class HTTP:

  http    = 'http'
  https   = 'https'
  content = 'content'

  # This is the var name content type returned 
  # from httplib.HTTPConnection.getheaders()
  content_type = 'content-type'

  class Status:
    ok                = 200
    redirect          = 302
    invalid_request   = 400
    permission_denied = 403
    not_found         = 404
    server_error      = 500

  class Errors:
    permission_denied   = "Permission Denied"
    server_error        = "Server Error"
    server_not_ready    = "Server Not Ready"
    cannot_send_request = "Cannot send request"
    not_conntect        = "Not Connected"
    cannot_send_header  = "Cannot Send Header"
    socket_error        = "Socket Error"
    general_exception   = "General HTTP Exception"

  class ContentTypes:
    content_type    = 'content_type'

    xml             = 'application/xml'
    bzip2           = 'application/bzip2' 
    plain           = 'text/plain'
    html            = 'text/html'
    html_utf8       = 'text/html; charset=utf-8'
    form_urlencoded = 'application/x-www-form-urlencoded'


class Chars:


  def __init__(self):
    self.newline      = '\n'
    self.tab          = '\t'
    self.slash        = '/'
    self.backslash    = '\\'
    self.colon        = ':'
    self.period       = '.'
    self.comma        = ','
    self.lt           = '<'
    self.gt           = '>'
    self.qm           = '?'
    self.amp          = '&'
    self.eq           = '='
    self.quot         = '"'
    self.singquot     = "'"
    self.underscore   = '_'
    self.hyphen       = '-'
    self.openparen    = '('
    self.closeparen   = ')'
    self.space        = ' '
    self.hash         = '#'
    self.openbracket  = '{'
    self.closebracket = '}'
    self.plus         = '+'

class Url:


  def __init__(self, scheme, host, port, path='', query=''):
    self.res                = Reserved()
    self.chars              = Chars()
    self.default_port       = '80'
    self.default_ssl_port   = '443'
    self.scheme             = scheme
    self.host               = host
    self.port               = port
    self.path               = path
    self.query              = query
    self.portext            = self.get_portext(self.port)
    self.base               = self.get_base_url()

  def get_portext(self, port):
    portext = ''
    try:
      if port is not None and isinstance(port, int):
        port = str(port)
      elif isinstance(port, str):
        pass
      else:
        raise ValueError
    except ValueError:
      self.error_out(ValueError)

    if not (port == self.default_port or port == self.default_ssl_port):
      portext = self.chars.colon + port
    return portext

  def get_base_url(self):
    return self.scheme + \
           self.chars.colon + \
           self.chars.slash + \
           self.chars.slash + \
           self.host + self.portext

