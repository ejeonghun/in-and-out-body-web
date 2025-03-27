import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from django.core.management import call_command

# inspectdb 명령 직접 호출
call_command('inspectdb', 'analysis_kioskinfo', database='default')