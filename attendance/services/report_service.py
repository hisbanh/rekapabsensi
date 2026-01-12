"""
Report Service Layer
Handles all business logic related to reporting and analytics
"""
from typing import List, Dict, Optional
from datetime import date, datetime, timedelta
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
import csv
from io import StringIO

from ..models import Student, AttendanceRecord, AttendanceStatus
from ..exceptions import ReportServiceError


class ReportService:
    """Service class for report generation and analytics"""
    
    @staticmethod
    def generate_attendance_report(
        start_date: date = None,
        end_date: date = None,
        classroom_id: str = None,
        status: str = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict:
        """Generate comprehensive attendance report with filters"""
        
        queryset = AttendanceRecord.objects.select_related(
            'student', 'student__classroom', 'student__classroom__academic_level', 'teacher'
        ).all()
        
        # Apply filters
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if classroom_id:
            queryset = queryset.filter(student__classroom_id=classroom_id)
        if status:
            queryset = queryset.filter(status=status)
        
        # Order by date descending
        queryset = queryset.order_by('-date', 'student__classroom__academic_level', 'student__classroom__grade', 'student__name')
        
        # Pagination
        paginator = Paginator(queryset, per_page)
        records_page = paginator.get_page(page)
        
        # Generate summary statistics
        summary = ReportService._generate_report_summary(queryset)
        
        return {
            'records': records_page,
            'summary': summary,
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'classroom_id': classroom_id,
                'status': status
            },
            'pagination': {
                'total_count': paginator.count,
                'page_count': paginator.num_pages,
                'current_page': page,
                'has_previous': records_page.has_previous(),
                'has_next': records_page.has_next(),
            }
        }
    
    @staticmethod
    def _generate_report_summary(queryset) -> Dict:
        """Generate summary statistics for a queryset"""
        total_records = queryset.count()
        
        if total_records == 0:
            return {
                'total_records': 0,
                'present': 0,
                'sick': 0,
                'permission': 0,
                'absent': 0,
                'attendance_rate': 0.0
            }
        
        present = queryset.filter(status=AttendanceStatus.HADIR).count()
        sick = queryset.filter(status=AttendanceStatus.SAKIT).count()
        permission = queryset.filter(status=AttendanceStatus.IZIN).count()
        absent = queryset.filter(status=AttendanceStatus.ALPA).count()
        
        return {
            'total_records': total_records,
            'present': present,
            'sick': sick,
            'permission': permission,
            'absent': absent,
            'attendance_rate': round((present / total_records * 100), 2)
        }
    
    @staticmethod
    def export_attendance_to_csv(
        start_date: date = None,
        end_date: date = None,
        classroom_id: str = None,
        status: str = None
    ) -> str:
        """Export attendance data to CSV format"""
        
        queryset = AttendanceRecord.objects.select_related(
            'student', 'student__classroom', 'student__classroom__academic_level', 'teacher'
        ).all()
        
        # Apply same filters as report
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if classroom_id:
            queryset = queryset.filter(student__classroom_id=classroom_id)
        if status:
            queryset = queryset.filter(status=status)
        
        queryset = queryset.order_by('-date', 'student__classroom__academic_level', 'student__classroom__grade', 'student__name')
        
        # Generate CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Tanggal', 'ID Siswa', 'Nama Siswa', 'Kelas', 'NISN', 
            'Status', 'Catatan', 'Guru', 'Waktu Input'
        ])
        
        # Data rows
        for record in queryset:
            writer.writerow([
                record.date.strftime('%Y-%m-%d'),
                record.student.student_id,
                record.student.name,
                str(record.student.classroom),
                record.student.nisn or '',
                record.get_status_display(),
                record.notes or '',
                record.teacher.get_full_name() or record.teacher.username,
                record.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return output.getvalue()
    
    @staticmethod
    def generate_monthly_summary(year: int, month: int) -> Dict:
        """Generate monthly attendance summary"""
        start_date = date(year, month, 1)
        
        # Calculate end date (last day of month)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        records = AttendanceRecord.objects.filter(
            date__range=[start_date, end_date]
        )
        
        # Daily statistics
        daily_stats = []
        current_date = start_date
        
        while current_date <= end_date:
            day_records = records.filter(date=current_date)
            daily_stats.append({
                'date': current_date,
                'total': day_records.count(),
                'present': day_records.filter(status=AttendanceStatus.HADIR).count(),
                'sick': day_records.filter(status=AttendanceStatus.SAKIT).count(),
                'permission': day_records.filter(status=AttendanceStatus.IZIN).count(),
                'absent': day_records.filter(status=AttendanceStatus.ALPA).count(),
            })
            current_date += timedelta(days=1)
        
        # Classroom-wise summary
        from ..models import Classroom
        classrooms = Classroom.objects.filter(is_active=True).select_related('academic_level')
        classroom_summary = []
        
        for classroom in classrooms:
            classroom_records = records.filter(student__classroom=classroom)
            total_students = Student.objects.filter(classroom=classroom, is_active=True).count()
            
            classroom_summary.append({
                'classroom': classroom,
                'classroom_name': str(classroom),
                'total_students': total_students,
                'total_records': classroom_records.count(),
                'present': classroom_records.filter(status=AttendanceStatus.HADIR).count(),
                'sick': classroom_records.filter(status=AttendanceStatus.SAKIT).count(),
                'permission': classroom_records.filter(status=AttendanceStatus.IZIN).count(),
                'absent': classroom_records.filter(status=AttendanceStatus.ALPA).count(),
            })
        
        return {
            'period': {'year': year, 'month': month, 'start_date': start_date, 'end_date': end_date},
            'overall_summary': ReportService._generate_report_summary(records),
            'daily_stats': daily_stats,
            'classroom_summary': classroom_summary
        }
    
    @staticmethod
    def generate_student_performance_report(
        classroom_id: str = None,
        min_attendance_rate: float = None
    ) -> List[Dict]:
        """Generate student performance report based on attendance"""
        
        students = Student.objects.select_related('classroom', 'classroom__academic_level').filter(is_active=True)
        if classroom_id:
            students = students.filter(classroom_id=classroom_id)
        
        performance_data = []
        
        for student in students:
            records = AttendanceRecord.objects.filter(student=student)
            total_records = records.count()
            
            if total_records == 0:
                attendance_rate = 0.0
                present_count = 0
            else:
                present_count = records.filter(status=AttendanceStatus.HADIR).count()
                attendance_rate = round((present_count / total_records * 100), 2)
            
            # Apply minimum attendance rate filter
            if min_attendance_rate is not None and attendance_rate < min_attendance_rate:
                continue
            
            performance_data.append({
                'student': student,
                'total_records': total_records,
                'present_count': present_count,
                'attendance_rate': attendance_rate,
                'sick_count': records.filter(status=AttendanceStatus.SAKIT).count(),
                'permission_count': records.filter(status=AttendanceStatus.IZIN).count(),
                'absent_count': records.filter(status=AttendanceStatus.ALPA).count(),
            })
        
        # Sort by attendance rate (descending)
        performance_data.sort(key=lambda x: x['attendance_rate'], reverse=True)
        
        return performance_data