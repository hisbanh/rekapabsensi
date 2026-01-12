"""
Custom permission decorators for the attendance application.
Implements role-based access control for Admin and Guru roles.

Requirements:
- 9.1: Support two roles: Admin and Guru
- 9.2: Guru access: Dashboard, Input, Report, read-only management
- 9.3: Admin access: Full access including Settings and Users
- 9.4: Redirect with permission denied message
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def admin_required(view_func):
    """
    Decorator to require admin (superuser) access.
    
    If user is not a superuser, redirects to dashboard with permission denied message.
    This decorator should be used after @login_required.
    
    Usage:
        @login_required
        @admin_required
        def my_admin_view(request):
            ...
    
    Requirements: 9.1, 9.3, 9.4
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not request.user.is_superuser:
            messages.error(request, "Anda tidak memiliki akses ke halaman ini")
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def guru_or_admin_required(view_func):
    """
    Decorator to require at least Guru role (any authenticated user).
    
    This is essentially the same as login_required but provides
    a consistent interface for role-based access control.
    
    Both Guru and Admin users can access views decorated with this.
    
    Usage:
        @guru_or_admin_required
        def my_view(request):
            ...
    
    Requirements: 9.1, 9.2
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required_for_write(view_func):
    """
    Decorator that allows read access for all authenticated users,
    but requires admin for write operations (POST, PUT, DELETE).
    
    This is useful for management pages where Guru can view but not modify.
    
    Usage:
        @admin_required_for_write
        def my_management_view(request):
            ...
    
    Requirements: 9.2, 9.3
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # For write operations, require admin
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            if not request.user.is_superuser:
                messages.error(request, "Anda tidak memiliki akses untuk melakukan perubahan ini")
                return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


class AdminRequiredMixin:
    """
    Mixin for class-based views that require admin access.
    
    Usage:
        class MyAdminView(AdminRequiredMixin, TemplateView):
            template_name = 'my_template.html'
    
    Requirements: 9.1, 9.3, 9.4
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not request.user.is_superuser:
            messages.error(request, "Anda tidak memiliki akses ke halaman ini")
            return redirect('dashboard')
        
        return super().dispatch(request, *args, **kwargs)


class GuruOrAdminRequiredMixin:
    """
    Mixin for class-based views that require at least Guru role.
    
    Usage:
        class MyView(GuruOrAdminRequiredMixin, TemplateView):
            template_name = 'my_template.html'
    
    Requirements: 9.1, 9.2
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        return super().dispatch(request, *args, **kwargs)
