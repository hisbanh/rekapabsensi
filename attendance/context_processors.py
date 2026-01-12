"""
Context processors for the attendance application
"""
from django.conf import settings


def app_context(request):
    """Add application-specific context variables"""
    return {
        'app_config': getattr(settings, 'SIPA_YAUMI', {}),
        'app_name': getattr(settings, 'SIPA_YAUMI', {}).get('APP_NAME', 'SIPA Beta '),
        'school_name': getattr(settings, 'SIPA_YAUMI', {}).get('SCHOOL_NAME', 'PESANTREN YAUMI YOGYAKARTA'),
        'app_version': getattr(settings, 'SIPA_YAUMI', {}).get('VERSION', '1.0.0'),
    }