"""
Tests for the attendance application models and services.
This checkpoint verifies that models and services from tasks 1 and 2 work correctly.
"""
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from .models import (
    DaySchedule, DailyAttendance, Holiday,
    Student, Classroom, AcademicLevel
)
from .services.schedule_service import ScheduleService
from .services.attendance_service import AttendanceService
from .services.holiday_service import HolidayService


class DayScheduleModelTests(TestCase):
    """Tests for DaySchedule model (Task 1.1, 1.4)"""
    
    def test_day_schedule_populated_with_7_days(self):
        """Verify that DaySchedule has exactly 7 records (one for each day)"""
        schedules = DaySchedule.objects.all()
        self.assertEqual(schedules.count(), 7)
    
    def test_day_schedule_default_jp_counts(self):
        """Verify default JP counts: Mon-Thu=6, Fri=4, Sat=6, Sun=0"""
        # Monday (0) - Thursday (3): 6 JP
        for day in range(4):
            schedule = DaySchedule.objects.get(day_of_week=day)
            self.assertEqual(schedule.default_jp_count, 6)
        
        # Friday (4): 4 JP
        friday = DaySchedule.objects.get(day_of_week=4)
        self.assertEqual(friday.default_jp_count, 4)
        
        # Saturday (5): 6 JP
        saturday = DaySchedule.objects.get(day_of_week=5)
        self.assertEqual(saturday.default_jp_count, 6)
        
        # Sunday (6): 0 JP, not a school day
        sunday = DaySchedule.objects.get(day_of_week=6)
        self.assertEqual(sunday.default_jp_count, 0)
        self.assertFalse(sunday.is_school_day)
    
    def test_day_schedule_jp_count_validation_min(self):
        """Verify JP count cannot be less than 1"""
        schedule = DaySchedule.objects.get(day_of_week=0)
        schedule.default_jp_count = 0
        with self.assertRaises(ValidationError):
            schedule.full_clean()
    
    def test_day_schedule_jp_count_validation_max(self):
        """Verify JP count cannot exceed 10"""
        schedule = DaySchedule.objects.get(day_of_week=0)
        schedule.default_jp_count = 11
        with self.assertRaises(ValidationError):
            schedule.full_clean()
    
    def test_day_schedule_valid_jp_count(self):
        """Verify valid JP counts (1-10) are accepted"""
        schedule = DaySchedule.objects.get(day_of_week=0)
        for jp_count in [1, 5, 10]:
            schedule.default_jp_count = jp_count
            schedule.full_clean()  # Should not raise


