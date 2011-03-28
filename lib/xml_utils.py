import os
from xml.dom import minidom

def get_data(api, api_nonunique, method_dom_objs, signature):
  tmp_dict = {}
  for inner_method_domobj in method_dom_objs.childNodes:
    tmp_dict_2 = {}
    node_name = inner_method_domobj.localName
    if node_name:
      tmp_dict[node_name] = {}
      tmp_dict_2[node_name] = {}
      for element in signature[node_name]:
        level = []
        if inner_method_domobj.hasAttribute(element):
          level.append(inner_method_domobj.getAttribute(element))
          if inner_method_domobj.hasChildNodes():
            for ii in inner_method_domobj.childNodes:
              if ii.localName and ii.hasAttribute(element):
                level.append(ii.getAttribute(element))
        if node_name == 'response':
          tmp_dict[node_name][element] = level
          tmp_dict_2[node_name][element] = level
        else:
          tmp_dict[node_name][element] = inner_method_domobj.getAttribute(element)
          tmp_dict_2[node_name][element] = inner_method_domobj.getAttribute(element)
    if tmp_dict_2:
      api_nonunique.append(tmp_dict_2)
  if tmp_dict:
    api.append(tmp_dict)
  return api, api_nonunique


def xml2dict(xml, signature):
  """
  For parsing api.xml

  TODO: SZ: Make recursive!
  """
  api = []
  api_nonunique = []
  try:
    if os.path.exists(xml):
      xmldoc = minidom.parse(xml)
      # SZ: Huge hack.  FIX!
      for method_dom_objs in xmldoc.childNodes[0].childNodes: api, api_nonunique = get_data(api, api_nonunique, method_dom_objs, signature)
    else:
      xmldoc = minidom.parseString(xml)
      api, api_nonunique = get_data(api, api_nonunique, xmldoc.childNodes[0], signature)
  except:
    return False
  return api, api_nonunique
