"""
Unit tests for teacher-related models.

Tests validation, business logic, and constraints for:
- Subject model
- Teacher model
- TeacherSchedule model
- TeacherAttendance model
- TeacherAttendanceSummary model
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import IntegrityError
from datetime import date, timedelta
from decimal import Decimal

from attendance.models import (
    Subject,
    Teacher,
    TeacherSchedule,
    TeacherAttendance,
    TeacherAttendanceSummary,
    Classroom,
    AcademicLevel
)


class SubjectModelTestCase(TestCase):
    """Test cases for Subject model validation."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_create_valid_subject(self):
        """Should create subject with valid data."""
        subject = Subject.objects.create(
            code='MAT01',
            name='Matematika',
            category='UMUM',
            description='Matematika Dasar',
            created_by=self.user
        )
        
        self.assertEqual(subject.code, 'MAT01')
        self.assertEqual(subject.name, 'Matematika')
        self.assertEqual(subject.category, 'UMUM')
        self.assertTrue(subject.is_active)
    
    def test_code_must_be_uppercase(self):
        """Subject code must be uppercase."""
        subject = Subject(
            code='mat01',
            name='Matematika',
            category='UMUM'
        )
        
        with self.assertRaises(ValidationError) as context:
            subject.full_clean()
        
        self.assertIn('code', context.exception.message_dict)
        self.assertIn('uppercase', str(context.exception))
    
    def test_code_auto_converts_to_uppercase(self):
        """Subject code should auto-convert to uppercase on save."""
        subject = Subject.objects.create(
            code='mat01',
            name='Matematika',
            category='UMUM'
        )
        
        self.assertEqual(subject.code, 'MAT01')
    
    def test_code_must_be_alphanumeric(self):
        """Subject code must be alphanumeric."""
        subject = Subject(
            code='MAT@01',
            name='Matematika',
            category='UMUM'
        )
        
        with self.assertRaises(ValidationError) as context:
            subject.full_clean()
        
        self.assertIn('code', context.exception.message_dict)
    
    def test_code_must_be_unique(self):
        """Subject code must be unique."""
        Subject.objects.create(
            code='MAT01',
            name='Matematika',
            category='UMUM'
        )
        
        with self.assertRaises(ValidationError):
            Subject.objects.create(
                code='MAT01',
                name='Matematika Lanjut',
                category='UMUM'
            )
    
    def test_invalid_category_raises_error(self):
        """Invalid category should raise validation error."""
        subject = Subject(
            code='MAT01',
            name='Matematika',
            category='INVALID'
        )
        
        with self.assertRaises(ValidationError) as context:
            subject.full_clean()
        
        self.assertIn('category', context.exception.message_dict)
    
    def test_subject_string_representation(self):
        """Subject __str__ should return code and name."""
        subject = Subject.objects.create(
            code='MAT01',
            name='Matematika',
            category='UMUM'
        )
        
        self.assertEqual(str(subject), 'MAT01 - Matematika')
    
    def test_all_valid_categories(self):
        """All defined categories should be valid."""
        categories = ['AGAMA', 'UMUM', 'KETERAMPILAN', 'EKSTRAKURIKULER']
        
        for category in categories:
            subject = Subject.objects.create(
                code=f'TEST{category[:3]}',
                name=f'Test {category}',
                category=category
            )
            self.assertEqual(subject.category, category)


