from client import IndivoClient
from xml.dom import minidom as XML

# Need to pass these in to the client
SERVER_PARAMS = {"api_base": "http://sandbox.indivohealth.org:8000",
                 "authorization_base": "http://sandbox.indivohealth.org"}
CONSUMER_PARAMS = {"consumer_key": "sampleweb@apps.indivo.org",
                   "consumer_secret": "yourwebapp"}

# If we already had a token (access token, request token, or session token), it should be formatted
# like this. We won't use this in the example.
RESOURCE_TOKEN = {"oauth_token": "asdfdsfa",
                  "oauth_token_secret": "adfasdf"}

# Set up the client (with no token): two-legged oauth only
client = IndivoClient(SERVER_PARAMS, CONSUMER_PARAMS, pha_email=CONSUMER_PARAMS["consumer_key"])

# make the get_version call, and print it out
resp, content = client.get_version(body={'a':'b', 'c':'d'})
if resp['status'] != '200':
    raise Exception("Bad Status: %s"%resp['status'])
print "Indivo Version: %s"%content

# make a two-legged oauth call: post an app-specific document
mydoc = "<xml>My sweet document</xml>"
resp, content = client.app_document_create(body=mydoc, content_type='application/xml')
if resp['status'] != '200':
    raise Exception("Bad Status: %s"%resp['status'])
print "Added app-specific doc: %s"%mydoc

# read the document back
doc_id = XML.parseString(content).firstChild.getAttribute('id')
resp, content = client.app_specific_document(document_id=doc_id)
if resp['status'] != '200':
    raise Exception("Bad Status: %s"%resp['status'])
if content != mydoc:
    raise Exception("Read back doc, but contents differed!")
print "read doc back: %s"%content
print "Response object looks like: %s"%resp
