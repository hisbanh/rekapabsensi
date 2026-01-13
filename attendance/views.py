"""
Views for the attendance application
Following enterprise architecture patterns with service layer separation

Authorization:
- Admin: Full access to all features including Settings and User management
- Guru: Access to Dashboard, Input Absensi, Laporan, and read-only management views
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db import models
from datetime import datetime, timedelta
import json
import logging

from .models import Student, AttendanceRecord, AttendanceStatus, Classroom, DailyAttendance, DaySchedule, Holiday
from .forms import AttendanceFilterForm
from .services.attendance_service import AttendanceService
from .services.student_service import StudentService
from .services.report_service import ReportService
from .services.schedule_service import ScheduleService
from .services.holiday_service import HolidayService
from .services.pdf_service import PDFService
from .exceptions import AttendanceServiceError, StudentServiceError, ReportServiceError
from .decorators import admin_required, guru_or_admin_required, admin_required_for_write, AdminRequiredMixin

logger = logging.getLogger(__name__)


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard view with comprehensive statistics"""
    template_name = 'attendance/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Get date range from request parameters
            start_date_str = self.request.GET.get('start_date')
            end_date_str = self.request.GET.get('end_date')
            
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
            
            # Get today's statistics for stat cards
            today_stats = AttendanceService.get_attendance_statistics()
            
            # Get classroom statistics for bar chart
            classroom_stats = AttendanceService.get_classroom_statistics()
            
            # Calculate attendance statistics for the date range (for donut chart)
            attendance_records = AttendanceRecord.objects.filter(
                date__gte=start_date,
                date__lte=end_date
            )
            
            attendance_stats = {
                'hadir': attendance_records.filter(status=AttendanceStatus.HADIR).count(),
                'sakit': attendance_records.filter(status=AttendanceStatus.SAKIT).count(),
                'izin': attendance_records.filter(status=AttendanceStatus.IZIN).count(),
                'alpa': attendance_records.filter(status=AttendanceStatus.ALPA).count(),
            }
            
            total_attendance = sum(attendance_stats.values())
            
            # Calculate total students and average attendance
            total_students = Student.objects.filter(is_active=True).count()
            average_attendance = 0
            main_absence_reason = 'Tidak ada data'
            
            if total_attendance > 0:
                average_attendance = round((attendance_stats['hadir'] / total_attendance) * 100, 1)
                
                # Determine main absence reason
                absence_counts = {
                    'Sakit': attendance_stats['sakit'],
                    'Izin': attendance_stats['izin'],
                    'Alpa': attendance_stats['alpa']
                }
                if any(absence_counts.values()):
                    main_absence_reason = max(absence_counts, key=absence_counts.get)
            
            # Get recent attendance records
            recent_attendance = AttendanceRecord.objects.select_related(
                'student', 'student__classroom', 'student__classroom__academic_level'
            ).order_by('-created_at')[:10]
            
            # Calculate missing attendance for current week
            missing_attendance_data = self._get_missing_attendance_for_week()
            
            context.update({
                # Date range
                'start_date': start_date,
                'end_date': end_date,
                
                # Stat cards data
                'total_students': total_students,
                'average_attendance': average_attendance,
                'main_absence_reason': main_absence_reason,
                
                # Chart data
                'attendance_stats': attendance_stats,
                'class_stats': classroom_stats,
                
                # Legacy data (for backward compatibility)
                'today_stats': today_stats,
                'classroom_stats': classroom_stats,
                'recent_attendance': recent_attendance,
                'today': timezone.now().date(),
                'missing_attendance': missing_attendance_data['classrooms_with_missing'],
                'all_attendance_complete': missing_attendance_data['all_complete'],
                'week_start': missing_attendance_data['week_start'],
                'week_end': missing_attendance_data['week_end'],
            })
            
        except Exception as e:
            logger.error(f"Error loading dashboard data: {str(e)}")
            messages.error(self.request, "Terjadi kesalahan saat memuat data dashboard")
            
        return context
    
    def _get_missing_attendance_for_week(self):
        """
        Calculate missing attendance for all classrooms for the current week.
        
        Returns:
            Dict with:
            - classrooms_with_missing: List of dicts with classroom and missing dates
            - all_complete: Boolean indicating if all classrooms have complete attendance
            - week_start: Start date of the week
            - week_end: End date of the week (today or last school day)
        """
        today = timezone.now().date()
        
        # Calculate week start (Monday of current week)
        # Python weekday(): 0=Monday, 6=Sunday
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
        
        # Week end is today (we only check up to today)
        week_end = today
        
        # Get all active classrooms
        classrooms = Classroom.objects.filter(is_active=True).select_related('academic_level')
        
        classrooms_with_missing = []
        
        for classroom in classrooms:
            # Check if classroom has any active students
            has_students = Student.objects.filter(
                classroom=classroom,
                is_active=True
            ).exists()
            
            if not has_students:
                continue
            
            # Get missing dates for this classroom
            missing_dates = AttendanceService.get_missing_attendance(
                classroom=classroom,
                start_date=week_start,
                end_date=week_end
            )
            
            if missing_dates:
                classrooms_with_missing.append({
                    'classroom': classroom,
                    'classroom_name': str(classroom),
                    'missing_dates': missing_dates,
                    'missing_count': len(missing_dates),
                })
        
        # Sort by classroom name
        classrooms_with_missing.sort(key=lambda x: x['classroom_name'])
        
        return {
            'classrooms_with_missing': classrooms_with_missing,
            'all_complete': len(classrooms_with_missing) == 0,
            'week_start': week_start,
            'week_end': week_end,
        }


dashboard = DashboardView.as_view()


