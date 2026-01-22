"""
Teacher Report API Endpoints
Provides RESTful API for teacher attendance reporting, analytics, and exports
"""
import json
from datetime import datetime, date
from uuid import UUID
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

from ..models import Teacher
from ..services.teacher_report_service import TeacherReportService, TeacherReportServiceError


# Helper functions for serialization
def serialize_teacher_stat(stat):
    """
    Serialize teacher statistics dictionary.
    
    Args:
        stat: Dictionary containing teacher statistics
        
    Returns:
        Dictionary with serialized data
    """
    return {
        'teacher_id': stat.get('teacher_id'),
        'teacher_name': stat.get('teacher_name'),
        'nip': stat.get('nip'),
        'total_jp': stat.get('total_jp', 0),
        'total_hadir': stat.get('total_hadir', 0),
        'total_sakit': stat.get('total_sakit', 0),
        'total_izin': stat.get('total_izin', 0),
        'total_cuti': stat.get('total_cuti', 0),
        'total_dinas': stat.get('total_dinas', 0),
        'total_alpa': stat.get('total_alpa', 0),
        'attendance_percentage': stat.get('attendance_percentage', 0.0),
    }


def serialize_daily_trend(trend):
    """
    Serialize daily trend dictionary.
    
    Args:
        trend: Dictionary containing daily trend data
        
    Returns:
        Dictionary with serialized data
    """
    return {
        'date': trend['date'].isoformat() if isinstance(trend['date'], date) else trend['date'],
        'day_name': trend.get('day_name', ''),
        'total_jp': trend.get('total_jp', 0),
        'total_hadir': trend.get('total_hadir', 0),
        'total_absent': trend.get('total_absent', 0),
        'attendance_percentage': trend.get('attendance_percentage', 0.0),
    }


def serialize_subject_stat(stat):
    """
    Serialize subject statistics dictionary.
    
    Args:
        stat: Dictionary containing subject statistics
        
    Returns:
        Dictionary with serialized data
    """
    return {
        'subject_name': stat.get('subject_name'),
        'subject_code': stat.get('subject_code'),
        'total_jp': stat.get('total_jp', 0),
        'total_hadir': stat.get('total_hadir', 0),
        'attendance_percentage': stat.get('attendance_percentage', 0.0),
    }


def error_response(message, status=400, errors=None):
    """
    Create an error response.
    
    Args:
        message: Error message
        status: HTTP status code
        errors: Additional error details (optional)
        
    Returns:
        JsonResponse with error information
    """
    response_data = {
        'success': False,
        'error': message,
    }
    
    if errors:
        response_data['errors'] = errors
    
    return JsonResponse(response_data, status=status)


def success_response(data=None, message=None, status=200):
    """
    Create a success response.
    
    Args:
        data: Response data
        message: Success message (optional)
        status: HTTP status code
        
    Returns:
        JsonResponse with success information
    """
    response_data = {
        'success': True,
    }
    
    if message:
        response_data['message'] = message
    
    if data is not None:
        response_data['data'] = data
    
    return JsonResponse(response_data, status=status)


# API Endpoints

@require_http_methods(["GET"])
@login_required
def teacher_report_pdf(request, teacher_id):
    """
    GET /api/reports/teacher/{id}/pdf/ - Generate PDF report for a teacher
    
    Path Parameters:
        - teacher_id: UUID of the teacher
    
    Query Parameters:
        - start_date: Start date (YYYY-MM-DD, required)
        - end_date: End date (YYYY-MM-DD, required)
    
    Response:
        PDF file download with Content-Type: application/pdf
        
    Permissions:
        - Teachers can only generate their own reports
        - Admin can generate reports for any teacher
    """
    # Validate teacher_id
    try:
        teacher_uuid = UUID(teacher_id)
    except ValueError:
        return error_response("Invalid teacher ID format", status=400)
    
    # Permission check: teachers can only view their own reports
    if not request.user.is_staff:
        try:
            teacher = Teacher.objects.get(user=request.user)
            if str(teacher.id) != teacher_id:
                return error_response("You can only generate your own reports", status=403)
        except Teacher.DoesNotExist:
            return error_response("No teacher profile associated with this user", status=403)
    
    # Get and validate date parameters
    if not request.GET.get('start_date') or not request.GET.get('end_date'):
        return error_response("Both start_date and end_date parameters are required", status=400)
    
    try:
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
    except ValueError:
        return error_response("Invalid date format. Use YYYY-MM-DD", status=400)
    
    try:
        # Generate PDF using service
        pdf_content = TeacherReportService.generate_teacher_report_pdf(
            teacher_uuid,
            start_date,
            end_date
        )
        
        # Get teacher name for filename
        teacher = Teacher.objects.get(id=teacher_uuid)
        filename = f"laporan_absensi_{teacher.full_name.replace(' ', '_')}_{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}.pdf"
        
        # Create HTTP response with PDF
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except TeacherReportServiceError as e:
        return error_response(str(e), status=400)
    except ObjectDoesNotExist:
        return error_response("Teacher not found", status=404)
    except Exception as e:
        return error_response(f"Error generating PDF report: {str(e)}", status=500)


