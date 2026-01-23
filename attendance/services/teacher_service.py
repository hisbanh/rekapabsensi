"""
Teacher Service Layer
Handles all business logic related to teacher management
"""
from typing import List, Dict, Optional
from uuid import UUID
from django.db.models import Q, Count, Prefetch
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone

from ..models import Teacher, Subject, Classroom, TeacherAttendanceSummary, TeacherSchedule
from ..exceptions import AttendanceBaseException


class TeacherServiceError(AttendanceBaseException):
    """Exception raised by teacher service operations"""
    pass


class TeacherService:
    """Service class for teacher-related business operations"""
    
    @staticmethod
    def validate_teacher_data(data: Dict, is_update: bool = False) -> List[str]:
        """
        Validate teacher data before creation or update.
        
        Args:
            data: Dictionary containing teacher data
            is_update: Whether this is an update operation (skips required field checks)
            
        Returns:
            List of validation error messages (empty if valid)
            
        Example:
            >>> errors = TeacherService.validate_teacher_data({
            ...     'nip': '12345',
            ...     'full_name': 'Ahmad Yusuf',
            ...     'employment_date': '2024-01-01'
            ... })
            >>> if errors:
            ...     print(f"Validation failed: {errors}")
        """
        errors = []
        
        # Required fields validation (only for creation)
        if not is_update:
            required_fields = ['nip', 'full_name', 'employment_date', 'employment_status']
            for field in required_fields:
                if not data.get(field):
                    errors.append(f"Field '{field}' is required")
        
        # NIP validation
        if data.get('nip'):
            nip = str(data['nip']).upper()
            
            # Check length
            if len(nip) > 20:
                errors.append("NIP must be maximum 20 characters")
            
            # Check format (alphanumeric)
            if not nip.replace('-', '').replace('_', '').isalnum():
                errors.append("NIP must contain only alphanumeric characters (and optionally hyphens or underscores)")
            
            # Check for duplicate NIP (only for new teachers)
            if not data.get('id'):  # New teacher
                existing = Teacher.objects.filter(nip=nip).exists()
                if existing:
                    errors.append(f"Teacher with NIP '{nip}' already exists")
        
        # Full name validation
        if data.get('full_name'):
            full_name = data['full_name']
            
            # Check minimum length
            if len(full_name) < 3:
                errors.append("Full name must be at least 3 characters")
            
            # Check for numbers in name
            if any(char.isdigit() for char in full_name):
                errors.append("Teacher name should not contain numbers")
        
        # Email validation
        if data.get('email'):
            email = data['email']
            if '@' not in email or '.' not in email:
                errors.append("Invalid email format")
        
        # Employment date validation
        if data.get('employment_date'):
            try:
                from datetime import datetime, date
                
                emp_date = data['employment_date']
                if isinstance(emp_date, str):
                    emp_date = datetime.strptime(emp_date, '%Y-%m-%d').date()
                
                if emp_date > timezone.now().date():
                    errors.append("Employment date cannot be in the future")
            except (ValueError, TypeError):
                errors.append("Invalid employment date format (use YYYY-MM-DD)")
        
        # Employment status validation
        if data.get('employment_status'):
            valid_statuses = ['ACTIVE', 'LEAVE', 'INACTIVE']
            if data['employment_status'] not in valid_statuses:
                errors.append(f"Invalid employment status. Valid values: {', '.join(valid_statuses)}")
        
        # Homeroom teacher validation
        if data.get('is_homeroom_teacher'):
            if not data.get('homeroom_class'):
                errors.append("Homeroom class must be specified if teacher is a homeroom teacher")
        
        # Homeroom class validation
        if data.get('homeroom_class'):
            classroom_id = data['homeroom_class']
            if isinstance(classroom_id, str):
                try:
                    Classroom.objects.get(id=classroom_id)
                except Classroom.DoesNotExist:
                    errors.append(f"Classroom with ID '{classroom_id}' does not exist")
        
        return errors
    
    @staticmethod
    def create_teacher(data: Dict) -> Teacher:
        """
        Create a new teacher with validation.
        
        Args:
            data: Dictionary containing teacher data with keys:
                - nip (str, required): Teacher's NIP
                - full_name (str, required): Teacher's full name
                - employment_date (date, required): Employment start date
                - employment_status (str, required): Employment status
                - email (str, optional): Email address
                - phone (str, optional): Phone number
                - address (str, optional): Home address
                - photo (file, optional): Teacher photo
                - is_homeroom_teacher (bool, optional): Homeroom teacher flag
                - homeroom_class (UUID, optional): Homeroom class ID
                - is_active (bool, optional): Active status
                
        Returns:
            Teacher: The created teacher instance
            
        Raises:
            TeacherServiceError: If validation fails or creation error occurs
            
        Example:
            >>> teacher_data = {
            ...     'nip': '12345',
            ...     'full_name': 'Ahmad Yusuf',
            ...     'employment_date': date(2024, 1, 1),
            ...     'employment_status': 'ACTIVE',
            ...     'email': 'ahmad@example.com'
            ... }
            >>> teacher = TeacherService.create_teacher(teacher_data)
            >>> print(f"Created teacher: {teacher.full_name}")
        """
        # Validate data
        errors = TeacherService.validate_teacher_data(data)
        if errors:
            raise TeacherServiceError(f"Validation errors: {', '.join(errors)}")
        
        try:
            # Ensure NIP is uppercase
            if 'nip' in data:
                data['nip'] = str(data['nip']).upper()
            
            # Create teacher
            teacher = Teacher.objects.create(**data)
            return teacher
            
        except DjangoValidationError as e:
            raise TeacherServiceError(f"Validation error: {e}")
        except Exception as e:
            raise TeacherServiceError(f"Error creating teacher: {e}")
    
    @staticmethod
    def update_teacher(teacher_id: UUID, data: Dict) -> Teacher:
        """
        Update existing teacher information.
        
        Args:
            teacher_id: UUID of the teacher to update
            data: Dictionary containing fields to update
            
        Returns:
            Teacher: The updated teacher instance
            
        Raises:
            TeacherServiceError: If teacher not found or validation fails
            
        Example:
            >>> teacher_id = UUID('...')
            >>> updates = {'phone': '081234567890', 'email': 'newemail@example.com'}
            >>> teacher = TeacherService.update_teacher(teacher_id, updates)
            >>> print(f"Updated teacher: {teacher.full_name}")
        """
        try:
            teacher = Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            raise TeacherServiceError(f"Teacher with ID '{teacher_id}' not found")
        
        # Add teacher ID to data for validation (to allow NIP check to exclude current teacher)
        validation_data = data.copy()
        validation_data['id'] = teacher_id
        
        # Validate update data (pass is_update=True to skip required field checks)
        errors = TeacherService.validate_teacher_data(validation_data, is_update=True)
        if errors:
            raise TeacherServiceError(f"Validation errors: {', '.join(errors)}")
        
        try:
            # Update fields
            for field, value in data.items():
                if hasattr(teacher, field):
                    # Ensure NIP is uppercase
                    if field == 'nip' and value:
                        value = str(value).upper()
                    setattr(teacher, field, value)
            
            # Validate and save
            teacher.full_clean()
            teacher.save()
            return teacher
            
        except DjangoValidationError as e:
            raise TeacherServiceError(f"Validation error: {e}")
        except Exception as e:
            raise TeacherServiceError(f"Error updating teacher: {e}")
    
    @staticmethod
    def get_teacher_profile(teacher_id: UUID) -> Dict:
        """
        Get complete teacher profile with related data.
        
        Args:
            teacher_id: UUID of the teacher
            
        Returns:
            Dictionary containing teacher profile with:
                - teacher: Teacher instance
                - subjects: List of subjects taught
                - homeroom_class: Classroom instance if homeroom teacher
                - total_schedules: Count of active schedules
                - teaching_load: Total JP per week
                
        Raises:
            TeacherServiceError: If teacher not found
            
        Example:
            >>> teacher_id = UUID('...')
            >>> profile = TeacherService.get_teacher_profile(teacher_id)
            >>> print(f"Teacher: {profile['teacher'].full_name}")
            >>> print(f"Subjects: {[s.name for s in profile['subjects']]}")
            >>> print(f"Teaching load: {profile['teaching_load']} JP/week")
        """
        from django.db.models import Prefetch, Sum, Count
        
        try:
            # Optimized query with proper prefetch
            teacher = Teacher.objects.select_related(
                'homeroom_class',
                'homeroom_class__academic_level',
                'user'
            ).prefetch_related(
                Prefetch(
                    'subjects',
                    queryset=Subject.objects.filter(is_active=True).only('id', 'name', 'code')
                ),
                Prefetch(
                    'schedules',
                    queryset=TeacherSchedule.objects.filter(is_active=True).only(
                        'id', 'jp_start', 'jp_end', 'teacher_id'
                    )
                )
            ).get(id=teacher_id)
        except Teacher.DoesNotExist:
            raise TeacherServiceError(f"Teacher with ID '{teacher_id}' not found")
        
        # Get subjects (already prefetched)
        subjects = list(teacher.subjects.all())
        
        # Get homeroom class
        homeroom_class = teacher.homeroom_class if teacher.is_homeroom_teacher else None
        
        # Count active schedules (use aggregate for better performance)
        from django.db.models import F
        
        schedule_stats = TeacherSchedule.objects.filter(
            teacher_id=teacher_id,
            is_active=True
        ).aggregate(
            total_schedules=Count('id'),
            total_jp=Sum(F('jp_end') - F('jp_start') + 1)
        )
        
        total_schedules = schedule_stats['total_schedules'] or 0
        teaching_load = schedule_stats['total_jp'] or 0
        
        return {
            'teacher': teacher,
            'subjects': subjects,
            'homeroom_class': homeroom_class,
            'total_schedules': total_schedules,
            'teaching_load': teaching_load,
        }
    
    @staticmethod
    def assign_subjects(teacher_id: UUID, subject_ids: List) -> None:
        """
        Assign multiple subjects to a teacher.
        
        Args:
            teacher_id: UUID of the teacher
            subject_ids: List of subject UUIDs to assign
            
        Raises:
            TeacherServiceError: If teacher not found or invalid subject IDs
            
        Example:
            >>> teacher_id = UUID('...')
            >>> subject_ids = [UUID('...'), UUID('...')]
            >>> TeacherService.assign_subjects(teacher_id, subject_ids)
            >>> print("Subjects assigned successfully")
        """
        try:
            teacher = Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            raise TeacherServiceError(f"Teacher with ID '{teacher_id}' not found")
        
        # Validate all subject IDs exist
        subjects = Subject.objects.filter(id__in=subject_ids, is_active=True)
        if subjects.count() != len(subject_ids):
            found_ids = set(str(s.id) for s in subjects)
            requested_ids = set(str(sid) for sid in subject_ids)
            missing_ids = requested_ids - found_ids
            raise TeacherServiceError(f"Invalid or inactive subject IDs: {', '.join(missing_ids)}")
        
        try:
            # Clear existing subjects and assign new ones
            teacher.subjects.set(subjects)
            teacher.save()
        except Exception as e:
            raise TeacherServiceError(f"Error assigning subjects: {e}")
    
    @staticmethod
    def get_teacher_statistics(teacher_id: UUID, year: int, month: int) -> Dict:
        """
        Get attendance statistics for a teacher for a specific month.
        
        Args:
            teacher_id: UUID of the teacher
            year: Year (e.g., 2024)
            month: Month (1-12)
            
        Returns:
            Dictionary containing:
                - teacher: Teacher instance
                - year: Year
                - month: Month
                - total_hadir: Count of present JP
                - total_sakit: Count of sick JP
                - total_izin: Count of permission JP
                - total_cuti: Count of leave JP
                - total_dinas: Count of official duty JP
                - total_alpa: Count of absent JP
                - total_jp_scheduled: Total scheduled JP
                - attendance_percentage: Attendance percentage
                - summary_exists: Whether summary record exists
                
        Raises:
            TeacherServiceError: If teacher not found or invalid month/year
            
        Example:
            >>> teacher_id = UUID('...')
            >>> stats = TeacherService.get_teacher_statistics(teacher_id, 2024, 1)
            >>> print(f"Attendance: {stats['attendance_percentage']}%")
            >>> print(f"Present: {stats['total_hadir']} JP")
        """
        from django.core.cache import cache
        
        # Validate month and year
        if not (1 <= month <= 12):
            raise TeacherServiceError("Month must be between 1 and 12")
        
        if not (2020 <= year <= 2030):
            raise TeacherServiceError("Year must be between 2020 and 2030")
        
        # Try cache first (cache for 5 minutes)
        cache_key = f'teacher_stats_{teacher_id}_{year}_{month}'
        cached_stats = cache.get(cache_key)
        if cached_stats:
            return cached_stats
        
        try:
            teacher = Teacher.objects.only('id', 'full_name', 'nip').get(id=teacher_id)
        except Teacher.DoesNotExist:
            raise TeacherServiceError(f"Teacher with ID '{teacher_id}' not found")
        
        # Try to get existing summary
        try:
            summary = TeacherAttendanceSummary.objects.get(
                teacher=teacher,
                year=year,
                month=month
            )
            
            stats = {
                'teacher': teacher,
                'year': year,
                'month': month,
                'total_hadir': summary.total_hadir,
                'total_sakit': summary.total_sakit,
                'total_izin': summary.total_izin,
                'total_cuti': summary.total_cuti,
                'total_dinas': summary.total_dinas,
                'total_alpa': summary.total_alpa,
                'total_jp_scheduled': summary.total_jp_scheduled,
                'attendance_percentage': summary.attendance_percentage,
                'summary_exists': True,
            }
            
            # Cache the result
            cache.set(cache_key, stats, 300)  # 5 minutes
            return stats
        except TeacherAttendanceSummary.DoesNotExist:
            # Return empty statistics if no summary exists
            return {
                'teacher': teacher,
                'year': year,
                'month': month,
                'total_hadir': 0,
                'total_sakit': 0,
                'total_izin': 0,
                'total_cuti': 0,
                'total_dinas': 0,
                'total_alpa': 0,
                'total_jp_scheduled': 0,
                'attendance_percentage': 0.0,
                'summary_exists': False,
            }
    
    @staticmethod
    def get_teachers_with_filters(filters: Dict) -> List[Teacher]:
        """
        Get filtered list of teachers.
        
        Args:
            filters: Dictionary containing filter criteria:
                - employment_status (str, optional): Filter by employment status
                - is_active (bool, optional): Filter by active status
                - subject_id (UUID, optional): Filter by subject taught
                - is_homeroom_teacher (bool, optional): Filter homeroom teachers
                - search_query (str, optional): Search by name or NIP
                - order_by (str, optional): Field to order by (default: 'full_name')
                
        Returns:
            List of Teacher instances matching the filters
            
        Example:
            >>> filters = {
            ...     'employment_status': 'ACTIVE',
            ...     'is_active': True,
            ...     'search_query': 'Ahmad'
            ... }
            >>> teachers = TeacherService.get_teachers_with_filters(filters)
            >>> for teacher in teachers:
            ...     print(f"{teacher.full_name} - {teacher.nip}")
        """
        queryset = Teacher.objects.select_related(
            'homeroom_class',
            'homeroom_class__academic_level',
            'user'
        ).prefetch_related('subjects').only(
            'id', 'nip', 'full_name', 'photo', 'email', 'phone',
            'employment_status', 'employment_date', 'is_homeroom_teacher',
            'is_active', 'homeroom_class__name', 'homeroom_class__grade',
            'homeroom_class__section', 'homeroom_class__academic_level__code',
            'user__username'
        )
        
        # Apply filters
        if filters.get('employment_status'):
            queryset = queryset.filter(employment_status=filters['employment_status'])
        
        if filters.get('is_active') is not None:
            queryset = queryset.filter(is_active=filters['is_active'])
        
        if filters.get('subject_id'):
            queryset = queryset.filter(subjects__id=filters['subject_id'])
        
        if filters.get('is_homeroom_teacher') is not None:
            queryset = queryset.filter(is_homeroom_teacher=filters['is_homeroom_teacher'])
        
        if filters.get('search_query'):
            search_query = filters['search_query']
            queryset = queryset.filter(
                Q(full_name__icontains=search_query) |
                Q(nip__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        # Order by
        order_by = filters.get('order_by', 'full_name')
        queryset = queryset.order_by(order_by)
        
        # Remove duplicates if filtering by subjects (many-to-many)
        if filters.get('subject_id'):
            queryset = queryset.distinct()
        
        return list(queryset)
