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

from ..models import (
    Student, AttendanceRecord, AttendanceStatus, AttendanceSummary,
    DailyAttendance, Classroom, DaySchedule, Holiday
)
from ..exceptions import AttendanceServiceError
from .schedule_service import ScheduleService


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
                'classroom_id': str(classroom.id),
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
                'date': current_date.isoformat(),
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


    # ============================================
    # JP-Based Daily Attendance Methods
    # ============================================
    
    @staticmethod
    def get_attendance(student: Student, target_date: date) -> Optional[DailyAttendance]:
        """
        Get DailyAttendance record for a specific student and date.
        
        Args:
            student: The student to get attendance for
            target_date: The date to get attendance for
            
        Returns:
            DailyAttendance or None if not found
        """
        try:
            return DailyAttendance.objects.get(student=student, date=target_date)
        except DailyAttendance.DoesNotExist:
            return None
    
    @staticmethod
    def get_class_attendance(classroom: Classroom, target_date: date) -> List[DailyAttendance]:
        """
        Get all DailyAttendance records for a classroom on a specific date.
        
        Args:
            classroom: The classroom to get attendance for
            target_date: The date to get attendance for
            
        Returns:
            List of DailyAttendance records
        """
        return list(
            DailyAttendance.objects.filter(
                student__classroom=classroom,
                date=target_date
            ).select_related('student', 'recorded_by')
            .order_by('student__name')
        )
    
    @staticmethod
    def save_attendance(
        student: Student,
        target_date: date,
        jp_statuses: Dict[str, str],
        user: User,
        notes: str = ''
    ) -> DailyAttendance:
        """
        Save or update DailyAttendance for a student.
        
        Args:
            student: The student to save attendance for
            target_date: The date of attendance
            jp_statuses: Dict of JP statuses {"1": "H", "2": "S", ...}
            user: User recording the attendance
            notes: Optional notes
            
        Returns:
            Created or updated DailyAttendance record
            
        Raises:
            ValidationError: If jp_statuses contains invalid values
        """
        # Validate jp_statuses
        valid_statuses = {'H', 'S', 'I', 'A'}
        for jp_num, status in jp_statuses.items():
            if status not in valid_statuses:
                raise ValidationError(
                    f'Invalid status "{status}" for JP {jp_num}. Valid values: H, S, I, A'
                )
        
        # Get expected JP count for validation
        expected_jp_count = ScheduleService.get_jp_count_for_date(target_date)
        if len(jp_statuses) != expected_jp_count:
            raise ValidationError(
                f'Expected {expected_jp_count} JP entries, got {len(jp_statuses)}'
            )
        
        # Create or update
        attendance, created = DailyAttendance.objects.update_or_create(
            student=student,
            date=target_date,
            defaults={
                'jp_statuses': jp_statuses,
                'recorded_by': user,
                'notes': notes,
                'updated_by': user
            }
        )
        
        if created:
            attendance.created_by = user
            attendance.save()
        
        return attendance
    
    @staticmethod
    @transaction.atomic
    def save_bulk_attendance(
        classroom: Classroom,
        target_date: date,
        attendance_data: List[Dict],
        user: User
    ) -> Tuple[int, int]:
        """
        Bulk save DailyAttendance for multiple students in a classroom.
        
        Args:
            classroom: The classroom
            target_date: The date of attendance
            attendance_data: List of dicts with student_id and jp_statuses
                [{"student_id": "uuid", "jp_statuses": {"1": "H", ...}, "notes": ""}]
            user: User recording the attendance
            
        Returns:
            Tuple of (created_count, updated_count)
            
        Raises:
            AttendanceServiceError: If any student not found or validation fails
        """
        created_count = 0
        updated_count = 0
        
        # Validate jp_statuses format
        valid_statuses = {'H', 'S', 'I', 'A'}
        expected_jp_count = ScheduleService.get_jp_count_for_date(target_date)
        
        for data in attendance_data:
            try:
                student = Student.objects.get(id=data['student_id'])
                
                # Validate student belongs to classroom
                if student.classroom_id != classroom.id:
                    raise AttendanceServiceError(
                        f"Student {student.name} does not belong to classroom {classroom}"
                    )
                
                jp_statuses = data.get('jp_statuses', {})
                
                # Validate statuses
                for jp_num, status in jp_statuses.items():
                    if status not in valid_statuses:
                        raise AttendanceServiceError(
                            f'Invalid status "{status}" for student {student.name}, JP {jp_num}'
                        )
                
                # Create or update
                attendance, created = DailyAttendance.objects.update_or_create(
                    student=student,
                    date=target_date,
                    defaults={
                        'jp_statuses': jp_statuses,
                        'recorded_by': user,
                        'notes': data.get('notes', ''),
                        'updated_by': user
                    }
                )
                
                if created:
                    attendance.created_by = user
                    attendance.save()
                    created_count += 1
                else:
                    updated_count += 1
                    
            except Student.DoesNotExist:
                raise AttendanceServiceError(
                    f"Student with ID {data['student_id']} not found"
                )
        
        return created_count, updated_count
    
    @staticmethod
    def get_missing_attendance(
        classroom: Classroom,
        start_date: date,
        end_date: date
    ) -> List[date]:
        """
        Get list of dates with missing attendance for a classroom.
        
        A date is considered missing if:
        1. It's a school day (according to DaySchedule)
        2. It's not a holiday for the classroom
        3. No DailyAttendance records exist for any student in the classroom
        
        Args:
            classroom: The classroom to check
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of dates with missing attendance
        """
        from .holiday_service import HolidayService
        
        missing_dates = []
        current_date = start_date
        
        # Get all students in classroom
        students = Student.objects.filter(
            classroom=classroom,
            is_active=True
        )
        
        if not students.exists():
            return []
        
        # Get all existing attendance dates for this classroom
        existing_dates = set(
            DailyAttendance.objects.filter(
                student__classroom=classroom,
                date__range=[start_date, end_date]
            ).values_list('date', flat=True).distinct()
        )
        
        while current_date <= end_date:
            # Check if it's a school day
            if ScheduleService.is_school_day(current_date):
                # Check if it's not a holiday for this classroom
                if not HolidayService.is_holiday(current_date, classroom):
                    # Check if attendance exists
                    if current_date not in existing_dates:
                        missing_dates.append(current_date)
            
            current_date += timedelta(days=1)
        
        return missing_dates
    
    @staticmethod
    def get_daily_attendance_summary(
        classroom: Classroom,
        target_date: date
    ) -> Dict:
        """
        Get attendance summary for a classroom on a specific date.
        
        Returns:
            Dict with total counts for H, S, I, A across all JP slots
        """
        attendances = DailyAttendance.objects.filter(
            student__classroom=classroom,
            date=target_date
        )
        
        total_h = 0
        total_s = 0
        total_i = 0
        total_a = 0
        total_jp = 0
        
        for attendance in attendances:
            for status in attendance.jp_statuses.values():
                total_jp += 1
                if status == 'H':
                    total_h += 1
                elif status == 'S':
                    total_s += 1
                elif status == 'I':
                    total_i += 1
                elif status == 'A':
                    total_a += 1
        
        return {
            'date': target_date,
            'classroom': classroom,
            'total_students': attendances.count(),
            'total_jp': total_jp,
            'total_hadir': total_h,
            'total_sakit': total_s,
            'total_izin': total_i,
            'total_alpa': total_a,
            'attendance_rate': round((total_h / total_jp * 100), 2) if total_jp > 0 else 0
        }
