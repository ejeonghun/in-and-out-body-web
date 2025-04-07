import logging
from django.http import JsonResponse

# 로그 설정
logger = logging.getLogger('bad_access_logger')
handler = logging.FileHandler('bad_access.log', encoding='utf-8')
formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def custom_csrf_failure_view(request, reason=""):
    log_message = [
        "\n=== CSRF ERROR DEBUGGING ===",
        f"REASON: {reason}",
        f"METHOD: {request.method}",
        f"PATH: {request.path}",
        "HEADERS:"
    ]
    
    for key, value in request.headers.items():
        log_message.append(f"{key}: {value}")
    
    log_message.append(f"COOKIES: {request.COOKIES}")
    
    try:
        body_content = request.body.decode('utf-8', errors='ignore')
    except Exception as e:
        body_content = f"Error decoding body: {e}"
    
    log_message.append(f"BODY: {body_content}")
    log_message.append("=== END DEBUG ===\n")

    # 로그 파일에 기록
    logger.info("\n".join(log_message))

    return JsonResponse({
        'detail': 'CSRF verification failed.',
        'reason': reason
    }, status=403)
