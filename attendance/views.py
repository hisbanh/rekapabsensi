"""
Views for the attendance application
Following enterprise architecture patterns with service layer separation
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

from .models import Student, AttendanceRecord, AttendanceStatus
from .forms import AttendanceFilterForm
from .services.attendance_service import AttendanceService
from .services.student_service import StudentService
from .services.report_service import ReportService
from .exceptions import AttendanceServiceError, StudentServiceError, ReportServiceError

logger = logging.getLogger(__name__)


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard view with comprehensive statistics"""
    template_name = 'attendance/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            # Get today's statistics
            today_stats = AttendanceService.get_attendance_statistics()
            
            # Get classroom statistics
            classroom_stats = AttendanceService.get_classroom_statistics()
            
            # Get recent attendance records
            recent_attendance = AttendanceRecord.objects.select_related(
                'student', 'student__classroom', 'student__classroom__academic_level'
            ).order_by('-created_at')[:10]
            
            # Get attendance trends
            trends = AttendanceService.get_attendance_trends(days=7)
            
            context.update({
                'today_stats': today_stats,
                'classroom_stats': classroom_stats,
                'recent_attendance': recent_attendance,
                'trends': trends,
                'today': timezone.now().date(),
            })
            
        except Exception as e:
            logger.error(f"Error loading dashboard data: {str(e)}")
            messages.error(self.request, "Terjadi kesalahan saat memuat data dashboard")
            
        return context


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
            if form.cleaned_data['class_name']:
                filters['class_name'] = form.cleaned_data['class_name']
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
            if form.cleaned_data['class_name']:
                filters['class_name'] = form.cleaned_data['class_name']
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