from lib.client import IndivoClient

token = 'HpbR4kdu0X41gyKMMCu1'
token_secret = 'LKExpgK5ZqvFhqW83rWa'
pha_client = IndivoClient('test_client', '057afcd440f7', {'host' : 'x-staging.indivo.org', 'port' : '8000'})
pha_client.update_token(oauth_token={'oauth_token' : token, 'oauth_token_secret' : token_secret})

record_id='c2dd7ab2-4929-4f16-a571-a0a0a53de219'
document_id='3bd74520-bdd9-4c6a-8974-88bef33e89bb'
chrome_client = IndivoClient('chrome', 'chrome')
chrome_client.create_session({'account_id' : 'stevezabak@informedcohort.org', 'username' : 'stevezabak', 'user_pass' : 'abc'})
chrome_client.read_record(record_id=record_id)
chrome_client.get_document_relate(document_id=document_id, record_id=record_id, rel_type='Annotation', debug=True)