class DailyAttendanceModelTests(TestCase):
    """Tests for DailyAttendance model (Task 1.2)"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        cls.user = User.objects.create_user(
            username='testteacher',
            password='testpass123'
        )
        cls.academic_level = AcademicLevel.objects.create(
            code='SMP',
            name='Sekolah Menengah Pertama',
            level_type='SMP',
            min_grade=7,
            max_grade=9
        )
        cls.classroom = Classroom.objects.create(
            academic_level=cls.academic_level,
            grade=7,
            section='A',
            name='Kelas 7A',
            academic_year='2025/2026'
        )
        cls.student = Student.objects.create(
            student_id='STU001',
            name='Ahmad Test',
            classroom=cls.classroom
        )
    
    def test_daily_attendance_creation(self):
        """Test creating a DailyAttendance record"""
        attendance = DailyAttendance.objects.create(
            student=self.student,
            date=date.today(),
            jp_statuses={'1': 'H', '2': 'H', '3': 'S', '4': 'H', '5': 'H', '6': 'H'},
            recorded_by=self.user
        )
        self.assertIsNotNone(attendance.id)
        self.assertEqual(attendance.total_hadir, 5)
        self.assertEqual(attendance.total_sakit, 1)
    
    def test_daily_attendance_unique_constraint(self):
        """Test unique constraint on (student, date)"""
        DailyAttendance.objects.create(
            student=self.student,
            date=date.today(),
            jp_statuses={'1': 'H'},
            recorded_by=self.user
        )
        # Django's full_clean catches unique constraint as ValidationError
        # when using model's save() method with full_clean()
        with self.assertRaises((IntegrityError, ValidationError)):
            DailyAttendance.objects.create(
                student=self.student,
                date=date.today(),
                jp_statuses={'1': 'S'},
                recorded_by=self.user
            )
    
    def test_daily_attendance_valid_statuses(self):
        """Test that only valid statuses (H, S, I, A) are accepted"""
        attendance = DailyAttendance(
            student=self.student,
            date=date.today(),
            jp_statuses={'1': 'X'},  # Invalid status
            recorded_by=self.user
        )
        with self.assertRaises(ValidationError):
            attendance.full_clean()
    
    def test_daily_attendance_status_counts(self):
        """Test status count properties"""
        attendance = DailyAttendance.objects.create(
            student=self.student,
            date=date.today(),
            jp_statuses={'1': 'H', '2': 'S', '3': 'I', '4': 'A', '5': 'H', '6': 'H'},
            recorded_by=self.user
        )
        self.assertEqual(attendance.total_hadir, 3)
        self.assertEqual(attendance.total_sakit, 1)
        self.assertEqual(attendance.total_izin, 1)
        self.assertEqual(attendance.total_alpa, 1)
        self.assertEqual(attendance.total_jp, 6)


class HolidayModelTests(TestCase):
    """Tests for Holiday model (Task 1.3)"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        cls.user = User.objects.create_user(
            username='testadmin',
            password='testpass123'
        )
        cls.academic_level = AcademicLevel.objects.create(
            code='SMA',
            name='Sekolah Menengah Atas',
            level_type='SMA',
            min_grade=10,
            max_grade=12
        )
        cls.classroom = Classroom.objects.create(
            academic_level=cls.academic_level,
            grade=10,
            section='A',
            name='Kelas 10A',
            academic_year='2025/2026'
        )
    
    def test_holiday_creation_global(self):
        """Test creating a global holiday (apply_to_all=True)"""
        holiday = Holiday.objects.create(
            date=date(2026, 1, 15),
            name='Libur Nasional',
            holiday_type='LAINNYA',
            apply_to_all=True,
            created_by=self.user
        )
        self.assertTrue(holiday.apply_to_all)
        self.assertTrue(holiday.applies_to_classroom(self.classroom))
    
    def test_holiday_creation_classroom_specific(self):
        """Test creating a classroom-specific holiday"""
        holiday = Holiday.objects.create(
            date=date(2026, 1, 16),
            name='UAS Kelas 10A',
            holiday_type='UAS',
            apply_to_all=False,
            created_by=self.user
        )
        holiday.classrooms.add(self.classroom)
        
        self.assertFalse(holiday.apply_to_all)
        self.assertTrue(holiday.applies_to_classroom(self.classroom))
    
    def test_holiday_type_validation(self):
        """Test that only valid holiday types are accepted"""
        holiday = Holiday(
            date=date(2026, 1, 17),
            name='Invalid Holiday',
            holiday_type='INVALID',
            apply_to_all=True
        )
        with self.assertRaises(ValidationError):
            holiday.full_clean()
    
    def test_holiday_valid_types(self):
        """Test all valid holiday types"""
        valid_types = ['UAS', 'UN', 'PESANTREN', 'LAINNYA']
        for i, holiday_type in enumerate(valid_types):
            holiday = Holiday(
                date=date(2026, 2, i + 1),
                name=f'Test {holiday_type}',
                holiday_type=holiday_type,
                apply_to_all=True
            )
            holiday.full_clean()  # Should not raise


class ScheduleServiceTests(TestCase):
    """Tests for ScheduleService (Task 2.1)"""
    
    def test_get_jp_count_for_date_monday(self):
        """Test getting JP count for a Monday"""
        # Find a Monday
        monday = date(2026, 1, 12)  # January 12, 2026 is a Monday
        jp_count = ScheduleService.get_jp_count_for_date(monday)
        self.assertEqual(jp_count, 6)
    
    def test_get_jp_count_for_date_friday(self):
        """Test getting JP count for a Friday"""
        friday = date(2026, 1, 16)  # January 16, 2026 is a Friday
        jp_count = ScheduleService.get_jp_count_for_date(friday)
        self.assertEqual(jp_count, 4)
    
    def test_get_day_schedule(self):
        """Test getting DaySchedule by day of week"""
        schedule = ScheduleService.get_day_schedule(0)  # Monday
        self.assertIsNotNone(schedule)
        self.assertEqual(schedule.day_name, 'Senin')
    
    def test_get_all_schedules(self):
        """Test getting all schedules"""
        schedules = ScheduleService.get_all_schedules()
        self.assertEqual(len(schedules), 7)
    
    def test_is_school_day_weekday(self):
        """Test is_school_day for weekdays"""
        monday = date(2026, 1, 12)
        self.assertTrue(ScheduleService.is_school_day(monday))
    
    def test_is_school_day_sunday(self):
        """Test is_school_day for Sunday"""
        sunday = date(2026, 1, 18)  # January 18, 2026 is a Sunday
        self.assertFalse(ScheduleService.is_school_day(sunday))
    
    def test_update_schedule(self):
        """Test updating a schedule"""
        user = User.objects.create_user(username='admin', password='pass')
        schedule = ScheduleService.update_schedule(0, 8, user)
        self.assertEqual(schedule.default_jp_count, 8)
        self.assertEqual(schedule.updated_by, user)
        
        # Reset to original
        ScheduleService.update_schedule(0, 6, user)
    
    def test_update_schedule_invalid_jp_count(self):
        """Test updating schedule with invalid JP count"""
        with self.assertRaises(ValidationError):
            ScheduleService.update_schedule(0, 15)