@login_required
def student_list(request):
    """Student list view with filtering and pagination"""
    try:
        # Get filter parameters
        classroom_filter = request.GET.get('classroom', '')
        academic_level_filter = request.GET.get('academic_level', '')
        grade_filter = request.GET.get('grade', '')
        search_query = request.GET.get('search', '')
        page = int(request.GET.get('page', 1))
        
        # Convert grade filter to int if provided
        grade = None
        if grade_filter:
            try:
                grade = int(grade_filter)
            except ValueError:
                pass
        
        # Get filtered students using service
        result = StudentService.get_students_with_filters(
            classroom_id=classroom_filter if classroom_filter else None,
            academic_level=academic_level_filter if academic_level_filter else None,
            grade=grade,
            search_query=search_query if search_query else None,
            page=page,
            per_page=20
        )
        
        # Get filter options
        classrooms = StudentService.get_classroom_list()
        academic_levels = StudentService.get_academic_levels()
        
        # Get unique grades
        grades = sorted(set(classroom.grade for classroom in classrooms))
        
        context = {
            'students': result['students'],
            'classrooms': classrooms,
            'academic_levels': academic_levels,
            'grades': grades,
            'current_classroom': classroom_filter,
            'current_academic_level': academic_level_filter,
            'current_grade': grade_filter,
            'search_query': search_query,
            'pagination': result
        }
        
    except Exception as e:
        logger.error(f"Error loading student list: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat memuat data siswa")
        context = {
            'students': [], 
            'classrooms': [], 
            'academic_levels': [], 
            'grades': []
        }
    
    return render(request, 'attendance/student_list.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def take_attendance(request):
    """Take attendance view with bulk processing"""
    try:
        # Get parameters
        date_str = request.GET.get('date', timezone.now().date().strftime('%Y-%m-%d'))
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        classroom_id = request.GET.get('classroom', '')
        
        if request.method == 'POST':
            return _process_attendance_submission(request, target_date)
        
        # GET request - show attendance form
        students = Student.objects.select_related('classroom', 'classroom__academic_level').filter(is_active=True)
        if classroom_id:
            students = students.filter(classroom_id=classroom_id)
        
        students = students.order_by('name')
        
        # Get existing records for the date
        existing_records = {}
        if students:
            records = AttendanceRecord.objects.filter(
                student__in=students,
                date=target_date
            ).select_related('student')
            existing_records = {record.student.id: record for record in records}
        
        # Prepare students with their existing records
        students_with_records = []
        for student in students:
            students_with_records.append({
                'student': student,
                'existing_record': existing_records.get(student.id)
            })
        
        # Get classroom list for filter
        classrooms = StudentService.get_classroom_list()
        
        context = {
            'students_with_records': students_with_records,
            'date': target_date,
            'classrooms': classrooms,
            'current_classroom': classroom_id,
            'status_choices': AttendanceStatus.choices,
        }
        
    except Exception as e:
        logger.error(f"Error loading attendance form: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat memuat form absensi")
        context = {'students_with_records': [], 'classes': []}
    
    return render(request, 'attendance/take_attendance.html', context)


def _process_attendance_submission(request, target_date):
    """Process attendance form submission"""
    try:
        attendance_data = request.POST.getlist('attendance')
        notes_data = request.POST.getlist('notes')
        student_ids = request.POST.getlist('student_ids')
        
        # Prepare data for service
        bulk_data = []
        for i, student_id in enumerate(student_ids):
            status = attendance_data[i] if i < len(attendance_data) else AttendanceStatus.HADIR
            notes = notes_data[i] if i < len(notes_data) else ''
            
            bulk_data.append({
                'student_id': int(student_id),
                'status': status,
                'notes': notes
            })
        
        # Validate data
        validation_errors = AttendanceService.validate_attendance_data(bulk_data)
        if validation_errors:
            for error in validation_errors:
                messages.error(request, error)
            return redirect('take_attendance')
        
        # Process attendance using service
        created, updated = AttendanceService.bulk_create_attendance(
            bulk_data, request.user, target_date
        )
        
        success_msg = f'Absensi berhasil disimpan! {created} data baru, {updated} data diperbarui'
        messages.success(request, success_msg)
        
    except AttendanceServiceError as e:
        logger.error(f"Attendance service error: {str(e)}")
        messages.error(request, f"Kesalahan layanan absensi: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error processing attendance: {str(e)}")
        messages.error(request, "Terjadi kesalahan tidak terduga saat memproses absensi")
    
    return redirect('take_attendance')


@login_required
def attendance_report(request):
    """Attendance report view with filtering"""
    try:
        form = AttendanceFilterForm(request.GET or None)
        
        # Default parameters
        filters = {
            'page': int(request.GET.get('page', 1)),
            'per_page': 50
        }
        
        if form.is_valid():
            if form.cleaned_data['start_date']:
                filters['start_date'] = form.cleaned_data['start_date']
            if form.cleaned_data['end_date']:
                filters['end_date'] = form.cleaned_data['end_date']
            if form.cleaned_data.get('classroom'):
                filters['classroom_id'] = str(form.cleaned_data['classroom'].id)
            if form.cleaned_data['status']:
                filters['status'] = form.cleaned_data['status']
        
        # Generate report using service
        report_data = ReportService.generate_attendance_report(**filters)
        
        context = {
            'form': form,
            'report_data': report_data,
            'records': report_data['records'],
            'summary': report_data['summary'],
            'pagination': report_data['pagination']
        }
        
    except ReportServiceError as e:
        logger.error(f"Report service error: {str(e)}")
        messages.error(request, f"Kesalahan layanan laporan: {str(e)}")
        context = {'form': AttendanceFilterForm(), 'records': []}
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat membuat laporan")
        context = {'form': AttendanceFilterForm(), 'records': []}
    
    return render(request, 'attendance/report.html', context)


@login_required
def student_detail(request, student_id):
    """Student detail view with attendance history"""
    try:
        student = StudentService.get_student_detail(student_id)
        if not student:
            messages.error(request, f"Siswa dengan ID {student_id} tidak ditemukan")
            return redirect('student_list')
        
        # Get attendance summary using service
        summary = AttendanceService.get_student_attendance_summary(student)
        
        # Pagination for records
        from django.core.paginator import Paginator
        paginator = Paginator(summary['recent_records'], 20)
        page_number = request.GET.get('page')
        records = paginator.get_page(page_number)
        
        context = {
            'student': student,
            'summary': summary,
            'records': records,
            'stats': {
                'total': summary['total_records'],
                'hadir': summary['present'],
                'sakit': summary['sick'],
                'izin': summary['permission'],
                'alpa': summary['absent'],
                'percentage': summary['attendance_rate']
            }
        }
        
    except Exception as e:
        logger.error(f"Error loading student detail: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat memuat detail siswa")
        return redirect('student_list')
    
    return render(request, 'attendance/student_detail.html', context)


@login_required
def export_csv(request):
    """Export attendance data to CSV"""
    try:
        # Get filter parameters (same as report)
        form = AttendanceFilterForm(request.GET or None)
        filters = {}
        
        if form.is_valid():
            if form.cleaned_data['start_date']:
                filters['start_date'] = form.cleaned_data['start_date']
            if form.cleaned_data['end_date']:
                filters['end_date'] = form.cleaned_data['end_date']
            if form.cleaned_data.get('classroom'):
                filters['classroom_id'] = str(form.cleaned_data['classroom'].id)
            if form.cleaned_data['status']:
                filters['status'] = form.cleaned_data['status']
        
        # Generate CSV using service
        csv_content = ReportService.export_attendance_to_csv(**filters)
        
        # Create response
        response = HttpResponse(csv_content, content_type='text/csv')
        filename = f"laporan_absensi_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except ReportServiceError as e:
        logger.error(f"CSV export error: {str(e)}")
        messages.error(request, f"Kesalahan ekspor CSV: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during CSV export: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat mengekspor data")
    
    return redirect('attendance_report')


@login_required
def api_attendance_stats(request):
    """API endpoint for attendance statistics (for charts/AJAX)"""
    try:
        # Get attendance trends
        trends = AttendanceService.get_attendance_trends(days=7)
        
        # Get class statistics
        class_stats = AttendanceService.get_class_statistics()
        
        return JsonResponse({
            'success': True,
            'trends': trends,
            'class_stats': class_stats
        })
        
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Terjadi kesalahan saat memuat data statistik'
        }, status=500)


