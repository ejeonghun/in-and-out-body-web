# API URL : https://sens.apigw.ntruss.com/sms/v2
# API Swagger : https://sens.apigw.ntruss.com/apigw/swagger-ui?productId=plv61henn8&apiId=j5tgfxp2ba&stageId=a0y11xe7vi&region=KR

# API Header 
# Content-Type : application/json
# x-ncp-apigw-timestamp : 
# x-ncp-iam-access-key :
# x-ncp-apigw-signature-v2 : 

import os
import hashlib
import hmac
import base64
import requests
import time
import json
import random

class NCPSMSSender:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NCPSMSSender, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.access_key = os.environ.get('NCP_ACCESS_KEY')
        self.secret_key = os.environ.get('NCP_SECRET_KEY')
        self.service_id = os.environ.get('NCP_SESN_SERVICE_ID')
        self.sender_number = os.environ.get('NCP_SENDER_NUMBER')
        self.message_content = os.environ.get('MESSAGE_CONTENT')
        
        self.url = "https://sens.apigw.ntruss.com"
        self.uri = f"/sms/v2/services/{self.service_id}/messages"
        
        self._initialized = True
    

    def _make_signature(self, timestamp): # 타임스탬프를 받아서 API 키를 암호화 - 시그니처를 생성
        secret_key_bytes = bytes(self.secret_key, 'UTF-8')
        method = "POST"
        message = method + " " + self.uri + "\n" + timestamp + "\n" + self.access_key
        message_bytes = bytes(message, 'UTF-8')
        signing_key = base64.b64encode(hmac.new(secret_key_bytes, message_bytes, digestmod=hashlib.sha256).digest())
        return signing_key
    
    def _get_headers(self): # 요청 헤더 설정 
        timestamp = str(int(time.time() * 1000))
        return {
            "Content-Type": "application/json; charset=utf-8",
            "x-ncp-apigw-timestamp": timestamp,
            "x-ncp-iam-access-key": self.access_key,
            "x-ncp-apigw-signature-v2": self._make_signature(timestamp)
        }
    

    def send(self, phone, verification_code=None):
        content = self.message_content + f'[{verification_code}] 입니다.'
            
        data = {
            "type": "SMS",
            "from": self.sender_number,
            "content": content,
            "subject": "SENS",
            "messages": [
                {
                    "to": phone,
                }
            ]
        }
        
        response = requests.post(
            self.url + self.uri,
            headers=self._get_headers(),
            data=json.dumps(data)
        )
        
        result = response.json()
        
        # response의 JSON 응답값에 statusCode를 추출 
        
        print(result)

        return result.get('statusCode') == '202'

            # 'request_id': result.get('requestId'),
            # 'status_code': response.status_code,
            # 'response': result,
            # 'verification_code': verification_code if verification_code else None

# 사용 예시
# sms_sender = NaverSMSSender()
# result = sms_sender.send(phone='01012345678', verification_code='139212')
# print(result)
