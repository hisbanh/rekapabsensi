"""
Tests for Teacher Report API Endpoints
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, timedelta
from uuid import uuid4

from attendance.models import Teacher, Subject, Classroom, TeacherSchedule, TeacherAttendance


class TeacherReportAPITestCase(TestCase):
    """Test cases for teacher report API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='teacher1',
            password='teacher123'
        )
        
        # Create teacher
        self.teacher = Teacher.objects.create(
            nip='12345',
            full_name='Ahmad Yusuf',
            employment_date=date(2024, 1, 1),
            employment_status='ACTIVE',
            user=self.regular_user
        )
        
        # Create another teacher without user
        self.teacher2 = Teacher.objects.create(
            nip='67890',
            full_name='Fatimah Zahra',
            employment_date=date(2024, 1, 1),
            employment_status='ACTIVE'
        )
        
        # Create subject
        self.subject = Subject.objects.create(
            code='MAT',
            name='Matematika',
            category='UMUM'
        )
        
        # Create academic level first
        from attendance.models import AcademicLevel
        self.academic_level, _ = AcademicLevel.objects.get_or_create(
            code='SMP',
            defaults={
                'name': 'SMP',
                'level_type': 'SMP',
                'description': 'Sekolah Menengah Pertama',
                'min_grade': 7,
                'max_grade': 9
            }
        )
        
        # Create classroom
        self.classroom = Classroom.objects.create(
            name='8A',
            grade='8',
            academic_level=self.academic_level
        )
        
        # Create schedule
        self.schedule = TeacherSchedule.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=0,
            jp_start=1,
            jp_end=2,
            effective_date=date(2024, 1, 1)
        )
        
        # Create attendance records
        today = date.today()
        for i in range(5):
            TeacherAttendance.objects.create(
                teacher=self.teacher,
                schedule=self.schedule,
                date=today - timedelta(days=i),
                jp_number=1,
                status='HADIR',
                recorded_by=self.admin_user
            )
        
        self.client = Client()
    
    def test_dashboard_stats_admin(self):
        """Test dashboard stats endpoint as admin"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get('/api/reports/dashboard/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('today', data['data'])
        self.assertIn('today_stats', data['data'])
        self.assertIn('absent_today', data['data'])
        self.assertIn('recent_trends', data['data'])
        self.assertIn('notifications', data['data'])
        self.assertIn('quick_stats', data['data'])
    
    def test_dashboard_stats_teacher(self):
        """Test dashboard stats endpoint as teacher"""
        self.client.login(username='teacher1', password='teacher123')
        
        response = self.client.get('/api/reports/dashboard/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        # Teachers should see filtered data
        self.assertIn('today_stats', data['data'])
    
    def test_dashboard_stats_unauthenticated(self):
        """Test dashboard stats endpoint without authentication"""
        response = self.client.get('/api/reports/dashboard/')
        
        # Should redirect to login or return 302/403
        self.assertIn(response.status_code, [302, 403])
    
    def test_analytics_admin(self):
        """Test analytics endpoint as admin"""
        self.client.login(username='admin', password='admin123')
        
        start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = date.today().strftime('%Y-%m-%d')
        
        response = self.client.get(
            f'/api/reports/analytics/?start_date={start_date}&end_date={end_date}'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('period', data['data'])
        self.assertIn('overall_stats', data['data'])
        self.assertIn('teacher_stats', data['data'])
        self.assertIn('daily_trends', data['data'])
    
    def test_analytics_teacher_forbidden(self):
        """Test analytics endpoint as teacher (should be forbidden)"""
        self.client.login(username='teacher1', password='teacher123')
        
        start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = date.today().strftime('%Y-%m-%d')
        
        response = self.client.get(
            f'/api/reports/analytics/?start_date={start_date}&end_date={end_date}'
        )
        
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_analytics_missing_dates(self):
        """Test analytics endpoint without required date parameters"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get('/api/reports/analytics/')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_export_excel_admin(self):
        """Test Excel export endpoint as admin"""
        self.client.login(username='admin', password='admin123')
        
        start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = date.today().strftime('%Y-%m-%d')
        
        response = self.client.get(
            f'/api/reports/export/excel/?start_date={start_date}&end_date={end_date}'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn('attachment', response['Content-Disposition'])
    
    def test_export_excel_teacher_forbidden(self):
        """Test Excel export endpoint as teacher (should be forbidden)"""
        self.client.login(username='teacher1', password='teacher123')
        
        start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = date.today().strftime('%Y-%m-%d')
        
        response = self.client.get(
            f'/api/reports/export/excel/?start_date={start_date}&end_date={end_date}'
        )
        
        self.assertEqual(response.status_code, 403)
    
    def test_teacher_report_pdf_admin(self):
        """Test PDF report generation as admin"""
        self.client.login(username='admin', password='admin123')
        
        start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = date.today().strftime('%Y-%m-%d')
        
        response = self.client.get(
            f'/api/reports/teacher/{self.teacher.id}/pdf/?start_date={start_date}&end_date={end_date}'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
    
    def test_teacher_report_pdf_own_report(self):
        """Test PDF report generation for own report as teacher"""
        self.client.login(username='teacher1', password='teacher123')
        
        start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = date.today().strftime('%Y-%m-%d')
        
        response = self.client.get(
            f'/api/reports/teacher/{self.teacher.id}/pdf/?start_date={start_date}&end_date={end_date}'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
    
    def test_teacher_report_pdf_other_teacher_forbidden(self):
        """Test PDF report generation for another teacher (should be forbidden)"""
        self.client.login(username='teacher1', password='teacher123')
        
        start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = date.today().strftime('%Y-%m-%d')
        
        response = self.client.get(
            f'/api/reports/teacher/{self.teacher2.id}/pdf/?start_date={start_date}&end_date={end_date}'
        )
        
        self.assertEqual(response.status_code, 403)
    
    def test_teacher_report_pdf_invalid_teacher_id(self):
        """Test PDF report generation with invalid teacher ID"""
        self.client.login(username='admin', password='admin123')
        
        start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = date.today().strftime('%Y-%m-%d')
        
        response = self.client.get(
            f'/api/reports/teacher/invalid-uuid/pdf/?start_date={start_date}&end_date={end_date}'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_teacher_report_pdf_missing_dates(self):
        """Test PDF report generation without required date parameters"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get(
            f'/api/reports/teacher/{self.teacher.id}/pdf/'
        )
        
        self.assertEqual(response.status_code, 400)
