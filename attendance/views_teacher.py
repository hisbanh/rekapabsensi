"""
Views for Teacher Attendance Management
Handles teacher CRUD, schedules, and attendance input
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import models
from datetime import datetime, timedelta
import json
import logging

from .models import Teacher, TeacherSchedule, TeacherDailyAttendance, TeacherStatus, DaySchedule
from .forms import TeacherForm, TeacherScheduleForm, TeacherAttendanceFilterForm
from .services.teacher_service import TeacherService
from .services.teacher_attendance_service import TeacherAttendanceService
from .services.schedule_service import ScheduleService
from .services.teacher_export_service import TeacherExportService
from .exceptions import AttendanceServiceError
from .decorators import admin_required, guru_or_admin_required

logger = logging.getLogger(__name__)


# ============================================
# Teacher Dashboard
# ============================================

@login_required
def teacher_dashboard(request):
    """Dashboard for teacher attendance overview"""
    try:
        # Get date range from request
        today = timezone.now().date()
        start_date = today - timedelta(days=30)
        end_date = today
        
        # Get statistics
        stats = TeacherAttendanceService.get_attendance_statistics(
            start_date=start_date,
            end_date=end_date
        )
        
        # Get total active teachers
        total_teachers = Teacher.objects.filter(is_active=True).count()
        
        # Calculate average JP per week
        teachers = Teacher.objects.filter(is_active=True)
        total_jp = sum(t.total_jp_per_week for t in teachers)
        avg_jp_per_week = round(total_jp / total_teachers, 1) if total_teachers > 0 else 0
        
        # Get teachers missing attendance today
        missing_today = TeacherAttendanceService.get_teachers_missing_attendance(today)
        
        # Get recent attendance records
        recent_attendance = TeacherDailyAttendance.objects.select_related(
            'teacher', 'recorded_by'
        ).order_by('-date', '-recorded_at')[:10]
        
        context = {
            'total_teachers': total_teachers,
            'stats': stats,
            'missing_today': missing_today,
            'missing_count': len(missing_today),
            'recent_attendance': recent_attendance,
            'today': today,
            'start_date': start_date,
            'end_date': end_date,
            'avg_jp_per_week': avg_jp_per_week,
            'total_jp': total_jp,
        }
        
    except Exception as e:
        logger.error(f"Error loading teacher dashboard: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat memuat dashboard")
        context = {}
    
    return render(request, 'attendance/teacher/dashboard.html', context)


# ============================================
# Teacher Management (CRUD)
# ============================================

@login_required
@guru_or_admin_required
def teacher_list(request):
    """List all teachers with filtering"""
    try:
        search_query = request.GET.get('search', '')
        is_active = request.GET.get('is_active', '')
        page = int(request.GET.get('page', 1))
        
        # Convert is_active to boolean
        is_active_filter = None
        if is_active == '1':
            is_active_filter = True
        elif is_active == '0':
            is_active_filter = False
        
        # Get filtered teachers
        result = TeacherService.get_teachers_with_filters(
            search_query=search_query if search_query else None,
            is_active=is_active_filter,
            page=page,
            per_page=20
        )
        
        # Calculate average JP per week
        total_jp = 0
        teacher_count = 0
        for teacher in result['teachers']:
            jp_count = teacher.total_jp_per_week
            if jp_count > 0:
                total_jp += jp_count
                teacher_count += 1
        
        avg_jp_per_week = round(total_jp / teacher_count, 1) if teacher_count > 0 else 0
        
        context = {
            'teachers': result['teachers'],
            'search_query': search_query,
            'is_active': is_active,
            'pagination': result,
            'avg_jp_per_week': avg_jp_per_week,
            'total_jp': total_jp,
        }
        
    except Exception as e:
        logger.error(f"Error loading teacher list: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat memuat data ustadz")
        context = {'teachers': []}
    
    return render(request, 'attendance/teacher/list.html', context)


@login_required
@admin_required
def teacher_create(request):
    """Create new teacher"""
    if request.method == 'POST':
        form = TeacherForm(request.POST)
        if form.is_valid():
            try:
                teacher = form.save(commit=False)
                teacher.created_by = request.user
                teacher.save()
                messages.success(request, f'Ustadz {teacher.name} berhasil ditambahkan')
                return redirect('teacher_list')
            except Exception as e:
                logger.error(f"Error creating teacher: {str(e)}")
                messages.error(request, f'Gagal menambahkan ustadz: {str(e)}')
        else:
            messages.error(request, 'Mohon perbaiki kesalahan pada form')
    else:
        form = TeacherForm()
    
    return render(request, 'attendance/teacher/form.html', {
        'form': form,
        'title': 'Tambah Ustadz',
        'action': 'create'
    })


@login_required
@admin_required
def teacher_edit(request, pk):
    """Edit existing teacher"""
    teacher = get_object_or_404(Teacher, pk=pk)
    
    if request.method == 'POST':
        form = TeacherForm(request.POST, instance=teacher)
        if form.is_valid():
            try:
                teacher = form.save(commit=False)
                teacher.updated_by = request.user
                teacher.save()
                messages.success(request, f'Ustadz {teacher.name} berhasil diperbarui')
                return redirect('teacher_list')
            except Exception as e:
                logger.error(f"Error updating teacher: {str(e)}")
                messages.error(request, f'Gagal memperbarui ustadz: {str(e)}')
        else:
            messages.error(request, 'Mohon perbaiki kesalahan pada form')
    else:
        form = TeacherForm(instance=teacher)
    
    return render(request, 'attendance/teacher/form.html', {
        'form': form,
        'teacher': teacher,
        'title': 'Edit Ustadz',
        'action': 'edit'
    })


@login_required
@admin_required
def teacher_delete(request, pk):
    """Delete teacher"""
    teacher = get_object_or_404(Teacher, pk=pk)
    
    if request.method == 'POST':
        try:
            teacher_name = teacher.name
            teacher.delete()
            messages.success(request, f'Ustadz {teacher_name} berhasil dihapus')
        except Exception as e:
            logger.error(f"Error deleting teacher: {str(e)}")
            messages.error(request, f'Gagal menghapus ustadz: {str(e)}')
        
        return redirect('teacher_list')
    
    return render(request, 'attendance/teacher/delete_confirm.html', {
        'teacher': teacher
    })


@login_required
def teacher_detail(request, pk):
    """View teacher detail with attendance history"""
    try:
        teacher = TeacherService.get_teacher_detail(pk)
        if not teacher:
            messages.error(request, "Ustadz tidak ditemukan")
            return redirect('teacher_list')
        
        # Get date range from request
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        start_date = None
        end_date = None
        
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
        
        # Get attendance summary
        summary = TeacherService.get_teacher_attendance_summary(
            teacher,
            start_date=start_date,
            end_date=end_date
        )
        
        # Get schedules
        schedules = TeacherService.get_teacher_schedule(teacher)
        
        # Pagination for records
        from django.core.paginator import Paginator
        paginator = Paginator(summary['recent_records'], 20)
        page_number = request.GET.get('page')
        records = paginator.get_page(page_number)
        
        context = {
            'teacher': teacher,
            'summary': summary,
            'schedules': schedules,
            'records': records,
            'start_date': start_date,
            'end_date': end_date,
        }
        
    except Exception as e:
        logger.error(f"Error loading teacher detail: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat memuat detail ustadz")
        return redirect('teacher_list')
    
    return render(request, 'attendance/teacher/detail.html', context)


# ============================================
# Teacher Schedule Management
# ============================================

@login_required
@admin_required
def teacher_schedule_manage(request, teacher_id):
    """Manage teacher's weekly schedule"""
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    
    # Get existing schedules
    schedules = TeacherSchedule.objects.filter(
        teacher=teacher
    ).order_by('day_of_week', 'jp_numbers')
    
    # Group schedules by day
    from collections import defaultdict
    schedules_by_day = defaultdict(list)
    for schedule in schedules:
        schedules_by_day[schedule.day_of_week].append(schedule)
    
    # Prepare schedule data for all days
    days = [
        (0, 'Senin'), 
        (1, 'Selasa'),
        (2, 'Rabu'),
        (3, 'Kamis'),
        (4, 'Jumat'),
        (5, 'Sabtu'),
        (6, 'Minggu'),
    ]
    
    schedule_data = []
    for day_num, day_name in days:
        day_schedules = schedules_by_day.get(day_num, [])
        total_jp = sum(len(s.jp_numbers) if s.jp_numbers else 0 for s in day_schedules)
        
        schedule_data.append({
            'day_num': day_num,
            'day_name': day_name,
            'schedules': day_schedules,
            'has_schedule': len(day_schedules) > 0,
            'total_jp': total_jp,
        })
    
    context = {
        'teacher': teacher,
        'schedule_data': schedule_data,
    }
    
    return render(request, 'attendance/teacher/schedule_manage.html', context)


