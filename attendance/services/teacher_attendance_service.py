"""
Teacher Attendance Service Layer
Handles all business logic related to teacher attendance recording and management
"""
from typing import List, Dict, Optional, Tuple
from uuid import UUID
from datetime import date, timedelta
from decimal import Decimal
from math import radians, cos, sin, asin, sqrt

from django.db import transaction
from django.db.models import Q, Count, Sum
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from django.conf import settings

from ..models import (
    Teacher, TeacherAttendance, TeacherSchedule, 
    TeacherAttendanceSummary
)
from ..exceptions import AttendanceBaseException


class TeacherAttendanceServiceError(AttendanceBaseException):
    """Exception raised by teacher attendance service operations"""
    pass


class TeacherAttendanceService:
    """Service class for teacher attendance-related business operations"""
    
    # School location settings (can be overridden in Django settings)
    SCHOOL_LATITUDE = getattr(settings, 'SCHOOL_LATITUDE', -7.7956)
    SCHOOL_LONGITUDE = getattr(settings, 'SCHOOL_LONGITUDE', 110.3695)
    SCHOOL_RADIUS_METERS = getattr(settings, 'SCHOOL_RADIUS_METERS', 150)
    
    @staticmethod
    def validate_location(latitude: float, longitude: float) -> bool:
        """
        Validate if coordinates are within school premises using Haversine formula.
        
        The Haversine formula calculates the great-circle distance between two points
        on a sphere given their longitudes and latitudes.
        
        Args:
            latitude: Latitude coordinate to validate (-90 to 90)
            longitude: Longitude coordinate to validate (-180 to 180)
            
        Returns:
            bool: True if location is within school radius, False otherwise
            
        Example:
            >>> # Location within school premises
            >>> is_valid = TeacherAttendanceService.validate_location(-7.7956, 110.3695)
            >>> print(f"Location valid: {is_valid}")  # True
            
            >>> # Location outside school premises
            >>> is_valid = TeacherAttendanceService.validate_location(-7.8000, 110.4000)
            >>> print(f"Location valid: {is_valid}")  # False
        """
        # Validate input ranges
        if not (-90 <= latitude <= 90):
            raise TeacherAttendanceServiceError("Latitude must be between -90 and 90")
        
        if not (-180 <= longitude <= 180):
            raise TeacherAttendanceServiceError("Longitude must be between -180 and 180")
        
        # Get school coordinates
        school_lat = TeacherAttendanceService.SCHOOL_LATITUDE
        school_lon = TeacherAttendanceService.SCHOOL_LONGITUDE
        radius_meters = TeacherAttendanceService.SCHOOL_RADIUS_METERS
        
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(
            radians, 
            [school_lat, school_lon, latitude, longitude]
        )
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        
        # Earth radius in meters
        earth_radius_meters = 6371000
        
        # Calculate distance in meters
        distance = earth_radius_meters * c
        
        # Check if within radius
        return distance <= radius_meters
    
    @staticmethod
    def _validate_attendance_data(data: Dict, user: User = None) -> List[str]:
        """
        Validate attendance data before recording.
        
        Args:
            data: Dictionary containing attendance data
            user: User recording the attendance (for date validation)
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Required fields validation
        required_fields = ['teacher_id', 'date', 'jp_number', 'status']
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Field '{field}' is required")
        
        # Teacher validation
        if data.get('teacher_id'):
            try:
                teacher = Teacher.objects.get(id=data['teacher_id'])
                if not teacher.is_active:
                    errors.append("Cannot record attendance for inactive teacher")
            except Teacher.DoesNotExist:
                errors.append(f"Teacher with ID '{data['teacher_id']}' not found")
        
        # Date validation
        if data.get('date'):
            attendance_date = data['date']
            if isinstance(attendance_date, str):
                from datetime import datetime
                try:
                    attendance_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
                except ValueError:
                    errors.append("Invalid date format (use YYYY-MM-DD)")
                    return errors
            
            # Check if date is in the future
            if attendance_date > timezone.now().date():
                errors.append("Attendance date cannot be in the future")
            
            # Check 7-day limit for non-admin users
            if user and not user.is_staff:
                days_past = (timezone.now().date() - attendance_date).days
                if days_past > 7:
                    errors.append("Teachers can only record attendance for dates within the last 7 days")
        
        # JP number validation
        if data.get('jp_number'):
            jp_number = data['jp_number']
            if not isinstance(jp_number, int) or jp_number < 1 or jp_number > 10:
                errors.append("JP number must be between 1 and 10")
        
        # Status validation
        if data.get('status'):
            valid_statuses = ['HADIR', 'SAKIT', 'IZIN', 'CUTI', 'DINAS', 'ALPA']
            if data['status'] not in valid_statuses:
                errors.append(f"Invalid status. Valid values: {', '.join(valid_statuses)}")
        
        # Location validation (if provided)
        if data.get('latitude') is not None:
            try:
                lat = float(data['latitude'])
                if not (-90 <= lat <= 90):
                    errors.append("Latitude must be between -90 and 90")
            except (ValueError, TypeError):
                errors.append("Invalid latitude value")
        
        if data.get('longitude') is not None:
            try:
                lon = float(data['longitude'])
                if not (-180 <= lon <= 180):
                    errors.append("Longitude must be between -180 and 180")
            except (ValueError, TypeError):
                errors.append("Invalid longitude value")
        
        # Substitute validation
        if data.get('is_substitute'):
            if not data.get('substitute_for'):
                errors.append("Substitute teacher must be specified when is_substitute is True")
        
        if data.get('substitute_for'):
            if not data.get('is_substitute'):
                errors.append("is_substitute must be True when substitute_for is specified")
            
            # Validate substitute_for teacher exists
            try:
                Teacher.objects.get(id=data['substitute_for'])
            except Teacher.DoesNotExist:
                errors.append(f"Substitute teacher with ID '{data['substitute_for']}' not found")
        
        return errors
    
    @staticmethod
    def record_attendance(data: Dict) -> TeacherAttendance:
        """
        Record teacher attendance with validation.
        
        Args:
            data: Dictionary containing attendance data with keys:
                - teacher_id (UUID, required): Teacher's ID
                - date (date, required): Attendance date
                - jp_number (int, required): JP number (1-10)
                - status (str, required): Attendance status (HADIR, SAKIT, IZIN, CUTI, DINAS, ALPA)
                - schedule_id (UUID, optional): Associated schedule ID
                - notes (str, optional): Additional notes
                - is_substitute (bool, optional): Whether this is substitute teaching
                - substitute_for (UUID, optional): Teacher being substituted
                - recorded_by (User, optional): User recording the attendance
                - latitude (float, optional): Latitude for location validation
                - longitude (float, optional): Longitude for location validation
                
        Returns:
            TeacherAttendance: The created attendance record
            
        Raises:
            TeacherAttendanceServiceError: If validation fails or creation error occurs
            
        Example:
            >>> from datetime import date
            >>> attendance_data = {
            ...     'teacher_id': UUID('...'),
            ...     'date': date(2024, 1, 20),
            ...     'jp_number': 1,
            ...     'status': 'HADIR',
            ...     'latitude': -7.7956,
            ...     'longitude': 110.3695
            ... }
            >>> attendance = TeacherAttendanceService.record_attendance(attendance_data)
            >>> print(f"Recorded: {attendance}")
        """
        # Get user from data or None
        user = data.get('recorded_by')
        
        # Validate data
        errors = TeacherAttendanceService._validate_attendance_data(data, user)
        if errors:
            raise TeacherAttendanceServiceError(f"Validation errors: {', '.join(errors)}")
        
        try:
            # Get teacher
            teacher = Teacher.objects.get(id=data['teacher_id'])
            
            # Get schedule if provided
            schedule = None
            if data.get('schedule_id'):
                try:
                    schedule = TeacherSchedule.objects.get(id=data['schedule_id'])
                except TeacherSchedule.DoesNotExist:
                    raise TeacherAttendanceServiceError(f"Schedule with ID '{data['schedule_id']}' not found")
            
            # Get substitute_for teacher if provided
            substitute_for = None
            if data.get('substitute_for'):
                substitute_for = Teacher.objects.get(id=data['substitute_for'])
            
            # Validate and set location
            is_location_valid = False
            latitude = None
            longitude = None
            
            if data.get('latitude') is not None and data.get('longitude') is not None:
                latitude = Decimal(str(data['latitude']))
                longitude = Decimal(str(data['longitude']))
                is_location_valid = TeacherAttendanceService.validate_location(
                    float(latitude), float(longitude)
                )
            
            # Check for duplicate attendance
            existing = TeacherAttendance.objects.filter(
                teacher=teacher,
                date=data['date'],
                jp_number=data['jp_number']
            ).first()
            
            if existing:
                # If attendance already exists, update it instead of creating new
                existing.status = data['status']
                existing.notes = data.get('notes', '')
                existing.schedule = schedule
                existing.is_substitute = data.get('is_substitute', False)
                existing.substitute_for = substitute_for
                existing.recorded_by = user
                
                # Update location if provided
                if latitude is not None and longitude is not None:
                    existing.latitude = latitude
                    existing.longitude = longitude
                    existing.is_location_valid = is_location_valid
                
                existing.save()
                return existing
            
            # Create attendance record
            attendance = TeacherAttendance.objects.create(
                teacher=teacher,
                schedule=schedule,
                date=data['date'],
                jp_number=data['jp_number'],
                status=data['status'],
                notes=data.get('notes', ''),
                is_substitute=data.get('is_substitute', False),
                substitute_for=substitute_for,
                recorded_by=user,
                latitude=latitude,
                longitude=longitude,
                is_location_valid=is_location_valid
            )
            
            return attendance
            
        except Teacher.DoesNotExist:
            raise TeacherAttendanceServiceError(f"Teacher with ID '{data['teacher_id']}' not found")
        except DjangoValidationError as e:
            raise TeacherAttendanceServiceError(f"Validation error: {e}")
        except Exception as e:
            raise TeacherAttendanceServiceError(f"Error recording attendance: {e}")
    
    @staticmethod
    def update_attendance(attendance_id: UUID, data: Dict) -> TeacherAttendance:
        """
        Update existing teacher attendance record.
        
        Args:
            attendance_id: UUID of the attendance record to update
            data: Dictionary containing fields to update (same keys as record_attendance)
            
        Returns:
            TeacherAttendance: The updated attendance record
            
        Raises:
            TeacherAttendanceServiceError: If attendance not found or validation fails
            
        Example:
            >>> attendance_id = UUID('...')
            >>> updates = {'status': 'SAKIT', 'notes': 'Demam tinggi'}
            >>> attendance = TeacherAttendanceService.update_attendance(attendance_id, updates)
            >>> print(f"Updated: {attendance.status}")
        """
        try:
            attendance = TeacherAttendance.objects.get(id=attendance_id)
        except TeacherAttendance.DoesNotExist:
            raise TeacherAttendanceServiceError(f"Attendance with ID '{attendance_id}' not found")
        
        # Get user from data or None
        user = data.get('recorded_by')
        
        # Validate update data (skip required field checks)
        validation_data = data.copy()
        validation_data['teacher_id'] = str(attendance.teacher_id)
        validation_data['date'] = data.get('date', attendance.date)
        validation_data['jp_number'] = data.get('jp_number', attendance.jp_number)
        validation_data['status'] = data.get('status', attendance.status)
        
        errors = TeacherAttendanceService._validate_attendance_data(validation_data, user)
        if errors:
            raise TeacherAttendanceServiceError(f"Validation errors: {', '.join(errors)}")
        
        try:
            # Update fields
            if 'status' in data:
                attendance.status = data['status']
            
            if 'notes' in data:
                attendance.notes = data['notes']
            
            if 'is_substitute' in data:
                attendance.is_substitute = data['is_substitute']
            
            if 'substitute_for' in data:
                if data['substitute_for']:
                    attendance.substitute_for = Teacher.objects.get(id=data['substitute_for'])
                else:
                    attendance.substitute_for = None
            
            if 'schedule_id' in data:
                if data['schedule_id']:
                    attendance.schedule = TeacherSchedule.objects.get(id=data['schedule_id'])
                else:
                    attendance.schedule = None
            
            # Update location if provided
            if 'latitude' in data and 'longitude' in data:
                if data['latitude'] is not None and data['longitude'] is not None:
                    attendance.latitude = Decimal(str(data['latitude']))
                    attendance.longitude = Decimal(str(data['longitude']))
                    attendance.is_location_valid = TeacherAttendanceService.validate_location(
                        float(attendance.latitude), float(attendance.longitude)
                    )
                else:
                    attendance.latitude = None
                    attendance.longitude = None
                    attendance.is_location_valid = False
            
            # Validate and save
            attendance.full_clean()
            attendance.save()
            return attendance
            
        except (Teacher.DoesNotExist, TeacherSchedule.DoesNotExist) as e:
            raise TeacherAttendanceServiceError(f"Related object not found: {e}")
        except DjangoValidationError as e:
            raise TeacherAttendanceServiceError(f"Validation error: {e}")
        except Exception as e:
            raise TeacherAttendanceServiceError(f"Error updating attendance: {e}")
    
    @staticmethod
    def get_daily_attendance(target_date: date) -> List[TeacherAttendance]:
        """
        Get all teacher attendance records for a specific date.
        
        Args:
            target_date: Date to get attendance for
            
        Returns:
            List of TeacherAttendance instances for that date, ordered by teacher name and JP
            
        Example:
            >>> from datetime import date
            >>> attendances = TeacherAttendanceService.get_daily_attendance(date(2024, 1, 20))
            >>> for att in attendances:
            ...     print(f"{att.teacher.full_name} - JP{att.jp_number} - {att.status}")
        """
        attendances = TeacherAttendance.objects.filter(
            date=target_date
        ).select_related(
            'teacher', 'schedule', 'schedule__subject', 'schedule__classroom', 'recorded_by'
        ).order_by('teacher__full_name', 'jp_number')
        
        return list(attendances)
    
    @staticmethod
    def get_teacher_attendance_history(
        teacher_id: UUID,
        start_date: date,
        end_date: date
    ) -> List[TeacherAttendance]:
        """
        Get attendance history for a teacher within a date range.
        
        Args:
            teacher_id: UUID of the teacher
            start_date: Start date of the range (inclusive)
            end_date: End date of the range (inclusive)
            
        Returns:
            List of TeacherAttendance instances within the date range, ordered by date and JP
            
        Raises:
            TeacherAttendanceServiceError: If teacher not found or invalid date range
            
        Example:
            >>> from datetime import date
            >>> teacher_id = UUID('...')
            >>> history = TeacherAttendanceService.get_teacher_attendance_history(
            ...     teacher_id,
            ...     date(2024, 1, 1),
            ...     date(2024, 1, 31)
            ... )
            >>> print(f"Total records: {len(history)}")
        """
        # Validate teacher exists
        try:
            Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            raise TeacherAttendanceServiceError(f"Teacher with ID '{teacher_id}' not found")
        
        # Validate date range
        if start_date > end_date:
            raise TeacherAttendanceServiceError("Start date must be before or equal to end date")
        
        # Get attendance records
        attendances = TeacherAttendance.objects.filter(
            teacher_id=teacher_id,
            date__gte=start_date,
            date__lte=end_date
        ).select_related(
            'schedule', 'schedule__subject', 'schedule__classroom', 'recorded_by', 'substitute_for'
        ).order_by('date', 'jp_number')
        
        return list(attendances)
    
    @staticmethod
    def calculate_monthly_summary(teacher_id: UUID, year: int, month: int) -> Dict:
        """
        Calculate monthly attendance summary for a teacher.
        
        This method calculates attendance statistics from actual attendance records
        and optionally updates or creates a TeacherAttendanceSummary record.
        
        Args:
            teacher_id: UUID of the teacher
            year: Year (e.g., 2024)
            month: Month (1-12)
            
        Returns:
            Dictionary containing:
                - teacher: Teacher instance
                - year: Year
                - month: Month
                - total_hadir: Count of HADIR status
                - total_sakit: Count of SAKIT status
                - total_izin: Count of IZIN status
                - total_cuti: Count of CUTI status
                - total_dinas: Count of DINAS status
                - total_alpa: Count of ALPA status
                - total_jp_scheduled: Total scheduled JP (from schedules)
                - attendance_percentage: Attendance percentage
                - summary_updated: Whether summary record was created/updated
                
        Raises:
            TeacherAttendanceServiceError: If teacher not found or invalid month/year
            
        Example:
            >>> teacher_id = UUID('...')
            >>> summary = TeacherAttendanceService.calculate_monthly_summary(teacher_id, 2024, 1)
            >>> print(f"Attendance: {summary['attendance_percentage']}%")
            >>> print(f"Present: {summary['total_hadir']} JP")
        """
        # Validate month and year
        if not (1 <= month <= 12):
            raise TeacherAttendanceServiceError("Month must be between 1 and 12")
        
        if not (2020 <= year <= 2030):
            raise TeacherAttendanceServiceError("Year must be between 2020 and 2030")
        
        # Validate teacher exists
        try:
            teacher = Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            raise TeacherAttendanceServiceError(f"Teacher with ID '{teacher_id}' not found")
        
        # Calculate date range for the month
        from calendar import monthrange
        _, last_day = monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        
        # Get all attendance records for the month
        attendances = TeacherAttendance.objects.filter(
            teacher=teacher,
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
        
        # Calculate total scheduled JP for the month
        # Get all active schedules for the teacher
        schedules = TeacherSchedule.objects.filter(
            teacher=teacher,
            is_active=True,
            effective_date__lte=end_date
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=start_date)
        )
        
        # Count total JP based on schedules and actual school days in the month
        total_jp_scheduled = 0
        current_date = start_date
        while current_date <= end_date:
            day_of_week = current_date.weekday()
            day_schedules = schedules.filter(day_of_week=day_of_week)
            for schedule in day_schedules:
                total_jp_scheduled += (schedule.jp_end - schedule.jp_start + 1)
            current_date += timedelta(days=1)
        
        # Calculate attendance percentage
        if total_jp_scheduled > 0:
            attendance_percentage = round((total_hadir / total_jp_scheduled) * 100, 2)
        else:
            attendance_percentage = 0.0
        
        # Update or create summary record
        summary, created = TeacherAttendanceSummary.objects.update_or_create(
            teacher=teacher,
            year=year,
            month=month,
            defaults={
                'total_hadir': total_hadir,
                'total_sakit': total_sakit,
                'total_izin': total_izin,
                'total_cuti': total_cuti,
                'total_dinas': total_dinas,
                'total_alpa': total_alpa,
                'total_jp_scheduled': total_jp_scheduled,
                'attendance_percentage': attendance_percentage,
            }
        )
        
        return {
            'teacher': teacher,
            'year': year,
            'month': month,
            'total_hadir': total_hadir,
            'total_sakit': total_sakit,
            'total_izin': total_izin,
            'total_cuti': total_cuti,
            'total_dinas': total_dinas,
            'total_alpa': total_alpa,
            'total_jp_scheduled': total_jp_scheduled,
            'attendance_percentage': attendance_percentage,
            'summary_updated': True,
            'summary_created': created,
        }
    
    @staticmethod
    def get_absent_teachers(target_date: date, jp_number: int) -> List[Dict]:
        """
        Get list of teachers who are absent (not present) for a specific JP on a date.
        
        This method finds teachers who have schedules for the given date and JP
        but either have no attendance record or have a non-HADIR status.
        
        Args:
            target_date: Date to check
            jp_number: JP number (1-10)
            
        Returns:
            List of dictionaries containing:
                - teacher: Teacher instance
                - schedule: TeacherSchedule instance
                - attendance: TeacherAttendance instance (if exists)
                - status: Attendance status or 'NOT_RECORDED'
                - subject: Subject name
                - classroom: Classroom name
                
        Raises:
            TeacherAttendanceServiceError: If invalid JP number
            
        Example:
            >>> from datetime import date
            >>> absent = TeacherAttendanceService.get_absent_teachers(date(2024, 1, 20), 1)
            >>> for item in absent:
            ...     print(f"{item['teacher'].full_name} - {item['status']} - {item['subject']}")
        """
        # Validate JP number
        if not (1 <= jp_number <= 10):
            raise TeacherAttendanceServiceError("JP number must be between 1 and 10")
        
        # Get day of week for the date
        day_of_week = target_date.weekday()
        
        # Get all active schedules for this day and JP
        schedules = TeacherSchedule.objects.filter(
            day_of_week=day_of_week,
            jp_start__lte=jp_number,
            jp_end__gte=jp_number,
            is_active=True,
            effective_date__lte=target_date
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=target_date)
        ).select_related(
            'teacher', 'subject', 'classroom'
        ).filter(
            teacher__is_active=True
        )
        
        absent_teachers = []
        
        for schedule in schedules:
            # Check if attendance record exists
            attendance = TeacherAttendance.objects.filter(
                teacher=schedule.teacher,
                date=target_date,
                jp_number=jp_number
            ).first()
            
            # Include if no attendance or non-HADIR status
            if not attendance or attendance.status != 'HADIR':
                absent_teachers.append({
                    'teacher': schedule.teacher,
                    'schedule': schedule,
                    'attendance': attendance,
                    'status': attendance.status if attendance else 'NOT_RECORDED',
                    'subject': schedule.subject.name,
                    'classroom': schedule.classroom.name,
                })
        
        return absent_teachers
    
    @staticmethod
    @transaction.atomic
    def bulk_record_attendance(
        attendance_data: List[Dict],
        user: User
    ) -> Tuple[List[TeacherAttendance], List[Dict]]:
        """
        Record multiple teacher attendance records at once.
        
        This method processes multiple attendance records in a single transaction.
        If any record fails validation, the entire operation is rolled back.
        
        Args:
            attendance_data: List of attendance data dictionaries (same format as record_attendance)
            user: User recording the attendance
            
        Returns:
            Tuple containing:
                - List of successfully created TeacherAttendance instances
                - List of error dictionaries with keys:
                    - index: Index in the input list
                    - data: Original data
                    - error: Error message
                
        Example:
            >>> from datetime import date
            >>> from django.contrib.auth.models import User
            >>> user = User.objects.get(username='admin')
            >>> attendance_list = [
            ...     {'teacher_id': UUID('...'), 'date': date(2024, 1, 20), 'jp_number': 1, 'status': 'HADIR'},
            ...     {'teacher_id': UUID('...'), 'date': date(2024, 1, 20), 'jp_number': 2, 'status': 'HADIR'},
            ... ]
            >>> created, errors = TeacherAttendanceService.bulk_record_attendance(attendance_list, user)
            >>> print(f"Created: {len(created)}, Errors: {len(errors)}")
        """
        created_attendances = []
        errors = []
        
        for index, data in enumerate(attendance_data):
            try:
                # Add user to data
                data['recorded_by'] = user
                
                # Record attendance
                attendance = TeacherAttendanceService.record_attendance(data)
                created_attendances.append(attendance)
                
            except TeacherAttendanceServiceError as e:
                errors.append({
                    'index': index,
                    'data': data,
                    'error': str(e)
                })
            except Exception as e:
                errors.append({
                    'index': index,
                    'data': data,
                    'error': f"Unexpected error: {str(e)}"
                })
        
        return created_attendances, errors
