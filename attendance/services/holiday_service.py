"""
Holiday Service Layer
Handles all business logic related to holiday management
"""
from typing import List, Dict, Optional
from datetime import date
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from ..models import Holiday, Classroom


class HolidayService:
    """Service class for holiday-related business operations"""
    
    @staticmethod
    def is_holiday(target_date: date, classroom: Classroom = None) -> bool:
        """
        Check if a specific date is a holiday.
        
        Args:
            target_date: The date to check
            classroom: Optional classroom to check for classroom-specific holidays
            
        Returns:
            bool: True if it's a holiday, False otherwise
            
        Note:
            A date is a holiday if:
            - A holiday exists with apply_to_all=True for that date, OR
            - A holiday exists for that date with the specific classroom in its classrooms relation
        """
        # Check for global holidays (apply_to_all=True)
        global_holiday = Holiday.objects.filter(
            date=target_date,
            apply_to_all=True
        ).exists()
        
        if global_holiday:
            return True
        
        # If classroom is specified, check for classroom-specific holidays
        if classroom is not None:
            classroom_holiday = Holiday.objects.filter(
                date=target_date,
                apply_to_all=False,
                classrooms=classroom
            ).exists()
            
            if classroom_holiday:
                return True
        
        return False
    
    @staticmethod
    def get_holidays(
        start_date: date,
        end_date: date,
        classroom: Classroom = None
    ) -> List[Holiday]:
        """
        Get all holidays within a date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            classroom: Optional classroom to filter classroom-specific holidays
            
        Returns:
            List of Holiday records
        """
        queryset = Holiday.objects.filter(
            date__range=[start_date, end_date]
        )
        
        if classroom is not None:
            # Get global holidays OR classroom-specific holidays
            queryset = queryset.filter(
                Q(apply_to_all=True) |
                Q(classrooms=classroom)
            )
        
        return list(queryset.order_by('date').distinct())
    
    @staticmethod
    def get_holidays_for_classroom(
        classroom: Classroom,
        start_date: date,
        end_date: date
    ) -> List[Holiday]:
        """
        Get all holidays that apply to a specific classroom within a date range.
        
        Args:
            classroom: The classroom to get holidays for
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of Holiday records that apply to the classroom
        """
        return list(
            Holiday.objects.filter(
                date__range=[start_date, end_date]
            ).filter(
                Q(apply_to_all=True) |
                Q(classrooms=classroom)
            ).order_by('date').distinct()
        )
    
    @staticmethod
    def create_holiday(
        data: Dict,
        user: User = None
    ) -> Holiday:
        """
        Create a new holiday.
        
        Args:
            data: Dict containing holiday data:
                - date: date (required)
                - name: str (required)
                - holiday_type: str (required, one of UAS, UN, PESANTREN, LAINNYA)
                - apply_to_all: bool (default True)
                - classroom_ids: List[str] (optional, required if apply_to_all=False)
                - description: str (optional)
            user: User creating the holiday
            
        Returns:
            Created Holiday record
            
        Raises:
            ValidationError: If required fields are missing or invalid
        """
        # Validate required fields
        required_fields = ['date', 'name', 'holiday_type']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Field '{field}' is required")
        
        # Validate holiday_type
        valid_types = [choice[0] for choice in Holiday.HOLIDAY_TYPES]
        if data['holiday_type'] not in valid_types:
            raise ValidationError(
                f"Invalid holiday type '{data['holiday_type']}'. "
                f"Valid types: {', '.join(valid_types)}"
            )
        
        apply_to_all = data.get('apply_to_all', True)
        classroom_ids = data.get('classroom_ids', [])
        
        # Validate classroom_ids if apply_to_all is False
        if not apply_to_all and not classroom_ids:
            raise ValidationError(
                "At least one classroom must be selected when 'apply_to_all' is False"
            )
        
        # Create holiday
        holiday = Holiday(
            date=data['date'],
            name=data['name'],
            holiday_type=data['holiday_type'],
            apply_to_all=apply_to_all,
            description=data.get('description', '')
        )
        
        if user:
            holiday.created_by = user
            holiday.updated_by = user
        
        holiday.save()
        
        # Add classrooms if not apply_to_all
        if not apply_to_all and classroom_ids:
            classrooms = Classroom.objects.filter(id__in=classroom_ids)
            holiday.classrooms.set(classrooms)
        
        return holiday
    
    @staticmethod
    def update_holiday(
        holiday: Holiday,
        data: Dict,
        user: User = None
    ) -> Holiday:
        """
        Update an existing holiday.
        
        Args:
            holiday: The Holiday to update
            data: Dict containing fields to update
            user: User updating the holiday
            
        Returns:
            Updated Holiday record
        """
        # Update basic fields
        if 'name' in data:
            holiday.name = data['name']
        if 'holiday_type' in data:
            # Validate holiday_type
            valid_types = [choice[0] for choice in Holiday.HOLIDAY_TYPES]
            if data['holiday_type'] not in valid_types:
                raise ValidationError(
                    f"Invalid holiday type '{data['holiday_type']}'"
                )
            holiday.holiday_type = data['holiday_type']
        if 'date' in data:
            holiday.date = data['date']
        if 'description' in data:
            holiday.description = data['description']
        if 'apply_to_all' in data:
            holiday.apply_to_all = data['apply_to_all']
        
        if user:
            holiday.updated_by = user
        
        holiday.save()
        
        # Update classrooms if provided
        if 'classroom_ids' in data:
            if holiday.apply_to_all:
                holiday.classrooms.clear()
            else:
                classrooms = Classroom.objects.filter(id__in=data['classroom_ids'])
                holiday.classrooms.set(classrooms)
        
        return holiday
    
    @staticmethod
    def delete_holiday(holiday: Holiday) -> bool:
        """
        Delete a holiday.
        
        Args:
            holiday: The Holiday to delete
            
        Returns:
            bool: True if deleted successfully
        """
        holiday.delete()
        return True
    
    @staticmethod
    def get_holiday_by_date(target_date: date) -> Optional[Holiday]:
        """
        Get the first holiday for a specific date (global holidays first).
        
        Args:
            target_date: The date to get holiday for
            
        Returns:
            Holiday or None if no holiday on that date
        """
        # Try global holiday first
        holiday = Holiday.objects.filter(
            date=target_date,
            apply_to_all=True
        ).first()
        
        if holiday:
            return holiday
        
        # Return any classroom-specific holiday
        return Holiday.objects.filter(date=target_date).first()
    
    @staticmethod
    def get_all_holidays() -> List[Holiday]:
        """
        Get all holidays ordered by date descending.
        
        Returns:
            List of all Holiday records
        """
        return list(Holiday.objects.all().order_by('-date'))