class AttendanceServiceTests(TestCase):
    """Tests for AttendanceService (Task 2.2)"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        cls.user = User.objects.create_user(
            username='testteacher',
            password='testpass123'
        )
        cls.academic_level = AcademicLevel.objects.create(
            code='SMP2',
            name='Sekolah Menengah Pertama',
            level_type='SMP',
            min_grade=7,
            max_grade=9
        )
        cls.classroom = Classroom.objects.create(
            academic_level=cls.academic_level,
            grade=8,
            section='B',
            name='Kelas 8B',
            academic_year='2025/2026'
        )
        cls.student = Student.objects.create(
            student_id='STU002',
            name='Budi Test',
            classroom=cls.classroom
        )
    
    def test_save_attendance(self):
        """Test saving attendance for a student"""
        target_date = date(2026, 1, 12)  # Monday - 6 JP
        jp_statuses = {'1': 'H', '2': 'H', '3': 'H', '4': 'H', '5': 'H', '6': 'H'}
        
        attendance = AttendanceService.save_attendance(
            student=self.student,
            target_date=target_date,
            jp_statuses=jp_statuses,
            user=self.user
        )
        
        self.assertIsNotNone(attendance)
        self.assertEqual(attendance.student, self.student)
        self.assertEqual(attendance.jp_statuses, jp_statuses)
    
    def test_get_attendance(self):
        """Test getting attendance for a student"""
        target_date = date(2026, 1, 13)  # Tuesday
        jp_statuses = {'1': 'H', '2': 'S', '3': 'H', '4': 'H', '5': 'H', '6': 'H'}
        
        AttendanceService.save_attendance(
            student=self.student,
            target_date=target_date,
            jp_statuses=jp_statuses,
            user=self.user
        )
        
        attendance = AttendanceService.get_attendance(self.student, target_date)
        self.assertIsNotNone(attendance)
        self.assertEqual(attendance.jp_statuses['2'], 'S')
    
    def test_get_class_attendance(self):
        """Test getting attendance for a classroom"""
        target_date = date(2026, 1, 14)  # Wednesday
        jp_statuses = {'1': 'H', '2': 'H', '3': 'H', '4': 'H', '5': 'H', '6': 'H'}
        
        AttendanceService.save_attendance(
            student=self.student,
            target_date=target_date,
            jp_statuses=jp_statuses,
            user=self.user
        )
        
        attendances = AttendanceService.get_class_attendance(self.classroom, target_date)
        self.assertEqual(len(attendances), 1)
    
    def test_save_attendance_invalid_status(self):
        """Test saving attendance with invalid status"""
        target_date = date(2026, 1, 15)
        jp_statuses = {'1': 'X', '2': 'H', '3': 'H', '4': 'H', '5': 'H', '6': 'H'}
        
        with self.assertRaises(ValidationError):
            AttendanceService.save_attendance(
                student=self.student,
                target_date=target_date,
                jp_statuses=jp_statuses,
                user=self.user
            )


class HolidayServiceTests(TestCase):
    """Tests for HolidayService (Task 2.3)"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        cls.user = User.objects.create_user(
            username='testadmin2',
            password='testpass123'
        )
        cls.academic_level = AcademicLevel.objects.create(
            code='SMA2',
            name='Sekolah Menengah Atas',
            level_type='SMA',
            min_grade=10,
            max_grade=12
        )
        cls.classroom1 = Classroom.objects.create(
            academic_level=cls.academic_level,
            grade=11,
            section='A',
            name='Kelas 11A',
            academic_year='2025/2026'
        )
        cls.classroom2 = Classroom.objects.create(
            academic_level=cls.academic_level,
            grade=11,
            section='B',
            name='Kelas 11B',
            academic_year='2025/2026'
        )
    
    def test_is_holiday_global(self):
        """Test checking global holiday"""
        Holiday.objects.create(
            date=date(2026, 1, 20),
            name='Global Holiday',
            holiday_type='LAINNYA',
            apply_to_all=True
        )
        
        self.assertTrue(HolidayService.is_holiday(date(2026, 1, 20)))
        self.assertTrue(HolidayService.is_holiday(date(2026, 1, 20), self.classroom1))
    
    def test_is_holiday_classroom_specific(self):
        """Test checking classroom-specific holiday"""
        holiday = Holiday.objects.create(
            date=date(2026, 1, 21),
            name='Class 11A Holiday',
            holiday_type='UAS',
            apply_to_all=False
        )
        holiday.classrooms.add(self.classroom1)
        
        self.assertTrue(HolidayService.is_holiday(date(2026, 1, 21), self.classroom1))
        self.assertFalse(HolidayService.is_holiday(date(2026, 1, 21), self.classroom2))
    
    def test_is_holiday_no_holiday(self):
        """Test checking a date with no holiday"""
        self.assertFalse(HolidayService.is_holiday(date(2026, 1, 22)))
    
    def test_get_holidays(self):
        """Test getting holidays in date range"""
        Holiday.objects.create(
            date=date(2026, 2, 1),
            name='Holiday 1',
            holiday_type='LAINNYA',
            apply_to_all=True
        )
        Holiday.objects.create(
            date=date(2026, 2, 5),
            name='Holiday 2',
            holiday_type='PESANTREN',
            apply_to_all=True
        )
        
        holidays = HolidayService.get_holidays(date(2026, 2, 1), date(2026, 2, 10))
        self.assertEqual(len(holidays), 2)
    
    def test_create_holiday(self):
        """Test creating a holiday via service"""
        data = {
            'date': date(2026, 2, 15),
            'name': 'New Holiday',
            'holiday_type': 'UN',
            'apply_to_all': True,
            'description': 'Test description'
        }
        
        holiday = HolidayService.create_holiday(data, self.user)
        self.assertIsNotNone(holiday)
        self.assertEqual(holiday.name, 'New Holiday')
        self.assertEqual(holiday.created_by, self.user)
    
    def test_create_holiday_classroom_specific(self):
        """Test creating classroom-specific holiday"""
        data = {
            'date': date(2026, 2, 16),
            'name': 'Class Holiday',
            'holiday_type': 'UAS',
            'apply_to_all': False,
            'classroom_ids': [str(self.classroom1.id)]
        }
        
        holiday = HolidayService.create_holiday(data, self.user)
        self.assertFalse(holiday.apply_to_all)
        self.assertTrue(holiday.classrooms.filter(id=self.classroom1.id).exists())
    
    def test_create_holiday_invalid_type(self):
        """Test creating holiday with invalid type"""
        data = {
            'date': date(2026, 2, 17),
            'name': 'Invalid Holiday',
            'holiday_type': 'INVALID'
        }
        
        with self.assertRaises(ValidationError):
            HolidayService.create_holiday(data, self.user)


