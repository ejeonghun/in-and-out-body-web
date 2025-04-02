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
def can_send_sms(phone_number: str) -> bool:
    redis_client = RedisClient().get_client()  # 싱글톤 인스턴스를 가져옴
    today = datetime.now().strftime("%Y-%m-%d")
    key = f"sms:{phone_number}:{today}"

    # 현재 요청 횟수 조회
    current_count = redis_client.get(key)

    if current_count is None:
        # 새로운 번호면 1로 설정하고 TTL 7일로 설정
        redis_client.set(key, 1, ex=7 * 24 * 60 * 60)
        return True

    current_count = int(current_count)

    if current_count < 2:
        # 횟수 증가
        redis_client.incr(key)
        return True

    # 2회 초과 시 전송 차단
    return False

# 테스트
# phone = "01012345678"
# if can_send_sms(phone):
#     # print(f"{phone} 번호로 SMS 전송 가능 ✅")
#     return True
# else:
#     print(f"{phone} 번호로 SMS 전송 불가 ❌ (최대 2회 초과)")
#     return False


def limit_reset(phone_number: str) -> None:
    redis_client = RedisClient().get_client()
    today = datetime.now().strftime("%Y-%m-%d")
    key = f"sms:{phone_number}:{today}"
    redis_client.delete(key)
        
limit_reset("01051237370")