@login_required
@admin_required
def teacher_schedule_edit(request, teacher_id, day_of_week):
    """Edit schedule for specific day"""
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    
    # Get schedule_id from query parameter if editing existing
    schedule_id = request.GET.get('schedule_id')
    schedule = None
    
    if schedule_id:
        schedule = get_object_or_404(TeacherSchedule, pk=schedule_id, teacher=teacher)
    
    if request.method == 'POST':
        form = TeacherScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            try:
                schedule = form.save(commit=False)
                schedule.teacher = teacher
                schedule.day_of_week = day_of_week
                if not schedule.created_by:
                    schedule.created_by = request.user
                schedule.updated_by = request.user
                schedule.save()
                
                day_name = dict(TeacherSchedule.DAY_CHOICES)[day_of_week]
                if schedule_id:
                    messages.success(request, f'Jadwal {day_name} berhasil diperbarui')
                else:
                    messages.success(request, f'Jadwal {day_name} berhasil ditambahkan')
                return redirect('teacher_schedule_manage', teacher_id=teacher.id)
            except Exception as e:
                logger.error(f"Error saving schedule: {str(e)}")
                messages.error(request, f'Gagal menyimpan jadwal: {str(e)}')
        else:
            messages.error(request, 'Mohon perbaiki kesalahan pada form')
    else:
        initial = {'teacher': teacher, 'day_of_week': day_of_week}
        if not schedule:
            initial['academic_year'] = teacher.academic_year
        form = TeacherScheduleForm(instance=schedule, initial=initial)
    
    day_name = dict(TeacherSchedule.DAY_CHOICES)[day_of_week]
    
    context = {
        'form': form,
        'teacher': teacher,
        'day_of_week': day_of_week,
        'day_name': day_name,
        'schedule': schedule,
        'is_edit': schedule is not None,
    }
    
    return render(request, 'attendance/teacher/schedule_form.html', context)


