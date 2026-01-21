"""
Schedule Service Layer
Handles all business logic related to day schedule and JP (Jam Pelajaran) management
Also handles teacher schedule management with conflict detection
"""
from typing import List, Optional, Dict, Any
from datetime import date
from uuid import UUID
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q, Count, Sum, Case, When, IntegerField

from ..models import DaySchedule, TeacherSchedule, Teacher, Subject, Classroom


class ScheduleService:
    """Service class for schedule-related business operations"""
    
    @staticmethod
    def get_jp_count_for_date(target_date: date) -> int:
        """
        Get the JP count for a specific date based on day of week.
        
        Args:
            target_date: The date to get JP count for
            
        Returns:
            int: Number of JP slots for that day
            
        Note:
            Python's weekday() returns 0=Monday, 6=Sunday
            Our DaySchedule uses 0=Senin (Monday), 6=Minggu (Sunday)
        """
        day_of_week = target_date.weekday()  # 0=Monday, 6=Sunday
        
        try:
            schedule = DaySchedule.objects.get(day_of_week=day_of_week)
            return schedule.default_jp_count
        except DaySchedule.DoesNotExist:
            # Default to 6 JP if schedule not found
            return 6
    
    @staticmethod
    def get_day_schedule(day_of_week: int) -> Optional[DaySchedule]:
        """
        Get the DaySchedule for a specific day of week.
        
        Args:
            day_of_week: Day of week (0=Senin/Monday, 6=Minggu/Sunday)
            
        Returns:
            DaySchedule or None if not found
        """
        try:
            return DaySchedule.objects.get(day_of_week=day_of_week)
        except DaySchedule.DoesNotExist:
            return None
    
    @staticmethod
    def get_all_schedules() -> List[DaySchedule]:
        """
        Get all day schedules ordered by day of week.
        
        Returns:
            List of all DaySchedule records
        """
        return list(DaySchedule.objects.all().order_by('day_of_week'))
    
    @staticmethod
    def update_schedule(
        day_of_week: int, 
        jp_count: int, 
        user: User = None,
        is_school_day: bool = None
    ) -> DaySchedule:
        """
        Update the JP count for a specific day of week.
        
        Args:
            day_of_week: Day of week (0=Senin/Monday, 6=Minggu/Sunday)
            jp_count: New JP count (must be 1-10)
            user: User making the update (optional)
            is_school_day: Whether this is a school day (optional)
            
        Returns:
            Updated DaySchedule
            
        Raises:
            ValidationError: If jp_count is outside valid range
            DaySchedule.DoesNotExist: If day_of_week not found
        """
        # Validate jp_count range
        if jp_count < 1 or jp_count > 10:
            raise ValidationError(
                f'JP count must be between 1 and 10, got {jp_count}'
            )
        
        schedule = DaySchedule.objects.get(day_of_week=day_of_week)
        schedule.default_jp_count = jp_count
        
        if user is not None:
            schedule.updated_by = user
            
        if is_school_day is not None:
            schedule.is_school_day = is_school_day
        
        schedule.save()
        return schedule
    
    @staticmethod
    def is_school_day(target_date: date) -> bool:
        """
        Check if a specific date is a school day based on DaySchedule.
        
        Args:
            target_date: The date to check
            
        Returns:
            bool: True if it's a school day, False otherwise
        """
        day_of_week = target_date.weekday()
        
        try:
            schedule = DaySchedule.objects.get(day_of_week=day_of_week)
            return schedule.is_school_day
        except DaySchedule.DoesNotExist:
            # Default: weekdays are school days, Sunday is not
            return day_of_week != 6
    
    @staticmethod
    def get_schedule_for_date(target_date: date) -> Optional[DaySchedule]:
        """
        Get the DaySchedule for a specific date.
        
        Args:
            target_date: The date to get schedule for
            
        Returns:
            DaySchedule or None if not found
        """
        day_of_week = target_date.weekday()
        return ScheduleService.get_day_schedule(day_of_week)



