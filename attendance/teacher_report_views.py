"""
Teacher Report Views
Handles all views related to teacher attendance reporting, analytics, and exports

Authorization:
- Admin: Full access to all reporting features
- Teachers: Can view and export own reports only

Requirements: FR-023 to FR-027
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib import messages
from datetime import datetime, timedelta, date
import logging

from .models import Teacher
from .services.teacher_report_service import (
    TeacherReportService,
    TeacherReportServiceError
)
from .decorators import admin_required

logger = logging.getLogger(__name__)


# ============================================
# Teacher Report Generation Page
# ============================================

@login_required
def teacher_report(request):
    """
    Main teacher report generation page with filters and options.
    
    Accessible by: All authenticated users
    - Admin: Can generate reports for any teacher or all teachers
    - Teachers: Can generate reports for themselves only
    
    Features:
    - Teacher selection (individual or all)
    - Date range selection
    - Report type selection (PDF, Excel)
    - Report preview with summary statistics
    - Export buttons
    
    Requirements: FR-023, FR-024, FR-026
    """
    try:
        # Get all active teachers for selection (admin only)
        teachers = []
        if request.user.is_superuser:
            teachers = Teacher.objects.filter(is_active=True).order_by('full_name')
        elif hasattr(request.user, 'teacher_profile'):
            # Teachers can only see themselves
            teachers = [request.user.teacher_profile]
        
        # Get filter parameters from query string
        teacher_id = request.GET.get('teacher_id')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        report_type = request.GET.get('report_type', 'summary')
        
        # Set default date range (current month)
        today = timezone.now().date()
        start_date = date(today.year, today.month, 1)
        end_date = today
        
        # Parse date parameters
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'Format tanggal mulai tidak valid, menggunakan default')
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'Format tanggal akhir tidak valid, menggunakan default')
        
        # Validate date range
        if start_date > end_date:
            messages.error(request, 'Tanggal mulai harus sebelum atau sama dengan tanggal akhir')
            start_date = date(today.year, today.month, 1)
            end_date = today
        
        # Get selected teacher
        selected_teacher = None
        if teacher_id:
            try:
                selected_teacher = Teacher.objects.get(id=teacher_id)
                
                # Check permission: teachers can only view their own reports
                if not request.user.is_superuser:
                    if not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.id != selected_teacher.id:
                        messages.error(request, 'Anda tidak memiliki akses untuk melihat laporan ustadz lain')
                        selected_teacher = None
            except Teacher.DoesNotExist:
                messages.error(request, 'Ustadz tidak ditemukan')
        
        # Generate report preview if teacher is selected
        report_data = None
        if selected_teacher:
            try:
                # Get attendance analytics for the selected teacher
                from .services.teacher_attendance_service import TeacherAttendanceService
                
                # Get attendance records
                attendances = TeacherAttendanceService.get_teacher_attendance_history(
                    selected_teacher.id,
                    start_date,
                    end_date
                )
                
                # Calculate summary statistics
                total_jp = len(attendances)
                total_hadir = sum(1 for a in attendances if a['status'] == 'HADIR')
                total_sakit = sum(1 for a in attendances if a['status'] == 'SAKIT')
                total_izin = sum(1 for a in attendances if a['status'] == 'IZIN')
                total_cuti = sum(1 for a in attendances if a['status'] == 'CUTI')
                total_dinas = sum(1 for a in attendances if a['status'] == 'DINAS')
                total_alpa = sum(1 for a in attendances if a['status'] == 'ALPA')
                
                attendance_percentage = round((total_hadir / total_jp * 100), 2) if total_jp > 0 else 0.0
                
                report_data = {
                    'teacher': selected_teacher,
                    'start_date': start_date,
                    'end_date': end_date,
                    'total_jp': total_jp,
                    'total_hadir': total_hadir,
                    'total_sakit': total_sakit,
                    'total_izin': total_izin,
                    'total_cuti': total_cuti,
                    'total_dinas': total_dinas,
                    'total_alpa': total_alpa,
                    'attendance_percentage': attendance_percentage,
                    'attendances': attendances[:50],  # Limit to 50 for preview
                }
            except Exception as e:
                logger.error(f"Error generating report preview: {str(e)}")
                messages.error(request, f'Gagal membuat preview laporan: {str(e)}')
        
        context = {
            'teachers': teachers,
            'selected_teacher': selected_teacher,
            'start_date': start_date,
            'end_date': end_date,
            'report_type': report_type,
            'report_data': report_data,
            'today': today,
        }
        
    except Exception as e:
        logger.error(f"Error loading teacher report page: {str(e)}")
        messages.error(request, f'Terjadi kesalahan: {str(e)}')
        context = {
            'teachers': [],
            'today': timezone.now().date(),
        }
    
    return render(request, 'teacher/report.html', context)


# ============================================
# PDF Report Generation
# ============================================

@login_required
def teacher_report_pdf(request, teacher_id):
    """
    Generate and download PDF report for a specific teacher.
    
    Accessible by: Authenticated users with permission
    - Admin: Can generate PDF for any teacher
    - Teachers: Can generate PDF for themselves only
    
    Query parameters:
    - start_date: Start date (YYYY-MM-DD, required)
    - end_date: End date (YYYY-MM-DD, required)
    
    Returns:
        PDF file download with filename: laporan_absensi_{teacher_name}_{date_range}.pdf
    
    Requirements: FR-024
    """
    try:
        # Get teacher
        teacher = get_object_or_404(Teacher, id=teacher_id)
        
        # Check permission: teachers can only generate their own reports
        if not request.user.is_superuser:
            if not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.id != teacher.id:
                return HttpResponse(
                    'Anda tidak memiliki akses untuk mengunduh laporan ustadz lain',
                    status=403
                )
        
        # Get date range from query parameters
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if not start_date_str or not end_date_str:
            return HttpResponse(
                'Parameter start_date dan end_date harus disertakan',
                status=400
            )
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return HttpResponse(
                'Format tanggal tidak valid (gunakan YYYY-MM-DD)',
                status=400
            )
        
        # Validate date range
        if start_date > end_date:
            return HttpResponse(
                'Tanggal mulai harus sebelum atau sama dengan tanggal akhir',
                status=400
            )
        
        # Generate PDF using service
        pdf_bytes = TeacherReportService.generate_teacher_report_pdf(
            teacher.id,
            start_date,
            end_date
        )
        
        # Create filename
        teacher_name_safe = teacher.full_name.replace(' ', '_').replace('/', '_')
        date_range = f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"
        filename = f"laporan_absensi_{teacher_name_safe}_{date_range}.pdf"
        
        # Create response
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        logger.info(f"PDF report generated for teacher {teacher.full_name} ({start_date} to {end_date})")
        
        return response
        
    except TeacherReportServiceError as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        return HttpResponse(f'Gagal membuat laporan PDF: {str(e)}', status=400)
    
    except Exception as e:
        logger.error(f"Unexpected error generating PDF report: {str(e)}")
        return HttpResponse(f'Terjadi kesalahan: {str(e)}', status=500)


# ============================================
# Excel Export
# ============================================

@login_required
@admin_required
def teacher_report_excel(request):
    """
    Export teacher attendance data to Excel format.
    
    Accessible by: Admin only
    
    Query parameters:
    - start_date: Start date (YYYY-MM-DD, required)
    - end_date: End date (YYYY-MM-DD, required)
    
    Returns:
        Excel file download with filename: absensi_ustadz_{date_range}.xlsx
    
    Features:
    - Multiple sheets (Summary, Detail, Analytics)
    - Conditional formatting (color-coded statuses)
    - Formulas for automatic calculations
    - Frozen header rows
    
    Requirements: FR-026
    """
    try:
        # Get date range from query parameters
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if not start_date_str or not end_date_str:
            return HttpResponse(
                'Parameter start_date dan end_date harus disertakan',
                status=400
            )
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return HttpResponse(
                'Format tanggal tidak valid (gunakan YYYY-MM-DD)',
                status=400
            )
        
        # Validate date range
        if start_date > end_date:
            return HttpResponse(
                'Tanggal mulai harus sebelum atau sama dengan tanggal akhir',
                status=400
            )
        
        # Generate Excel using service
        excel_bytes = TeacherReportService.export_attendance_excel(
            start_date,
            end_date
        )
        
        # Create filename
        date_range = f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"
        filename = f"absensi_ustadz_{date_range}.xlsx"
        
        # Create response
        response = HttpResponse(
            excel_bytes,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        logger.info(f"Excel export generated for date range {start_date} to {end_date}")
        
        return response
        
    except TeacherReportServiceError as e:
        logger.error(f"Error exporting to Excel: {str(e)}")
        return HttpResponse(f'Gagal export ke Excel: {str(e)}', status=400)
    
    except Exception as e:
        logger.error(f"Unexpected error exporting to Excel: {str(e)}")
        return HttpResponse(f'Terjadi kesalahan: {str(e)}', status=500)


# ============================================
# Analytics Dashboard
# ============================================

@login_required
@admin_required
def teacher_analytics(request):
    """
    Comprehensive analytics dashboard for teacher attendance.
    
    Accessible by: Admin only
    
    Features:
    - Display comprehensive analytics
    - Show attendance trends over time
    - Display teacher performance comparison
    - Show subject-wise attendance
    - Add filters: date range, teacher, subject
    - Use charts and visualizations
    
    Query parameters:
    - start_date: Start date (YYYY-MM-DD, optional, default: 30 days ago)
    - end_date: End date (YYYY-MM-DD, optional, default: today)
    - teacher_id: Filter by specific teacher (optional)
    - subject_id: Filter by specific subject (optional)
    
    Requirements: FR-025, FR-027
    """
    try:
        # Get date range from query parameters
        today = timezone.now().date()
        start_date = today - timedelta(days=30)
        end_date = today
        
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'Format tanggal mulai tidak valid, menggunakan default')
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'Format tanggal akhir tidak valid, menggunakan default')
        
        # Validate date range
        if start_date > end_date:
            messages.error(request, 'Tanggal mulai harus sebelum atau sama dengan tanggal akhir')
            start_date = today - timedelta(days=30)
            end_date = today
        
        # Get analytics data from service
        analytics = TeacherReportService.get_attendance_analytics(
            start_date,
            end_date
        )
        
        # Get filter options
        from .models import Subject
        teachers = Teacher.objects.filter(is_active=True).order_by('full_name')
        subjects = Subject.objects.filter(is_active=True).order_by('category', 'name')
        
        # Apply filters if provided
        teacher_id = request.GET.get('teacher_id')
        subject_id = request.GET.get('subject_id')
        
        selected_teacher = None
        selected_subject = None
        
        if teacher_id:
            try:
                selected_teacher = Teacher.objects.get(id=teacher_id)
                # Filter analytics data by teacher
                analytics['teacher_stats'] = [
                    t for t in analytics['teacher_stats']
                    if t['teacher_id'] == str(selected_teacher.id)
                ]
            except Teacher.DoesNotExist:
                messages.warning(request, 'Ustadz tidak ditemukan')
        
        if subject_id:
            try:
                selected_subject = Subject.objects.get(id=subject_id)
                # Filter analytics data by subject
                analytics['subject_stats'] = [
                    s for s in analytics['subject_stats']
                    if s['subject'].id == selected_subject.id
                ]
            except Subject.DoesNotExist:
                messages.warning(request, 'Mata pelajaran tidak ditemukan')
        
        # Prepare chart data for templates
        # Daily trends chart data
        daily_trends_labels = [t['date'].strftime('%d/%m') for t in analytics['daily_trends']]
        daily_trends_hadir = [t['total_hadir'] for t in analytics['daily_trends']]
        daily_trends_absent = [t['total_absent'] for t in analytics['daily_trends']]
        daily_trends_percentage = [t['attendance_percentage'] for t in analytics['daily_trends']]
        
        # Teacher performance chart data (top 10)
        top_teachers = analytics['teacher_stats'][:10]
        teacher_names = [t['teacher_name'] for t in top_teachers]
        teacher_percentages = [t['attendance_percentage'] for t in top_teachers]
        
        # Subject-wise chart data
        subject_names = [s['subject_name'] for s in analytics['subject_stats']]
        subject_percentages = [s['attendance_percentage'] for s in analytics['subject_stats']]
        
        # Status breakdown chart data
        status_labels = ['Hadir', 'Sakit', 'Izin', 'Cuti', 'Dinas', 'Alpa']
        status_counts = [
            analytics['overall_stats']['total_hadir'],
            analytics['overall_stats']['total_sakit'],
            analytics['overall_stats']['total_izin'],
            analytics['overall_stats']['total_cuti'],
            analytics['overall_stats']['total_dinas'],
            analytics['overall_stats']['total_alpa'],
        ]
        
        context = {
            # Date range
            'start_date': start_date,
            'end_date': end_date,
            
            # Analytics data
            'analytics': analytics,
            
            # Filter options
            'teachers': teachers,
            'subjects': subjects,
            'selected_teacher': selected_teacher,
            'selected_subject': selected_subject,
            
            # Chart data
            'daily_trends_labels': daily_trends_labels,
            'daily_trends_hadir': daily_trends_hadir,
            'daily_trends_absent': daily_trends_absent,
            'daily_trends_percentage': daily_trends_percentage,
            'teacher_names': teacher_names,
            'teacher_percentages': teacher_percentages,
            'subject_names': subject_names,
            'subject_percentages': subject_percentages,
            'status_labels': status_labels,
            'status_counts': status_counts,
            
            # Current date
            'today': today,
        }
        
    except TeacherReportServiceError as e:
        logger.error(f"Error loading analytics: {str(e)}")
        messages.error(request, f'Gagal memuat analytics: {str(e)}')
        context = {
            'analytics': None,
            'today': timezone.now().date(),
        }
    
    except Exception as e:
        logger.error(f"Unexpected error loading analytics: {str(e)}")
        messages.error(request, f'Terjadi kesalahan: {str(e)}')
        context = {
            'analytics': None,
            'today': timezone.now().date(),
        }
    
    return render(request, 'teacher/analytics.html', context)


# ============================================
# API Endpoints for AJAX Requests
# ============================================

@login_required
@require_http_methods(["GET"])
def api_teacher_report_data(request):
    """
    AJAX endpoint for fetching teacher report data.
    
    Accessible by: Authenticated users with permission
    
    Query parameters:
    - teacher_id: Teacher ID (required)
    - start_date: Start date (YYYY-MM-DD, required)
    - end_date: End date (YYYY-MM-DD, required)
    
    Returns JSON:
    {
        "success": true|false,
        "data": {...},
        "error": "error message" (if success=false)
    }
    """
    try:
        # Get parameters
        teacher_id = request.GET.get('teacher_id')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if not teacher_id or not start_date_str or not end_date_str:
            return JsonResponse({
                'success': False,
                'error': 'Parameter teacher_id, start_date, dan end_date harus disertakan'
            }, status=400)
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
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
                'error': 'Ustadz tidak ditemukan'
            }, status=404)
        
        # Check permission
        if not request.user.is_superuser:
            if not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile.id != teacher.id:
                return JsonResponse({
                    'success': False,
                    'error': 'Anda tidak memiliki akses untuk melihat data ustadz lain'
                }, status=403)
        
        # Get attendance data
        from .services.teacher_attendance_service import TeacherAttendanceService
        
        attendances = TeacherAttendanceService.get_teacher_attendance_history(
            teacher.id,
            start_date,
            end_date
        )
        
        # Calculate summary
        total_jp = len(attendances)
        total_hadir = sum(1 for a in attendances if a['status'] == 'HADIR')
        total_sakit = sum(1 for a in attendances if a['status'] == 'SAKIT')
        total_izin = sum(1 for a in attendances if a['status'] == 'IZIN')
        total_cuti = sum(1 for a in attendances if a['status'] == 'CUTI')
        total_dinas = sum(1 for a in attendances if a['status'] == 'DINAS')
        total_alpa = sum(1 for a in attendances if a['status'] == 'ALPA')
        
        attendance_percentage = round((total_hadir / total_jp * 100), 2) if total_jp > 0 else 0.0
        
        return JsonResponse({
            'success': True,
            'data': {
                'teacher': {
                    'id': str(teacher.id),
                    'full_name': teacher.full_name,
                    'nip': teacher.nip,
                },
                'period': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                },
                'summary': {
                    'total_jp': total_jp,
                    'total_hadir': total_hadir,
                    'total_sakit': total_sakit,
                    'total_izin': total_izin,
                    'total_cuti': total_cuti,
                    'total_dinas': total_dinas,
                    'total_alpa': total_alpa,
                    'attendance_percentage': attendance_percentage,
                },
                'attendances': attendances,
            }
        })
        
    except Exception as e:
        logger.error(f"Error in API teacher report data: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Terjadi kesalahan: {str(e)}'
        }, status=500)