class MissingAttendanceTests(TestCase):
    """Tests for missing attendance calculation"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        cls.user = User.objects.create_user(
            username='testteacher3',
            password='testpass123'
        )
        cls.academic_level = AcademicLevel.objects.create(
            code='SMP3',
            name='Sekolah Menengah Pertama',
            level_type='SMP',
            min_grade=7,
            max_grade=9
        )
        cls.classroom = Classroom.objects.create(
            academic_level=cls.academic_level,
            grade=9,
            section='C',
            name='Kelas 9C',
            academic_year='2025/2026'
        )
        cls.student = Student.objects.create(
            student_id='STU003',
            name='Citra Test',
            classroom=cls.classroom
        )
    
    def test_get_missing_attendance_all_missing(self):
        """Test getting missing attendance when no records exist"""
        # Use a week with no attendance records
        start_date = date(2026, 2, 2)  # Monday
        end_date = date(2026, 2, 6)    # Friday
        
        missing = AttendanceService.get_missing_attendance(
            self.classroom, start_date, end_date
        )
        
        # Should have 5 missing days (Mon-Fri are school days)
        self.assertEqual(len(missing), 5)
    
    def test_get_missing_attendance_with_records(self):
        """Test getting missing attendance with some records"""
        start_date = date(2026, 2, 9)   # Monday
        end_date = date(2026, 2, 13)    # Friday
        
        # Add attendance for Monday
        AttendanceService.save_attendance(
            student=self.student,
            target_date=date(2026, 2, 9),
            jp_statuses={'1': 'H', '2': 'H', '3': 'H', '4': 'H', '5': 'H', '6': 'H'},
            user=self.user
        )
        
        missing = AttendanceService.get_missing_attendance(
            self.classroom, start_date, end_date
        )
        
        # Should have 4 missing days (Tue-Fri)
        self.assertEqual(len(missing), 4)
        self.assertNotIn(date(2026, 2, 9), missing)
    
    def test_get_missing_attendance_excludes_holidays(self):
        """Test that holidays are excluded from missing attendance"""
        start_date = date(2026, 3, 2)   # Monday
        end_date = date(2026, 3, 6)     # Friday
        
        # Create a holiday on Wednesday
        Holiday.objects.create(
            date=date(2026, 3, 4),
            name='Test Holiday',
            holiday_type='LAINNYA',
            apply_to_all=True
        )
        
        missing = AttendanceService.get_missing_attendance(
            self.classroom, start_date, end_date
        )
        
        # Should have 4 missing days (Mon, Tue, Thu, Fri - Wed is holiday)
        self.assertEqual(len(missing), 4)
        self.assertNotIn(date(2026, 3, 4), missing)
