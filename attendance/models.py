"""
Models for the attendance application
Following enterprise architecture patterns with proper validation and business logic
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import RegexValidator, MinLengthValidator
from django.core.exceptions import ValidationError
import uuid


class AttendanceStatus(models.TextChoices):
    """Enumeration for attendance status options"""
    HADIR = 'HADIR', 'Hadir'
    SAKIT = 'SAKIT', 'Sakit'
    IZIN = 'IZIN', 'Izin'
    ALPA = 'ALPA', 'Alpa'


class BaseModel(models.Model):
    """Abstract base model with common fields"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='%(class)s_updated'
    )
    
    class Meta:
        abstract = True


class AcademicLevel(models.Model):
    """Academic level model (SMP, SMA, etc.)"""
    
    LEVEL_CHOICES = [
        ('SMP', 'Sekolah Menengah Pertama'),
        ('SMA', 'Sekolah Menengah Atas'),
        ('MA', 'Madrasah Aliyah'),
        ('MTS', 'Madrasah Tsanawiyah'),
    ]
    
    code = models.CharField(max_length=10, unique=True, primary_key=True)
    name = models.CharField(max_length=50)
    level_type = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    # Academic settings
    min_grade = models.PositiveIntegerField(help_text="Minimum grade level (e.g., 7 for SMP)")
    max_grade = models.PositiveIntegerField(help_text="Maximum grade level (e.g., 9 for SMP)")
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['level_type', 'code']
        verbose_name = 'Academic Level'
        verbose_name_plural = 'Academic Levels'
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        if self.min_grade and self.max_grade and self.min_grade > self.max_grade:
            raise ValidationError("Minimum grade cannot be greater than maximum grade")
    
    @property
    def grade_range(self):
        """Get grade range as string"""
        return f"{self.min_grade}-{self.max_grade}"


class Classroom(BaseModel):
    """Classroom model with proper relationships"""
    
    academic_level = models.ForeignKey(
        AcademicLevel, 
        on_delete=models.CASCADE,
        help_text="Academic level (SMP/SMA)"
    )
    grade = models.PositiveIntegerField(help_text="Grade level (7, 8, 9, 10, 11, 12)")
    section = models.CharField(
        max_length=5, 
        blank=True,
        help_text="Class section (A, B, C, etc.)"
    )
    
    # Classroom details
    name = models.CharField(max_length=50, help_text="Display name for the classroom")
    capacity = models.PositiveIntegerField(default=30)
    room_number = models.CharField(max_length=20, blank=True)
    homeroom_teacher = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='homeroom_classes'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    academic_year = models.CharField(
        max_length=9, 
        help_text="Academic year (e.g., 2024/2025)"
    )
    
    class Meta:
        unique_together = ['academic_level', 'grade', 'section', 'academic_year']
        ordering = ['academic_level', 'grade', 'section']
        indexes = [
            models.Index(fields=['academic_level', 'grade']),
            models.Index(fields=['is_active']),
            models.Index(fields=['academic_year']),
        ]
        verbose_name = 'Classroom'
        verbose_name_plural = 'Classrooms'
    
    def __str__(self):
        if self.section:
            return f"{self.grade}-{self.section} ({self.academic_level.code})"
        return f"{self.grade} ({self.academic_level.code})"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        # Validate grade is within academic level range
        if self.academic_level and self.grade:
            if not (self.academic_level.min_grade <= self.grade <= self.academic_level.max_grade):
                raise ValidationError({
                    'grade': f'Grade {self.grade} is not valid for {self.academic_level.name}. '
                            f'Valid range: {self.academic_level.min_grade}-{self.academic_level.max_grade}'
                })
        
        # Auto-generate name if not provided
        if not self.name:
            if self.section:
                self.name = f"Kelas {self.grade}-{self.section}"
            else:
                self.name = f"Kelas {self.grade}"
    
    @property
    def full_name(self):
        """Get full classroom name"""
        return f"{self.academic_level.code} {self.grade}-{self.section}" if self.section else f"{self.academic_level.code} {self.grade}"
    
    @property
    def student_count(self):
        """Get current student count"""
        return self.students.filter(is_active=True).count()
    
    @property
    def is_full(self):
        """Check if classroom is at capacity"""
        return self.student_count >= self.capacity


