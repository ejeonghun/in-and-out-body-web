import logging
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import NotFound

# 로거 설정
logger = logging.getLogger(__name__)


# 허용된 IP 주소만 접근 가능한 Permission + 로깅
class IsAllowedIP(BasePermission):
    def has_permission(self, request, view):
        # X-Forwarded-For 헤더에서 실제 클라이언트 IP 가져오기
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

        path = request.path
        response_code = 404

        # IP 체크 로직
        if (ip.startswith('192.168.0.') and 1 <= int(ip.split('.')[-1]) <= 254) or \
                (ip.startswith('172.21.0.') and 1 <= int(ip.split('.')[-1]) <= 254) or \
                ip in ['14.46.152.143', '127.0.0.1']:
            return True

        # 허용되지 않은 IP일 경우 로깅 및 404 Page not found 에러 발생
        logger.warning(f"Unauthorized access attempt: {path}, {response_code}, IP Addr: {ip}")  # IP 로깅
        # raise AuthenticationFailed("Unauthorized access")  # 401 Unauthorized 에러 발생
        raise NotFound("Page not found")  # 404 page not found 에러 발생