#!/usr/bin/env python
"""
ngrok을 사용하여 장고 프로젝트를 외부에서 접근 가능하도록 설정하는 스크립트
환경 변수에서 NGROK_AUTH_TOKEN을 읽어 ngrok 터널을 생성하고
임시로 ALLOWED_HOSTS와 CSRF_TRUSTED_ORIGINS에 ngrok 도메인을 추가합니다.
"""
import os
import sys
import signal
import subprocess
import dotenv
from pyngrok import ngrok, conf

# .env 파일 로드
dotenv.load_dotenv(override=True)

# 기본 설정
DEFAULT_PORT = 8000
NGROK_AUTH_TOKEN = os.getenv('NGROK_AUTH_TOKEN')

def signal_handler(sig, frame):
    """시그널 핸들러: 프로그램 종료 시 ngrok 터널 닫기"""
    print("\n프로그램을 종료합니다...")
    ngrok.kill()
    sys.exit(0)

def setup_ngrok(port):
    """ngrok 설정 및 터널 생성"""
    if not NGROK_AUTH_TOKEN:
        print("오류: NGROK_AUTH_TOKEN 환경 변수가 설정되지 않았습니다.")
        print("환경 변수에 NGROK_AUTH_TOKEN을 추가하거나 .env 파일에 설정해주세요.")
        sys.exit(1)

    # ngrok 설정
    conf.get_default().auth_token = NGROK_AUTH_TOKEN

    try:
        # 기존 터널 모두 닫기
        ngrok.kill()

        # 새 터널 생성
        print(f"ngrok 터널을 생성 중입니다 (포트: {port})...")
        tunnel = ngrok.connect(port, "http")
        public_url = tunnel.public_url

        if public_url.startswith("http://"):
            # https URL로 변환
            public_url = "https://" + public_url[7:]

        print(f"ngrok 터널이 생성되었습니다: {public_url}")
        return public_url
    except Exception as e:
        print(f"ngrok 터널 생성 중 오류가 발생했습니다: {e}")
        sys.exit(1)

def update_django_settings(ngrok_url):
    """ngrok URL을 포함하도록 환경 변수 업데이트"""
    ngrok_host = ngrok_url.replace("https://", "").replace("http://", "")

    # 현재 ALLOWED_HOSTS 가져오기 (settings.py에서)
    try:
        from mysite.settings import ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS
        current_hosts = ALLOWED_HOSTS.copy()
        current_origins = CSRF_TRUSTED_ORIGINS.copy() if 'CSRF_TRUSTED_ORIGINS' in locals() else []
    except (ImportError, AttributeError):
        current_hosts = []
        current_origins = []

    # ngrok 호스트 추가
    if ngrok_host not in current_hosts:
        current_hosts.append(ngrok_host)

    # ngrok URL을 CSRF 신뢰할 수 있는 출처에 추가
    if ngrok_url not in current_origins:
        current_origins.append(ngrok_url)

    # 환경 변수로 설정 (장고가 이를 읽을 수 있도록)
    os.environ['DJANGO_ALLOWED_HOSTS'] = ','.join(current_hosts)
    os.environ['DJANGO_CSRF_TRUSTED_ORIGINS'] = ','.join(current_origins)

    print(f"\nALLOWED_HOSTS에 {ngrok_host}가 추가됩니다.")
    print(f"CSRF_TRUSTED_ORIGINS에 {ngrok_url}가 추가됩니다.")

def run_django_server(port):
    """장고 개발 서버 실행"""
    try:
        print(f"\n장고 개발 서버를 포트 {port}에서 시작합니다...")

        # 환경 변수를 사용하여 서버 실행
        process = subprocess.Popen([
            sys.executable, "manage.py", "runserver", f"0.0.0.0:{port}"
        ], env=os.environ.copy())

        return process
    except Exception as e:
        print(f"장고 서버 실행 중 오류가 발생했습니다: {e}")
        ngrok.kill()
        sys.exit(1)

def main():
    """메인 함수"""
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)

    # 명령줄 인자에서 포트 가져오기 (기본값: 8000)
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"오류: 유효하지 않은 포트 번호입니다. 기본값 {DEFAULT_PORT}을 사용합니다.")

    # ngrok 설정 및 터널 생성
    ngrok_url = setup_ngrok(port)

    # 환경 변수로 설정 업데이트
    update_django_settings(ngrok_url)

    # 장고 서버 실행
    django_process = run_django_server(port)

    print("\n개발 서버가 실행 중입니다.")
    print(f"외부 URL: {ngrok_url}")
    print("종료하려면 Ctrl+C를 누르세요.")

    try:
        # 프로세스가 종료될 때까지 대기
        django_process.wait()
    except KeyboardInterrupt:
        # 키보드 인터럽트 처리
        pass
    finally:
        # 정리 작업
        django_process.terminate()
        ngrok.kill()
        print("\n모든 프로세스가 종료되었습니다.")

if __name__ == "__main__":
    main()