@login_required
@admin_required
@require_http_methods(["POST"])
def teacher_schedule_delete(request, schedule_id):
    """Delete teacher schedule"""
    schedule = get_object_or_404(TeacherSchedule, pk=schedule_id)
    teacher_id = schedule.teacher.id
    
    try:
        day_name = dict(TeacherSchedule.DAY_CHOICES)[schedule.day_of_week]
        schedule.delete()
        messages.success(request, f'Jadwal {day_name} berhasil dihapus')
    except Exception as e:
        logger.error(f"Error deleting schedule: {str(e)}")
        messages.error(request, f'Gagal menghapus jadwal: {str(e)}')
    
    return redirect('teacher_schedule_manage', teacher_id=teacher_id)


# ============================================
# Teacher Attendance Input
# ============================================

@login_required
def teacher_attendance_input(request):
    """Select date for teacher attendance input"""
    today = timezone.now().date()
    
    # Check if user is teacher
    is_teacher_user = hasattr(request.user, 'teacher_profile')
    teacher = request.user.teacher_profile if is_teacher_user else None
    
    context = {
        'today': today,
        'is_teacher_user': is_teacher_user,
        'teacher': teacher,
    }
    
    return render(request, 'attendance/teacher/attendance_select.html', context)


@login_required
def teacher_attendance_form(request, date_str):
    """Attendance input form for specific date"""
    try:
        # Parse date
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Validate date
        today = timezone.now().date()
        is_admin = request.user.is_superuser
        
        if not is_admin:
            # For non-admin: only allow current week (Monday-Saturday)
            # Get Monday of current week
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)
            
            # Get Saturday of current week
            week_end = week_start + timedelta(days=5)
            
            if target_date < week_start or target_date > today:
                messages.error(
                    request, 
                    f'Anda hanya dapat input absensi untuk minggu berjalan '
                    f'({week_start.strftime("%d %b")} - {today.strftime("%d %b %Y")})'
                )
                return redirect('teacher_attendance_input')
        else:
            # Admin: allow input for dates up to 2 months in the past and future
            min_date = today - timedelta(days=60)
            max_date = today + timedelta(days=60)
            
            if target_date < min_date or target_date > max_date:
                messages.warning(
                    request,
                    f'Anda dapat input absensi dalam range ±2 bulan dari hari ini '
                    f'({min_date.strftime("%d %b %Y")} - {max_date.strftime("%d %b %Y")})'
                )
                # Still allow but show warning
                # Uncomment line below to restrict strictly:
                # return redirect('teacher_attendance_input')
        
        # Check if user is teacher
        is_teacher_user = hasattr(request.user, 'teacher_profile')
        
        # Get JP count for this day
        jp_count = ScheduleService.get_jp_count_for_date(target_date)
        day_schedule = ScheduleService.get_schedule_for_date(target_date)
        
        # Determine which teachers to show
        if is_teacher_user and not is_admin:
            # Teacher can only see their own
            teachers = [request.user.teacher_profile]
        else:
            # Admin can see all active teachers
            teachers = Teacher.objects.filter(is_active=True).order_by('name')
        
        # Get existing attendance records
        existing_records = {}
        daily_attendances = TeacherDailyAttendance.objects.filter(
            date=target_date,
            teacher__in=teachers
        ).select_related('teacher')
        
        for attendance in daily_attendances:
            existing_records[str(attendance.teacher.id)] = {
                'jp_statuses': attendance.jp_statuses,
                'notes': attendance.notes,
                'is_replacement': attendance.is_replacement,
            }
        
        # Prepare teachers data with schedules
        teachers_data = []
        for teacher in teachers:
            teacher_id_str = str(teacher.id)
            
            # Get schedule for this day
            schedule = TeacherService.get_schedule_for_date(teacher, target_date)
            
            # Get existing record
            existing = existing_records.get(teacher_id_str, {})
            existing_statuses = existing.get('jp_statuses', {})
            
            # Build JP statuses list
            jp_statuses = []
            for jp_num in range(1, jp_count + 1):
                jp_key = str(jp_num)
                
                # Default status
                if schedule and jp_num in schedule.jp_numbers:
                    default_status = 'H'  # Default to Hadir if in schedule
                else:
                    default_status = ''  # Empty if not in schedule
                
                status = existing_statuses.get(jp_key, default_status)
                
                jp_statuses.append({
                    'jp_num': jp_num,
                    'status': status,
                    'in_schedule': schedule and jp_num in schedule.jp_numbers,
                })
            
            teachers_data.append({
                'teacher': teacher,
                'schedule': schedule,
                'jp_statuses': jp_statuses,
                'notes': existing.get('notes', ''),
                'is_replacement': existing.get('is_replacement', False),
                'has_existing': teacher_id_str in existing_records,
            })
        
        # Generate JP range
        jp_range = list(range(1, jp_count + 1))
        
        # Status choices
        status_choices = TeacherStatus.choices
        
        context = {
            'date': target_date,
            'date_str': date_str,
            'jp_count': jp_count,
            'jp_range': jp_range,
            'day_schedule': day_schedule,
            'teachers_data': teachers_data,
            'total_teachers': len(teachers_data),
            'status_choices': status_choices,
            'is_teacher_user': is_teacher_user,
            'is_admin': is_admin,
            'show_reset_button': True,  # Show reset button
            'show_mark_all_present': True,  # Show mark all present button
        }
        
    except ValueError:
        messages.error(request, "Format tanggal tidak valid")
        return redirect('teacher_attendance_input')
    except Exception as e:
        logger.error(f"Error loading teacher attendance form: {str(e)}")
        messages.error(request, f"Terjadi kesalahan: {str(e)}")
        return redirect('teacher_attendance_input')
    
    return render(request, 'attendance/teacher/attendance_form.html', context)


