from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FarmerViewSet, DiseaseViewSet, VendorViewSet, DiagnosisViewSet,
    health_check, login, me, password_reset_confirm,
    password_reset_request, register
)

router = DefaultRouter()
router.register(r'farmers', FarmerViewSet, basename='farmer')
router.register(r'diseases', DiseaseViewSet, basename='disease')
router.register(r'vendors', VendorViewSet, basename='vendor')
router.register(r'diagnoses', DiagnosisViewSet, basename='diagnosis')

urlpatterns = [
    path('health/', health_check, name='api-health'),
    path('auth/register/', register, name='register'),
    path('auth/login/', login, name='login'),
    path('auth/me/', me, name='me'),
    path('auth/password-reset/', password_reset_request, name='password-reset'),
    path('auth/password-reset/confirm/', password_reset_confirm, name='password-reset-confirm'),
    path('diagnose/', DiagnosisViewSet.as_view({'post': 'create'}), name='diagnose'),
    path('', include(router.urls)),
]
