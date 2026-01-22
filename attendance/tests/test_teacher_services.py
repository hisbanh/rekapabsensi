"""
Unit tests for teacher-related service layers.

Tests business logic for:
- TeacherService
- ScheduleService (especially conflict detection)
- TeacherAttendanceService (especially location validation)
- TeacherReportService
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils import timezone
from django.conf import settings
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from attendance.models import (
    Subject,
    Teacher,
    TeacherSchedule,
    TeacherAttendance,
    TeacherAttendanceSummary,
    Classroom,
    AcademicLevel
)
from attendance.services.teacher_service import TeacherService, TeacherServiceError
from attendance.services.schedule_service import TeacherScheduleService
from attendance.services.teacher_attendance_service import (
    TeacherAttendanceService,
    TeacherAttendanceServiceError
)
from attendance.services.teacher_report_service import (
    TeacherReportService,
    TeacherReportServiceError
)


class TeacherServiceTestCase(TestCase):
    """Test cases for TeacherService business logic."""
    
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
        
        self.subject = Subject.objects.create(
            code='MAT01',
            name='Matematika',
            category='UMUM'
        )
    
    def test_validate_teacher_data_valid(self):
        """Should validate correct teacher data."""
        data = {
            'nip': '12345',
            'full_name': 'Ahmad Yusuf',
            'employment_date': date(2020, 1, 1),
            'employment_status': 'ACTIVE',
            'email': 'ahmad@example.com'
        }
        
        errors = TeacherService.validate_teacher_data(data)
        self.assertEqual(len(errors), 0)
    
    def test_validate_teacher_data_missing_required_fields(self):
        """Should return errors for missing required fields."""
        data = {
            'nip': '12345'
        }
        
        errors = TeacherService.validate_teacher_data(data)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any('full_name' in err for err in errors))
    
    def test_validate_teacher_data_invalid_email(self):
        """Should return error for invalid email format."""
        data = {
            'nip': '12345',
            'full_name': 'Ahmad Yusuf',
            'employment_date': date(2020, 1, 1),
            'employment_status': 'ACTIVE',
            'email': 'invalid-email'
        }
        
        errors = TeacherService.validate_teacher_data(data)
        self.assertTrue(any('email' in err.lower() for err in errors))
    
    def test_validate_teacher_data_future_employment_date(self):
        """Should return error for future employment date."""
        future_date = timezone.now().date() + timedelta(days=30)
        data = {
            'nip': '12345',
            'full_name': 'Ahmad Yusuf',
            'employment_date': future_date,
            'employment_status': 'ACTIVE'
        }
        
        errors = TeacherService.validate_teacher_data(data)
        self.assertTrue(any('future' in err.lower() for err in errors))
    
    def test_create_teacher_success(self):
        """Should create teacher with valid data."""
        data = {
            'nip': '12345',
            'full_name': 'Ahmad Yusuf',
            'employment_date': date(2020, 1, 1),
            'employment_status': 'ACTIVE',
            'email': 'ahmad@example.com'
        }
        
        teacher = TeacherService.create_teacher(data)
        
        self.assertIsNotNone(teacher.id)
        self.assertEqual(teacher.nip, '12345')
        self.assertEqual(teacher.full_name, 'Ahmad Yusuf')
    
    def test_create_teacher_nip_uppercase(self):
        """Should convert NIP to uppercase."""
        data = {
            'nip': 'abc123',
            'full_name': 'Ahmad Yusuf',
            'employment_date': date(2020, 1, 1),
            'employment_status': 'ACTIVE'
        }
        
        teacher = TeacherService.create_teacher(data)
        self.assertEqual(teacher.nip, 'ABC123')
    
    def test_create_teacher_validation_error(self):
        """Should raise error for invalid data."""
        data = {
            'nip': '12345',
            'full_name': 'Ab',  # Too short
            'employment_date': date(2020, 1, 1),
            'employment_status': 'ACTIVE'
        }
        
        with self.assertRaises(TeacherServiceError):
            TeacherService.create_teacher(data)
    
    def test_update_teacher_success(self):
        """Should update teacher with valid data."""
        teacher = Teacher.objects.create(
            nip='12345',
            full_name='Ahmad Yusuf',
            employment_date=date(2020, 1, 1),
            employment_status='ACTIVE'
        )
        
        updates = {
            'email': 'newemail@example.com',
            'phone': '081234567890'
        }
        
        updated_teacher = TeacherService.update_teacher(teacher.id, updates)
        
        self.assertEqual(updated_teacher.email, 'newemail@example.com')
        self.assertEqual(updated_teacher.phone, '081234567890')
    
    def test_update_teacher_not_found(self):
        """Should raise error if teacher not found."""
        fake_id = uuid4()
        
        with self.assertRaises(TeacherServiceError):
            TeacherService.update_teacher(fake_id, {'email': 'test@example.com'})
    
    def test_get_teacher_profile_success(self):
        """Should return complete teacher profile."""
        teacher = Teacher.objects.create(
            nip='12345',
            full_name='Ahmad Yusuf',
            employment_date=date(2020, 1, 1),
            employment_status='ACTIVE'
        )
        teacher.subjects.add(self.subject)
        
        profile = TeacherService.get_teacher_profile(teacher.id)
        
        self.assertEqual(profile['teacher'], teacher)
        self.assertIn(self.subject, profile['subjects'])
        self.assertIn('teaching_load', profile)
    
    def test_assign_subjects_success(self):
        """Should assign subjects to teacher."""
        teacher = Teacher.objects.create(
            nip='12345',
            full_name='Ahmad Yusuf',
            employment_date=date(2020, 1, 1),
            employment_status='ACTIVE'
        )
        
        subject2 = Subject.objects.create(
            code='FIS01',
            name='Fisika',
            category='UMUM'
        )
        
        TeacherService.assign_subjects(teacher.id, [self.subject.id, subject2.id])
        
        teacher.refresh_from_db()
        self.assertEqual(teacher.subjects.count(), 2)
    
    def test_get_teacher_statistics_success(self):
        """Should return teacher statistics."""
        teacher = Teacher.objects.create(
            nip='12345',
            full_name='Ahmad Yusuf',
            employment_date=date(2020, 1, 1),
            employment_status='ACTIVE'
        )
        
        stats = TeacherService.get_teacher_statistics(teacher.id, 2024, 1)
        
        self.assertEqual(stats['teacher'], teacher)
        self.assertEqual(stats['year'], 2024)
        self.assertEqual(stats['month'], 1)
        self.assertIn('total_hadir', stats)
    
    def test_get_teachers_with_filters_search(self):
        """Should filter teachers by search query."""
        Teacher.objects.create(
            nip='12345',
            full_name='Ahmad Yusuf',
            employment_date=date(2020, 1, 1),
            employment_status='ACTIVE'
        )
        Teacher.objects.create(
            nip='67890',
            full_name='Fatimah Zahra',
            employment_date=date(2020, 1, 1),
            employment_status='ACTIVE'
        )
        
        filters = {'search_query': 'Ahmad'}
        teachers = TeacherService.get_teachers_with_filters(filters)
        
        self.assertEqual(len(teachers), 1)
        self.assertEqual(teachers[0].full_name, 'Ahmad Yusuf')


class ScheduleServiceTestCase(TestCase):
    """Test cases for ScheduleService, especially conflict detection."""
    
    def setUp(self):
        """Set up test data."""
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
            employment_date=date(2020, 1, 1),
            employment_status='ACTIVE'
        )
        
        self.subject = Subject.objects.create(
            code='MAT01',
            name='Matematika',
            category='UMUM'
        )
    
    def test_create_schedule_success(self):
        """Should create schedule with valid data."""
        data = {
            'teacher_id': self.teacher.id,
            'subject_id': self.subject.id,
            'classroom_id': self.classroom.id,
            'day_of_week': 0,
            'jp_start': 1,
            'jp_end': 2,
            'effective_date': date(2024, 1, 1)
        }
        
        schedule = TeacherScheduleService.create_schedule(data)
        
        self.assertIsNotNone(schedule.id)
        self.assertEqual(schedule.teacher, self.teacher)
        self.assertEqual(schedule.jp_start, 1)
    
    def test_detect_conflicts_teacher_overlap(self):
        """Should detect teacher schedule conflicts."""
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
        
        # Check for conflicts with overlapping schedule
        conflicts = TeacherScheduleService.detect_conflicts(
            teacher_id=self.teacher.id,
            day=0,
            jp_start=2,
            jp_end=3,
            effective_date=date(2024, 1, 1)
        )
        
        self.assertGreater(len(conflicts), 0)
        self.assertEqual(conflicts[0]['type'], 'teacher')
    
    def test_detect_conflicts_classroom_overlap(self):
        """Should detect classroom schedule conflicts."""
        teacher2 = Teacher.objects.create(
            nip='67890',
            full_name='Fatimah Zahra',
            employment_date=date(2020, 1, 1),
            employment_status='ACTIVE'
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
        
        # Check for conflicts with same classroom
        conflicts = TeacherScheduleService.detect_conflicts(
            teacher_id=teacher2.id,
            day=0,
            jp_start=2,
            jp_end=3,
            effective_date=date(2024, 1, 1),
            classroom_id=self.classroom.id
        )
        
        self.assertGreater(len(conflicts), 0)
        self.assertEqual(conflicts[0]['type'], 'classroom')
    
    def test_detect_conflicts_no_overlap(self):
        """Should not detect conflicts for non-overlapping schedules."""
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
        
        # Check for conflicts with non-overlapping schedule
        conflicts = TeacherScheduleService.detect_conflicts(
            teacher_id=self.teacher.id,
            day=0,
            jp_start=3,
            jp_end=4,
            effective_date=date(2024, 1, 1)
        )
        
        self.assertEqual(len(conflicts), 0)
    
    def test_get_weekly_schedule_success(self):
        """Should return teacher's weekly schedule."""
        TeacherSchedule.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=0,
            jp_start=1,
            jp_end=2,
            effective_date=date(2024, 1, 1)
        )
        
        weekly_schedule = TeacherScheduleService.get_weekly_schedule(self.teacher.id)
        
        self.assertIsInstance(weekly_schedule, dict)
        self.assertIn(0, weekly_schedule)
        self.assertEqual(len(weekly_schedule[0]), 1)
    
    def test_get_classroom_schedule_success(self):
        """Should return classroom schedule for a day."""
        TeacherSchedule.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=0,
            jp_start=1,
            jp_end=2,
            effective_date=date(2024, 1, 1)
        )
        
        schedules = TeacherScheduleService.get_classroom_schedule(self.classroom.id, 0)
        
        self.assertEqual(len(schedules), 1)
        self.assertEqual(schedules[0].teacher, self.teacher)
    
    def test_get_teacher_teaching_load_success(self):
        """Should calculate teacher's teaching load."""
        TeacherSchedule.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=0,
            jp_start=1,
            jp_end=4,
            effective_date=date(2024, 1, 1)
        )
        
        load = TeacherScheduleService.get_teacher_teaching_load(self.teacher.id)
        
        self.assertEqual(load['total_jp_per_week'], 4)
        self.assertEqual(load['schedules_count'], 1)