@login_required
@require_http_methods(["POST"])
def api_save_teacher_attendance(request):
    """AJAX endpoint for saving teacher attendance"""
    try:
        # Parse JSON body
        data = json.loads(request.body)
        
        date_str = data.get('date')
        attendance_data = data.get('attendance', [])
        
        # Validate required fields
        if not date_str:
            return JsonResponse({
                'success': False,
                'error': 'date is required'
            }, status=400)
        
        if not attendance_data:
            return JsonResponse({
                'success': False,
                'error': 'attendance data is required'
            }, status=400)
        
        # Parse date
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=400)
        
        # Check permissions
        is_teacher_user = hasattr(request.user, 'teacher_profile')
        is_admin = request.user.is_superuser
        
        # Validate and save attendance
        created_count = 0
        updated_count = 0
        
        for item in attendance_data:
            teacher_id = item.get('teacher_id')
            jp_statuses = item.get('jp_statuses', {})
            notes = item.get('notes', '')
            is_replacement = item.get('is_replacement', False)
            
            # Get teacher
            try:
                teacher = Teacher.objects.get(id=teacher_id)
            except Teacher.DoesNotExist:
                continue
            
            # Check permission
            if is_teacher_user and not is_admin:
                if teacher.id != request.user.teacher_profile.id:
                    continue  # Skip if not own record
            
            # Validate data
            errors = TeacherAttendanceService.validate_attendance_data(
                jp_statuses, target_date
            )
            if errors:
                return JsonResponse({
                    'success': False,
                    'error': '; '.join(errors)
                }, status=400)
            
            # Save attendance
            attendance, created = TeacherAttendanceService.save_attendance(
                teacher=teacher,
                target_date=target_date,
                jp_statuses=jp_statuses,
                notes=notes,
                is_replacement=is_replacement,
                user=request.user
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Absensi berhasil disimpan! {created_count} data baru, {updated_count} data diperbarui',
            'created': created_count,
            'updated': updated_count
        })
        
    except AttendanceServiceError as e:
        logger.error(f"Attendance service error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON payload'
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error saving teacher attendance: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Terjadi kesalahan: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_reset_teacher_attendance_form(request):
    """AJAX endpoint for resetting attendance form fields"""
    try:
        data = json.loads(request.body)
        date_str = data.get('date')
        
        if not date_str:
            return JsonResponse({
                'success': False,
                'error': 'date is required'
            }, status=400)
        
        # Parse date
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=400)
        
        # Get JP count for this day
        jp_count = ScheduleService.get_jp_count_for_date(target_date)
        
        # Reset data - generate empty form data
        reset_data = {
            'success': True,
            'message': 'Form telah direset ke kondisi awal',
            'jp_count': jp_count,
            'jp_range': list(range(1, jp_count + 1))
        }
        
        return JsonResponse(reset_data)
        
    except Exception as e:
        logger.error(f"Error resetting attendance form: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Terjadi kesalahan: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_mark_all_teachers_present(request):
    """AJAX endpoint for marking all teachers as present"""
    try:
        data = json.loads(request.body)
        date_str = data.get('date')
        
        if not date_str:
            return JsonResponse({
                'success': False,
                'error': 'date is required'
            }, status=400)
        
        # Parse date
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=400)
        
        # Check permissions
        is_admin = request.user.is_superuser
        if not is_admin:
            return JsonResponse({
                'success': False,
                'error': 'Hanya admin yang dapat menggunakan fitur ini'
            }, status=403)
        
        # Get JP count for this day
        jp_count = ScheduleService.get_jp_count_for_date(target_date)
        
        # Get all active teachers
        teachers = Teacher.objects.filter(is_active=True).order_by('name')
        
        # Create default "Hadir" status for all JPs
        all_present_data = []
        for teacher in teachers:
            # Create JP statuses - all set to 'H' (Hadir)
            jp_statuses = {}
            for jp_num in range(1, jp_count + 1):
                jp_statuses[str(jp_num)] = 'H'
            
            all_present_data.append({
                'teacher_id': str(teacher.id),
                'jp_statuses': jp_statuses,
                'notes': '',
                'is_replacement': False
            })
        
        return JsonResponse({
            'success': True,
            'message': f'Semua {len(teachers)} guru siap ditandai sebagai Hadir',
            'attendance_data': all_present_data,
            'teachers_count': len(teachers)
        })
        
    except Exception as e:
        logger.error(f"Error marking all teachers present: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Terjadi kesalahan: {str(e)}'
        }, status=500)


