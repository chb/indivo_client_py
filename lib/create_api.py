import os
import sys
import xml_utils
import datetime
from iaux import Reserved, Chars

class CreateAPI():


  def __init__(self):
    path = os.path.abspath(os.path.dirname(__file__))

    self.char = Chars()
    signature = {'call' : ['name', 'method', 'url'], 'response' : ['element', 'attribute']}
    self.api, unused  = xml_utils.xml2dict(path + '/../config/api.xml', signature)

  def get_params(self, url):
    params = []
    while url.find(self.char.closebracket) - url.find(self.char.openbracket) > 0:
      params.append(url[url.find(self.char.openbracket)+1:url.find(self.char.closebracket)].lower())
      url = url[url.find(self.char.closebracket)+1:]
    return params
  
  def write_api(self, f):
    data = 'data'
    debug = 'debug'
    slf = 'self'
    python_def = 'def'
    app_info = 'app_info'
    path = os.path.abspath(os.path.dirname(__file__))

    f = open(path + '/' + f + '.py', 'w')
    f.write(self.get_file_header())

    # SZ: FIX!
    call_func = """\n\n\tdef __init__(self, utils_obj):\n\t\tself.utils_obj = utils_obj\n\t\tself.call_count = 0\n\n\tdef call(self, *args):\n\t\tif hasattr(self, inspect.stack()[1][3]):\n\t\t\tcount = 1\n\t\t\tkwargs = {}\n\t\t\tmethod = getattr(self, inspect.stack()[1][3])\n\t\t\tmethod_arguments = inspect.getargspec(method)[0]\n\t\t\tfor arg in args:\n\t\t\t\tkwargs[method_arguments[count]] = arg\n\t\t\t\tcount += 1\n\t\t\tself.call_count += 1\n\t\t\treturn method(**kwargs)\n\t\telse:\n\t\t\treturn False"""
    f.write(call_func)

    for method in self.api:
      funcname = method['call']['name']
      api_url = method['call']['url']  
      api_method = method['call']['method']  
      resp_data = self.get_resp_data(method)
      params = self.get_params(api_url)
      get_resp_params = ''
      for p in params: 
        get_resp_params +=  p+self.char.eq+p + self.char.comma + self.char.space
      sparams = ''
      eqempty =   self.char.eq+self.char.singquot+self.char.singquot + \
                  self.char.comma + \
                  self.char.space
      if params:
        sparams = params[0] + eqempty
        if len(sparams) > 1:
          sparams = eqempty.join(params) + eqempty
      f.write(
            self.get_func_def(python_def, funcname, slf, app_info, sparams, data, debug) + \
            self.get_ret_val(funcname, api_method, api_url, resp_data, app_info, data, get_resp_params, debug))
    f.close()
    return True

  def get_resp_data(self, method):
    # SZ: very, very inefficient.  clean up
    resp_data = []
    if method.has_key('response'):
      if method['response'].has_key('element') and \
          method['response'].has_key('attribute'):
        if len(method['response']['element']) > 1 and \
          len(method['response']['attribute']) > 1:
          resp_data.append(method['response']['element'][0])
          resp_data.append(method['response']['attribute'][0])
          resp_data.append(method['response']['element'][1])
          resp_data.append(method['response']['attribute'][1])
        elif len(method['response']['element']) == 1 and \
              len(method['response']['attribute']) == 1:
          resp_data.append(method['response']['element'][0])
          resp_data.append(method['response']['attribute'][0])
    return resp_data

  def get_file_header(self):
    now = datetime.datetime.now().strftime("on %A %m/%d/%Y at %H:%M:%S") 
    msg_line1 = "do not write to this file"
    msg_line2 = "this file was automatically generated " + now
    import_inspect= "import inspect"

    define_class = "class API:"

    file_header = self.char.hash * 80 + \
                  self.char.newline + \
                  self.char.hash + \
                  msg_line1.upper() + \
                  self.char.newline + \
                  self.char.hash + \
                  msg_line2.upper() + \
                  self.char.newline + \
                  self.char.hash * 80 + \
                  self.char.newline + \
                  import_inspect + self.char.newline + \
                  define_class + \
                  self.char.newline
    return file_header

  def get_func_def(self, python_def, funcname, slf, app_info, sparams, data, debug):
    bool_tuple = ("False", "True")
    return  self.char.newline + \
            self.char.newline + \
            self.char.tab + \
            python_def + \
            self.char.space + \
            funcname + \
            self.char.openparen + \
            slf + \
            self.char.comma + \
            self.char.space + \
            app_info + \
            self.char.comma + \
            sparams + \
            self.char.space + \
            data + \
            self.char.eq + \
            'None' + \
            self.char.comma + \
            self.char.space + \
            debug + \
            self.char.eq + \
            bool_tuple[0] + \
            self.char.closeparen + \
            self.char.colon + \
            self.char.space
  
  def get_ret_val(self, funcname, api_method, api_url, resp_data, app_info, data, get_resp_params, debug):
    python_return = 'return'
    get_response = 'self.utils_obj.get_response'
    new_param = self.char.space + self.char.newline + self.char.tab + self.char.tab + self.char.tab + self.char.tab + self.char.tab
    return  self.char.newline + \
            self.char.tab + \
            self.char.tab + \
            python_return + \
            self.char.space + \
            get_response + \
            self.char.openparen + \
            self.char.singquot + \
            funcname + \
            self.char.singquot + \
            self.char.comma + \
            new_param + \
            self.char.singquot + \
            api_method + \
            self.char.singquot + \
            self.char.comma + \
            new_param + \
            self.char.singquot + \
            api_url + \
            self.char.singquot + \
            self.char.comma + \
            new_param + \
            str(resp_data) + \
            self.char.comma + \
            new_param + \
            app_info + \
            self.char.comma + \
            new_param + \
            data + \
            self.char.comma + \
            new_param + \
            get_resp_params + \
            debug + \
            self.char.eq + \
            debug + \
            self.char.closeparen + \
            self.char.newline

if __name__ == '__main__':
  ca = CreateAPI() 
  ca.write_api('api')