class TeacherModelTestCase(TestCase):
    """Test cases for Teacher model validation."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.academic_level, _ = AcademicLevel.objects.get_or_create(
            code='SMP',
            defaults={
                'name': 'Sekolah Menengah Pertama',
                'level_type': 'SMP',
                'min_grade': 7,
                'max_grade': 9
            }
        )
        
        self.classroom, _ = Classroom.objects.get_or_create(
            academic_level=self.academic_level,
            grade=8,
            section='A',
            academic_year='2024/2025',
            defaults={'name': 'Kelas 8-A'}
        )
    
    def test_create_valid_teacher(self):
        """Should create teacher with valid data."""
        teacher = Teacher.objects.create(
            nip='12345678901234567890',
            full_name='Ahmad Yusuf',
            email='ahmad@example.com',
            phone='081234567890',
            employment_date=date(2020, 1, 1),
            employment_status='ACTIVE'
        )
        
        self.assertEqual(teacher.nip, '12345678901234567890')
        self.assertEqual(teacher.full_name, 'Ahmad Yusuf')
        self.assertTrue(teacher.is_active)
    
    def test_nip_must_be_unique(self):
        """NIP must be unique."""
        Teacher.objects.create(
            nip='12345',
            full_name='Ahmad Yusuf',
            employment_date=date(2020, 1, 1)
        )
        
        with self.assertRaises(ValidationError):
            Teacher.objects.create(
                nip='12345',
                full_name='Fatimah Zahra',
                employment_date=date(2020, 1, 1)
            )
    
    def test_full_name_minimum_length(self):
        """Full name must be at least 3 characters."""
        teacher = Teacher(
            nip='12345',
            full_name='Ab',
            employment_date=date(2020, 1, 1)
        )
        
        with self.assertRaises(ValidationError) as context:
            teacher.full_clean()
        
        self.assertIn('full_name', context.exception.message_dict)
    
    def test_full_name_cannot_contain_numbers(self):
        """Full name should not contain numbers."""
        teacher = Teacher(
            nip='12345',
            full_name='Ahmad123',
            employment_date=date(2020, 1, 1)
        )
        
        with self.assertRaises(ValidationError) as context:
            teacher.full_clean()
        
        self.assertIn('full_name', context.exception.message_dict)
        self.assertIn('should not contain numbers', str(context.exception))
    
    def test_employment_date_cannot_be_future(self):
        """Employment date cannot be in the future."""
        future_date = timezone.now().date() + timedelta(days=30)
        teacher = Teacher(
            nip='12345',
            full_name='Ahmad Yusuf',
            employment_date=future_date
        )
        
        with self.assertRaises(ValidationError) as context:
            teacher.full_clean()
        
        self.assertIn('employment_date', context.exception.message_dict)
        self.assertIn('cannot be in the future', str(context.exception))
    
    def test_invalid_employment_status(self):
        """Invalid employment status should raise error."""
        teacher = Teacher(
            nip='12345',
            full_name='Ahmad Yusuf',
            employment_date=date(2020, 1, 1),
            employment_status='INVALID'
        )
        
        with self.assertRaises(ValidationError) as context:
            teacher.full_clean()
        
        self.assertIn('employment_status', context.exception.message_dict)
    
    def test_homeroom_teacher_requires_classroom(self):
        """Homeroom teacher must have homeroom_class set."""
        teacher = Teacher(
            nip='12345',
            full_name='Ahmad Yusuf',
            employment_date=date(2020, 1, 1),
            is_homeroom_teacher=True,
            homeroom_class=None
        )
        
        with self.assertRaises(ValidationError) as context:
            teacher.full_clean()
        
        self.assertIn('homeroom_class', context.exception.message_dict)
    
    def test_homeroom_teacher_with_classroom(self):
        """Homeroom teacher with classroom should be valid."""
        teacher = Teacher.objects.create(
            nip='12345',
            full_name='Ahmad Yusuf',
            employment_date=date(2020, 1, 1),
            is_homeroom_teacher=True,
            homeroom_class=self.classroom
        )
        
        self.assertTrue(teacher.is_homeroom_teacher)
        self.assertEqual(teacher.homeroom_class, self.classroom)
    
    def test_teacher_string_representation(self):
        """Teacher __str__ should return name and NIP."""
        teacher = Teacher.objects.create(
            nip='12345',
            full_name='Ahmad Yusuf',
            employment_date=date(2020, 1, 1)
        )
        
        self.assertEqual(str(teacher), 'Ahmad Yusuf (12345)')
    
    def test_teacher_subject_list_property(self):
        """Teacher should have subject_list property."""
        teacher = Teacher.objects.create(
            nip='12345',
            full_name='Ahmad Yusuf',
            employment_date=date(2020, 1, 1)
        )
        
        subject1 = Subject.objects.create(
            code='MAT01',
            name='Matematika',
            category='UMUM'
        )
        subject2 = Subject.objects.create(
            code='FIS01',
            name='Fisika',
            category='UMUM'
        )
        
        teacher.subjects.add(subject1, subject2)
        
        self.assertIn('Matematika', teacher.subject_list)
        self.assertIn('Fisika', teacher.subject_list)


class TeacherScheduleModelTestCase(TestCase):
    """Test cases for TeacherSchedule model validation and conflict detection."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.academic_level, _ = AcademicLevel.objects.get_or_create(
            code='SMP',
            defaults={
                'name': 'Sekolah Menengah Pertama',
                'level_type': 'SMP',
                'min_grade': 7,
                'max_grade': 9
            }
        )
        
        self.classroom, _ = Classroom.objects.get_or_create(
            academic_level=self.academic_level,
            grade=8,
            section='A',
            academic_year='2024/2025',
            defaults={'name': 'Kelas 8-A'}
        )
        
        self.teacher = Teacher.objects.create(
            nip='12345',
            full_name='Ahmad Yusuf',
            employment_date=date(2020, 1, 1)
        )
        
        self.subject = Subject.objects.create(
            code='MAT01',
            name='Matematika',
            category='UMUM'
        )
    
    def test_create_valid_schedule(self):
        """Should create schedule with valid data."""
        schedule = TeacherSchedule.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=0,
            jp_start=1,
            jp_end=2,
            effective_date=date(2024, 1, 1)
        )
        
        self.assertEqual(schedule.teacher, self.teacher)
        self.assertEqual(schedule.jp_start, 1)
        self.assertEqual(schedule.jp_end, 2)
        self.assertTrue(schedule.is_active)
    
    def test_jp_start_must_be_between_1_and_10(self):
        """JP start must be between 1 and 10."""
        schedule = TeacherSchedule(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=0,
            jp_start=0,
            jp_end=2,
            effective_date=date(2024, 1, 1)
        )
        
        with self.assertRaises(ValidationError) as context:
            schedule.full_clean()
        
        self.assertIn('jp_start', context.exception.message_dict)
    
    def test_jp_end_must_be_between_1_and_10(self):
        """JP end must be between 1 and 10."""
        schedule = TeacherSchedule(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=0,
            jp_start=1,
            jp_end=11,
            effective_date=date(2024, 1, 1)
        )
        
        with self.assertRaises(ValidationError) as context:
            schedule.full_clean()
        
        self.assertIn('jp_end', context.exception.message_dict)
    
    def test_jp_end_must_be_greater_or_equal_to_jp_start(self):
        """JP end must be >= JP start."""
        schedule = TeacherSchedule(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=0,
            jp_start=5,
            jp_end=3,
            effective_date=date(2024, 1, 1)
        )
        
        with self.assertRaises(ValidationError) as context:
            schedule.full_clean()
        
        self.assertIn('jp_end', context.exception.message_dict)
    
    def test_end_date_must_be_after_effective_date(self):
        """End date must be >= effective date."""
        schedule = TeacherSchedule(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=0,
            jp_start=1,
            jp_end=2,
            effective_date=date(2024, 6, 1),
            end_date=date(2024, 1, 1)
        )
        
        with self.assertRaises(ValidationError) as context:
            schedule.full_clean()
        
        self.assertIn('end_date', context.exception.message_dict)
    
    def test_teacher_conflict_detection(self):
        """Should detect when teacher has conflicting schedule."""
        # Create first schedule
        TeacherSchedule.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=0,
            jp_start=1,
            jp_end=2,
            effective_date=date(2024, 1, 1)
        )
        
        # Try to create overlapping schedule for same teacher
        schedule2 = TeacherSchedule(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=0,
            jp_start=2,
            jp_end=3,
            effective_date=date(2024, 1, 1)
        )
        
        with self.assertRaises(ValidationError) as context:
            schedule2.full_clean()
        
        self.assertIn('jp_start', context.exception.message_dict)
        self.assertIn('already has a schedule', str(context.exception))
    
    def test_classroom_conflict_detection(self):
        """Should detect when classroom has conflicting schedule."""
        teacher2 = Teacher.objects.create(
            nip='67890',
            full_name='Fatimah Zahra',
            employment_date=date(2020, 1, 1)
        )
        
        # Create first schedule
        TeacherSchedule.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=0,
            jp_start=1,
            jp_end=2,
            effective_date=date(2024, 1, 1)
        )
        
        # Try to create overlapping schedule for same classroom
        schedule2 = TeacherSchedule(
            teacher=teacher2,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=0,
            jp_start=2,
            jp_end=3,
            effective_date=date(2024, 1, 1)
        )
        
        with self.assertRaises(ValidationError) as context:
            schedule2.full_clean()
        
        self.assertIn('classroom', context.exception.message_dict)
        self.assertIn('already scheduled', str(context.exception))
    
    def test_no_conflict_different_days(self):
        """No conflict if schedules are on different days."""
        TeacherSchedule.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=0,
            jp_start=1,
            jp_end=2,
            effective_date=date(2024, 1, 1)
        )
        
        # Different day - should be valid
        schedule2 = TeacherSchedule.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=1,
            jp_start=1,
            jp_end=2,
            effective_date=date(2024, 1, 1)
        )
        
        self.assertIsNotNone(schedule2.pk)
    
    def test_no_conflict_non_overlapping_jp(self):
        """No conflict if JP ranges don't overlap."""
        TeacherSchedule.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=0,
            jp_start=1,
            jp_end=2,
            effective_date=date(2024, 1, 1)
        )
        
        # Non-overlapping JP - should be valid
        schedule2 = TeacherSchedule.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=0,
            jp_start=3,
            jp_end=4,
            effective_date=date(2024, 1, 1)
        )
        
        self.assertIsNotNone(schedule2.pk)
    
    def test_jp_count_property(self):
        """jp_count property should calculate correctly."""
        schedule = TeacherSchedule.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=0,
            jp_start=1,
            jp_end=4,
            effective_date=date(2024, 1, 1)
        )
        
        self.assertEqual(schedule.jp_count, 4)
    
    def test_day_name_property(self):
        """day_name property should return Indonesian day name."""
        schedule = TeacherSchedule.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=0,
            jp_start=1,
            jp_end=2,
            effective_date=date(2024, 1, 1)
        )
        
        self.assertEqual(schedule.day_name, 'Senin')