# ============================================
# Teacher Attendance Reports
# ============================================

@login_required
def teacher_attendance_report(request):
    """Teacher attendance report with filtering"""
    try:
        form = TeacherAttendanceFilterForm(request.GET or None)
        
        teachers_data = []
        
        if form.is_valid():
            teacher = form.cleaned_data.get('teacher')
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            
            # Get teachers to report
            if teacher:
                teachers = [teacher]
            else:
                teachers = Teacher.objects.filter(is_active=True).order_by('name')
            
            # Generate report for each teacher
            for t in teachers:
                summary = TeacherService.get_teacher_attendance_summary(
                    t, start_date=start_date, end_date=end_date
                )
                
                teachers_data.append({
                    'teacher': t,
                    'summary': summary,
                })
        
        context = {
            'form': form,
            'teachers_data': teachers_data,
        }
        
    except Exception as e:
        logger.error(f"Error generating teacher report: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat membuat laporan")
        context = {'form': TeacherAttendanceFilterForm()}
    
    return render(request, 'attendance/teacher/report.html', context)



# ============================================
# Export Views
# ============================================

@login_required
def teacher_export_excel(request):
    """Export teacher attendance report to Excel"""
    try:
        # Get filter parameters
        teacher_id = request.GET.get('teacher')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        # Parse dates
        start_date = None
        end_date = None
        
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
        
        # Get teachers data
        if teacher_id:
            try:
                teacher = Teacher.objects.get(id=teacher_id)
                teachers = [teacher]
            except Teacher.DoesNotExist:
                teachers = Teacher.objects.filter(is_active=True).order_by('name')
        else:
            teachers = Teacher.objects.filter(is_active=True).order_by('name')
        
        # Generate report data
        teachers_data = []
        for t in teachers:
            summary = TeacherService.get_teacher_attendance_summary(
                t, start_date=start_date, end_date=end_date
            )
            teachers_data.append({
                'teacher': t,
                'summary': summary,
            })
        
        # Export to Excel
        return TeacherExportService.export_to_excel(
            teachers_data, start_date=start_date, end_date=end_date
        )
        
    except Exception as e:
        logger.error(f"Error exporting to Excel: {str(e)}")
        messages.error(request, f"Gagal export ke Excel: {str(e)}")
        return redirect('teacher_attendance_report')


