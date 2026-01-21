"""
Teacher Dashboard Views
Handles all views related to teacher attendance dashboard and analytics

Authorization:
- Admin: Full access to all teacher dashboard features
- Teachers: Can view own dashboard statistics

Requirements: FR-018 to FR-022
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, Count, Sum
from datetime import datetime, timedelta, date
import logging

from .models import (
    Teacher, TeacherAttendance, TeacherSchedule, 
    TeacherAttendanceSummary
)
from .services.teacher_attendance_service import (
    TeacherAttendanceService,
    TeacherAttendanceServiceError
)
from .services.schedule_service import ScheduleService
from .services.notification_service import NotificationService, NotificationServiceError
from .decorators import admin_required, guru_or_admin_required

logger = logging.getLogger(__name__)


# ============================================
# Teacher Dashboard View
# ============================================

@login_required
def teacher_dashboard(request):
    """
    Main teacher attendance dashboard with comprehensive statistics.
    
    Accessible by: All authenticated users
    - Admin: Can view all teacher statistics
    - Teachers: Can view own statistics
    
    Features:
    - Display summary cards (Hadir %, Sakit %, Izin %, Alpa %)
    - Show attendance trend chart (last 30 days)
    - Display notifications section
    - List absent teachers today
    - Show upcoming schedule
    
    Requirements: FR-018, FR-019, FR-020, FR-021, FR-022
    """
    try:
        # Get date range from query parameters (default: last 30 days)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Calculate real-time statistics
        stats = _calculate_dashboard_statistics(start_date, end_date)
        
        # Get absent teachers for today
        absent_teachers_today = _get_absent_teachers_today()
        
        # Get attendance trends (last 30 days)
        trends = _get_attendance_trends(days=30)
        
        # Get notifications
        notifications = _get_dashboard_notifications()
        
        # Get teacher-specific data if user is a teacher
        teacher_data = None
        if hasattr(request.user, 'teacher_profile'):
            teacher = request.user.teacher_profile
            teacher_data = _get_teacher_specific_data(teacher, start_date, end_date)
        
        context = {
            # Date range
            'start_date': start_date,
            'end_date': end_date,
            
            # Statistics
            'stats': stats,
            
            # Absent teachers
            'absent_teachers_today': absent_teachers_today,
            'absent_count': len(absent_teachers_today),
            
            # Trends
            'trends': trends,
            
            # Notifications
            'notifications': notifications,
            'notification_count': len(notifications),
            
            # Teacher-specific data
            'teacher_data': teacher_data,
            
            # Current date
            'today': timezone.now().date(),
        }
        
    except Exception as e:
        logger.error(f"Error loading teacher dashboard: {str(e)}")
        context = {
            'stats': {},
            'absent_teachers_today': [],
            'trends': [],
            'notifications': [],
            'today': timezone.now().date(),
        }
    
    return render(request, 'teacher/dashboard.html', context)


def _calculate_dashboard_statistics(start_date: date, end_date: date) -> dict:
    """
    Calculate comprehensive dashboard statistics for the date range.
    
    Returns:
        Dictionary containing:
        - total_teachers: Total active teachers
        - total_jp_scheduled: Total JP scheduled in the period
        - total_hadir: Total HADIR records
        - total_sakit: Total SAKIT records
        - total_izin: Total IZIN records
        - total_cuti: Total CUTI records
        - total_dinas: Total DINAS records
        - total_alpa: Total ALPA records
        - attendance_percentage: Overall attendance percentage
        - hadir_percentage: Percentage of HADIR
        - sakit_percentage: Percentage of SAKIT
        - izin_percentage: Percentage of IZIN
        - alpa_percentage: Percentage of ALPA
    """
    # Get all active teachers
    total_teachers = Teacher.objects.filter(is_active=True).count()
    
    # Get all attendance records in the date range
    attendances = TeacherAttendance.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    )
    
    # Count by status
    total_hadir = attendances.filter(status='HADIR').count()
    total_sakit = attendances.filter(status='SAKIT').count()
    total_izin = attendances.filter(status='IZIN').count()
    total_cuti = attendances.filter(status='CUTI').count()
    total_dinas = attendances.filter(status='DINAS').count()
    total_alpa = attendances.filter(status='ALPA').count()
    
    # Calculate total records
    total_records = attendances.count()
    
    # Calculate percentages
    attendance_percentage = 0.0
    hadir_percentage = 0.0
    sakit_percentage = 0.0
    izin_percentage = 0.0
    alpa_percentage = 0.0
    
    if total_records > 0:
        hadir_percentage = round((total_hadir / total_records) * 100, 1)
        sakit_percentage = round((total_sakit / total_records) * 100, 1)
        izin_percentage = round((total_izin / total_records) * 100, 1)
        alpa_percentage = round((total_alpa / total_records) * 100, 1)
        attendance_percentage = hadir_percentage
    
    # Calculate total JP scheduled (estimate based on active schedules)
    # This is an approximation - actual scheduled JP would need day-by-day calculation
    active_schedules = TeacherSchedule.objects.filter(
        is_active=True,
        effective_date__lte=end_date
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=start_date)
    )
    
    # Estimate total JP scheduled (rough calculation)
    total_jp_scheduled = 0
    current_date = start_date
    while current_date <= end_date:
        day_of_week = current_date.weekday()
        day_schedules = active_schedules.filter(day_of_week=day_of_week)
        for schedule in day_schedules:
            total_jp_scheduled += (schedule.jp_end - schedule.jp_start + 1)
        current_date += timedelta(days=1)
    
    return {
        'total_teachers': total_teachers,
        'total_jp_scheduled': total_jp_scheduled,
        'total_records': total_records,
        'total_hadir': total_hadir,
        'total_sakit': total_sakit,
        'total_izin': total_izin,
        'total_cuti': total_cuti,
        'total_dinas': total_dinas,
        'total_alpa': total_alpa,
        'attendance_percentage': attendance_percentage,
        'hadir_percentage': hadir_percentage,
        'sakit_percentage': sakit_percentage,
        'izin_percentage': izin_percentage,
        'alpa_percentage': alpa_percentage,
    }


def _get_absent_teachers_today() -> list:
    """
    Get list of teachers who are absent today.
    
    Returns:
        List of dictionaries containing:
        - teacher: Teacher instance
        - status: Attendance status or 'NOT_RECORDED'
        - jp_numbers: List of JP numbers where absent
        - schedules: List of schedules for today
    """
    today = timezone.now().date()
    day_of_week = today.weekday()
    
    # Get all active teachers with schedules today
    teachers_with_schedules = Teacher.objects.filter(
        is_active=True,
        teacher_schedules__day_of_week=day_of_week,
        teacher_schedules__is_active=True,
        teacher_schedules__effective_date__lte=today
    ).filter(
        Q(teacher_schedules__end_date__isnull=True) | 
        Q(teacher_schedules__end_date__gte=today)
    ).distinct()
    
    absent_teachers = []
    
    for teacher in teachers_with_schedules:
        # Get today's schedules for this teacher
        schedules = TeacherSchedule.objects.filter(
            teacher=teacher,
            day_of_week=day_of_week,
            is_active=True,
            effective_date__lte=today
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=today)
        ).select_related('subject', 'classroom')
        
        # Get all JP numbers from schedules
        scheduled_jp_numbers = set()
        for schedule in schedules:
            for jp_num in range(schedule.jp_start, schedule.jp_end + 1):
                scheduled_jp_numbers.add(jp_num)
        
        # Get attendance records for today
        attendances = TeacherAttendance.objects.filter(
            teacher=teacher,
            date=today
        )
        
        # Check which JP are absent or not recorded
        absent_jp_numbers = []
        attendance_statuses = {}
        
        for attendance in attendances:
            attendance_statuses[attendance.jp_number] = attendance.status
        
        for jp_num in scheduled_jp_numbers:
            status = attendance_statuses.get(jp_num)
            if not status or status != 'HADIR':
                absent_jp_numbers.append({
                    'jp_number': jp_num,
                    'status': status if status else 'NOT_RECORDED'
                })
        
        # If teacher has any absent JP, add to list
        if absent_jp_numbers:
            # Get the most common status (or NOT_RECORDED)
            status_counts = {}
            for jp_info in absent_jp_numbers:
                status = jp_info['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            main_status = max(status_counts, key=status_counts.get)
            
            absent_teachers.append({
                'teacher': teacher,
                'status': main_status,
                'jp_numbers': absent_jp_numbers,
                'schedules': list(schedules),
                'total_absent_jp': len(absent_jp_numbers),
            })
    
    # Sort by teacher name
    absent_teachers.sort(key=lambda x: x['teacher'].full_name)
    
    return absent_teachers


def _get_attendance_trends(days: int = 30) -> list:
    """
    Get attendance trends for the last N days.
    
    Returns:
        List of dictionaries containing:
        - date: Date string (YYYY-MM-DD)
        - total_hadir: Count of HADIR
        - total_sakit: Count of SAKIT
        - total_izin: Count of IZIN
        - total_alpa: Count of ALPA
        - attendance_percentage: Percentage of HADIR
    """
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days - 1)
    
    trends = []
    current_date = start_date
    
    while current_date <= end_date:
        # Get attendance records for this date
        attendances = TeacherAttendance.objects.filter(date=current_date)
        
        total_hadir = attendances.filter(status='HADIR').count()
        total_sakit = attendances.filter(status='SAKIT').count()
        total_izin = attendances.filter(status='IZIN').count()
        total_alpa = attendances.filter(status='ALPA').count()
        total_records = attendances.count()
        
        attendance_percentage = 0.0
        if total_records > 0:
            attendance_percentage = round((total_hadir / total_records) * 100, 1)
        
        trends.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'date_display': current_date.strftime('%d/%m'),
            'total_hadir': total_hadir,
            'total_sakit': total_sakit,
            'total_izin': total_izin,
            'total_alpa': total_alpa,
            'total_records': total_records,
            'attendance_percentage': attendance_percentage,
        })
        
        current_date += timedelta(days=1)
    
    return trends


def _get_dashboard_notifications() -> list:
    """
    Get dashboard notifications for missing attendance and conflicts.
    
    Uses the NotificationService to get comprehensive notifications.
    
    Returns:
        List of dictionaries containing:
        - type: Notification type ('missing_attendance', 'conflict', 'absent', 'info')
        - message: Notification message
        - priority: Priority level ('high', 'medium', 'low')
        - date: Related date (if applicable)
    """
    notifications = []
    today = timezone.now().date()
    
    try:
        # Get all notifications from NotificationService
        all_notifs = NotificationService.get_all_notifications(today)
        
        # Convert to dashboard format
        for notif in all_notifs['all_notifications']:
            notifications.append({
                'type': notif['type'],
                'message': notif['message'],
                'priority': notif['priority'],
                'date': notif.get('date'),
            })
        
        # Add summary notification if there are high priority items
        if all_notifs['high_priority_count'] > 0:
            notifications.insert(0, {
                'type': NotificationService.TYPE_WARNING,
                'message': f'{all_notifs["high_priority_count"]} notifikasi prioritas tinggi memerlukan perhatian',
                'priority': NotificationService.PRIORITY_HIGH,
                'date': today,
            })
        
    except NotificationServiceError as e:
        logger.error(f"Error getting notifications from NotificationService: {str(e)}")
        # Fallback to basic notifications
        notifications = _get_basic_notifications(today)
    except Exception as e:
        logger.error(f"Unexpected error getting notifications: {str(e)}")
        notifications = []
    
    return notifications


def _get_basic_notifications(today: date) -> list:
    """
    Fallback method for basic notifications if NotificationService fails.
    
    Returns:
        List of basic notification dictionaries
    """
    notifications = []
    day_of_week = today.weekday()
    
    # Check for missing attendance today
    teachers_with_schedules = Teacher.objects.filter(
        is_active=True,
        schedules__day_of_week=day_of_week,
        schedules__is_active=True,
        schedules__effective_date__lte=today
    ).filter(
        Q(schedules__end_date__isnull=True) | 
        Q(schedules__end_date__gte=today)
    ).distinct().count()
    
    # Get teachers who have recorded attendance today
    teachers_with_attendance = TeacherAttendance.objects.filter(
        date=today
    ).values('teacher').distinct().count()
    
    missing_count = teachers_with_schedules - teachers_with_attendance
    
    if missing_count > 0:
        notifications.append({
            'type': 'missing_attendance',
            'message': f'{missing_count} ustadz belum mencatat absensi hari ini',
            'priority': 'high',
            'date': today,
        })
    
    # Check for teachers on leave today
    on_leave = TeacherAttendance.objects.filter(
        date=today,
        status__in=['SAKIT', 'IZIN', 'CUTI']
    ).select_related('teacher').distinct()
    
    if on_leave.exists():
        leave_count = on_leave.count()
        notifications.append({
            'type': 'info',
            'message': f'{leave_count} ustadz sedang izin/sakit/cuti hari ini',
            'priority': 'low',
            'date': today,
        })
    
    return notifications


def _check_scheduling_conflicts() -> list:
    """
    Check for scheduling conflicts (same teacher or classroom at same time).
    
    Returns:
        List of conflict dictionaries
    """
    conflicts = []
    today = timezone.now().date()
    
    # Get all active schedules
    schedules = TeacherSchedule.objects.filter(
        is_active=True,
        effective_date__lte=today
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=today)
    ).select_related('teacher', 'subject', 'classroom')
    
    # Check for teacher conflicts (same teacher, same day, overlapping JP)
    teacher_schedules = {}
    for schedule in schedules:
        key = (schedule.teacher_id, schedule.day_of_week)
        if key not in teacher_schedules:
            teacher_schedules[key] = []
        teacher_schedules[key].append(schedule)
    
    for (teacher_id, day), teacher_schedule_list in teacher_schedules.items():
        for i, schedule1 in enumerate(teacher_schedule_list):
            for schedule2 in teacher_schedule_list[i+1:]:
                # Check for JP overlap
                if not (schedule1.jp_end < schedule2.jp_start or schedule2.jp_end < schedule1.jp_start):
                    conflicts.append({
                        'type': 'teacher_conflict',
                        'teacher': schedule1.teacher,
                        'day': schedule1.day_of_week,
                        'schedule1': schedule1,
                        'schedule2': schedule2,
                    })
    
    return conflicts


def _get_teacher_specific_data(teacher: Teacher, start_date: date, end_date: date) -> dict:
    """
    Get teacher-specific dashboard data.
    
    Returns:
        Dictionary containing:
        - teacher: Teacher instance
        - stats: Personal attendance statistics
        - upcoming_schedule: Today's schedule
        - recent_attendance: Recent attendance records
    """
    # Get personal statistics
    attendances = TeacherAttendance.objects.filter(
        teacher=teacher,
        date__gte=start_date,
        date__lte=end_date
    )
    
    total_hadir = attendances.filter(status='HADIR').count()
    total_sakit = attendances.filter(status='SAKIT').count()
    total_izin = attendances.filter(status='IZIN').count()
    total_alpa = attendances.filter(status='ALPA').count()
    total_records = attendances.count()
    
    attendance_percentage = 0.0
    if total_records > 0:
        attendance_percentage = round((total_hadir / total_records) * 100, 1)
    
    # Get today's schedule
    today = timezone.now().date()
    day_of_week = today.weekday()
    
    today_schedules = TeacherSchedule.objects.filter(
        teacher=teacher,
        day_of_week=day_of_week,
        is_active=True,
        effective_date__lte=today
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=today)
    ).select_related('subject', 'classroom').order_by('jp_start')
    
    # Get recent attendance records
    recent_attendance = TeacherAttendance.objects.filter(
        teacher=teacher
    ).select_related('schedule', 'schedule__subject', 'schedule__classroom').order_by('-date', '-jp_number')[:10]
    
    return {
        'teacher': teacher,
        'stats': {
            'total_hadir': total_hadir,
            'total_sakit': total_sakit,
            'total_izin': total_izin,
            'total_alpa': total_alpa,
            'total_records': total_records,
            'attendance_percentage': attendance_percentage,
        },
        'upcoming_schedule': list(today_schedules),
        'recent_attendance': list(recent_attendance),
    }


# ============================================
# Teacher Dashboard API (JSON for Charts)
# ============================================

@login_required
@require_http_methods(["GET"])
def teacher_dashboard_api(request):
    """
    AJAX endpoint for teacher dashboard data (for charts and real-time updates).
    
    Accessible by: All authenticated users
    
    Query parameters:
    - start_date: Start date (YYYY-MM-DD, optional)
    - end_date: End date (YYYY-MM-DD, optional)
    - teacher_id: Specific teacher ID (optional, admin only)
    
    Returns JSON:
    {
        "success": true|false,
        "stats": {...},
        "trends": [...],
        "absent_teachers": [...],
        "notifications": [...]
    }
    
    Requirements: FR-018, FR-019, FR-020
    """
    try:
        # Get date range from query parameters
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid start_date format (use YYYY-MM-DD)'
                }, status=400)
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid end_date format (use YYYY-MM-DD)'
                }, status=400)
        
        # Get teacher_id if provided (admin only)
        teacher_id = request.GET.get('teacher_id')
        teacher_data = None
        
        if teacher_id:
            if not request.user.is_superuser:
                return JsonResponse({
                    'success': False,
                    'error': 'Only admin can view other teacher data'
                }, status=403)
            
            try:
                teacher = Teacher.objects.get(id=teacher_id)
                teacher_data = _get_teacher_specific_data(teacher, start_date, end_date)
                
                # Convert teacher data to JSON-serializable format
                teacher_data = {
                    'teacher': {
                        'id': str(teacher.id),
                        'full_name': teacher.full_name,
                        'nip': teacher.nip,
                    },
                    'stats': teacher_data['stats'],
                    'upcoming_schedule': [
                        {
                            'id': str(schedule.id),
                            'subject': schedule.subject.name,
                            'classroom': schedule.classroom.name,
                            'jp_start': schedule.jp_start,
                            'jp_end': schedule.jp_end,
                        }
                        for schedule in teacher_data['upcoming_schedule']
                    ],
                    'recent_attendance': [
                        {
                            'id': str(att.id),
                            'date': att.date.strftime('%Y-%m-%d'),
                            'jp_number': att.jp_number,
                            'status': att.status,
                            'subject': att.schedule.subject.name if att.schedule else None,
                            'classroom': att.schedule.classroom.name if att.schedule else None,
                        }
                        for att in teacher_data['recent_attendance']
                    ],
                }
            except Teacher.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Teacher not found'
                }, status=404)
        
        # Calculate statistics
        stats = _calculate_dashboard_statistics(start_date, end_date)
        
        # Get trends
        trends = _get_attendance_trends(days=30)
        
        # Get absent teachers
        absent_teachers = _get_absent_teachers_today()
        
        # Convert absent teachers to JSON-serializable format
        absent_teachers_json = [
            {
                'teacher': {
                    'id': str(item['teacher'].id),
                    'full_name': item['teacher'].full_name,
                    'nip': item['teacher'].nip,
                },
                'status': item['status'],
                'total_absent_jp': item['total_absent_jp'],
                'jp_numbers': item['jp_numbers'],
            }
            for item in absent_teachers
        ]
        
        # Get notifications
        notifications = _get_dashboard_notifications()
        
        return JsonResponse({
            'success': True,
            'stats': stats,
            'trends': trends,
            'absent_teachers': absent_teachers_json,
            'notifications': notifications,
            'teacher_data': teacher_data,
            'date_range': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
            }
        })
        
    except Exception as e:
        logger.error(f"Error in teacher dashboard API: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Terjadi kesalahan: {str(e)}'
        }, status=500)
