from lib.client import IndivoClient

INDIVO_SERVER = {'host':'192.168.1.101','port':'8000'}

record_id = '52df6370-3810-4d20-a456-034c4d71454c'

admin_client = IndivoClient('chrome_key','chrome_secret', INDIVO_SERVER)

# Missioncontrol sends message to Indivo


for i in range(100):
  msg_id, msg_subject, msg_body  = 'test', 'hello world '+str(i) , 'testing '+str(i)
  admin_client.message_record(record_id = record_id, message_id = msg_id, data={'subject' : msg_subject, 'body' : msg_body})
  admin_client.record_notify(record_id = record_id, data={'content':'testing '+str(i)})
  

# # Missioncontrol gives access to problems@apps.indivo.org
# token = admin_client.setup_app( record_id = record_id, 
#                                 app_id = 'problems@apps.indivo.org').response['prd']
# user_client = IndivoClient('problems@apps.indivo.org','problems', INDIVO_SERVER)
# user_client.update_token(token)
# 
# # Problems app gets the messages
# user_client.get_messages(record_id = record_id)
