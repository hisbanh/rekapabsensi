"""
Custom middleware for the attendance application
"""
import logging
import threading
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from .models import AuditLog

logger = logging.getLogger(__name__)

# Thread-local storage for current user
_thread_locals = threading.local()


def get_current_user():
    """
    Get the current user from thread-local storage.
    Returns None if no user is set or user is anonymous.
    """
    user = getattr(_thread_locals, 'user', None)
    if user and not isinstance(user, AnonymousUser):
        return user
    return None


def set_current_user(user):
    """
    Set the current user in thread-local storage.
    """
    _thread_locals.user = user


class CurrentUserMiddleware(MiddlewareMixin):
    """
    Middleware to store the current user in thread-local storage.
    This allows models to access the current user without passing it explicitly.
    """
    
    def process_request(self, request):
        """Store the current user in thread-local storage"""
        if hasattr(request, 'user'):
            set_current_user(request.user)
        return None
    
    def process_response(self, request, response):
        """Clear the current user from thread-local storage"""
        set_current_user(None)
        return response
    
    def process_exception(self, request, exception):
        """Clear the current user on exception"""
        set_current_user(None)
        return None


class AuditMiddleware(MiddlewareMixin):
    """Middleware to log important user actions for audit purposes"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Process incoming request"""
        # Store IP address in request for later use
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            request.ip_address = x_forwarded_for.split(',')[0]
        else:
            request.ip_address = request.META.get('REMOTE_ADDR')
        
        return None
    
    def process_response(self, request, response):
        """Process outgoing response"""
        # Log important actions
        if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
            if request.method in ['POST', 'PUT', 'DELETE']:
                self._log_action(request, response)
        
        return response
    
    def _log_action(self, request, response):
        """Log user action to audit log"""
        try:
            # Only log successful actions (2xx status codes)
            if 200 <= response.status_code < 300:
                action = self._determine_action(request)
                if action:
                    AuditLog.objects.create(
                        user=request.user,
                        action=action,
                        model_name=self._get_model_name(request),
                        description=self._get_description(request, action),
                        ip_address=getattr(request, 'ip_address', None),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
                    )
        except Exception as e:
            logger.error(f"Error logging audit action: {str(e)}")
    
    def _determine_action(self, request):
        """Determine the action type based on request"""
        if request.method == 'POST':
            if 'attendance' in request.path:
                return 'CREATE'
            elif 'export' in request.path:
                return 'EXPORT'
        elif request.method == 'PUT':
            return 'UPDATE'
        elif request.method == 'DELETE':
            return 'DELETE'
        
        return None
    
    def _get_model_name(self, request):
        """Get model name from request path"""
        if 'attendance' in request.path:
            return 'AttendanceRecord'
        elif 'student' in request.path:
            return 'Student'
        else:
            return 'Unknown'
    
    def _get_description(self, request, action):
        """Generate description for the action"""
        path = request.path
        if action == 'CREATE' and 'attendance' in path:
            return f"Created attendance records via {path}"
        elif action == 'EXPORT':
            return f"Exported data from {path}"
        else:
            return f"{action} action on {path}"


class SecurityMiddleware(MiddlewareMixin):
    """Additional security middleware"""
    
    def process_request(self, request):
        """Add security headers and checks"""
        # Add custom security headers
        return None
    
    def process_response(self, request, response):
        """Add security headers to response"""
        # Add custom security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response