class Student(BaseModel):
    """Student model with enhanced validation and business logic"""
    
    # Validators
    student_id_validator = RegexValidator(
        regex=r'^[0-9A-Z]{2,10}$',
        message='Student ID must be 2-10 characters long and contain only numbers and uppercase letters'
    )
    
    nisn_validator = RegexValidator(
        regex=r'^\d{10}$',
        message='NISN must be exactly 10 digits'
    )
    
    # Core fields
    student_id = models.CharField(
        max_length=10, 
        unique=True,
        validators=[student_id_validator],
        help_text='Unique student identifier'
    )
    nisn = models.CharField(
        max_length=10, 
        blank=True,
        validators=[nisn_validator],
        help_text='National Student Identification Number (10 digits)'
    )
    name = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        help_text='Full name of the student'
    )
    
    # Classroom relationship
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name='students',
        help_text='Student\'s classroom'
    )
    
    # Personal information
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=1,
        choices=[('M', 'Laki-laki'), ('F', 'Perempuan')],
        blank=True
    )
    address = models.TextField(blank=True)
    parent_phone = models.CharField(max_length=15, blank=True)
    
    # Academic information
    enrollment_date = models.DateField(default=timezone.now)
    graduation_date = models.DateField(null=True, blank=True)
    student_number = models.CharField(max_length=20, blank=True, help_text="Internal student number")
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['classroom']),
            models.Index(fields=['student_id']),
            models.Index(fields=['nisn']),
            models.Index(fields=['is_active']),
            models.Index(fields=['enrollment_date']),
        ]
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

    def __str__(self):
        return f"{self.name} ({self.classroom})"
    
    def clean(self):
        """Custom validation logic"""
        super().clean()
        
        # Validate name doesn't contain numbers
        if self.name and any(char.isdigit() for char in self.name):
            raise ValidationError({
                'name': 'Student name should not contain numbers'
            })
        
        # Validate enrollment date
        if self.enrollment_date and self.enrollment_date > timezone.now().date():
            raise ValidationError({
                'enrollment_date': 'Enrollment date cannot be in the future'
            })
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def class_name(self):
        """Backward compatibility property"""
        return str(self.classroom)
    
    @property
    def academic_level(self):
        """Get academic level"""
        return self.classroom.academic_level
    
    @property
    def grade(self):
        """Get grade level"""
        return self.classroom.grade
    
    @property
    def attendance_rate(self):
        """Calculate overall attendance rate for this student"""
        total_records = self.attendancerecord_set.count()
        if total_records == 0:
            return 0.0
        
        present_records = self.attendancerecord_set.filter(
            status=AttendanceStatus.HADIR
        ).count()
        
        return round((present_records / total_records) * 100, 2)
    
    @property
    def total_absences(self):
        """Get total number of absences (excluding present)"""
        return self.attendancerecord_set.exclude(
            status=AttendanceStatus.HADIR
        ).count()


class AttendanceRecord(BaseModel):
    """Attendance record with enhanced business logic and validation"""
    
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE,
        help_text='Student for this attendance record'
    )
    date = models.DateField(
        default=timezone.now,
        help_text='Date of attendance'
    )
    status = models.CharField(
        max_length=10,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.HADIR,
        help_text='Attendance status'
    )
    teacher = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        help_text='Teacher who recorded the attendance'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about the attendance'
    )
    
    # Additional fields for better tracking
    recorded_at = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date', 'student__name']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['status']),
            models.Index(fields=['student', 'date']),
            models.Index(fields=['teacher']),
        ]
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'

    def __str__(self):
        return f"{self.student.name} - {self.date} - {self.get_status_display()}"
    
    def clean(self):
        """Custom validation logic"""
        super().clean()
        
        # Validate date is not in the future
        if self.date and self.date > timezone.now().date():
            raise ValidationError({
                'date': 'Attendance date cannot be in the future'
            })
        
        # Validate student is active
        if self.student and not self.student.is_active:
            raise ValidationError({
                'student': 'Cannot record attendance for inactive student'
            })
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_present(self):
        """Check if student was present"""
        return self.status == AttendanceStatus.HADIR
    
    @property
    def is_absent(self):
        """Check if student was absent (any non-present status)"""
        return self.status != AttendanceStatus.HADIR


class AttendanceSummary(models.Model):
    """Monthly attendance summary for performance optimization"""
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    year = models.PositiveIntegerField(default=2024)
    month = models.PositiveIntegerField(default=1)
    
    # Attendance counts
    total_hadir = models.PositiveIntegerField(default=0)
    total_sakit = models.PositiveIntegerField(default=0)
    total_izin = models.PositiveIntegerField(default=0)
    total_alpa = models.PositiveIntegerField(default=0)
    total_days = models.PositiveIntegerField(default=0)
    
    # Calculated fields
    attendance_percentage = models.FloatField(default=0.0)
    
    # Timestamp fields
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'year', 'month']
        ordering = ['-year', '-month', 'student__name']
        indexes = [
            models.Index(fields=['year', 'month']),
            models.Index(fields=['student']),
        ]
        verbose_name = 'Attendance Summary'
        verbose_name_plural = 'Attendance Summaries'

    def __str__(self):
        return f"{self.student.name} - {self.year}/{self.month:02d}"
    
    def clean(self):
        """Custom validation logic"""
        super().clean()
        
        # Validate month range
        if self.month and not (1 <= self.month <= 12):
            raise ValidationError({
                'month': 'Month must be between 1 and 12'
            })
        
        # Validate year range
        if self.year and not (2020 <= self.year <= 2030):
            raise ValidationError({
                'year': 'Year must be between 2020 and 2030'
            })
    
    def calculate_percentage(self):
        """Calculate and update attendance percentage"""
        if self.total_days > 0:
            self.attendance_percentage = round(
                (self.total_hadir / self.total_days) * 100, 2
            )
        else:
            self.attendance_percentage = 0.0
    
    def save(self, *args, **kwargs):
        """Override save to calculate percentage"""
        self.calculate_percentage()
        self.full_clean()
        super().save(*args, **kwargs)


class AuditLog(models.Model):
    """Audit log for tracking important system events"""
    
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('EXPORT', 'Export'),
        ('IMPORT', 'Import'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.CharField(max_length=50, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamp fields
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['action']),
            models.Index(fields=['model_name']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name} - {self.created_at}"