@login_required
def teacher_export_csv(request):
    """Export teacher attendance report to CSV"""
    try:
        # Get filter parameters (same as Excel)
        teacher_id = request.GET.get('teacher')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        # Parse dates
        start_date = None
        end_date = None
        
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
        
        # Get teachers data
        if teacher_id:
            try:
                teacher = Teacher.objects.get(id=teacher_id)
                teachers = [teacher]
            except Teacher.DoesNotExist:
                teachers = Teacher.objects.filter(is_active=True).order_by('name')
        else:
            teachers = Teacher.objects.filter(is_active=True).order_by('name')
        
        # Generate report data
        teachers_data = []
        for t in teachers:
            summary = TeacherService.get_teacher_attendance_summary(
                t, start_date=start_date, end_date=end_date
            )
            teachers_data.append({
                'teacher': t,
                'summary': summary,
            })
        
        # Export to CSV
        return TeacherExportService.export_to_csv(
            teachers_data, start_date=start_date, end_date=end_date
        )
        
    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")
        messages.error(request, f"Gagal export ke CSV: {str(e)}")
        return redirect('teacher_attendance_report')


@login_required
def teacher_export_pdf(request):
    """Export teacher attendance report to PDF"""
    try:
        form = TeacherAttendanceFilterForm(request.GET)
        
        teacher = None
        start_date = None
        end_date = None
        
        if form.is_valid():
            teacher = form.cleaned_data.get('teacher')
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
        
        # Get teachers
        if teacher:
            teachers = [teacher]
        else:
            teachers = Teacher.objects.filter(is_active=True).order_by('name')
        
        # Generate report data
        teachers_data = []
        for t in teachers:
            summary = TeacherService.get_teacher_attendance_summary(
                t, start_date=start_date, end_date=end_date
            )
            teachers_data.append({
                'teacher': t,
                'summary': summary,
            })
        
        # Export to PDF
        return TeacherExportService.export_to_pdf(
            teachers_data, start_date=start_date, end_date=end_date
        )
        
    except Exception as e:
        logger.error(f"Error exporting to PDF: {str(e)}")
        messages.error(request, f"Gagal export ke PDF: {str(e)}")
        return redirect('teacher_attendance_report')


