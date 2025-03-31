from django.contrib import admin
from django.urls import include, path
from prometheus_client import make_wsgi_app

def trigger_error(request):
    division_by_zero = 1 / 0
urlpatterns = [
    path('admin/', admin.site.urls),

    path('sentry-debug-ababnswkskc/', trigger_error),
    path('', include('analysis.urls')),
    path('metrics', make_wsgi_app()),
]