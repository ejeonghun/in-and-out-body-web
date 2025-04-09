import redis
import os
from datetime import datetime

import dotenv
dotenv.load_dotenv(override=True)

class RedisClient:
    _instance = None  # 싱글톤 인스턴스 저장용

    def __new__(cls):
        if cls._instance is None:
            # 환경 변수에서 Redis 정보 가져오기
            rd_host = os.environ.get("REDIS_HOST", "localhost")
            rd_pw = os.environ.get("REDIS_PASSWORD", None)

            # Redis 연결 생성
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance.client = redis.StrictRedis(
                host=rd_host,
                port=6379,
                db=0,
                decode_responses=True,
                password=rd_pw
            )
        return cls._instance

    def get_client(self):
        return self.client

    # SMS 요청 함수
    def can_send_sms(self ,phone_number: str) -> bool:
        redis_client = self.get_client()  # 싱글톤 인스턴스를 가져옴
        today = datetime.now().strftime("%Y-%m-%d")
        key = f"sms:{phone_number}:{today}"

        # 현재 요청 횟수 조회
        current_count = redis_client.get(key)

        if current_count is None:
        # 새로운 번호면 1로 설정하고 TTL 7일로 설정
            redis_client.set(key, 1, ex=7 * 24 * 60 * 60)
            return True

        current_count = int(current_count)

        if current_count < 11:
            # 횟수 증가
            redis_client.incr(key)
            return True

        # # 10회 초과 시 전송 차단
        return False



    def save_code(self, phone_number: str, verification_code: str) -> None:
        redis_client = RedisClient().get_client()
        key = f"code:{phone_number}"
        redis_client.set(key, verification_code, ex=5 * 60) # 5분 동안 유효

    def check_code(self, phone_number: str, verification_code: str) -> bool:
        redis_client = RedisClient().get_client()
        key = f"code:{phone_number}"
        saved_code = redis_client.get(key)
        
        if (saved_code == verification_code):
            redis_client.delete(key) # 사용한 코드 삭제
            return True
        else:
            return False
        
    def redis_test(self):
        phone = "01012345678"
        if self.can_send_sms(phone):
            print(f"{phone} 번호로 SMS 전송 가능 ✅")
        else:
            print(f"{phone} 번호로 SMS 전송 불가 ❌ (최대 2회 초과)")


    
