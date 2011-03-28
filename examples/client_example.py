from lib.client import IndivoClient

client = IndivoClient('chrome', 'chrome')
client.create_session({ 'user_email'  : 'steve.zabak@childrens.harvard.edu', 
                        'user_pass'   : 'abc'})

client.read_record(record_id='b4a05559-31f1-4764-9c3d-324d06704c9c')
client.read_documents()
