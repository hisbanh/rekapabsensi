"""
Teacher Attendance Recording Views
Handles all views related to teacher attendance input, history, and management

Authorization:
- Teacher: Can record own attendance (self-service) with location validation
- Admin: Can record/edit/delete attendance for any teacher on any date
- Teachers: Can only view/edit attendance within 7 days
- Admin: Unlimited date range access

Requirements: FR-012 to FR-017, FR-028 to FR-032
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta, date
import logging
import json

from .models import Teacher, TeacherAttendance, TeacherSchedule
from .services.teacher_attendance_service import (
    TeacherAttendanceService,
    TeacherAttendanceServiceError
)
from .services.schedule_service import ScheduleService
from .decorators import admin_required, guru_or_admin_required

logger = logging.getLogger(__name__)


# ============================================
# Self-Service Attendance Input (Teachers)
# ============================================

@login_required
def attendance_input(request):
    """
    Self-service attendance input for teachers.
    
    Accessible by: Teachers (for own attendance)
    
    Features:
    - Display today's schedule for logged-in teacher
    - Show JP slots with status selection
    - Location detection and validation
    - Record attendance with location check
    - 7-day limit for past dates
    
    Requirements: FR-012, FR-013, FR-014, FR-016, FR-028
    """
    try:
        # Check if user has associated teacher profile
        if not hasattr(request.user, 'teacher_profile'):
            messages.error(request, "Anda tidak memiliki profil ustadz/ustadzah")
            return redirect('dashboard')
        
        teacher = request.user.teacher_profile
        
        # Get date from query parameter or default to today
        date_str = request.GET.get('date', timezone.now().date().strftime('%Y-%m-%d'))
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Format tanggal tidak valid")
            target_date = timezone.now().date()
        
        # Validate date is not in the future
        if target_date > timezone.now().date():
            messages.error(request, "Tidak dapat mengisi absensi untuk tanggal di masa depan")
            target_date = timezone.now().date()
        
        # Validate 7-day limit for teachers
        days_past = (timezone.now().date() - target_date).days
        if days_past > 7:
            messages.error(request, "Ustadz/ustadzah hanya dapat mengisi absensi untuk 7 hari terakhir")
            target_date = timezone.now().date()
        
        # Handle POST request - record attendance
        if request.method == 'POST':
            return _process_teacher_attendance_input(request, teacher, target_date)
        
        # GET request - show form
        # Get teacher's schedule for the target date
        day_of_week = target_date.weekday()
        schedules = TeacherSchedule.objects.filter(
            teacher=teacher,
            day_of_week=day_of_week,
            is_active=True,
            effective_date__lte=target_date
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=target_date)
        ).select_related('subject', 'classroom').order_by('jp_start')
        
        # Get existing attendance records for the date
        existing_records = {}
        attendances = TeacherAttendance.objects.filter(
            teacher=teacher,
            date=target_date
        ).select_related('schedule')
        
        for attendance in attendances:
            existing_records[attendance.jp_number] = attendance
        
        # Prepare schedule data with attendance status
        schedule_data = []
        for schedule in schedules:
            # Generate JP range for this schedule
            for jp_num in range(schedule.jp_start, schedule.jp_end + 1):
                existing = existing_records.get(jp_num)
                schedule_data.append({
                    'schedule': schedule,
                    'jp_number': jp_num,
                    'subject': schedule.subject.name,
                    'classroom': schedule.classroom.name,
                    'existing_attendance': existing,
                    'status': existing.status if existing else None,
                    'notes': existing.notes if existing else '',
                })
        
        # Get date range for date picker (7 days back)
        min_date = timezone.now().date() - timedelta(days=7)
        max_date = timezone.now().date()
        
        context = {
            'teacher': teacher,
            'target_date': target_date,
            'schedule_data': schedule_data,
            'min_date': min_date,
            'max_date': max_date,
            'status_choices': TeacherAttendance.STATUS_CHOICES,
            'is_today': target_date == timezone.now().date(),
        }
        
    except Exception as e:
        logger.error(f"Error loading teacher attendance input: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat memuat form absensi")
        context = {
            'teacher': None,
            'schedule_data': [],
            'status_choices': TeacherAttendance.STATUS_CHOICES,
        }
    
    return render(request, 'teacher/attendance_input.html', context)


def _process_teacher_attendance_input(request, teacher, target_date):
    """Process self-service attendance form submission"""
    try:
        # Get form data
        jp_numbers = request.POST.getlist('jp_numbers')
        statuses = request.POST.getlist('statuses')
        notes_list = request.POST.getlist('notes')
        schedule_ids = request.POST.getlist('schedule_ids')
        
        # Get location data
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        
        # Validate location if provided
        is_location_valid = False
        if latitude and longitude:
            try:
                lat = float(latitude)
                lon = float(longitude)
                is_location_valid = TeacherAttendanceService.validate_location(lat, lon)
                
                if not is_location_valid:
                    messages.warning(
                        request,
                        "Lokasi Anda di luar area sekolah. Absensi tetap dicatat tetapi ditandai sebagai lokasi tidak valid."
                    )
            except (ValueError, TeacherAttendanceServiceError) as e:
                logger.error(f"Location validation error: {str(e)}")
                messages.warning(request, "Gagal memvalidasi lokasi")
        
        # Prepare attendance data
        attendance_records = []
        for i, jp_num in enumerate(jp_numbers):
            status = statuses[i] if i < len(statuses) else 'HADIR'
            notes = notes_list[i] if i < len(notes_list) else ''
            schedule_id = schedule_ids[i] if i < len(schedule_ids) and schedule_ids[i] else None
            
            attendance_data = {
                'teacher_id': str(teacher.id),
                'date': target_date,
                'jp_number': int(jp_num),
                'status': status,
                'notes': notes,
                'recorded_by': request.user,
                'latitude': float(latitude) if latitude else None,
                'longitude': float(longitude) if longitude else None,
            }
            
            if schedule_id:
                attendance_data['schedule_id'] = schedule_id
            
            attendance_records.append(attendance_data)
        
        # Record attendance using service
        created, errors = TeacherAttendanceService.bulk_record_attendance(
            attendance_records,
            request.user
        )
        
        if errors:
            for error in errors:
                messages.error(request, f"JP {error['data']['jp_number']}: {error['error']}")
        
        if created:
            messages.success(
                request,
                f"Absensi berhasil dicatat untuk {len(created)} JP"
            )
        
    except Exception as e:
        logger.error(f"Error processing teacher attendance: {str(e)}")
        messages.error(request, f"Terjadi kesalahan: {str(e)}")
    
    return redirect('teacher_attendance_input')


# ============================================
# Admin Attendance Input (Any Teacher, Any Date)
# ============================================

@login_required
@admin_required
def attendance_admin_input(request):
    """
    Admin attendance input for any teacher on any date.
    
    Accessible by: Admin only
    
    Features:
    - Select any teacher
    - Select any past date (no 7-day limit)
    - Display teacher's schedule for selected date
    - Record/update attendance for any JP
    - No location validation required
    
    Requirements: FR-012, FR-013, FR-015, FR-029, FR-031
    """
    try:
        # Get parameters
        teacher_id = request.GET.get('teacher')
        date_str = request.GET.get('date', timezone.now().date().strftime('%Y-%m-%d'))
        
        # Parse date
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Format tanggal tidak valid")
            target_date = timezone.now().date()
        
        # Validate date is not in the future
        if target_date > timezone.now().date():
            messages.error(request, "Tidak dapat mengisi absensi untuk tanggal di masa depan")
            target_date = timezone.now().date()
        
        # Handle POST request - record attendance
        if request.method == 'POST':
            return _process_admin_attendance_input(request, target_date)
        
        # GET request - show form
        teacher = None
        schedule_data = []
        
        if teacher_id:
            try:
                teacher = Teacher.objects.get(id=teacher_id)
                
                # Get teacher's schedule for the target date
                day_of_week = target_date.weekday()
                schedules = TeacherSchedule.objects.filter(
                    teacher=teacher,
                    day_of_week=day_of_week,
                    is_active=True,
                    effective_date__lte=target_date
                ).filter(
                    Q(end_date__isnull=True) | Q(end_date__gte=target_date)
                ).select_related('subject', 'classroom').order_by('jp_start')
                
                # Get existing attendance records
                existing_records = {}
                attendances = TeacherAttendance.objects.filter(
                    teacher=teacher,
                    date=target_date
                ).select_related('schedule')
                
                for attendance in attendances:
                    existing_records[attendance.jp_number] = attendance
                
                # Prepare schedule data
                for schedule in schedules:
                    for jp_num in range(schedule.jp_start, schedule.jp_end + 1):
                        existing = existing_records.get(jp_num)
                        schedule_data.append({
                            'schedule': schedule,
                            'jp_number': jp_num,
                            'subject': schedule.subject.name,
                            'classroom': schedule.classroom.name,
                            'existing_attendance': existing,
                            'status': existing.status if existing else None,
                            'notes': existing.notes if existing else '',
                        })
                
            except Teacher.DoesNotExist:
                messages.error(request, "Ustadz/ustadzah tidak ditemukan")
        
        # Get all active teachers for dropdown
        teachers = Teacher.objects.filter(is_active=True).order_by('full_name')
        
        context = {
            'teachers': teachers,
            'selected_teacher': teacher,
            'target_date': target_date,
            'schedule_data': schedule_data,
            'status_choices': TeacherAttendance.STATUS_CHOICES,
        }
        
    except Exception as e:
        logger.error(f"Error loading admin attendance input: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat memuat form absensi")
        context = {
            'teachers': [],
            'schedule_data': [],
            'status_choices': TeacherAttendance.STATUS_CHOICES,
        }
    
    return render(request, 'teacher/attendance_admin_input.html', context)


def _process_admin_attendance_input(request, target_date):
    """Process admin attendance form submission"""
    try:
        # Get form data
        teacher_id = request.POST.get('teacher_id')
        jp_numbers = request.POST.getlist('jp_numbers')
        statuses = request.POST.getlist('statuses')
        notes_list = request.POST.getlist('notes')
        schedule_ids = request.POST.getlist('schedule_ids')
        
        if not teacher_id:
            messages.error(request, "Ustadz/ustadzah harus dipilih")
            return redirect('teacher_attendance_admin')
        
        # Prepare attendance data
        attendance_records = []
        for i, jp_num in enumerate(jp_numbers):
            status = statuses[i] if i < len(statuses) else 'HADIR'
            notes = notes_list[i] if i < len(notes_list) else ''
            schedule_id = schedule_ids[i] if i < len(schedule_ids) and schedule_ids[i] else None
            
            attendance_data = {
                'teacher_id': teacher_id,
                'date': target_date,
                'jp_number': int(jp_num),
                'status': status,
                'notes': notes,
                'recorded_by': request.user,
            }
            
            if schedule_id:
                attendance_data['schedule_id'] = schedule_id
            
            attendance_records.append(attendance_data)
        
        # Record attendance using service
        created, errors = TeacherAttendanceService.bulk_record_attendance(
            attendance_records,
            request.user
        )
        
        if errors:
            for error in errors:
                messages.error(request, f"JP {error['data']['jp_number']}: {error['error']}")
        
        if created:
            messages.success(
                request,
                f"Absensi berhasil dicatat untuk {len(created)} JP"
            )
        
    except Exception as e:
        logger.error(f"Error processing admin attendance: {str(e)}")
        messages.error(request, f"Terjadi kesalahan: {str(e)}")
    
    return redirect('teacher_attendance_admin')


# ============================================
# Attendance History View
# ============================================

@login_required
def attendance_history(request):
    """
    View attendance history with filtering and pagination.
    
    Accessible by: All authenticated users
    - Teachers: Can only view own attendance history
    - Admin: Can view all teachers' attendance history
    
    Features:
    - Filter by date range, teacher, status
    - Search functionality
    - Pagination (50 per page)
    - Display attendance details with schedule info
    - Edit/Delete buttons (admin only, within constraints)
    
    Requirements: FR-028, FR-029, FR-030
    """
    try:
        # Get filter parameters
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        teacher_id = request.GET.get('teacher')
        status_filter = request.GET.get('status')
        search_query = request.GET.get('search', '').strip()
        
        # Default date range (last 30 days)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
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
        
        # Build query
        attendances = TeacherAttendance.objects.select_related(
            'teacher', 'schedule', 'schedule__subject', 'schedule__classroom',
            'recorded_by', 'substitute_for'
        ).filter(
            date__gte=start_date,
            date__lte=end_date
        )
        
        # Filter by teacher (teachers can only see own records)
        if request.user.is_superuser:
            # Admin can see all or filter by specific teacher
            if teacher_id:
                attendances = attendances.filter(teacher_id=teacher_id)
        else:
            # Teachers can only see own records
            if hasattr(request.user, 'teacher_profile'):
                attendances = attendances.filter(teacher=request.user.teacher_profile)
            else:
                # User has no teacher profile, show empty results
                attendances = TeacherAttendance.objects.none()
        
        # Filter by status
        if status_filter:
            attendances = attendances.filter(status=status_filter)
        
        # Search by teacher name or notes
        if search_query:
            attendances = attendances.filter(
                Q(teacher__full_name__icontains=search_query) |
                Q(notes__icontains=search_query)
            )
        
        # Order by date and JP
        attendances = attendances.order_by('-date', 'jp_number')
        
        # Pagination
        paginator = Paginator(attendances, 50)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Get teachers list for filter (admin only)
        teachers = []
        if request.user.is_superuser:
            teachers = Teacher.objects.filter(is_active=True).order_by('full_name')
        
        # Calculate summary statistics
        total_records = attendances.count()
        hadir_count = attendances.filter(status='HADIR').count()
        sakit_count = attendances.filter(status='SAKIT').count()
        izin_count = attendances.filter(status='IZIN').count()
        alpa_count = attendances.filter(status='ALPA').count()
        
        context = {
            'attendances': page_obj,
            'teachers': teachers,
            'status_choices': TeacherAttendance.STATUS_CHOICES,
            # Preserve filter values
            'start_date': start_date,
            'end_date': end_date,
            'selected_teacher': teacher_id,
            'selected_status': status_filter,
            'search_query': search_query,
            # Summary statistics
            'total_records': total_records,
            'hadir_count': hadir_count,
            'sakit_count': sakit_count,
            'izin_count': izin_count,
            'alpa_count': alpa_count,
        }
        
    except Exception as e:
        logger.error(f"Error loading attendance history: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat memuat riwayat absensi")
        context = {
            'attendances': [],
            'teachers': [],
            'status_choices': TeacherAttendance.STATUS_CHOICES,
        }
    
    return render(request, 'teacher/attendance_history.html', context)


# ============================================
# Attendance Update View
# ============================================

@login_required
def attendance_update(request, pk):
    """
    Update existing attendance record.
    
    Accessible by:
    - Admin: Can update any attendance record
    - Teachers: Can update own attendance within 7 days
    
    Features:
    - Edit status, notes
    - Validation based on user role
    - Audit trail maintained
    
    Requirements: FR-014, FR-015, FR-028, FR-029, FR-030
    """
    try:
        attendance = get_object_or_404(
            TeacherAttendance.objects.select_related('teacher', 'schedule'),
            id=pk
        )
        
        # Permission check
        if not request.user.is_superuser:
            # Teachers can only edit own attendance
            if not hasattr(request.user, 'teacher_profile') or \
               attendance.teacher != request.user.teacher_profile:
                messages.error(request, "Anda tidak memiliki akses untuk mengedit absensi ini")
                return redirect('teacher_attendance_history')
            
            # Check 7-day limit for teachers
            days_past = (timezone.now().date() - attendance.date).days
            if days_past > 7:
                messages.error(request, "Anda hanya dapat mengedit absensi dalam 7 hari terakhir")
                return redirect('teacher_attendance_history')
        
        # Handle POST request - update attendance
        if request.method == 'POST':
            try:
                update_data = {
                    'status': request.POST.get('status'),
                    'notes': request.POST.get('notes', ''),
                    'recorded_by': request.user,
                }
                
                # Update using service
                updated_attendance = TeacherAttendanceService.update_attendance(
                    pk,
                    update_data
                )
                
                messages.success(request, "Absensi berhasil diperbarui")
                return redirect('teacher_attendance_history')
                
            except TeacherAttendanceServiceError as e:
                logger.error(f"Error updating attendance: {str(e)}")
                messages.error(request, f"Gagal memperbarui absensi: {str(e)}")
        
        # GET request - show form
        context = {
            'attendance': attendance,
            'status_choices': TeacherAttendance.STATUS_CHOICES,
        }
        
    except Exception as e:
        logger.error(f"Error loading attendance update form: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat memuat form")
        return redirect('teacher_attendance_history')
    
    return render(request, 'teacher/attendance_update.html', context)


# ============================================
# Attendance Delete View
# ============================================

@login_required
@require_http_methods(["POST"])
def attendance_delete(request, pk):
    """
    Delete attendance record.
    
    Accessible by:
    - Admin: Can delete any attendance record
    - Teachers: Can delete own attendance within 7 days
    
    Features:
    - Soft delete (mark as inactive) or hard delete
    - Validation based on user role
    - Confirmation required
    
    Requirements: FR-029, FR-030, FR-031
    """
    try:
        attendance = get_object_or_404(
            TeacherAttendance.objects.select_related('teacher'),
            id=pk
        )
        
        # Permission check
        if not request.user.is_superuser:
            # Teachers can only delete own attendance
            if not hasattr(request.user, 'teacher_profile') or \
               attendance.teacher != request.user.teacher_profile:
                messages.error(request, "Anda tidak memiliki akses untuk menghapus absensi ini")
                return redirect('teacher_attendance_history')
            
            # Check 7-day limit for teachers
            days_past = (timezone.now().date() - attendance.date).days
            if days_past > 7:
                messages.error(request, "Anda hanya dapat menghapus absensi dalam 7 hari terakhir")
                return redirect('teacher_attendance_history')
        
        # Store info for success message
        teacher_name = attendance.teacher.full_name
        date_str = attendance.date.strftime('%d/%m/%Y')
        jp_num = attendance.jp_number
        
        # Delete attendance
        attendance.delete()
        
        messages.success(
            request,
            f"Absensi {teacher_name} tanggal {date_str} JP {jp_num} berhasil dihapus"
        )
        
    except Exception as e:
        logger.error(f"Error deleting attendance: {str(e)}")
        messages.error(request, f"Gagal menghapus absensi: {str(e)}")
    
    return redirect('teacher_attendance_history')


# ============================================
# AJAX API Endpoints
# ============================================

@login_required
@require_http_methods(["POST"])
def api_validate_location(request):
    """
    AJAX endpoint for validating location coordinates.
    
    Accessible by: All authenticated users
    
    Accepts JSON payload:
    {
        "latitude": <float>,
        "longitude": <float>
    }
    
    Returns JSON:
    {
        "success": true|false,
        "is_valid": true|false,
        "message": "<message>",
        "distance": <distance_in_meters>
    }
    
    Requirements: FR-016
    """
    try:
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if latitude is None or longitude is None:
            return JsonResponse({
                'success': False,
                'error': 'Latitude dan longitude harus disediakan'
            }, status=400)
        
        # Validate location
        try:
            lat = float(latitude)
            lon = float(longitude)
            is_valid = TeacherAttendanceService.validate_location(lat, lon)
            
            return JsonResponse({
                'success': True,
                'is_valid': is_valid,
                'message': 'Lokasi valid' if is_valid else 'Lokasi di luar area sekolah',
            })
            
        except (ValueError, TeacherAttendanceServiceError) as e:
            return JsonResponse({
                'success': False,
                'error': f'Validasi lokasi gagal: {str(e)}'
            }, status=400)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Format JSON tidak valid'
        }, status=400)
    except Exception as e:
        logger.error(f"Error validating location: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Terjadi kesalahan: {str(e)}'
        }, status=500)


@login_required
def api_teacher_schedule(request):
    """
    AJAX endpoint to get teacher's schedule for a specific date.
    
    Accessible by: All authenticated users
    
    Query parameters:
    - teacher_id: UUID of the teacher
    - date: Date in YYYY-MM-DD format
    
    Returns JSON:
    {
        "success": true|false,
        "schedules": [
            {
                "jp_number": <int>,
                "subject": "<subject_name>",
                "classroom": "<classroom_name>",
                "has_attendance": true|false,
                "status": "<status>" (if has_attendance)
            }
        ]
    }
    
    Requirements: FR-006, FR-007
    """
    try:
        teacher_id = request.GET.get('teacher_id')
        date_str = request.GET.get('date')
        
        if not teacher_id or not date_str:
            return JsonResponse({
                'success': False,
                'error': 'teacher_id dan date harus disediakan'
            }, status=400)
        
        # Parse date
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Format tanggal tidak valid (gunakan YYYY-MM-DD)'
            }, status=400)
        
        # Get teacher
        try:
            teacher = Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Ustadz/ustadzah tidak ditemukan'
            }, status=404)
        
        # Get schedule for the date
        day_of_week = target_date.weekday()
        schedules = TeacherSchedule.objects.filter(
            teacher=teacher,
            day_of_week=day_of_week,
            is_active=True,
            effective_date__lte=target_date
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=target_date)
        ).select_related('subject', 'classroom').order_by('jp_start')
        
        # Get existing attendance
        existing_records = {}
        attendances = TeacherAttendance.objects.filter(
            teacher=teacher,
            date=target_date
        )
        for attendance in attendances:
            existing_records[attendance.jp_number] = attendance
        
        # Build response
        schedule_list = []
        for schedule in schedules:
            for jp_num in range(schedule.jp_start, schedule.jp_end + 1):
                existing = existing_records.get(jp_num)
                schedule_list.append({
                    'jp_number': jp_num,
                    'subject': schedule.subject.name,
                    'classroom': schedule.classroom.name,
                    'has_attendance': existing is not None,
                    'status': existing.status if existing else None,
                    'notes': existing.notes if existing else '',
                })
        
        return JsonResponse({
            'success': True,
            'schedules': schedule_list
        })
        
    except Exception as e:
        logger.error(f"Error getting teacher schedule: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Terjadi kesalahan: {str(e)}'
        }, status=500)
