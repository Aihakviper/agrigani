"""
URL configuration for AgriGani Core project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from agrigani_core.api.views import DiagnosisViewSet, health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health'),
    path('diagnose/', DiagnosisViewSet.as_view({'post': 'create'}), name='diagnose-legacy'),
    path('api/v1/', include('agrigani_core.api.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