class TeacherScheduleService:
    """Service class for teacher schedule-related business operations"""
    
    @staticmethod
    def create_schedule(data: Dict[str, Any]) -> TeacherSchedule:
        """
        Create a new teacher schedule with validation and conflict detection.
        
        Args:
            data: Dictionary containing schedule data with keys:
                - teacher_id: UUID of the teacher
                - subject_id: UUID of the subject
                - classroom_id: UUID of the classroom
                - day_of_week: Integer (0-6, 0=Monday)
                - jp_start: Integer (1-10)
                - jp_end: Integer (1-10)
                - room_number: String (optional)
                - notes: String (optional)
                - effective_date: Date object
                - end_date: Date object (optional)
                - is_active: Boolean (default True)
        
        Returns:
            TeacherSchedule: The created schedule instance
            
        Raises:
            ValidationError: If validation fails or conflicts are detected
            ObjectDoesNotExist: If referenced objects don't exist
        """
        try:
            # Fetch related objects
            teacher = Teacher.objects.get(id=data['teacher_id'])
            subject = Subject.objects.get(id=data['subject_id'])
            classroom = Classroom.objects.get(id=data['classroom_id'])
            
            # Create schedule instance
            schedule = TeacherSchedule(
                teacher=teacher,
                subject=subject,
                classroom=classroom,
                day_of_week=data['day_of_week'],
                jp_start=data['jp_start'],
                jp_end=data['jp_end'],
                room_number=data.get('room_number', ''),
                notes=data.get('notes', ''),
                effective_date=data['effective_date'],
                end_date=data.get('end_date'),
                is_active=data.get('is_active', True)
            )
            
            # Validate and save (clean() will be called automatically)
            schedule.full_clean()
            schedule.save()
            
            return schedule
            
        except Teacher.DoesNotExist:
            raise ObjectDoesNotExist(f"Teacher with id {data.get('teacher_id')} not found")
        except Subject.DoesNotExist:
            raise ObjectDoesNotExist(f"Subject with id {data.get('subject_id')} not found")
        except Classroom.DoesNotExist:
            raise ObjectDoesNotExist(f"Classroom with id {data.get('classroom_id')} not found")
    
    @staticmethod
    def detect_conflicts(
        teacher_id: UUID,
        day: int,
        jp_start: int,
        jp_end: int,
        effective_date: date = None,
        end_date: date = None,
        exclude_schedule_id: UUID = None,
        classroom_id: UUID = None
    ) -> List[Dict[str, Any]]:
        """
        Detect scheduling conflicts for a teacher and/or classroom.
        
        Args:
            teacher_id: UUID of the teacher
            day: Day of week (0-6, 0=Monday)
            jp_start: Starting JP (1-10)
            jp_end: Ending JP (1-10)
            effective_date: Effective date for the schedule (optional)
            end_date: End date for the schedule (optional)
            exclude_schedule_id: Schedule ID to exclude from conflict check (for updates)
            classroom_id: UUID of classroom to check for conflicts (optional)
            
        Returns:
            List of conflict dictionaries with keys:
                - type: 'teacher' or 'classroom'
                - schedule: TeacherSchedule instance
                - message: Human-readable conflict description
        """
        conflicts = []
        
        # Use today's date if effective_date not provided
        if effective_date is None:
            effective_date = date.today()
        
        # Build base query for teacher conflicts
        teacher_query = TeacherSchedule.objects.filter(
            teacher_id=teacher_id,
            day_of_week=day,
            is_active=True,
            effective_date__lte=effective_date
        )
        
        # Exclude specific schedule if provided (for updates)
        if exclude_schedule_id:
            teacher_query = teacher_query.exclude(id=exclude_schedule_id)
        
        # Filter by date range overlap
        if end_date:
            teacher_query = teacher_query.filter(
                Q(end_date__isnull=True) | Q(end_date__gte=effective_date)
            )
        
        # Check for JP overlap with teacher schedules
        for schedule in teacher_query.select_related('teacher', 'subject', 'classroom'):
            # Check if JP ranges overlap: not (end < start or start > end)
            if not (jp_end < schedule.jp_start or jp_start > schedule.jp_end):
                day_name = dict(TeacherSchedule.DAY_CHOICES).get(day, 'Unknown')
                conflicts.append({
                    'type': 'teacher',
                    'schedule': schedule,
                    'message': (
                        f"Teacher {schedule.teacher.full_name} already has a schedule on {day_name} "
                        f"from JP {schedule.jp_start} to {schedule.jp_end} "
                        f"({schedule.subject.name} in {schedule.classroom.name})"
                    )
                })
        
        # Check classroom conflicts if classroom_id provided
        if classroom_id:
            classroom_query = TeacherSchedule.objects.filter(
                classroom_id=classroom_id,
                day_of_week=day,
                is_active=True,
                effective_date__lte=effective_date
            )
            
            # Exclude specific schedule if provided
            if exclude_schedule_id:
                classroom_query = classroom_query.exclude(id=exclude_schedule_id)
            
            # Filter by date range overlap
            if end_date:
                classroom_query = classroom_query.filter(
                    Q(end_date__isnull=True) | Q(end_date__gte=effective_date)
                )
            
            # Check for JP overlap with classroom schedules
            for schedule in classroom_query.select_related('teacher', 'subject', 'classroom'):
                # Check if JP ranges overlap
                if not (jp_end < schedule.jp_start or jp_start > schedule.jp_end):
                    day_name = dict(TeacherSchedule.DAY_CHOICES).get(day, 'Unknown')
                    conflicts.append({
                        'type': 'classroom',
                        'schedule': schedule,
                        'message': (
                            f"Classroom {schedule.classroom.name} is already scheduled on {day_name} "
                            f"from JP {schedule.jp_start} to {schedule.jp_end} "
                            f"with {schedule.teacher.full_name} ({schedule.subject.name})"
                        )
                    })
        
        return conflicts
    
    @staticmethod
    def get_weekly_schedule(teacher_id: UUID) -> Dict[int, List[TeacherSchedule]]:
        """
        Get a teacher's complete weekly schedule organized by day.
        
        Args:
            teacher_id: UUID of the teacher
            
        Returns:
            Dictionary with day_of_week as keys (0-6) and lists of schedules as values
            Example: {0: [schedule1, schedule2], 1: [schedule3], ...}
            
        Raises:
            ObjectDoesNotExist: If teacher not found
        """
        # Verify teacher exists
        if not Teacher.objects.filter(id=teacher_id).exists():
            raise ObjectDoesNotExist(f"Teacher with id {teacher_id} not found")
        
        # Get all active schedules for the teacher
        schedules = TeacherSchedule.objects.filter(
            teacher_id=teacher_id,
            is_active=True,
            effective_date__lte=date.today()
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=date.today())
        ).select_related(
            'subject', 'classroom'
        ).order_by('day_of_week', 'jp_start')
        
        # Organize by day of week
        weekly_schedule = {day: [] for day in range(7)}
        for schedule in schedules:
            weekly_schedule[schedule.day_of_week].append(schedule)
        
        return weekly_schedule
    
    @staticmethod
    def get_classroom_schedule(classroom_id: UUID, day: int) -> List[TeacherSchedule]:
        """
        Get all teacher schedules for a specific classroom on a specific day.
        
        Args:
            classroom_id: UUID of the classroom
            day: Day of week (0-6, 0=Monday)
            
        Returns:
            List of TeacherSchedule instances for that classroom and day
            
        Raises:
            ObjectDoesNotExist: If classroom not found
        """
        # Verify classroom exists
        if not Classroom.objects.filter(id=classroom_id).exists():
            raise ObjectDoesNotExist(f"Classroom with id {classroom_id} not found")
        
        # Get all active schedules for the classroom on the specified day
        schedules = TeacherSchedule.objects.filter(
            classroom_id=classroom_id,
            day_of_week=day,
            is_active=True,
            effective_date__lte=date.today()
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=date.today())
        ).select_related(
            'teacher', 'subject'
        ).order_by('jp_start')
        
        return list(schedules)
    
    @staticmethod
    @transaction.atomic
    def bulk_create_schedules(schedules: List[Dict[str, Any]]) -> List[TeacherSchedule]:
        """
        Create multiple teacher schedules at once with validation.
        
        Args:
            schedules: List of schedule data dictionaries (same format as create_schedule)
            
        Returns:
            List of created TeacherSchedule instances
            
        Raises:
            ValidationError: If any schedule validation fails
            
        Note:
            This operation is atomic - if any schedule fails, all are rolled back
        """
        created_schedules = []
        
        for schedule_data in schedules:
            try:
                schedule = TeacherScheduleService.create_schedule(schedule_data)
                created_schedules.append(schedule)
            except (ValidationError, ObjectDoesNotExist) as e:
                # Re-raise with context about which schedule failed
                raise ValidationError(
                    f"Failed to create schedule for teacher {schedule_data.get('teacher_id')}: {str(e)}"
                )
        
        return created_schedules
    
    @staticmethod
    def update_schedule(schedule_id: UUID, data: Dict[str, Any]) -> TeacherSchedule:
        """
        Update an existing teacher schedule with validation.
        
        Args:
            schedule_id: UUID of the schedule to update
            data: Dictionary containing fields to update (same keys as create_schedule)
            
        Returns:
            TeacherSchedule: The updated schedule instance
            
        Raises:
            ObjectDoesNotExist: If schedule not found
            ValidationError: If validation fails or conflicts are detected
        """
        try:
            schedule = TeacherSchedule.objects.get(id=schedule_id)
            
            # Update foreign key fields if provided
            if 'teacher_id' in data:
                schedule.teacher = Teacher.objects.get(id=data['teacher_id'])
            if 'subject_id' in data:
                schedule.subject = Subject.objects.get(id=data['subject_id'])
            if 'classroom_id' in data:
                schedule.classroom = Classroom.objects.get(id=data['classroom_id'])
            
            # Update other fields if provided
            if 'day_of_week' in data:
                schedule.day_of_week = data['day_of_week']
            if 'jp_start' in data:
                schedule.jp_start = data['jp_start']
            if 'jp_end' in data:
                schedule.jp_end = data['jp_end']
            if 'room_number' in data:
                schedule.room_number = data['room_number']
            if 'notes' in data:
                schedule.notes = data['notes']
            if 'effective_date' in data:
                schedule.effective_date = data['effective_date']
            if 'end_date' in data:
                schedule.end_date = data['end_date']
            if 'is_active' in data:
                schedule.is_active = data['is_active']
            
            # Validate and save
            schedule.full_clean()
            schedule.save()
            
            return schedule
            
        except TeacherSchedule.DoesNotExist:
            raise ObjectDoesNotExist(f"Schedule with id {schedule_id} not found")
        except Teacher.DoesNotExist:
            raise ObjectDoesNotExist(f"Teacher with id {data.get('teacher_id')} not found")
        except Subject.DoesNotExist:
            raise ObjectDoesNotExist(f"Subject with id {data.get('subject_id')} not found")
        except Classroom.DoesNotExist:
            raise ObjectDoesNotExist(f"Classroom with id {data.get('classroom_id')} not found")
    
    @staticmethod
    def delete_schedule(schedule_id: UUID) -> bool:
        """
        Delete (soft delete by setting is_active=False) a teacher schedule.
        
        Args:
            schedule_id: UUID of the schedule to delete
            
        Returns:
            bool: True if successfully deleted, False otherwise
            
        Raises:
            ObjectDoesNotExist: If schedule not found
        """
        try:
            schedule = TeacherSchedule.objects.get(id=schedule_id)
            schedule.is_active = False
            schedule.save()
            return True
        except TeacherSchedule.DoesNotExist:
            raise ObjectDoesNotExist(f"Schedule with id {schedule_id} not found")
    
    @staticmethod
    def get_teacher_teaching_load(teacher_id: UUID) -> Dict[str, Any]:
        """
        Calculate a teacher's teaching load statistics.
        
        Args:
            teacher_id: UUID of the teacher
            
        Returns:
            Dictionary containing:
                - total_jp_per_week: Total JP count per week
                - schedules_count: Number of active schedules
                - subjects: List of subjects taught with JP counts
                - classrooms: List of classrooms taught with JP counts
                - by_day: JP count breakdown by day of week
                
        Raises:
            ObjectDoesNotExist: If teacher not found
        """
        # Verify teacher exists
        teacher = Teacher.objects.filter(id=teacher_id).first()
        if not teacher:
            raise ObjectDoesNotExist(f"Teacher with id {teacher_id} not found")
        
        # Get all active schedules
        schedules = TeacherSchedule.objects.filter(
            teacher_id=teacher_id,
            is_active=True,
            effective_date__lte=date.today()
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=date.today())
        ).select_related('subject', 'classroom')
        
        # Calculate total JP per week
        total_jp = 0
        for schedule in schedules:
            total_jp += (schedule.jp_end - schedule.jp_start + 1)
        
        # Group by subject
        subjects_dict = {}
        for schedule in schedules:
            subject_name = schedule.subject.name
            jp_count = schedule.jp_end - schedule.jp_start + 1
            if subject_name in subjects_dict:
                subjects_dict[subject_name] += jp_count
            else:
                subjects_dict[subject_name] = jp_count
        
        subjects = [
            {'name': name, 'jp_count': count}
            for name, count in subjects_dict.items()
        ]
        
        # Group by classroom
        classrooms_dict = {}
        for schedule in schedules:
            classroom_name = schedule.classroom.name
            jp_count = schedule.jp_end - schedule.jp_start + 1
            if classroom_name in classrooms_dict:
                classrooms_dict[classroom_name] += jp_count
            else:
                classrooms_dict[classroom_name] = jp_count
        
        classrooms = [
            {'name': name, 'jp_count': count}
            for name, count in classrooms_dict.items()
        ]
        
        # Group by day of week
        by_day = {day: 0 for day in range(7)}
        for schedule in schedules:
            jp_count = schedule.jp_end - schedule.jp_start + 1
            by_day[schedule.day_of_week] += jp_count
        
        # Convert to list with day names
        day_names = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        by_day_list = [
            {'day': day_names[day], 'day_number': day, 'jp_count': count}
            for day, count in by_day.items()
        ]
        
        return {
            'teacher_id': str(teacher_id),
            'teacher_name': teacher.full_name,
            'total_jp_per_week': total_jp,
            'schedules_count': schedules.count(),
            'subjects': subjects,
            'classrooms': classrooms,
            'by_day': by_day_list
        }
