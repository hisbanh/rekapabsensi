"""
Teacher Attendance Service Layer
Business logic for teacher attendance operations
"""
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from attendance.models import (
    Teacher, TeacherSchedule, TeacherDailyAttendance, 
    TeacherStatus, DaySchedule
)
from attendance.exceptions import AttendanceServiceError

logger = logging.getLogger(__name__)


class TeacherAttendanceService:
    """Service class for teacher attendance operations"""
    
    @staticmethod
    def get_attendance_for_date(teacher, target_date):
        """
        Get attendance record for a specific date
        
        Args:
            teacher: Teacher instance
            target_date: Date object
            
        Returns:
            TeacherDailyAttendance instance or None
        """
        try:
            return TeacherDailyAttendance.objects.filter(
                teacher=teacher,
                date=target_date
            ).first()
        except Exception as e:
            logger.error(f"Error getting attendance for date: {str(e)}")
            return None
    
    @staticmethod
    def save_attendance(teacher, target_date, jp_statuses, notes='', 
                       is_replacement=False, replaced_teacher=None, user=None):
        """
        Save or update teacher attendance
        
        Args:
            teacher: Teacher instance
            target_date: Date object
            jp_statuses: Dict of JP statuses {"1": "H", "2": "H", ...}
            notes: Additional notes
            is_replacement: Flag for replacement
            replaced_teacher: Teacher being replaced
            user: User recording attendance
            
        Returns:
            Tuple (attendance, created)
        """
        try:
            # Validate JP statuses
            valid_statuses = {choice[0] for choice in TeacherStatus.choices}
            for jp_num, status in jp_statuses.items():
                if status not in valid_statuses:
                    raise AttendanceServiceError(
                        f"Invalid status '{status}' for JP {jp_num}"
                    )
            
            # Validate JP numbers against day schedule
            day_schedule = DaySchedule.objects.filter(
                day_of_week=target_date.weekday()
            ).first()
            
            if day_schedule:
                max_jp = day_schedule.default_jp_count
                for jp_num in jp_statuses.keys():
                    if int(jp_num) > max_jp:
                        raise AttendanceServiceError(
                            f"JP {jp_num} exceeds maximum JP ({max_jp}) for this day"
                        )
            
            # Create or update attendance
            attendance, created = TeacherDailyAttendance.objects.update_or_create(
                teacher=teacher,
                date=target_date,
                defaults={
                    'jp_statuses': jp_statuses,
                    'notes': notes,
                    'is_replacement': is_replacement,
                    'replaced_teacher': replaced_teacher,
                    'recorded_by': user,
                }
            )
            
            return attendance, created
            
        except AttendanceServiceError:
            raise
        except Exception as e:
            logger.error(f"Error saving attendance: {str(e)}")
            raise AttendanceServiceError(f"Failed to save attendance: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def bulk_save_attendance(attendance_data_list, target_date, user=None):
        """
        Bulk save attendance for multiple teachers
        
        Args:
            attendance_data_list: List of dicts with teacher_id, jp_statuses, notes, etc.
            target_date: Date object
            user: User recording attendance
            
        Returns:
            Tuple (created_count, updated_count)
        """
        try:
            created_count = 0
            updated_count = 0
            
            for data in attendance_data_list:
                teacher_id = data.get('teacher_id')
                jp_statuses = data.get('jp_statuses', {})
                notes = data.get('notes', '')
                is_replacement = data.get('is_replacement', False)
                replaced_teacher_id = data.get('replaced_teacher_id')
                
                # Get teacher
                try:
                    teacher = Teacher.objects.get(id=teacher_id)
                except Teacher.DoesNotExist:
                    logger.warning(f"Teacher {teacher_id} not found, skipping")
                    continue
                
                # Get replaced teacher if applicable
                replaced_teacher = None
                if replaced_teacher_id:
                    try:
                        replaced_teacher = Teacher.objects.get(id=replaced_teacher_id)
                    except Teacher.DoesNotExist:
                        pass
                
                # Save attendance
                attendance, created = TeacherAttendanceService.save_attendance(
                    teacher=teacher,
                    target_date=target_date,
                    jp_statuses=jp_statuses,
                    notes=notes,
                    is_replacement=is_replacement,
                    replaced_teacher=replaced_teacher,
                    user=user
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            
            return created_count, updated_count
            
        except Exception as e:
            logger.error(f"Error bulk saving attendance: {str(e)}")
            raise AttendanceServiceError(f"Failed to bulk save attendance: {str(e)}")
    
    @staticmethod
    def get_attendance_statistics(start_date=None, end_date=None):
        """
        Get overall attendance statistics
        
        Args:
            start_date: Start date (optional)
            end_date: End date (optional)
            
        Returns:
            Dict with statistics
        """
        try:
            queryset = TeacherDailyAttendance.objects.all()
            
            if start_date:
                queryset = queryset.filter(date__gte=start_date)
            if end_date:
                queryset = queryset.filter(date__lte=end_date)
            
            # Count JP statuses
            stats = {
                'hadir': 0,
                'sakit': 0,
                'izin': 0,
                'alpa': 0,
                'tidak_ada_jadwal': 0,
                'dinas_luar': 0,
                'cuti': 0,
                'terlambat': 0,
                'total_jp': 0,
            }
            
            for attendance in queryset:
                for status in attendance.jp_statuses.values():
                    stats['total_jp'] += 1
                    if status == 'H':
                        stats['hadir'] += 1
                    elif status == 'S':
                        stats['sakit'] += 1
                    elif status == 'I':
                        stats['izin'] += 1
                    elif status == 'A':
                        stats['alpa'] += 1
                    elif status == 'T':
                        stats['tidak_ada_jadwal'] += 1
                    elif status == 'D':
                        stats['dinas_luar'] += 1
                    elif status == 'C':
                        stats['cuti'] += 1
                    elif status == 'L':
                        stats['terlambat'] += 1
            
            # Calculate percentage
            if stats['total_jp'] > 0:
                stats['attendance_rate'] = round(
                    (stats['hadir'] / stats['total_jp']) * 100, 2
                )
            else:
                stats['attendance_rate'] = 0.0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting attendance statistics: {str(e)}")
            raise AttendanceServiceError(f"Failed to get statistics: {str(e)}")
    
    @staticmethod
    def get_teachers_missing_attendance(target_date):
        """
        Get teachers who have schedule but haven't recorded attendance
        
        Args:
            target_date: Date object
            
        Returns:
            List of dicts with teacher and schedule info
        """
        try:
            day_of_week = target_date.weekday()
            
            # Get schedules for this day
            schedules = TeacherSchedule.objects.filter(
                day_of_week=day_of_week,
                teacher__is_active=True
            ).select_related('teacher')
            
            # Get teachers who already recorded attendance
            recorded_teacher_ids = TeacherDailyAttendance.objects.filter(
                date=target_date
            ).values_list('teacher_id', flat=True)
            
            # Filter out teachers who already recorded
            missing = []
            for schedule in schedules:
                if schedule.teacher.id not in recorded_teacher_ids:
                    missing.append({
                        'teacher': schedule.teacher,
                        'schedule': schedule,
                        'jp_numbers': schedule.jp_numbers,
                        'subject': schedule.subject,
                        'is_piket': schedule.is_piket,
                    })
            
            return missing
            
        except Exception as e:
            logger.error(f"Error getting missing attendance: {str(e)}")
            return []
    
    @staticmethod
    def validate_attendance_data(jp_statuses, target_date):
        """
        Validate attendance data
        
        Args:
            jp_statuses: Dict of JP statuses
            target_date: Date object
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        try:
            # Validate statuses
            valid_statuses = {choice[0] for choice in TeacherStatus.choices}
            for jp_num, status in jp_statuses.items():
                if status not in valid_statuses:
                    errors.append(f"Status tidak valid untuk JP {jp_num}: {status}")
            
            # Validate JP numbers
            day_schedule = DaySchedule.objects.filter(
                day_of_week=target_date.weekday()
            ).first()
            
            if day_schedule:
                max_jp = day_schedule.default_jp_count
                for jp_num in jp_statuses.keys():
                    try:
                        jp_int = int(jp_num)
                        if jp_int < 1 or jp_int > max_jp:
                            errors.append(
                                f"JP {jp_num} tidak valid (maksimal {max_jp} untuk hari ini)"
                            )
                    except ValueError:
                        errors.append(f"Nomor JP tidak valid: {jp_num}")
            
            # Validate date
            if target_date > timezone.now().date():
                errors.append("Tanggal tidak boleh di masa depan")
            
        except Exception as e:
            logger.error(f"Error validating attendance data: {str(e)}")
            errors.append(f"Error validasi: {str(e)}")
        
        return errors