@require_http_methods(["GET"])
@login_required
def analytics(request):
    """
    GET /api/reports/analytics/ - Get comprehensive attendance analytics
    
    Query Parameters:
        - start_date: Start date (YYYY-MM-DD, required)
        - end_date: End date (YYYY-MM-DD, required)
    
    Response:
        {
            "success": true,
            "data": {
                "period": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "total_days": 31
                },
                "overall_stats": {
                    "total_teachers": 25,
                    "total_records": 500,
                    "total_hadir": 425,
                    "total_sakit": 30,
                    "total_izin": 25,
                    "total_cuti": 10,
                    "total_dinas": 5,
                    "total_alpa": 5,
                    "attendance_percentage": 85.0
                },
                "teacher_stats": [...],
                "daily_trends": [...],
                "subject_stats": [...],
                "top_performers": [...],
                "needs_attention": [...]
            }
        }
        
    Permissions:
        - Only admin can access analytics
    """
    # Permission check: only admin can access analytics
    if not request.user.is_staff:
        return error_response("Permission denied. Admin access required.", status=403)
    
    # Get and validate date parameters
    if not request.GET.get('start_date') or not request.GET.get('end_date'):
        return error_response("Both start_date and end_date parameters are required", status=400)
    
    try:
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
    except ValueError:
        return error_response("Invalid date format. Use YYYY-MM-DD", status=400)
    
    try:
        # Get analytics from service
        analytics_data = TeacherReportService.get_attendance_analytics(
            start_date,
            end_date
        )
        
        # Serialize the response
        response_data = {
            'period': {
                'start_date': analytics_data['period']['start_date'].isoformat(),
                'end_date': analytics_data['period']['end_date'].isoformat(),
                'total_days': analytics_data['period']['total_days'],
            },
            'overall_stats': analytics_data['overall_stats'],
            'teacher_stats': [serialize_teacher_stat(stat) for stat in analytics_data['teacher_stats']],
            'daily_trends': [serialize_daily_trend(trend) for trend in analytics_data['daily_trends']],
            'subject_stats': [serialize_subject_stat(stat) for stat in analytics_data['subject_stats']],
            'top_performers': [serialize_teacher_stat(stat) for stat in analytics_data['top_performers']],
            'needs_attention': [serialize_teacher_stat(stat) for stat in analytics_data['needs_attention']],
        }
        
        return success_response(response_data)
        
    except TeacherReportServiceError as e:
        return error_response(str(e), status=400)
    except Exception as e:
        return error_response(f"Error retrieving analytics: {str(e)}", status=500)