class TeacherAttendanceModelTestCase(TestCase):
    """Test cases for TeacherAttendance model validation."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.teacher = Teacher.objects.create(
            nip='12345',
            full_name='Ahmad Yusuf',
            employment_date=date(2020, 1, 1)
        )
    
    def test_create_valid_attendance(self):
        """Should create attendance with valid data."""
        attendance = TeacherAttendance.objects.create(
            teacher=self.teacher,
            date=date.today(),
            jp_number=1,
            status='HADIR',
            recorded_by=self.user
        )
        
        self.assertEqual(attendance.teacher, self.teacher)
        self.assertEqual(attendance.status, 'HADIR')
        self.assertFalse(attendance.is_substitute)
    
    def test_jp_number_must_be_between_1_and_10(self):
        """JP number must be between 1 and 10."""
        attendance = TeacherAttendance(
            teacher=self.teacher,
            date=date.today(),
            jp_number=11,
            status='HADIR',
            recorded_by=self.user
        )
        
        with self.assertRaises(ValidationError) as context:
            attendance.full_clean()
        
        self.assertIn('jp_number', context.exception.message_dict)
    
    def test_latitude_must_be_valid_range(self):
        """Latitude must be between -90 and 90."""
        attendance = TeacherAttendance(
            teacher=self.teacher,
            date=date.today(),
            jp_number=1,
            status='HADIR',
            recorded_by=self.user,
            latitude=Decimal('91.0')
        )
        
        with self.assertRaises(ValidationError) as context:
            attendance.full_clean()
        
        self.assertIn('latitude', context.exception.message_dict)
    
    def test_longitude_must_be_valid_range(self):
        """Longitude must be between -180 and 180."""
        attendance = TeacherAttendance(
            teacher=self.teacher,
            date=date.today(),
            jp_number=1,
            status='HADIR',
            recorded_by=self.user,
            longitude=Decimal('181.0')
        )
        
        with self.assertRaises(ValidationError) as context:
            attendance.full_clean()
        
        self.assertIn('longitude', context.exception.message_dict)
    
    def test_date_cannot_be_future(self):
        """Attendance date cannot be in the future."""
        future_date = timezone.now().date() + timedelta(days=1)
        attendance = TeacherAttendance(
            teacher=self.teacher,
            date=future_date,
            jp_number=1,
            status='HADIR',
            recorded_by=self.user
        )
        
        with self.assertRaises(ValidationError) as context:
            attendance.full_clean()
        
        self.assertIn('date', context.exception.message_dict)
        self.assertIn('cannot be in the future', str(context.exception))
    
    def test_invalid_status_raises_error(self):
        """Invalid status should raise validation error."""
        attendance = TeacherAttendance(
            teacher=self.teacher,
            date=date.today(),
            jp_number=1,
            status='INVALID',
            recorded_by=self.user
        )
        
        with self.assertRaises(ValidationError) as context:
            attendance.full_clean()
        
        self.assertIn('status', context.exception.message_dict)
    
    def test_substitute_requires_substitute_for(self):
        """is_substitute=True requires substitute_for to be set."""
        attendance = TeacherAttendance(
            teacher=self.teacher,
            date=date.today(),
            jp_number=1,
            status='HADIR',
            recorded_by=self.user,
            is_substitute=True,
            substitute_for=None
        )
        
        with self.assertRaises(ValidationError) as context:
            attendance.full_clean()
        
        self.assertIn('substitute_for', context.exception.message_dict)
    
    def test_substitute_for_requires_is_substitute(self):
        """substitute_for set requires is_substitute=True."""
        teacher2 = Teacher.objects.create(
            nip='67890',
            full_name='Fatimah Zahra',
            employment_date=date(2020, 1, 1)
        )
        
        attendance = TeacherAttendance(
            teacher=self.teacher,
            date=date.today(),
            jp_number=1,
            status='HADIR',
            recorded_by=self.user,
            is_substitute=False,
            substitute_for=teacher2
        )
        
        with self.assertRaises(ValidationError) as context:
            attendance.full_clean()
        
        self.assertIn('is_substitute', context.exception.message_dict)
    
    def test_cannot_record_for_inactive_teacher(self):
        """Cannot record attendance for inactive teacher."""
        inactive_teacher = Teacher.objects.create(
            nip='99999',
            full_name='Inactive Teacher',
            employment_date=date(2020, 1, 1),
            is_active=False
        )
        
        attendance = TeacherAttendance(
            teacher=inactive_teacher,
            date=date.today(),
            jp_number=1,
            status='HADIR',
            recorded_by=self.user
        )
        
        with self.assertRaises(ValidationError) as context:
            attendance.full_clean()
        
        self.assertIn('teacher', context.exception.message_dict)
        self.assertIn('inactive', str(context.exception))
    
    def test_unique_constraint_teacher_date_jp(self):
        """Teacher can only have one attendance per date per JP."""
        TeacherAttendance.objects.create(
            teacher=self.teacher,
            date=date.today(),
            jp_number=1,
            status='HADIR',
            recorded_by=self.user
        )
        
        with self.assertRaises(ValidationError):
            TeacherAttendance.objects.create(
                teacher=self.teacher,
                date=date.today(),
                jp_number=1,
                status='SAKIT',
                recorded_by=self.user
            )
    
    def test_is_present_property(self):
        """is_present property should return True for HADIR."""
        attendance = TeacherAttendance.objects.create(
            teacher=self.teacher,
            date=date.today(),
            jp_number=1,
            status='HADIR',
            recorded_by=self.user
        )
        
        self.assertTrue(attendance.is_present)
    
    def test_is_absent_property(self):
        """is_absent property should return True for non-HADIR."""
        attendance = TeacherAttendance.objects.create(
            teacher=self.teacher,
            date=date.today(),
            jp_number=1,
            status='SAKIT',
            recorded_by=self.user
        )
        
        self.assertTrue(attendance.is_absent)
        self.assertFalse(attendance.is_present)
    
    def test_all_valid_statuses(self):
        """All defined statuses should be valid."""
        statuses = ['HADIR', 'SAKIT', 'IZIN', 'CUTI', 'DINAS', 'ALPA']
        
        for idx, status in enumerate(statuses):
            attendance = TeacherAttendance.objects.create(
                teacher=self.teacher,
                date=date.today(),
                jp_number=idx + 1,
                status=status,
                recorded_by=self.user
            )
            self.assertEqual(attendance.status, status)


class TeacherAttendanceSummaryModelTestCase(TestCase):
    """Test cases for TeacherAttendanceSummary model calculation."""
    
    def setUp(self):
        """Set up test data."""
        self.teacher = Teacher.objects.create(
            nip='12345',
            full_name='Ahmad Yusuf',
            employment_date=date(2020, 1, 1)
        )
    
    def test_create_valid_summary(self):
        """Should create summary with valid data."""
        summary = TeacherAttendanceSummary.objects.create(
            teacher=self.teacher,
            year=2024,
            month=1,
            total_hadir=80,
            total_sakit=5,
            total_izin=3,
            total_cuti=2,
            total_dinas=0,
            total_alpa=0,
            total_jp_scheduled=90
        )
        
        self.assertEqual(summary.teacher, self.teacher)
        self.assertEqual(summary.total_hadir, 80)
    
    def test_month_must_be_between_1_and_12(self):
        """Month must be between 1 and 12."""
        summary = TeacherAttendanceSummary(
            teacher=self.teacher,
            year=2024,
            month=13,
            total_jp_scheduled=90
        )
        
        with self.assertRaises(ValidationError) as context:
            summary.full_clean()
        
        self.assertIn('month', context.exception.message_dict)
    
    def test_year_must_be_between_2020_and_2030(self):
        """Year must be between 2020 and 2030."""
        summary = TeacherAttendanceSummary(
            teacher=self.teacher,
            year=2031,
            month=1,
            total_jp_scheduled=90
        )
        
        with self.assertRaises(ValidationError) as context:
            summary.full_clean()
        
        self.assertIn('year', context.exception.message_dict)
    
    def test_calculate_percentage_method(self):
        """calculate_percentage should compute correct percentage."""
        summary = TeacherAttendanceSummary(
            teacher=self.teacher,
            year=2024,
            month=1,
            total_hadir=80,
            total_jp_scheduled=100
        )
        
        summary.calculate_percentage()
        
        self.assertEqual(summary.attendance_percentage, 80.0)
    
    def test_calculate_percentage_with_zero_scheduled(self):
        """calculate_percentage should handle zero scheduled JP."""
        summary = TeacherAttendanceSummary(
            teacher=self.teacher,
            year=2024,
            month=1,
            total_hadir=0,
            total_jp_scheduled=0
        )
        
        summary.calculate_percentage()
        
        self.assertEqual(summary.attendance_percentage, 0.0)
    
    def test_percentage_auto_calculated_on_save(self):
        """Percentage should be auto-calculated on save."""
        summary = TeacherAttendanceSummary.objects.create(
            teacher=self.teacher,
            year=2024,
            month=1,
            total_hadir=85,
            total_jp_scheduled=100
        )
        
        self.assertEqual(summary.attendance_percentage, 85.0)
    
    def test_percentage_rounds_to_two_decimals(self):
        """Percentage should round to 2 decimal places."""
        summary = TeacherAttendanceSummary.objects.create(
            teacher=self.teacher,
            year=2024,
            month=1,
            total_hadir=85,
            total_jp_scheduled=90
        )
        
        # 85/90 = 94.444...
        self.assertEqual(summary.attendance_percentage, 94.44)
    
    def test_unique_constraint_teacher_year_month(self):
        """Teacher can only have one summary per year-month."""
        TeacherAttendanceSummary.objects.create(
            teacher=self.teacher,
            year=2024,
            month=1,
            total_jp_scheduled=90
        )
        
        with self.assertRaises(ValidationError):
            TeacherAttendanceSummary.objects.create(
                teacher=self.teacher,
                year=2024,
                month=1,
                total_jp_scheduled=90
            )
    
    def test_summary_string_representation(self):
        """Summary __str__ should return teacher name and period."""
        summary = TeacherAttendanceSummary.objects.create(
            teacher=self.teacher,
            year=2024,
            month=1,
            total_jp_scheduled=90
        )
        
        self.assertEqual(str(summary), 'Ahmad Yusuf - 2024/01')