@login_required
def search(request):
    """Simple search view for Unfold compatibility"""
    query = request.GET.get('q', '')
    results = []
    
    if query:
        try:
            # Search students by name or student_id
            students = Student.objects.filter(
                models.Q(name__icontains=query) | 
                models.Q(student_id__icontains=query)
            ).select_related('classroom', 'classroom__academic_level')[:10]
            
            for student in students:
                results.append({
                    'title': student.name,
                    'subtitle': f"{student.student_id} - {student.classroom}",
                    'url': f'/admin/attendance/student/{student.pk}/change/'
                })
                
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
    
    return JsonResponse({
        'results': results,
        'query': query
    })



# ============================================
# JP-Based Attendance Input Views
# ============================================

@login_required
def attendance_input_select(request):
    """
    Attendance input selection view - choose classroom and date.
    This is the first step in the JP-based attendance input flow.
    """
    try:
        # Get all active classrooms
        classrooms = Classroom.objects.filter(
            is_active=True
        ).select_related('academic_level').order_by(
            'academic_level__code', 'grade', 'section'
        )
        
        # Default date is today
        today = timezone.now().date()
        
        context = {
            'classrooms': classrooms,
            'today': today,
        }
        
    except Exception as e:
        logger.error(f"Error loading attendance input select: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat memuat halaman")
        context = {'classrooms': [], 'today': timezone.now().date()}
    
    return render(request, 'attendance/input_select.html', context)


@login_required
def attendance_input_form(request, classroom_id, date_str):
    """
    Attendance input form view with dynamic JP columns.
    Displays students for the selected classroom with JP status cells.
    """
    try:
        # Parse date
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get classroom
        classroom = get_object_or_404(Classroom, id=classroom_id, is_active=True)
        
        # Get current JP from query parameter (default to 1)
        current_jp = int(request.GET.get('jp', 1))
        
        # Get JP count for this day
        jp_count = ScheduleService.get_jp_count_for_date(target_date)
        day_schedule = ScheduleService.get_schedule_for_date(target_date)
        
        # Validate current JP
        if current_jp < 1 or current_jp > jp_count:
            current_jp = 1
        
        # Check if it's a holiday
        is_holiday = HolidayService.is_holiday(target_date, classroom)
        holiday_info = None
        if is_holiday:
            holiday_info = HolidayService.get_holiday_by_date(target_date)
        
        # Get active students in this classroom
        students = Student.objects.filter(
            classroom=classroom,
            is_active=True
        ).order_by('name')
        
        # Get existing attendance records for this date
        existing_records = {}
        daily_attendances = DailyAttendance.objects.filter(
            student__classroom=classroom,
            date=target_date
        ).select_related('student')
        
        for attendance in daily_attendances:
            existing_records[str(attendance.student.id)] = attendance.jp_statuses
        
        # Get all classrooms for filter dropdown
        classrooms = Classroom.objects.filter(is_active=True).order_by('name')
        
        # Prepare students with their existing records for current JP
        students_data = []
        for student in students:
            student_id_str = str(student.id)
            existing_statuses = existing_records.get(student_id_str, {})
            
            # Get status for current JP (default to 'H' if no existing record)
            current_jp_key = str(current_jp)
            current_status = existing_statuses.get(current_jp_key, 'H')
            
            # Build JP statuses list for current JP only
            jp_statuses = [{
                'jp_num': current_jp,
                'status': current_status
            }]
            
            students_data.append({
                'student': student,
                'jp_statuses': jp_statuses,
                'has_existing': student_id_str in existing_records
            })
        
        # Generate JP range for template
        jp_range = list(range(1, jp_count + 1))
        
        context = {
            'classroom': classroom,
            'classrooms': classrooms,
            'date': target_date,
            'date_str': date_str,
            'current_jp': current_jp,
            'jp_count': jp_count,
            'jp_range': jp_range,
            'day_schedule': day_schedule,
            'is_holiday': is_holiday,
            'holiday_info': holiday_info,
            'students_data': students_data,
            'total_students': len(students_data),
        }
        
    except ValueError:
        messages.error(request, "Format tanggal tidak valid")
        return redirect('attendance_input')
    except Exception as e:
        logger.error(f"Error loading attendance input form: {str(e)}")
        messages.error(request, f"Terjadi kesalahan saat memuat form absensi: {str(e)}")
        return redirect('attendance_input')
    
    # Use new template
    return render(request, 'attendance/input_form_new.html', context)


@login_required
@require_http_methods(["POST"])
def api_save_attendance(request):
    """
    AJAX endpoint for saving JP-based attendance data.
    Expects JSON payload with classroom_id, date, and attendance data.
    """
    try:
        # Parse JSON body
        data = json.loads(request.body)
        
        classroom_id = data.get('classroom_id')
        date_str = data.get('date')
        attendance_data = data.get('attendance', [])
        
        # Validate required fields
        if not classroom_id:
            return JsonResponse({
                'success': False,
                'error': 'classroom_id is required'
            }, status=400)
        
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
        
        # Get classroom
        try:
            classroom = Classroom.objects.get(id=classroom_id, is_active=True)
        except Classroom.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Classroom not found'
            }, status=404)
        
        # Validate and save attendance using service
        created_count, updated_count = AttendanceService.save_bulk_attendance(
            classroom=classroom,
            target_date=target_date,
            attendance_data=attendance_data,
            user=request.user
        )
        
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
        logger.error(f"Unexpected error saving attendance: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Terjadi kesalahan tidak terduga'
        }, status=500)


# ============================================
# Management CRUD Views
# ============================================

from django.core.paginator import Paginator
from django.db import transaction
from django.contrib.auth.models import User
from .forms import (
    StudentForm, StudentFilterForm, ClassroomForm, 
    HolidayForm, DayScheduleForm, UserForm
)


# Note: admin_required decorator is now imported from .decorators module


# ============================================
# Student Management Views
# Read: All authenticated users (Guru + Admin)
# Write: Admin only
# ============================================