@require_http_methods(["GET"])
@login_required
def export_excel(request):
    """
    GET /api/reports/export/excel/ - Export attendance data to Excel
    
    Query Parameters:
        - start_date: Start date (YYYY-MM-DD, required)
        - end_date: End date (YYYY-MM-DD, required)
        - teacher_ids: Comma-separated list of teacher UUIDs (optional)
                      If provided, creates individual sheets per teacher
    
    Response:
        Excel file download with Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
        
    Permissions:
        - Only admin can export attendance data
    """
    # Permission check: only admin can export data
    if not request.user.is_staff:
        return error_response("Permission denied. Admin access required.", status=403)
    
    # Get and validate date parameters
    if not request.GET.get('start_date') or not request.GET.get('end_date'):
        return error_response("Both start_date and end_date parameters are required", status=400)
    
    try:
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
    except ValueError:
        return error_response("Invalid date format. Use YYYY-MM-DD", status=400)
    
    # Parse teacher_ids if provided
    teacher_ids = None
    if request.GET.get('teacher_ids'):
        try:
            teacher_ids = [UUID(tid.strip()) for tid in request.GET.get('teacher_ids').split(',')]
        except ValueError:
            return error_response("Invalid teacher_ids format. Use comma-separated UUIDs", status=400)
    
    try:
        # Generate Excel using service
        excel_content = TeacherReportService.export_attendance_excel(
            start_date,
            end_date,
            teacher_ids
        )
        
        # Create filename
        filename = f"absensi_ustadz_{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}.xlsx"
        
        # Create HTTP response with Excel
        response = HttpResponse(
            excel_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except TeacherReportServiceError as e:
        return error_response(str(e), status=400)
    except Exception as e:
        return error_response(f"Error exporting to Excel: {str(e)}", status=500)


@require_http_methods(["GET"])
@login_required
def dashboard_stats(request):
    """
    GET /api/reports/dashboard/ - Get real-time dashboard statistics
    
    Response:
        {
            "success": true,
            "data": {
                "today": "2024-01-20",
                "today_stats": {
                    "total_jp": 120,
                    "total_hadir": 100,
                    "total_sakit": 10,
                    "total_izin": 5,
                    "total_cuti": 2,
                    "total_dinas": 2,
                    "total_alpa": 1,
                    "attendance_percentage": 83.33,
                    "teachers_recorded": 20,
                    "total_active_teachers": 25
                },
                "absent_today": [
                    {
                        "teacher_name": "Ahmad Yusuf",
                        "nip": "12345",
                        "status": "SAKIT",
                        "schedule": {...}
                    }
                ],
                "recent_trends": [
                    {
                        "date": "2024-01-14",
                        "day_name": "Sunday",
                        "total_jp": 100,
                        "total_hadir": 85,
                        "total_absent": 15,
                        "attendance_percentage": 85.0
                    }
                ],
                "notifications": [
                    {
                        "type": "warning",
                        "message": "5 ustadz belum mencatat kehadiran hari ini",
                        "priority": "high"
                    }
                ],
                "quick_stats": {
                    "month_total_jp": 2400,
                    "month_total_hadir": 2040,
                    "month_attendance_percentage": 85.0,
                    "total_active_teachers": 25
                }
            }
        }
        
    Permissions:
        - Admin can access all dashboard statistics
        - Teachers can access limited dashboard statistics (their own data)
    """
    try:
        # Get dashboard statistics from service
        stats = TeacherReportService.get_dashboard_statistics()
        
        # Serialize absent_today
        serialized_absent = []
        for absent in stats['absent_today']:
            serialized_absent.append({
                'teacher_name': absent['teacher_name'],
                'nip': absent['nip'],
                'status': absent['status'],
                'schedule': {
                    'id': str(absent['schedule'].id),
                    'subject': absent['schedule'].subject.name,
                    'classroom': absent['schedule'].classroom.name,
                    'jp_start': absent['schedule'].jp_start,
                    'jp_end': absent['schedule'].jp_end,
                } if absent.get('schedule') else None,
            })
        
        # Serialize recent_trends
        serialized_trends = [serialize_daily_trend(trend) for trend in stats['recent_trends']]
        
        # Build response
        response_data = {
            'today': stats['today'].isoformat(),
            'today_stats': stats['today_stats'],
            'absent_today': serialized_absent,
            'recent_trends': serialized_trends,
            'notifications': stats['notifications'],
            'quick_stats': stats['quick_stats'],
        }
        
        # If user is not admin, filter to show only their own data
        if not request.user.is_staff:
            try:
                teacher = Teacher.objects.get(user=request.user)
                
                # Filter absent_today to only show this teacher
                response_data['absent_today'] = [
                    a for a in serialized_absent 
                    if a['nip'] == teacher.nip
                ]
                
                # Modify notifications to be teacher-specific
                response_data['notifications'] = [
                    n for n in stats['notifications']
                    if 'ustadz' not in n['message'].lower() or teacher.full_name in n['message']
                ]
                
            except Teacher.DoesNotExist:
                return error_response("No teacher profile associated with this user", status=403)
        
        return success_response(response_data)
        
    except Exception as e:
        return error_response(f"Error retrieving dashboard statistics: {str(e)}", status=500)