class TeacherAttendanceServiceTestCase(TestCase):
    """Test cases for TeacherAttendanceService, especially location validation."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.teacher = Teacher.objects.create(
            nip='12345',
            full_name='Ahmad Yusuf',
            employment_date=date(2020, 1, 1),
            employment_status='ACTIVE'
        )
    
    def test_validate_location_within_radius(self):
        """Should validate location within school radius."""
        # Use school coordinates (should be valid)
        lat = TeacherAttendanceService.SCHOOL_LATITUDE
        lon = TeacherAttendanceService.SCHOOL_LONGITUDE
        
        is_valid = TeacherAttendanceService.validate_location(lat, lon)
        
        self.assertTrue(is_valid)
    
    def test_validate_location_outside_radius(self):
        """Should reject location outside school radius."""
        # Use coordinates far from school
        lat = -7.9000  # Far from school
        lon = 110.5000
        
        is_valid = TeacherAttendanceService.validate_location(lat, lon)
        
        self.assertFalse(is_valid)
    
    def test_validate_location_invalid_latitude(self):
        """Should raise error for invalid latitude."""
        with self.assertRaises(TeacherAttendanceServiceError):
            TeacherAttendanceService.validate_location(91.0, 110.0)
    
    def test_validate_location_invalid_longitude(self):
        """Should raise error for invalid longitude."""
        with self.assertRaises(TeacherAttendanceServiceError):
            TeacherAttendanceService.validate_location(-7.7956, 181.0)
    
    def test_record_attendance_success(self):
        """Should record attendance with valid data."""
        data = {
            'teacher_id': self.teacher.id,
            'date': date.today(),
            'jp_number': 1,
            'status': 'HADIR',
            'recorded_by': self.user
        }
        
        attendance = TeacherAttendanceService.record_attendance(data)
        
        self.assertIsNotNone(attendance.id)
        self.assertEqual(attendance.teacher, self.teacher)
        self.assertEqual(attendance.status, 'HADIR')
    
    def test_record_attendance_with_location(self):
        """Should record attendance with location validation."""
        data = {
            'teacher_id': self.teacher.id,
            'date': date.today(),
            'jp_number': 1,
            'status': 'HADIR',
            'recorded_by': self.user,
            'latitude': TeacherAttendanceService.SCHOOL_LATITUDE,
            'longitude': TeacherAttendanceService.SCHOOL_LONGITUDE
        }
        
        attendance = TeacherAttendanceService.record_attendance(data)
        
        self.assertTrue(attendance.is_location_valid)
    
    def test_record_attendance_duplicate_error(self):
        """Should raise error for duplicate attendance."""
        data = {
            'teacher_id': self.teacher.id,
            'date': date.today(),
            'jp_number': 1,
            'status': 'HADIR',
            'recorded_by': self.user
        }
        
        TeacherAttendanceService.record_attendance(data)
        
        with self.assertRaises(TeacherAttendanceServiceError):
            TeacherAttendanceService.record_attendance(data)
    
    def test_get_daily_attendance_success(self):
        """Should return daily attendance records."""
        TeacherAttendance.objects.create(
            teacher=self.teacher,
            date=date.today(),
            jp_number=1,
            status='HADIR',
            recorded_by=self.user
        )
        
        attendances = TeacherAttendanceService.get_daily_attendance(date.today())
        
        self.assertEqual(len(attendances), 1)
        self.assertEqual(attendances[0].teacher, self.teacher)
    
    def test_get_teacher_attendance_history_success(self):
        """Should return teacher attendance history."""
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        TeacherAttendance.objects.create(
            teacher=self.teacher,
            date=date.today(),
            jp_number=1,
            status='HADIR',
            recorded_by=self.user
        )
        
        history = TeacherAttendanceService.get_teacher_attendance_history(
            self.teacher.id,
            start_date,
            end_date
        )
        
        self.assertEqual(len(history), 1)
    
    def test_calculate_monthly_summary_success(self):
        """Should calculate monthly attendance summary."""
        today = date.today()
        
        # Create some attendance records
        TeacherAttendance.objects.create(
            teacher=self.teacher,
            date=today,
            jp_number=1,
            status='HADIR',
            recorded_by=self.user
        )
        
        summary = TeacherAttendanceService.calculate_monthly_summary(
            self.teacher.id,
            today.year,
            today.month
        )
        
        self.assertEqual(summary['teacher'], self.teacher)
        self.assertGreaterEqual(summary['total_hadir'], 1)
    
    def test_get_absent_teachers_success(self):
        """Should return list of absent teachers."""
        # Create a schedule for today
        academic_level, _ = AcademicLevel.objects.get_or_create(
            code='SMP',
            defaults={
                'name': 'Sekolah Menengah Pertama',
                'level_type': 'SMP',
                'min_grade': 7,
                'max_grade': 9
            }
        )
        
        classroom, _ = Classroom.objects.get_or_create(
            academic_level=academic_level,
            grade=8,
            section='A',
            academic_year='2024/2025',
            defaults={'name': 'Kelas 8-A'}
        )
        
        subject = Subject.objects.create(
            code='MAT01',
            name='Matematika',
            category='UMUM'
        )
        
        today = date.today()
        day_of_week = today.weekday()
        
        TeacherSchedule.objects.create(
            teacher=self.teacher,
            subject=subject,
            classroom=classroom,
            day_of_week=day_of_week,
            jp_start=1,
            jp_end=2,
            effective_date=today - timedelta(days=30)
        )
        
        absent = TeacherAttendanceService.get_absent_teachers(today, 1)
        
        # Teacher should be in absent list since no attendance recorded
        self.assertGreater(len(absent), 0)


class TeacherReportServiceTestCase(TestCase):
    """Test cases for TeacherReportService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.teacher = Teacher.objects.create(
            nip='12345',
            full_name='Ahmad Yusuf',
            employment_date=date(2020, 1, 1),
            employment_status='ACTIVE'
        )
        
        # Create some attendance records
        for i in range(5):
            TeacherAttendance.objects.create(
                teacher=self.teacher,
                date=date.today() - timedelta(days=i),
                jp_number=1,
                status='HADIR',
                recorded_by=self.user
            )
    
    def test_generate_teacher_report_pdf_success(self):
        """Should generate PDF report."""
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        pdf_bytes = TeacherReportService.generate_teacher_report_pdf(
            self.teacher.id,
            start_date,
            end_date
        )
        
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 0)
    
    def test_get_attendance_analytics_success(self):
        """Should return attendance analytics."""
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        analytics = TeacherReportService.get_attendance_analytics(
            start_date,
            end_date
        )
        
        self.assertIn('overall_stats', analytics)
        self.assertIn('teacher_stats', analytics)
        self.assertIn('daily_trends', analytics)
    
    def test_export_attendance_excel_success(self):
        """Should export attendance to Excel."""
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        excel_bytes = TeacherReportService.export_attendance_excel(
            start_date,
            end_date
        )
        
        self.assertIsInstance(excel_bytes, bytes)
        self.assertGreater(len(excel_bytes), 0)
    
    def test_get_dashboard_statistics_success(self):
        """Should return dashboard statistics."""
        stats = TeacherReportService.get_dashboard_statistics()
        
        self.assertIn('today', stats)
        self.assertIn('today_stats', stats)
        self.assertIn('recent_trends', stats)
        self.assertIn('notifications', stats)
    
    def test_generate_monthly_report_success(self):
        """Should generate monthly report."""
        today = date.today()
        
        report = TeacherReportService.generate_monthly_report(
            today.year,
            today.month
        )
        
        self.assertIn('period', report)
        self.assertIn('monthly_summaries', report)
        self.assertIn('aggregate_stats', report)
