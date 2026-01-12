"""
Custom exceptions for the attendance application
"""


class AttendanceBaseException(Exception):
    """Base exception for attendance application"""
    pass


class AttendanceServiceError(AttendanceBaseException):
    """Exception raised by attendance service operations"""
    pass


class StudentServiceError(AttendanceBaseException):
    """Exception raised by student service operations"""
    pass


class ReportServiceError(AttendanceBaseException):
    """Exception raised by report service operations"""
    pass


class ValidationError(AttendanceBaseException):
    """Exception raised for validation errors"""
    pass


class PermissionDeniedError(AttendanceBaseException):
    """Exception raised when user lacks required permissions"""
    pass