@login_required
def manage_student_list(request):
    """Student list view with filtering, search, and pagination (All users)"""
    try:
        # Get filter parameters
        filter_form = StudentFilterForm(request.GET)
        
        # Base queryset
        students = Student.objects.select_related(
            'classroom', 'classroom__academic_level'
        ).order_by('name')
        
        # Apply filters
        if filter_form.is_valid():
            search = filter_form.cleaned_data.get('search')
            classroom = filter_form.cleaned_data.get('classroom')
            status = filter_form.cleaned_data.get('status')
            
            if search:
                students = students.filter(
                    models.Q(name__icontains=search) |
                    models.Q(student_id__icontains=search) |
                    models.Q(nisn__icontains=search)
                )
            
            if classroom:
                students = students.filter(classroom=classroom)
            
            if status == 'active':
                students = students.filter(is_active=True)
            elif status == 'inactive':
                students = students.filter(is_active=False)
        
        # Pagination
        paginator = Paginator(students, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Stats
        total_students = Student.objects.count()
        active_students = Student.objects.filter(is_active=True).count()
        inactive_students = total_students - active_students
        
        context = {
            'students': page_obj,
            'filter_form': filter_form,
            'total_students': total_students,
            'active_students': active_students,
            'inactive_students': inactive_students,
        }
        
    except Exception as e:
        logger.error(f"Error loading student list: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat memuat data siswa")
        context = {'students': [], 'filter_form': StudentFilterForm()}
    
    return render(request, 'manage/students/list.html', context)


@login_required
@admin_required
def manage_student_create(request):
    """Create new student (Admin only)"""
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            try:
                student = form.save(commit=False)
                student.created_by = request.user
                student.save()
                messages.success(request, f'Siswa "{student.name}" berhasil ditambahkan')
                return redirect('manage_student_list')
            except Exception as e:
                logger.error(f"Error creating student: {str(e)}")
                messages.error(request, f"Gagal menambahkan siswa: {str(e)}")
    else:
        form = StudentForm()
    
    return render(request, 'manage/students/form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
@admin_required
def manage_student_edit(request, pk):
    """Edit existing student (Admin only)"""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            try:
                student = form.save(commit=False)
                student.updated_by = request.user
                student.save()
                messages.success(request, f'Siswa "{student.name}" berhasil diperbarui')
                return redirect('manage_student_list')
            except Exception as e:
                logger.error(f"Error updating student: {str(e)}")
                messages.error(request, f"Gagal memperbarui siswa: {str(e)}")
    else:
        form = StudentForm(instance=student)
    
    return render(request, 'manage/students/form.html', {
        'form': form,
        'student': student,
        'is_edit': True,
    })


@login_required
@admin_required
@require_http_methods(["POST"])
def manage_student_delete(request, pk):
    """Delete student (Admin only)"""
    student = get_object_or_404(Student, pk=pk)
    
    try:
        name = student.name
        student.delete()
        messages.success(request, f'Siswa "{name}" berhasil dihapus')
    except Exception as e:
        logger.error(f"Error deleting student: {str(e)}")
        messages.error(request, f"Gagal menghapus siswa: {str(e)}")
    
    return redirect('manage_student_list')


@login_required
@admin_required
@require_http_methods(["POST"])
def api_student_inline_edit(request):
    """AJAX endpoint for inline editing student fields (Admin only)"""
    try:
        data = json.loads(request.body)
        student_id = data.get('id')
        field = data.get('field')
        value = data.get('value')
        
        if not all([student_id, field]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
        
        # Allowed fields for inline edit
        allowed_fields = ['name', 'student_id', 'nisn', 'is_active']
        if field not in allowed_fields:
            return JsonResponse({'success': False, 'error': 'Field not allowed for inline edit'}, status=400)
        
        student = Student.objects.get(pk=student_id)
        
        # Handle boolean fields
        if field == 'is_active':
            value = value in ['true', 'True', True, 1, '1']
        
        setattr(student, field, value)
        student.updated_by = request.user
        student.save()
        
        return JsonResponse({
            'success': True,
            'value': getattr(student, field),
            'message': 'Data berhasil diperbarui'
        })
        
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Siswa tidak ditemukan'}, status=404)
    except Exception as e:
        logger.error(f"Error in inline edit: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@admin_required
@require_http_methods(["POST"])
def api_inline_edit(request):
    """
    Generic AJAX endpoint for inline editing fields across multiple models.
    
    Accepts JSON payload:
    {
        "model_type": "student|classroom|holiday|user",
        "id": "<object_id>",
        "field": "<field_name>",
        "value": "<new_value>"
    }
    
    Returns JSON:
    {
        "success": true|false,
        "value": "<updated_value>",
        "message": "<success_message>",
        "error": "<error_message>"  // only on failure
    }
    
    Requirements: 7.7
    """
    try:
        data = json.loads(request.body)
        model_type = data.get('model_type')
        object_id = data.get('id')
        field = data.get('field')
        value = data.get('value')
        
        # Validate required fields
        if not all([model_type, object_id, field]):
            return JsonResponse({
                'success': False, 
                'error': 'Parameter tidak lengkap. Diperlukan: model_type, id, field'
            }, status=400)
        
        # Define allowed fields per model type for security
        allowed_fields = {
            'student': ['name', 'student_id', 'nisn', 'is_active', 'parent_phone', 'address'],
            'classroom': ['name', 'room_number', 'capacity', 'is_active'],
            'holiday': ['name', 'description', 'holiday_type'],
            'user': ['first_name', 'last_name', 'email', 'is_active'],
        }
        
        # Map model types to model classes
        model_map = {
            'student': Student,
            'classroom': Classroom,
            'holiday': Holiday,
            'user': User,
        }
        
        # Validate model type
        if model_type not in model_map:
            return JsonResponse({
                'success': False, 
                'error': f'Tipe model tidak valid: {model_type}'
            }, status=400)
        
        # Validate field is allowed for this model
        if field not in allowed_fields.get(model_type, []):
            return JsonResponse({
                'success': False, 
                'error': f'Field "{field}" tidak diizinkan untuk inline edit pada {model_type}'
            }, status=400)
        
        # Get the model class and object
        model_class = model_map[model_type]
        
        try:
            obj = model_class.objects.get(pk=object_id)
        except model_class.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'error': f'{model_type.capitalize()} tidak ditemukan'
            }, status=404)
        
        # Handle boolean fields
        boolean_fields = ['is_active']
        if field in boolean_fields:
            value = value in ['true', 'True', True, 1, '1']
        
        # Handle integer fields
        integer_fields = ['capacity']
        if field in integer_fields:
            try:
                value = int(value)
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False, 
                    'error': f'Nilai untuk {field} harus berupa angka'
                }, status=400)
        
        # Validate value is not empty for required fields
        required_fields = ['name', 'student_id']
        if field in required_fields and not value:
            return JsonResponse({
                'success': False, 
                'error': f'Field {field} tidak boleh kosong'
            }, status=400)
        
        # Set the new value
        old_value = getattr(obj, field)
        setattr(obj, field, value)
        
        # Update audit fields if available
        if hasattr(obj, 'updated_by'):
            obj.updated_by = request.user
        
        # Save the object
        try:
            obj.save()
        except ValidationError as e:
            return JsonResponse({
                'success': False, 
                'error': str(e.message_dict if hasattr(e, 'message_dict') else e)
            }, status=400)
        
        # Get the updated value (may be transformed by model)
        updated_value = getattr(obj, field)
        
        # Format display value for boolean fields
        display_value = updated_value
        if field in boolean_fields:
            display_value = 'Aktif' if updated_value else 'Nonaktif'
        
        logger.info(f"Inline edit: {model_type}.{field} changed from '{old_value}' to '{updated_value}' by {request.user}")
        
        return JsonResponse({
            'success': True,
            'value': updated_value,
            'display_value': display_value,
            'message': 'Data berhasil diperbarui'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'error': 'Format JSON tidak valid'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in generic inline edit: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': f'Terjadi kesalahan: {str(e)}'
        }, status=500)


