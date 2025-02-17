#!/bin/bash

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Kill existing Gunicorn process
PID=$(pgrep -f "gunicorn.*:8000")
if [ -n "$PID" ]; then
    echo "Stopping Gunicorn process: $PID"
    kill -9 $PID
fi

# 운영 환경일 때만 collectstatic
if [ "$ENVIRONMENT" == "prod" ] || [ "$ENVIRONMENT" == "dev" ]; then
    echo "Running collectstatic..."
    echo "yes" | python manage.py collectstatic > /dev/null 2>&1
fi

echo "Starting Gunicorn..."
gunicorn --bind 0.0.0.0:8000 mysite.wsgi:application --daemon
