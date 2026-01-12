"""
Schedule Service Layer
Handles all business logic related to day schedule and JP (Jam Pelajaran) management
"""
from typing import List, Optional
from datetime import date
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from ..models import DaySchedule


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
