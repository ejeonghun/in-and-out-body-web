# API URL : https://sens.apigw.ntruss.com/sms/v2
# API Swagger : https://sens.apigw.ntruss.com/apigw/swagger-ui?productId=plv61henn8&apiId=j5tgfxp2ba&stageId=a0y11xe7vi&region=KR

# API Header 
# Content-Type : application/json
# x-ncp-apigw-timestamp : 
# x-ncp-iam-access-key :
# x-ncp-apigw-signature-v2 : 

import sys
import os
import hashlib
import hmac
import base64
import requests
import time
import json

# import dotenv
# dotenv.load_dotenv(override=True)

timestamp=int(time.time() * 1000)
timestamp=str(timestamp)

access_key = os.environ['NCP_ACCESS_KEY']				# access key id (from portal or Sub Account)
secret_key = os.environ['NCP_SECRET_KEY']		# secret key (from portal or Sub Account)

url="https://sens.apigw.ntruss.com"
uri= f"/sms/v2/services/{os.environ['NCP_SESN_SERVICE_ID']}/messages"


#print(access_key)
#print(secret_key)
#print(uri)

def	make_signature():
	global secret_key
	global access_key
	global timestamp
	global url
	global uri
	secret_key = bytes(secret_key, 'UTF-8')
	method = "POST"
	message = method + " " + uri + "\n" + timestamp + "\n" + access_key
	message = bytes(message, 'UTF-8')
	signingKey = base64.b64encode(hmac.new(secret_key, message, digestmod=hashlib.sha256).digest())
	return signingKey


header = {

"Content-Type": "application/json; charset=utf-8",
"x-ncp-apigw-timestamp": timestamp, 
"x-ncp-iam-access-key": access_key,
"x-ncp-apigw-signature-v2": make_signature()
}


data = {
    "type":"SMS",
    "from":"07088608188",
    "content":contents,
	"subject":"SENS",
    "messages":[
        {
            "to":number,
        }
    ]
}


res = requests.post(url+uri,headers=header,data=json.dumps(data))
datas=json.loads(res.text)
reid=datas['requestId']

print("메시지 전송 상태")
print(res.text+"\n")