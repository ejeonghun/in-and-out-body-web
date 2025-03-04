#!/bin/bash

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Gunicorn 프로세스 종료
GUNICORN_PIDS=$(pgrep -f "gunicorn.*:8000")
if [ -n "$GUNICORN_PIDS" ]; then
    echo "Stopping Gunicorn processes:"
    for PID in $GUNICORN_PIDS; do
        echo "Stopping Gunicorn process: $PID"
        kill -9 $PID
    done
fi

# mail_fetch_thread.py 프로세스 종료
MAIL_FETCH_PIDS=$(pgrep -f "mail_fetch_thread.py")
if [ -n "$MAIL_FETCH_PIDS" ]; then
    echo "Stopping mail_fetch_thread.py processes:"
    for PID in $MAIL_FETCH_PIDS; do
        echo "Stopping mail_fetch_thread.py process: $PID"
        kill -9 $PID
    done
fi

# 운영 환경일 때만 collectstatic
if [ "$ENVIRONMENT" == "prod" ] || [ "$ENVIRONMENT" == "dev" ]; then
    echo "Running collectstatic..."
    echo "yes" | python manage.py collectstatic > /dev/null 2>&1
fi

# mail_fetch_thread.py를 백그라운드에서 실행하고 PID를 저장
echo "Starting mail_fetch_thread.py with hourly restart..."
nohup bash -c "while true; do
    timeout 3600 python mail_fetch_thread.py
    sleep 1
done" >/dev/null 2>&1 &
MAIL_FETCH_PID=$!
echo "mail_fetch_thread.py PID: $MAIL_FETCH_PID"

# Gunicorn 시작
echo "Starting Gunicorn..."
nohup gunicorn --bind 0.0.0.0:8000 mysite.wsgi:application >/dev/null 2>&1 &  # 백그라운드 실행 및 출력 닫기

# 스크립트 완료 메시지 출력 (GitHub Actions용)
echo "restart_django.sh script completed successfully."