# ============================================
# Classroom Management Views
# Read: All authenticated users (Guru + Admin)
# Write: Admin only
# ============================================

@login_required
def manage_classroom_list(request):
    """Classroom list view (All users)"""
    try:
        classrooms = Classroom.objects.select_related(
            'academic_level', 'homeroom_teacher'
        ).annotate(
            student_count_val=models.Count('students', filter=models.Q(students__is_active=True))
        ).order_by('academic_level__code', 'grade', 'section')
        
        # Pagination
        paginator = Paginator(classrooms, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Stats
        total_classrooms = Classroom.objects.count()
        active_classrooms = Classroom.objects.filter(is_active=True).count()
        
        context = {
            'classrooms': page_obj,
            'total_classrooms': total_classrooms,
            'active_classrooms': active_classrooms,
        }
        
    except Exception as e:
        logger.error(f"Error loading classroom list: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat memuat data kelas")
        context = {'classrooms': []}
    
    return render(request, 'manage/classrooms/list.html', context)


@login_required
@admin_required
def manage_classroom_create(request):
    """Create new classroom (Admin only)"""
    if request.method == 'POST':
        form = ClassroomForm(request.POST)
        if form.is_valid():
            try:
                classroom = form.save(commit=False)
                classroom.created_by = request.user
                classroom.save()
                messages.success(request, f'Kelas "{classroom}" berhasil ditambahkan')
                return redirect('manage_classroom_list')
            except Exception as e:
                logger.error(f"Error creating classroom: {str(e)}")
                messages.error(request, f"Gagal menambahkan kelas: {str(e)}")
    else:
        form = ClassroomForm()
    
    return render(request, 'manage/classrooms/form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
@admin_required
def manage_classroom_edit(request, pk):
    """Edit existing classroom (Admin only)"""
    classroom = get_object_or_404(Classroom, pk=pk)
    
    if request.method == 'POST':
        form = ClassroomForm(request.POST, instance=classroom)
        if form.is_valid():
            try:
                classroom = form.save(commit=False)
                classroom.updated_by = request.user
                classroom.save()
                messages.success(request, f'Kelas "{classroom}" berhasil diperbarui')
                return redirect('manage_classroom_list')
            except Exception as e:
                logger.error(f"Error updating classroom: {str(e)}")
                messages.error(request, f"Gagal memperbarui kelas: {str(e)}")
    else:
        form = ClassroomForm(instance=classroom)
    
    return render(request, 'manage/classrooms/form.html', {
        'form': form,
        'classroom': classroom,
        'is_edit': True,
    })


@login_required
@admin_required
@require_http_methods(["POST"])
def manage_classroom_delete(request, pk):
    """Delete classroom (Admin only)"""
    classroom = get_object_or_404(Classroom, pk=pk)
    
    try:
        name = str(classroom)
        classroom.delete()
        messages.success(request, f'Kelas "{name}" berhasil dihapus')
    except Exception as e:
        logger.error(f"Error deleting classroom: {str(e)}")
        messages.error(request, f"Gagal menghapus kelas: {str(e)}")
    
    return redirect('manage_classroom_list')


# ============================================
# Holiday Management Views
# Read: All authenticated users (Guru + Admin)
# Write: Admin only
# ============================================

@login_required
def manage_holiday_list(request):
    """Holiday list view (All users)"""
    try:
        holidays = Holiday.objects.prefetch_related('classrooms').order_by('-date')
        
        # Pagination
        paginator = Paginator(holidays, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Stats
        total_holidays = Holiday.objects.count()
        upcoming_holidays = Holiday.objects.filter(date__gte=timezone.now().date()).count()
        
        context = {
            'holidays': page_obj,
            'total_holidays': total_holidays,
            'upcoming_holidays': upcoming_holidays,
        }
        
    except Exception as e:
        logger.error(f"Error loading holiday list: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat memuat data hari libur")
        context = {'holidays': []}
    
    return render(request, 'manage/holidays/list.html', context)


@login_required
@admin_required
def manage_holiday_create(request):
    """Create new holiday (Admin only)"""
    if request.method == 'POST':
        form = HolidayForm(request.POST)
        if form.is_valid():
            try:
                holiday = form.save(commit=False)
                holiday.created_by = request.user
                holiday.save()
                form.save_m2m()  # Save M2M relationships
                messages.success(request, f'Hari libur "{holiday.name}" berhasil ditambahkan')
                return redirect('manage_holiday_list')
            except Exception as e:
                logger.error(f"Error creating holiday: {str(e)}")
                messages.error(request, f"Gagal menambahkan hari libur: {str(e)}")
    else:
        form = HolidayForm()
    
    return render(request, 'manage/holidays/form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
@admin_required
def manage_holiday_edit(request, pk):
    """Edit existing holiday (Admin only)"""
    holiday = get_object_or_404(Holiday, pk=pk)
    
    if request.method == 'POST':
        form = HolidayForm(request.POST, instance=holiday)
        if form.is_valid():
            try:
                holiday = form.save(commit=False)
                holiday.updated_by = request.user
                holiday.save()
                form.save_m2m()
                messages.success(request, f'Hari libur "{holiday.name}" berhasil diperbarui')
                return redirect('manage_holiday_list')
            except Exception as e:
                logger.error(f"Error updating holiday: {str(e)}")
                messages.error(request, f"Gagal memperbarui hari libur: {str(e)}")
    else:
        form = HolidayForm(instance=holiday)
    
    return render(request, 'manage/holidays/form.html', {
        'form': form,
        'holiday': holiday,
        'is_edit': True,
    })


@login_required
@admin_required
@require_http_methods(["POST"])
def manage_holiday_delete(request, pk):
    """Delete holiday (Admin only)"""
    holiday = get_object_or_404(Holiday, pk=pk)
    
    try:
        name = holiday.name
        holiday.delete()
        messages.success(request, f'Hari libur "{name}" berhasil dihapus')
    except Exception as e:
        logger.error(f"Error deleting holiday: {str(e)}")
        messages.error(request, f"Gagal menghapus hari libur: {str(e)}")
    
    return redirect('manage_holiday_list')


# ============================================
# Day Schedule Settings View (Admin Only)
# ============================================

@login_required
@admin_required
def manage_day_schedule(request):
    """Day schedule settings page (Admin only)"""
    try:
        schedules = DaySchedule.objects.all().order_by('day_of_week')
        
        if request.method == 'POST':
            # Process form data for each day
            with transaction.atomic():
                for schedule in schedules:
                    jp_count = request.POST.get(f'jp_count_{schedule.day_of_week}')
                    is_school_day = request.POST.get(f'is_school_day_{schedule.day_of_week}') == 'on'
                    
                    if jp_count:
                        try:
                            jp_count = int(jp_count)
                            if 1 <= jp_count <= 10:
                                schedule.default_jp_count = jp_count
                                schedule.is_school_day = is_school_day
                                schedule.updated_by = request.user
                                schedule.save()
                        except ValueError:
                            pass
                
                messages.success(request, 'Jadwal JP berhasil diperbarui')
                return redirect('manage_day_schedule')
        
        context = {
            'schedules': schedules,
        }
        
    except Exception as e:
        logger.error(f"Error loading day schedule: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat memuat jadwal JP")
        context = {'schedules': []}
    
    return render(request, 'manage/settings/day_schedule.html', context)


# ============================================
# User Management Views (Admin Only)
# ============================================

@login_required
@admin_required
def manage_user_list(request):
    """User list view (Admin only)"""
    try:
        users = User.objects.all().order_by('username')
        
        # Pagination
        paginator = Paginator(users, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Stats
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        admin_users = User.objects.filter(is_superuser=True).count()
        
        context = {
            'users': page_obj,
            'total_users': total_users,
            'active_users': active_users,
            'admin_users': admin_users,
        }
        
    except Exception as e:
        logger.error(f"Error loading user list: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat memuat data pengguna")
        context = {'users': []}
    
    return render(request, 'manage/users/list.html', context)


@login_required
@admin_required
def manage_user_create(request):
    """Create new user (Admin only)"""
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(request, f'Pengguna "{user.username}" berhasil ditambahkan')
                return redirect('manage_user_list')
            except Exception as e:
                logger.error(f"Error creating user: {str(e)}")
                messages.error(request, f"Gagal menambahkan pengguna: {str(e)}")
    else:
        form = UserForm()
    
    return render(request, 'manage/users/form.html', {
        'form': form,
        'is_edit': False,
    })


@login_required
@admin_required
def manage_user_edit(request, pk):
    """Edit existing user (Admin only)"""
    user_obj = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user_obj)
        if form.is_valid():
            try:
                user_obj = form.save()
                messages.success(request, f'Pengguna "{user_obj.username}" berhasil diperbarui')
                return redirect('manage_user_list')
            except Exception as e:
                logger.error(f"Error updating user: {str(e)}")
                messages.error(request, f"Gagal memperbarui pengguna: {str(e)}")
    else:
        form = UserForm(instance=user_obj)
    
    return render(request, 'manage/users/form.html', {
        'form': form,
        'user_obj': user_obj,
        'is_edit': True,
    })


@login_required
@admin_required
@require_http_methods(["POST"])
def manage_user_delete(request, pk):
    """Delete user (Admin only)"""
    user_obj = get_object_or_404(User, pk=pk)
    
    # Prevent self-deletion
    if user_obj == request.user:
        messages.error(request, "Anda tidak dapat menghapus akun Anda sendiri")
        return redirect('manage_user_list')
    
    try:
        username = user_obj.username
        user_obj.delete()
        messages.success(request, f'Pengguna "{username}" berhasil dihapus')
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        messages.error(request, f"Gagal menghapus pengguna: {str(e)}")
    
    return redirect('manage_user_list')


# ============================================
# Bulk Actions (Admin Only)
# ============================================

@login_required
@admin_required
@require_http_methods(["POST"])
def bulk_action(request):
    """Handle bulk actions for management pages (Admin only)"""
    try:
        action = request.POST.get('action')
        model_type = request.POST.get('model_type')
        selected_ids = request.POST.getlist('selected_ids')
        
        if not action or not model_type or not selected_ids:
            messages.error(request, 'Parameter tidak lengkap')
            return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
        
        # Map model types to models
        model_map = {
            'student': Student,
            'classroom': Classroom,
            'holiday': Holiday,
        }
        
        model_class = model_map.get(model_type)
        if not model_class:
            messages.error(request, 'Tipe model tidak valid')
            return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
        
        # Perform action within transaction
        with transaction.atomic():
            queryset = model_class.objects.filter(pk__in=selected_ids)
            count = queryset.count()
            
            if action == 'delete':
                queryset.delete()
                messages.success(request, f'{count} item berhasil dihapus')
            
            elif action == 'activate':
                queryset.update(is_active=True, updated_by=request.user)
                messages.success(request, f'{count} item berhasil diaktifkan')
            
            elif action == 'deactivate':
                queryset.update(is_active=False, updated_by=request.user)
                messages.success(request, f'{count} item berhasil dinonaktifkan')
            
            else:
                messages.error(request, 'Aksi tidak valid')
        
    except Exception as e:
        logger.error(f"Error in bulk action: {str(e)}")
        messages.error(request, f"Gagal melakukan aksi: {str(e)}")
    
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


# ============================================
# JP-Based Report Views
# ============================================

from .forms import JPReportFilterForm


@login_required
def jp_report(request):
    """
    JP-based attendance report view with date range filter and export options.
    Supports both class-level and student-level reports.
    
    Requirements: 5.1, 6.1
    """
    try:
        form = JPReportFilterForm(request.GET or None)
        report_data = None
        report_type = request.GET.get('report_type', 'class')
        
        # Get all classrooms and students for the form
        classrooms = Classroom.objects.filter(
            is_active=True
        ).select_related('academic_level').order_by(
            'academic_level__code', 'grade', 'section'
        )
        
        students = Student.objects.filter(
            is_active=True
        ).select_related('classroom', 'classroom__academic_level').order_by('name')
        
        # Process form if submitted with valid data
        if request.GET and form.is_valid():
            report_type = form.cleaned_data['report_type']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            
            if report_type == 'class':
                classroom = form.cleaned_data['classroom']
                if classroom:
                    report_data = ReportService.generate_class_report(
                        classroom=classroom,
                        start_date=start_date,
                        end_date=end_date
                    )
            else:  # student report
                student = form.cleaned_data['student']
                if student:
                    report_data = ReportService.generate_student_report(
                        student=student,
                        start_date=start_date,
                        end_date=end_date
                    )
        
        context = {
            'form': form,
            'report_data': report_data,
            'report_type': report_type,
            'classrooms': classrooms,
            'students': students,
        }
        
    except ReportServiceError as e:
        logger.error(f"Report service error: {str(e)}")
        messages.error(request, f"Kesalahan layanan laporan: {str(e)}")
        context = {
            'form': JPReportFilterForm(),
            'report_data': None,
            'report_type': 'class',
            'classrooms': [],
            'students': [],
        }
    except Exception as e:
        logger.error(f"Error generating JP report: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat membuat laporan")
        context = {
            'form': JPReportFilterForm(),
            'report_data': None,
            'report_type': 'class',
            'classrooms': [],
            'students': [],
        }
    
    return render(request, 'attendance/jp_report.html', context)


@login_required
def export_jp_csv(request):
    """
    Export JP-based attendance data to CSV format.
    
    Requirements: 6.6
    """
    try:
        # Get parameters
        classroom_id = request.GET.get('classroom')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if not all([classroom_id, start_date_str, end_date_str]):
            messages.error(request, 'Parameter tidak lengkap')
            return redirect('jp_report')
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Format tanggal tidak valid')
            return redirect('jp_report')
        
        # Get classroom
        try:
            classroom = Classroom.objects.get(id=classroom_id, is_active=True)
        except Classroom.DoesNotExist:
            messages.error(request, 'Kelas tidak ditemukan')
            return redirect('jp_report')
        
        # Generate CSV
        csv_content = ReportService.export_jp_attendance_to_csv(
            classroom=classroom,
            start_date=start_date,
            end_date=end_date
        )
        
        # Create response
        response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
        filename = f"laporan_absensi_jp_{classroom}_{start_date_str}_{end_date_str}.csv"
        # Sanitize filename
        filename = filename.replace(' ', '_').replace('/', '-')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting JP CSV: {str(e)}")
        messages.error(request, f"Gagal mengekspor data: {str(e)}")
        return redirect('jp_report')


@login_required
def api_get_students_by_classroom(request):
    """
    AJAX endpoint to get students filtered by classroom.
    Used for dynamic student dropdown in report form.
    """
    try:
        classroom_id = request.GET.get('classroom_id')
        
        if not classroom_id:
            return JsonResponse({'students': []})
        
        students = Student.objects.filter(
            classroom_id=classroom_id,
            is_active=True
        ).order_by('name').values('id', 'name', 'student_id')
        
        return JsonResponse({
            'students': list(students)
        })
        
    except Exception as e:
        logger.error(f"Error getting students by classroom: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


# ============================================
# PDF Export Views
# ============================================

@login_required
def export_pdf_class(request):
    """
    Export class attendance report as PDF.
    
    Query Parameters:
        - classroom: UUID of the classroom
        - start_date: Start date (YYYY-MM-DD)
        - end_date: End date (YYYY-MM-DD)
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.7
    """
    try:
        # Get parameters
        classroom_id = request.GET.get('classroom')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if not all([classroom_id, start_date_str, end_date_str]):
            messages.error(request, 'Parameter tidak lengkap')
            return redirect('jp_report')
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Format tanggal tidak valid')
            return redirect('jp_report')
        
        # Get classroom
        try:
            classroom = Classroom.objects.get(id=classroom_id, is_active=True)
        except Classroom.DoesNotExist:
            messages.error(request, 'Kelas tidak ditemukan')
            return redirect('jp_report')
        
        # Generate PDF
        pdf_content = PDFService.export_pdf_class(
            classroom=classroom,
            start_date=start_date,
            end_date=end_date
        )
        
        # Create response
        response = HttpResponse(pdf_content, content_type='application/pdf')
        filename = f"laporan_absensi_{classroom}_{start_date_str}_{end_date_str}.pdf"
        # Sanitize filename
        filename = filename.replace(' ', '_').replace('/', '-')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting class PDF: {str(e)}")
        messages.error(request, f"Gagal mengekspor PDF: {str(e)}")
        return redirect('jp_report')


@login_required
def export_pdf_student(request):
    """
    Export student attendance report as PDF.
    
    Query Parameters:
        - student: UUID of the student
        - start_date: Start date (YYYY-MM-DD)
        - end_date: End date (YYYY-MM-DD)
    
    Requirements: 5.1, 5.5, 5.6, 5.7
    """
    try:
        # Get parameters
        student_id = request.GET.get('student')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if not all([student_id, start_date_str, end_date_str]):
            messages.error(request, 'Parameter tidak lengkap')
            return redirect('jp_report')
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Format tanggal tidak valid')
            return redirect('jp_report')
        
        # Get student
        try:
            student = Student.objects.select_related('classroom').get(id=student_id)
        except Student.DoesNotExist:
            messages.error(request, 'Siswa tidak ditemukan')
            return redirect('jp_report')
        
        # Generate PDF
        pdf_content = PDFService.export_pdf_student(
            student=student,
            start_date=start_date,
            end_date=end_date
        )
        
        # Create response
        response = HttpResponse(pdf_content, content_type='application/pdf')
        # Sanitize student name for filename
        safe_name = student.name.replace(' ', '_').replace('/', '-')[:30]
        filename = f"laporan_absensi_{safe_name}_{start_date_str}_{end_date_str}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting student PDF: {str(e)}")
        messages.error(request, f"Gagal mengekspor PDF: {str(e)}")
        return redirect('jp_report')


# ============================================
# Excel Export Views
# ============================================

@login_required
def export_excel_class(request):
    """
    Export class attendance report as Excel with advanced features.
    
    Query Parameters:
        - classroom: UUID of the classroom (can be multiple, comma-separated)
        - start_date: Start date (YYYY-MM-DD)
        - end_date: End date (YYYY-MM-DD)
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    """
    try:
        # Get parameters
        classroom_ids = request.GET.get('classroom', '')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if not all([classroom_ids, start_date_str, end_date_str]):
            messages.error(request, 'Parameter tidak lengkap')
            return redirect('jp_report')
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Format tanggal tidak valid')
            return redirect('jp_report')
        
        # Get classrooms (support multiple classrooms separated by comma)
        classroom_id_list = [cid.strip() for cid in classroom_ids.split(',') if cid.strip()]
        classrooms = []
        
        for classroom_id in classroom_id_list:
            try:
                classroom = Classroom.objects.get(id=classroom_id, is_active=True)
                classrooms.append(classroom)
            except Classroom.DoesNotExist:
                continue
        
        if not classrooms:
            messages.error(request, 'Kelas tidak ditemukan')
            return redirect('jp_report')
        
        # Generate Excel
        excel_content = ReportService.export_jp_attendance_to_excel(
            classrooms=classrooms,
            start_date=start_date,
            end_date=end_date
        )
        
        # Create response
        response = HttpResponse(
            excel_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Generate filename
        if len(classrooms) == 1:
            filename = f"laporan_absensi_{classrooms[0]}_{start_date_str}_{end_date_str}.xlsx"
        else:
            filename = f"laporan_absensi_multi_kelas_{start_date_str}_{end_date_str}.xlsx"
        
        # Sanitize filename
        filename = filename.replace(' ', '_').replace('/', '-')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting Excel: {str(e)}")
        messages.error(request, f"Gagal mengekspor Excel: {str(e)}")
        return redirect('jp_report')


@login_required
def export_excel_all(request):
    """
    Export attendance report for all active classrooms as Excel.
    Creates one sheet per classroom.
    
    Query Parameters:
        - start_date: Start date (YYYY-MM-DD)
        - end_date: End date (YYYY-MM-DD)
    
    Requirements: 6.1, 6.2
    """
    try:
        # Get parameters
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if not all([start_date_str, end_date_str]):
            messages.error(request, 'Parameter tidak lengkap')
            return redirect('jp_report')
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Format tanggal tidak valid')
            return redirect('jp_report')
        
        # Get all active classrooms
        classrooms = list(Classroom.objects.filter(
            is_active=True
        ).select_related('academic_level').order_by(
            'academic_level__code', 'grade', 'section'
        ))
        
        if not classrooms:
            messages.error(request, 'Tidak ada kelas aktif')
            return redirect('jp_report')
        
        # Generate Excel
        excel_content = ReportService.export_jp_attendance_to_excel(
            classrooms=classrooms,
            start_date=start_date,
            end_date=end_date
        )
        
        # Create response
        response = HttpResponse(
            excel_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        filename = f"laporan_absensi_semua_kelas_{start_date_str}_{end_date_str}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting Excel (all classes): {str(e)}")
        messages.error(request, f"Gagal mengekspor Excel: {str(e)}")
        return redirect('jp_report')


# ============================================
# Dashboard API Endpoints
# ============================================

@login_required
def api_student_search(request):
    """
    API endpoint for student search functionality in dashboard.
    
    Query Parameters:
        - q: Search query (name or student ID)
    
    Returns:
        JSON response with matching students
    """
    try:
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return JsonResponse({'students': []})
        
        # Search students by name or student ID
        students = Student.objects.filter(
            models.Q(name__icontains=query) | 
            models.Q(student_id__icontains=query),
            is_active=True
        ).select_related('classroom', 'classroom__academic_level').order_by('name')[:10]
        
        student_data = []
        for student in students:
            student_data.append({
                'id': str(student.id),
                'name': student.name,
                'student_id': student.student_id or '',
                'classroom_name': str(student.classroom) if student.classroom else 'Tidak ada kelas'
            })
        
        return JsonResponse({'students': student_data})
        
    except Exception as e:
        logger.error(f"Error in student search API: {str(e)}")
        return JsonResponse({'error': 'Terjadi kesalahan saat mencari siswa'}, status=500)


@login_required
def api_student_stats(request, student_id):
    """
    API endpoint for individual student attendance statistics.
    
    Path Parameters:
        - student_id: UUID of the student
    
    Query Parameters:
        - start_date: Start date (YYYY-MM-DD) - optional
        - end_date: End date (YYYY-MM-DD) - optional
    
    Returns:
        JSON response with student attendance statistics
    """
    try:
        # Get student
        try:
            student = Student.objects.select_related('classroom').get(id=student_id, is_active=True)
        except Student.DoesNotExist:
            return JsonResponse({'error': 'Siswa tidak ditemukan'}, status=404)
        
        # Get date range
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'error': 'Format start_date tidak valid'}, status=400)
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'error': 'Format end_date tidak valid'}, status=400)
        
        # Default to last 30 days if no dates provided
        if not start_date and not end_date:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        elif not start_date:
            start_date = end_date - timedelta(days=30)
        elif not end_date:
            end_date = timezone.now().date()
        
        # Get attendance records for the student in the date range
        records = AttendanceRecord.objects.filter(
            student=student,
            date__gte=start_date,
            date__lte=end_date
        )
        
        # Calculate statistics
        total_records = records.count()
        
        if total_records == 0:
            return JsonResponse({
                'hadir_count': 0,
                'sakit_count': 0,
                'izin_count': 0,
                'alpa_count': 0,
                'hadir_percentage': 0,
                'sakit_percentage': 0,
                'izin_percentage': 0,
                'alpa_percentage': 0,
                'attendance_index': 0,
                'total_records': 0,
                'date_range': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            })
        
        hadir_count = records.filter(status=AttendanceStatus.HADIR).count()
        sakit_count = records.filter(status=AttendanceStatus.SAKIT).count()
        izin_count = records.filter(status=AttendanceStatus.IZIN).count()
        alpa_count = records.filter(status=AttendanceStatus.ALPA).count()
        
        # Calculate percentages
        hadir_percentage = round((hadir_count / total_records) * 100, 1)
        sakit_percentage = round((sakit_count / total_records) * 100, 1)
        izin_percentage = round((izin_count / total_records) * 100, 1)
        alpa_percentage = round((alpa_count / total_records) * 100, 1)
        
        # Calculate attendance index (Hadir + Sakit + Izin = acceptable attendance)
        acceptable_count = hadir_count + sakit_count + izin_count
        attendance_index = round((acceptable_count / total_records) * 100, 1)
        
        return JsonResponse({
            'hadir_count': hadir_count,
            'sakit_count': sakit_count,
            'izin_count': izin_count,
            'alpa_count': alpa_count,
            'hadir_percentage': hadir_percentage,
            'sakit_percentage': sakit_percentage,
            'izin_percentage': izin_percentage,
            'alpa_percentage': alpa_percentage,
            'attendance_index': attendance_index,
            'total_records': total_records,
            'date_range': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in student stats API: {str(e)}")
        return JsonResponse({'error': 'Terjadi kesalahan saat memuat statistik siswa'}, status=500)