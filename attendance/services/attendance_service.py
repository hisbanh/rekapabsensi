"""
Attendance Service Layer
Handles all business logic related to attendance management
"""
from typing import List, Dict, Optional, Tuple
from datetime import date, datetime, timedelta
from django.db import transaction
from django.db.models import Q, Count, Avg
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from ..models import Student, AttendanceRecord, AttendanceStatus, AttendanceSummary
from ..exceptions import AttendanceServiceError


class AttendanceService:
    """Service class for attendance-related business operations"""
    
    @staticmethod
    def get_attendance_statistics(target_date: date = None) -> Dict:
        """Get comprehensive attendance statistics for a given date"""
        if target_date is None:
            target_date = date.today()
            
        records = AttendanceRecord.objects.filter(date=target_date)
        total_students = Student.objects.count()
        
        stats = {
            'date': target_date,
            'total_students': total_students,
            'total_recorded': records.count(),
            'present': records.filter(status=AttendanceStatus.HADIR).count(),
            'sick': records.filter(status=AttendanceStatus.SAKIT).count(),
            'permission': records.filter(status=AttendanceStatus.IZIN).count(),
            'absent': records.filter(status=AttendanceStatus.ALPA).count(),
            'not_recorded': total_students - records.count(),
            'attendance_rate': 0.0
        }
        
        if stats['total_recorded'] > 0:
            stats['attendance_rate'] = round(
                (stats['present'] / stats['total_recorded']) * 100, 2
            )
            
        return stats
    
    @staticmethod
    def get_classroom_statistics(target_date: date = None) -> List[Dict]:
        """Get attendance statistics grouped by classroom"""
        if target_date is None:
            target_date = date.today()
            
        from ..models import Classroom
        classrooms = Classroom.objects.filter(is_active=True).select_related('academic_level')
        classroom_stats = []
        
        for classroom in classrooms:
            students_in_classroom = Student.objects.filter(classroom=classroom, is_active=True)
            records = AttendanceRecord.objects.filter(
                student__in=students_in_classroom,
                date=target_date
            )
            
            total_students = students_in_classroom.count()
            present = records.filter(status=AttendanceStatus.HADIR).count()
            
            classroom_stats.append({
                'classroom': classroom,
                'classroom_name': str(classroom),
                'academic_level': classroom.academic_level.code,
                'grade': classroom.grade,
                'section': classroom.section,
                'total_students': total_students,
                'present': present,
                'sick': records.filter(status=AttendanceStatus.SAKIT).count(),
                'permission': records.filter(status=AttendanceStatus.IZIN).count(),
                'absent': records.filter(status=AttendanceStatus.ALPA).count(),
                'not_recorded': total_students - records.count(),
                'attendance_rate': round((present / total_students * 100), 2) if total_students > 0 else 0
            })
            
        return sorted(classroom_stats, key=lambda x: (x['academic_level'], x['grade'], x['section']))
    
    @staticmethod
    def get_class_statistics(target_date: date = None) -> List[Dict]:
        """Get attendance statistics grouped by class (backward compatibility)"""
        return AttendanceService.get_classroom_statistics(target_date)
    
    @staticmethod
    @transaction.atomic
    def bulk_create_attendance(
        attendance_data: List[Dict], 
        teacher: User, 
        target_date: date
    ) -> Tuple[int, int]:
        """
        Bulk create or update attendance records
        Returns tuple of (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0
        
        for data in attendance_data:
            try:
                student = Student.objects.get(id=data['student_id'])
                
                record, created = AttendanceRecord.objects.update_or_create(
                    student=student,
                    date=target_date,
                    defaults={
                        'status': data['status'],
                        'teacher': teacher,
                        'notes': data.get('notes', '')
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                    
            except Student.DoesNotExist:
                raise AttendanceServiceError(f"Student with ID {data['student_id']} not found")
            except Exception as e:
                raise AttendanceServiceError(f"Error processing attendance for student {data['student_id']}: {str(e)}")
                
        return created_count, updated_count
    
    @staticmethod
    def get_student_attendance_summary(
        student: Student, 
        start_date: date = None, 
        end_date: date = None
    ) -> Dict:
        """Get comprehensive attendance summary for a student"""
        if start_date is None:
            start_date = date.today() - timedelta(days=30)
        if end_date is None:
            end_date = date.today()
            
        records = AttendanceRecord.objects.filter(
            student=student,
            date__range=[start_date, end_date]
        )
        
        total_records = records.count()
        present_count = records.filter(status=AttendanceStatus.HADIR).count()
        sick_count = records.filter(status=AttendanceStatus.SAKIT).count()
        permission_count = records.filter(status=AttendanceStatus.IZIN).count()
        absent_count = records.filter(status=AttendanceStatus.ALPA).count()
        
        return {
            'student': student,
            'period': {'start': start_date, 'end': end_date},
            'total_records': total_records,
            'present': present_count,
            'sick': sick_count,
            'permission': permission_count,
            'absent': absent_count,
            'attendance_rate': round((present_count / total_records * 100), 2) if total_records > 0 else 0,
            'recent_records': records.order_by('-date')[:10]
        }
    
    @staticmethod
    def get_attendance_trends(days: int = 7) -> List[Dict]:
        """Get attendance trends for the last N days"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        trends = []
        current_date = start_date
        
        while current_date <= end_date:
            stats = AttendanceService.get_attendance_statistics(current_date)
            trends.append({
                'date': current_date,
                'present': stats['present'],
                'absent': stats['sick'] + stats['permission'] + stats['absent'],
                'attendance_rate': stats['attendance_rate']
            })
            current_date += timedelta(days=1)
            
        return trends
    
    @staticmethod
    def validate_attendance_data(attendance_data: List[Dict]) -> List[str]:
        """Validate attendance data before processing"""
        errors = []
        
        for i, data in enumerate(attendance_data):
            if 'student_id' not in data:
                errors.append(f"Row {i+1}: Missing student_id")
                continue
                
            if 'status' not in data:
                errors.append(f"Row {i+1}: Missing status")
                continue
                
            if data['status'] not in [choice[0] for choice in AttendanceStatus.choices]:
                errors.append(f"Row {i+1}: Invalid status '{data['status']}'")
                
            try:
                Student.objects.get(id=data['student_id'])
            except Student.DoesNotExist:
                errors.append(f"Row {i+1}: Student with ID {data['student_id']} not found")
                
        return errors