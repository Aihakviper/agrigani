from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agrigani_core.api'
    label = 'agrigani_api' 
    verbose_name = 'AgriGani API'