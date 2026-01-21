"""
Tests for Notification Service
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta

from attendance.models import (
    Teacher, Subject, Classroom, AcademicLevel,
    TeacherSchedule, TeacherAttendance
)
from attendance.services.notification_service import (
    NotificationService,
    NotificationServiceError
)


class NotificationServiceTest(TestCase):
    """Test cases for NotificationService"""
    
    def setUp(self):
        """Set up test data"""
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Get or create academic level
        self.academic_level, _ = AcademicLevel.objects.get_or_create(
            code='SMP',
            defaults={
                'name': 'Sekolah Menengah Pertama',
                'level_type': 'SMP',
                'min_grade': 7,
                'max_grade': 9
            }
        )
        
        # Create classroom
        self.classroom = Classroom.objects.create(
            academic_level=self.academic_level,
            grade=8,
            section='A',
            name='Kelas 8-A',
            academic_year='2024/2025'
        )
        
        # Create subject
        self.subject = Subject.objects.create(
            code='MAT',
            name='Matematika',
            category='UMUM'
        )
        
        # Create teachers
        self.teacher1 = Teacher.objects.create(
            nip='12345',
            full_name='Ahmad Yusuf',
            employment_date=date(2024, 1, 1),
            employment_status='ACTIVE'
        )
        
        self.teacher2 = Teacher.objects.create(
            nip='67890',
            full_name='Fatimah Zahra',
            employment_date=date(2024, 1, 1),
            employment_status='ACTIVE'
        )
        
        # Create schedules for today
        today = timezone.now().date()
        day_of_week = today.weekday()
        
        self.schedule1 = TeacherSchedule.objects.create(
            teacher=self.teacher1,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=day_of_week,
            jp_start=1,
            jp_end=2,
            effective_date=today - timedelta(days=7),
            is_active=True
        )
        
        self.schedule2 = TeacherSchedule.objects.create(
            teacher=self.teacher2,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=day_of_week,
            jp_start=3,
            jp_end=4,
            effective_date=today - timedelta(days=7),
            is_active=True
        )
    
    def test_get_missing_attendance_notification(self):
        """Test getting notifications for missing attendance"""
        today = timezone.now().date()
        
        # No attendance recorded yet
        notifications = NotificationService.get_missing_attendance_notification(today)
        
        # Should have 2 notifications (one for each teacher)
        self.assertEqual(len(notifications), 2)
        
        # Check notification structure
        notif = notifications[0]
        self.assertEqual(notif['type'], NotificationService.TYPE_MISSING_ATTENDANCE)
        self.assertEqual(notif['priority'], NotificationService.PRIORITY_HIGH)
        self.assertEqual(notif['date'], today)
        self.assertIn('teacher', notif)
        self.assertIn('scheduled_jp', notif)
        self.assertIn('total_jp', notif)
        
        # Record attendance for teacher1
        TeacherAttendance.objects.create(
            teacher=self.teacher1,
            date=today,
            jp_number=1,
            status='HADIR',
            recorded_by=self.user
        )
        
        # Now should have only 1 notification (teacher2)
        notifications = NotificationService.get_missing_attendance_notification(today)
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0]['teacher'], self.teacher2)
    
    def test_get_absent_teachers_notification(self):
        """Test getting notifications for absent teachers"""
        today = timezone.now().date()
        
        # Record attendance with SAKIT status
        TeacherAttendance.objects.create(
            teacher=self.teacher1,
            date=today,
            jp_number=1,
            status='SAKIT',
            recorded_by=self.user
        )
        
        # Get notifications
        notifications = NotificationService.get_absent_teachers_notification(today)
        
        # Should have notifications for absent teacher
        self.assertGreater(len(notifications), 0)
        
        # Find notification for teacher1
        teacher1_notifs = [n for n in notifications if n['teacher'] == self.teacher1]
        self.assertGreater(len(teacher1_notifs), 0)
        
        # Check notification structure
        notif = teacher1_notifs[0]
        self.assertEqual(notif['type'], NotificationService.TYPE_ABSENT)
        self.assertEqual(notif['status'], 'SAKIT')
        self.assertEqual(notif['priority'], NotificationService.PRIORITY_MEDIUM)
    
    def test_get_scheduling_conflicts_notification(self):
        """Test getting notifications for scheduling conflicts"""
        today = timezone.now().date()
        day_of_week = today.weekday()
        
        # Create conflicting schedule (same teacher, overlapping JP)
        conflicting_schedule = TeacherSchedule.objects.create(
            teacher=self.teacher1,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=day_of_week,
            jp_start=2,  # Overlaps with schedule1 (JP 1-2)
            jp_end=3,
            effective_date=today - timedelta(days=7),
            is_active=True
        )
        
        # Get conflict notifications
        notifications = NotificationService.get_scheduling_conflicts_notification()
        
        # Should have at least one conflict
        self.assertGreater(len(notifications), 0)
        
        # Check notification structure
        notif = notifications[0]
        self.assertEqual(notif['type'], NotificationService.TYPE_CONFLICT)
        self.assertEqual(notif['priority'], NotificationService.PRIORITY_MEDIUM)
        self.assertIn('conflict_type', notif)
        self.assertIn('jp_overlap', notif)
    
    def test_get_all_notifications(self):
        """Test getting all notifications at once"""
        today = timezone.now().date()
        
        # Record some attendance
        TeacherAttendance.objects.create(
            teacher=self.teacher1,
            date=today,
            jp_number=1,
            status='SAKIT',
            recorded_by=self.user
        )
        
        # Get all notifications
        all_notifs = NotificationService.get_all_notifications(today)
        
        # Check structure
        self.assertIn('absent_teachers', all_notifs)
        self.assertIn('missing_attendance', all_notifs)
        self.assertIn('scheduling_conflicts', all_notifs)
        self.assertIn('all_notifications', all_notifs)
        self.assertIn('total_count', all_notifs)
        self.assertIn('high_priority_count', all_notifs)
        
        # Should have some notifications
        self.assertGreater(all_notifs['total_count'], 0)
    
    def test_send_notification(self):
        """Test sending notification (placeholder)"""
        # This is a placeholder method, just test it doesn't raise errors
        try:
            NotificationService.send_notification(
                self.user,
                'Test notification',
                NotificationService.TYPE_INFO
            )
        except Exception as e:
            self.fail(f"send_notification raised exception: {e}")
    
    def test_notification_priority_levels(self):
        """Test that different statuses get correct priority levels"""
        today = timezone.now().date()
        
        # Test ALPA (high priority)
        TeacherAttendance.objects.create(
            teacher=self.teacher1,
            date=today,
            jp_number=1,
            status='ALPA',
            recorded_by=self.user
        )
        
        notifications = NotificationService.get_absent_teachers_notification(today)
        alpa_notifs = [n for n in notifications if n['status'] == 'ALPA']
        if alpa_notifs:
            self.assertEqual(alpa_notifs[0]['priority'], NotificationService.PRIORITY_HIGH)
        
        # Test SAKIT (medium priority)
        TeacherAttendance.objects.create(
            teacher=self.teacher2,
            date=today,
            jp_number=3,
            status='SAKIT',
            recorded_by=self.user
        )
        
        notifications = NotificationService.get_absent_teachers_notification(today)
        sakit_notifs = [n for n in notifications if n['status'] == 'SAKIT']
        if sakit_notifs:
            self.assertEqual(sakit_notifs[0]['priority'], NotificationService.PRIORITY_MEDIUM)
