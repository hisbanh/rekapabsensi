"""
Unit tests for teacher dashboard views.

Tests the teacher dashboard view and API endpoint functionality.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import json

from attendance.models import Teacher, TeacherAttendance, TeacherSchedule, Subject, Classroom, AcademicLevel


class TeacherDashboardViewTestCase(TestCase):
    """Test cases for teacher dashboard view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='teacher',
            email='teacher@test.com',
            password='testpass123'
        )
        
        # Create academic level
        self.academic_level = AcademicLevel.objects.create(
            code='SMP',
            name='Sekolah Menengah Pertama'
        )
        
        # Create classroom
        self.classroom = Classroom.objects.create(
            name='8A',
            academic_level=self.academic_level,
            grade=8,
            section='A',
            is_active=True
        )
        
        # Create subject
        self.subject = Subject.objects.create(
            code='MAT',
            name='Matematika',
            category='UMUM',
            is_active=True
        )
        
        # Create teacher
        self.teacher = Teacher.objects.create(
            nip='1234567890',
            full_name='Ahmad Yusuf',
            email='ahmad@test.com',
            employment_date=timezone.now().date(),
            employment_status='ACTIVE',
            is_active=True
        )
        
        # Link teacher to user
        self.teacher.user = self.regular_user
        self.teacher.save()
        
        # Create schedule
        self.schedule = TeacherSchedule.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=0,  # Monday
            jp_start=1,
            jp_end=2,
            effective_date=timezone.now().date() - timedelta(days=30),
            is_active=True
        )
        
        # Create some attendance records
        today = timezone.now().date()
        for i in range(5):
            date = today - timedelta(days=i)
            TeacherAttendance.objects.create(
                teacher=self.teacher,
                schedule=self.schedule,
                date=date,
                jp_number=1,
                status='HADIR',
                recorded_by=self.admin_user
            )
    
    def test_dashboard_requires_login(self):
        """Dashboard should require authentication."""
        response = self.client.get(reverse('teacher_dashboard'))
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)
    
    def test_dashboard_loads_for_authenticated_user(self):
        """Dashboard should load for authenticated users."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('teacher_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'teacher/dashboard.html')
    
    def test_dashboard_contains_statistics(self):
        """Dashboard should contain attendance statistics."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('teacher_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('stats', response.context)
        
        stats = response.context['stats']
        self.assertIn('total_teachers', stats)
        self.assertIn('total_hadir', stats)
        self.assertIn('attendance_percentage', stats)
    
    def test_dashboard_contains_trends(self):
        """Dashboard should contain attendance trends."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('teacher_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('trends', response.context)
        
        trends = response.context['trends']
        self.assertIsInstance(trends, list)
        self.assertGreater(len(trends), 0)
    
    def test_dashboard_shows_teacher_specific_data(self):
        """Dashboard should show teacher-specific data for teachers."""
        self.client.login(username='teacher', password='testpass123')
        response = self.client.get(reverse('teacher_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('teacher_data', response.context)
        
        teacher_data = response.context['teacher_data']
        self.assertIsNotNone(teacher_data)
        self.assertEqual(teacher_data['teacher'], self.teacher)


class TeacherDashboardAPITestCase(TestCase):
    """Test cases for teacher dashboard API endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        # Create academic level
        self.academic_level = AcademicLevel.objects.create(
            code='SMP',
            name='Sekolah Menengah Pertama'
        )
        
        # Create classroom
        self.classroom = Classroom.objects.create(
            name='8A',
            academic_level=self.academic_level,
            grade=8,
            section='A',
            is_active=True
        )
        
        # Create subject
        self.subject = Subject.objects.create(
            code='MAT',
            name='Matematika',
            category='UMUM',
            is_active=True
        )
        
        # Create teacher
        self.teacher = Teacher.objects.create(
            nip='1234567890',
            full_name='Ahmad Yusuf',
            email='ahmad@test.com',
            employment_date=timezone.now().date(),
            employment_status='ACTIVE',
            is_active=True
        )
    
    def test_api_requires_login(self):
        """API should require authentication."""
        response = self.client.get(reverse('teacher_dashboard_api'))
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_api_returns_json(self):
        """API should return JSON response."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('teacher_dashboard_api'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_api_contains_required_fields(self):
        """API response should contain required fields."""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('teacher_dashboard_api'))
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('stats', data)
        self.assertIn('trends', data)
        self.assertIn('absent_teachers', data)
        self.assertIn('notifications', data)
    
    def test_api_accepts_date_range(self):
        """API should accept date range parameters."""
        self.client.login(username='admin', password='testpass123')
        
        start_date = (timezone.now().date() - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = timezone.now().date().strftime('%Y-%m-%d')
        
        response = self.client.get(
            reverse('teacher_dashboard_api'),
            {'start_date': start_date, 'end_date': end_date}
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('date_range', data)
        self.assertEqual(data['date_range']['start_date'], start_date)
        self.assertEqual(data['date_range']['end_date'], end_date)
    
    def test_api_rejects_invalid_date_format(self):
        """API should reject invalid date format."""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(
            reverse('teacher_dashboard_api'),
            {'start_date': 'invalid-date'}
        )
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
