import logging
from apscheduler.schedulers.background import BackgroundScheduler
from analysis.models import SessionInfo
from django.utils import timezone
from datetime import timedelta
import atexit
from django.conf import settings
import os
import logging.config

# 로그 파일 위치 설정
# 로그는 프로젝트 루트 디렉토리 /logs 에 저장됨
log_dir = os.path.join(settings.BASE_DIR, 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 로깅 설정
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'session_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(log_dir, 'session_cleanup.log'),
            'maxBytes': 1024 * 1024,  # 1MB
            'backupCount': 1,
            'formatter': 'detailed',
        }
    },
    'loggers': {
        'session_cleanup': {
            'handlers': ['session_file'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}

logger = logging.getLogger('session_cleanup')
logging.config.dictConfig(LOGGING)


def delete_old_sessions():
    """
    sessionInfo table의 created_dt 기준 현재 날짜로 부터
    1일 이상 경과 된(오래된 세션)을 삭제,
    """
    try:
        # 1일 이상 경과 된 세션 삭제
        old_cutoff_date = timezone.now() - timedelta(days=1)
        old_deleted_count, _ = SessionInfo.objects.filter(created_dt__lt=old_cutoff_date).delete()

        # 로그 및 콘솔 출력
        logger.info(f"오래된 세션 만료 {old_deleted_count} 개 삭제")
    except Exception as e:
        logger.error(f"세션 삭제 오류: {e}")


def session_expired():
    """ last_active_dt 기준으로 50분 이상 경과 된 세션 삭제 """
    try:
        # 마지막 활동시간으로 부터 50분 이상 경과 된 세션 삭제
        cutoff_date = timezone.now() - timedelta(minutes=50)
        deleted_count, _ = SessionInfo.objects.filter(last_active_dt__lt=cutoff_date).delete()

        logger.info(f"세션 만료 {deleted_count} 개 삭제")
    except Exception as e:
        logger.error(f"세션 삭제 오류: {e}")

# 작업 등록
scheduler = BackgroundScheduler()


scheduler.remove_all_jobs() # 스케줄러 초기화



# 매일 00:00에 실행
# 동일한 작업이 이미 등록되어 있다면 대체
scheduler.add_job(delete_old_sessions, 'cron', hour=00, minute=00, replace_existing=True) # 매일 00:00에 실행

# 2분 간격으로 실행 (세션 마지막활동 50분 검증 및 만료)
scheduler.add_job(session_expired, 'interval', minutes=2, replace_existing=True) # 2분 간격으로 실행


# 서버 종료 시 스케줄러 중지 및 로그 출력
def stop_scheduler():
    if scheduler.running:
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()

atexit.register(stop_scheduler)
