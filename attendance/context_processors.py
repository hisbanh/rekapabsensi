"""
Context processors for the attendance application
"""
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def app_context(request):
    """Add application-specific context variables"""
    return {
        'app_config': getattr(settings, 'SIPA_YAUMI', {}),
        'app_name': getattr(settings, 'SIPA_YAUMI', {}).get('APP_NAME', 'SIPA Beta '),
        'school_name': getattr(settings, 'SIPA_YAUMI', {}).get('SCHOOL_NAME', 'PESANTREN YAUMI YOGYAKARTA'),
        'app_version': getattr(settings, 'SIPA_YAUMI', {}).get('VERSION', '1.0.0'),
    }


def notification_context(request):
    """
    Add notification count to context for all templates.
    
    This makes the notification count available in the sidebar badge.
    Only calculates for authenticated users who are staff/admin.
    """
    notification_count = 0
    
    # Only calculate for authenticated staff/admin users
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        try:
            # Import here to avoid circular imports
            from .services.notification_service import NotificationService
            
            # Get today's notifications
            today = timezone.now().date()
            all_notifs = NotificationService.get_all_notifications(today)
            
            # Count high priority notifications only for the badge
            notification_count = all_notifs.get('high_priority_count', 0)
            
        except Exception as e:
            # Log error but don't break the page
            logger.error(f"Error getting notification count: {str(e)}")
            notification_count = 0
    
    return {
        'notification_count': notification_count,
    }