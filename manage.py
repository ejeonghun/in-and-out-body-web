#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

    # 만약 프로젝트 루트폴더에 logs 폴더가 없다면 생성
    if not os.path.exists('logs'):
        os.makedirs('logs')
        # 만약 logs폴더안에 'bad_access.log' 파일이 없다면 생성
        with open('logs/bad_access.log', 'w') as f:
            f.write('')


if __name__ == '__main__':
    main()