@login_required
def teacher_export_individual_pdf(request, teacher_id):
    """Export individual teacher attendance report to PDF"""
    try:
        teacher = get_object_or_404(Teacher, pk=teacher_id)
        
        # Get date range from request
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        start_date = None
        end_date = None
        
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
        
        # Export to PDF
        return TeacherExportService.export_teacher_individual_pdf(
            teacher, start_date=start_date, end_date=end_date
        )
        
    except Exception as e:
        logger.error(f"Error exporting individual PDF: {str(e)}")
        messages.error(request, f"Gagal export laporan: {str(e)}")
        return redirect('teacher_detail', pk=teacher_id)


@login_required
def teacher_export_html_pdf(request, teacher_id):
    """
    Export individual teacher attendance report to PDF/HTML
    Menggunakan HTML template dengan CSS styling modern
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Akses ditolak'}, status=403)
    
    try:
        teacher = get_object_or_404(Teacher, pk=teacher_id)
        
        # Get date range from request
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Export menggunakan HTML template + WeasyPrint
        return TeacherExportService.export_teacher_attendance_pdf_html(
            teacher, start_date=start_date, end_date=end_date
        )
        
    except Exception as e:
        logger.error(f"Error exporting HTML PDF: {str(e)}")
        messages.error(request, f"Gagal export laporan: {str(e)}")
        return redirect('teacher_attendance_report')


@login_required
def teacher_export_all_pdf_html(request):
    """
    Export laporan semua guru ke PDF/HTML dengan HTML template
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Akses ditolak'}, status=403)
    
    try:
        # Get date range
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Export semua guru
        return TeacherExportService.export_all_teachers_pdf_html(
            teachers=None, start_date=start_date, end_date=end_date
        )
        
    except Exception as e:
        logger.error(f"Error exporting all teachers PDF: {str(e)}")
        messages.error(request, f"Gagal export laporan: {str(e)}")
        return redirect('teacher_attendance_report')

