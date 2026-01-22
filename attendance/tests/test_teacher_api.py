"""
Tests for Teacher API Endpoints
Tests all teacher management, schedule, and attendance API endpoints
"""
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, timedelta
from uuid import uuid4

from attendance.models import (
    Teacher, Subject, Classroom, TeacherSchedule, 
    TeacherAttendance, AcademicLevel
)


class TeacherAPITestCase(TestCase):
    """Test cases for teacher CRUD API endpoints"""
    
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
            email='ahmad@example.com',
            phone='081234567890',
            user=self.regular_user
        )
        
        # Create another teacher
        self.teacher2 = Teacher.objects.create(
            nip='67890',
            full_name='Fatimah Zahra',
            employment_date=date(2024, 1, 1),
            employment_status='ACTIVE',
            email='fatimah@example.com'
        )
        
        # Create subject
        self.subject = Subject.objects.create(
            code='MAT',
            name='Matematika',
            category='UMUM'
        )
        
        # Create academic level
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
        
        # Assign subject to teacher
        self.teacher.subjects.add(self.subject)
        
        self.client = Client()
    
    # Teacher List/Create Tests
    
    def test_teacher_list_authenticated(self):
        """Test listing teachers as authenticated user"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get('/api/teachers/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('teachers', data['data'])
        self.assertIn('pagination', data['data'])
    
    def test_teacher_list_unauthenticated(self):
        """Test listing teachers without authentication"""
        response = self.client.get('/api/teachers/')
        
        # Should redirect to login or return 302/403
        self.assertIn(response.status_code, [302, 403])
    
    def test_teacher_list_with_filters(self):
        """Test listing teachers with filters"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get('/api/teachers/?employment_status=ACTIVE')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertGreater(len(data['data']['teachers']), 0)
    
    def test_teacher_list_pagination(self):
        """Test teacher list pagination"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get('/api/teachers/?page=1&page_size=1')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']['teachers']), 1)
        self.assertEqual(data['data']['pagination']['page_size'], 1)
    
    def test_teacher_create_admin(self):
        """Test creating teacher as admin"""
        self.client.login(username='admin', password='admin123')
        
        teacher_data = {
            'nip': '99999',
            'full_name': 'New Teacher',
            'employment_date': '2024-01-01',
            'employment_status': 'ACTIVE',
            'email': 'newteacher@example.com',
            'phone': '081234567890',
            'is_active': True
        }
        
        response = self.client.post(
            '/api/teachers/',
            data=json.dumps(teacher_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['nip'], '99999')
    
    def test_teacher_create_non_admin_forbidden(self):
        """Test creating teacher as non-admin (should be forbidden)"""
        self.client.login(username='teacher1', password='teacher123')
        
        teacher_data = {
            'nip': '88888',
            'full_name': 'Another Teacher',
            'employment_date': '2024-01-01',
            'employment_status': 'ACTIVE'
        }
        
        response = self.client.post(
            '/api/teachers/',
            data=json.dumps(teacher_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_teacher_create_invalid_data(self):
        """Test creating teacher with invalid data"""
        self.client.login(username='admin', password='admin123')
        
        teacher_data = {
            'nip': '',  # Empty NIP
            'full_name': 'Test',
            'employment_date': '2024-01-01'
        }
        
        response = self.client.post(
            '/api/teachers/',
            data=json.dumps(teacher_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    # Teacher Detail/Update/Delete Tests
    
    def test_teacher_detail_authenticated(self):
        """Test getting teacher detail as authenticated user"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get(f'/api/teachers/{self.teacher.id}/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['nip'], '12345')
        self.assertEqual(data['data']['full_name'], 'Ahmad Yusuf')
    
    def test_teacher_detail_invalid_id(self):
        """Test getting teacher detail with invalid ID"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get('/api/teachers/invalid-uuid/')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_teacher_detail_not_found(self):
        """Test getting teacher detail for non-existent teacher"""
        self.client.login(username='admin', password='admin123')
        
        random_uuid = uuid4()
        response = self.client.get(f'/api/teachers/{random_uuid}/')
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_teacher_update_admin(self):
        """Test updating teacher as admin"""
        self.client.login(username='admin', password='admin123')
        
        update_data = {
            'full_name': 'Ahmad Yusuf Updated',
            'email': 'updated@example.com'
        }
        
        response = self.client.put(
            f'/api/teachers/{self.teacher.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['full_name'], 'Ahmad Yusuf Updated')
    
    def test_teacher_update_non_admin_forbidden(self):
        """Test updating teacher as non-admin (should be forbidden)"""
        self.client.login(username='teacher1', password='teacher123')
        
        update_data = {
            'full_name': 'Should Not Update'
        }
        
        response = self.client.put(
            f'/api/teachers/{self.teacher.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_teacher_delete_admin(self):
        """Test deleting teacher as admin (soft delete)"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.delete(f'/api/teachers/{self.teacher2.id}/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Verify soft delete
        self.teacher2.refresh_from_db()
        self.assertFalse(self.teacher2.is_active)
    
    def test_teacher_delete_non_admin_forbidden(self):
        """Test deleting teacher as non-admin (should be forbidden)"""
        self.client.login(username='teacher1', password='teacher123')
        
        response = self.client.delete(f'/api/teachers/{self.teacher2.id}/')
        
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data['success'])
    
    # Teacher Schedule Tests
    
    def test_teacher_schedule_authenticated(self):
        """Test getting teacher schedule as authenticated user"""
        self.client.login(username='admin', password='admin123')
        
        # Create a schedule first
        TeacherSchedule.objects.create(
            teacher=self.teacher,
            subject=self.subject,
            classroom=self.classroom,
            day_of_week=0,
            jp_start=1,
            jp_end=2,
            effective_date=date(2024, 1, 1)
        )
        
        response = self.client.get(f'/api/teachers/{self.teacher.id}/schedule/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('weekly_schedule', data['data'])
        self.assertEqual(data['data']['teacher_name'], 'Ahmad Yusuf')
    
    def test_teacher_schedule_invalid_id(self):
        """Test getting teacher schedule with invalid ID"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get('/api/teachers/invalid-uuid/schedule/')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    # Teacher Statistics Tests
    
    def test_teacher_statistics_authenticated(self):
        """Test getting teacher statistics as authenticated user"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get(
            f'/api/teachers/{self.teacher.id}/statistics/?year=2024&month=1'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('total_hadir', data['data'])
        self.assertIn('attendance_percentage', data['data'])
    
    def test_teacher_statistics_missing_params(self):
        """Test getting teacher statistics without required parameters"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get(f'/api/teachers/{self.teacher.id}/statistics/')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])


class ScheduleAPITestCase(TestCase):
    """Test cases for schedule API endpoints"""
    
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
        
        # Create subject
        self.subject = Subject.objects.create(
            code='MAT',
            name='Matematika',
            category='UMUM'
        )
        
        # Create academic level
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
        
        self.client = Client()
    
    # Schedule List/Create Tests
    
    def test_schedule_list_authenticated(self):
        """Test listing schedules as authenticated user"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get('/api/schedules/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('schedules', data['data'])
        self.assertIn('pagination', data['data'])
    
    def test_schedule_list_with_filters(self):
        """Test listing schedules with filters"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get(f'/api/schedules/?teacher_id={self.teacher.id}')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertGreater(len(data['data']['schedules']), 0)
    
    def test_schedule_create_admin(self):
        """Test creating schedule as admin"""
        self.client.login(username='admin', password='admin123')
        
        schedule_data = {
            'teacher_id': str(self.teacher.id),
            'subject_id': str(self.subject.id),
            'classroom_id': str(self.classroom.id),
            'day_of_week': 1,
            'jp_start': 3,
            'jp_end': 4,
            'effective_date': '2024-01-01',
            'is_active': True
        }
        
        response = self.client.post(
            '/api/schedules/',
            data=json.dumps(schedule_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['jp_start'], 3)
    
    def test_schedule_create_non_admin_forbidden(self):
        """Test creating schedule as non-admin (should be forbidden)"""
        self.client.login(username='teacher1', password='teacher123')
        
        schedule_data = {
            'teacher_id': str(self.teacher.id),
            'subject_id': str(self.subject.id),
            'classroom_id': str(self.classroom.id),
            'day_of_week': 1,
            'jp_start': 3,
            'jp_end': 4,
            'effective_date': '2024-01-01'
        }
        
        response = self.client.post(
            '/api/schedules/',
            data=json.dumps(schedule_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data['success'])
    
    # Schedule Detail/Update/Delete Tests
    
    def test_schedule_detail_authenticated(self):
        """Test getting schedule detail as authenticated user"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get(f'/api/schedules/{self.schedule.id}/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['day_of_week'], 0)
    
    def test_schedule_update_admin(self):
        """Test updating schedule as admin"""
        self.client.login(username='admin', password='admin123')
        
        update_data = {
            'jp_start': 5,
            'jp_end': 6,
            'room_number': 'A101'
        }
        
        response = self.client.put(
            f'/api/schedules/{self.schedule.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['jp_start'], 5)
    
    def test_schedule_delete_admin(self):
        """Test deleting schedule as admin"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.delete(f'/api/schedules/{self.schedule.id}/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
    
    # Conflict Detection Tests
    
    def test_detect_conflicts_admin(self):
        """Test conflict detection as admin"""
        self.client.login(username='admin', password='admin123')
        
        conflict_data = {
            'teacher_id': str(self.teacher.id),
            'day_of_week': 0,
            'jp_start': 1,
            'jp_end': 2,
            'effective_date': '2024-01-01'
        }
        
        response = self.client.post(
            '/api/schedules/detect-conflicts/',
            data=json.dumps(conflict_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('has_conflicts', data['data'])
        self.assertTrue(data['data']['has_conflicts'])  # Should conflict with existing schedule
    
    def test_detect_conflicts_non_admin_forbidden(self):
        """Test conflict detection as non-admin (should be forbidden)"""
        self.client.login(username='teacher1', password='teacher123')
        
        conflict_data = {
            'teacher_id': str(self.teacher.id),
            'day_of_week': 0,
            'jp_start': 1,
            'jp_end': 2
        }
        
        response = self.client.post(
            '/api/schedules/detect-conflicts/',
            data=json.dumps(conflict_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data['success'])
    
    # Weekly Schedule Tests
    
    def test_weekly_schedule_authenticated(self):
        """Test getting weekly schedule as authenticated user"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get(f'/api/schedules/weekly/{self.teacher.id}/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('weekly_schedule', data['data'])
        self.assertIn('total_jp_per_week', data['data'])


class TeacherAttendanceAPITestCase(TestCase):
    """Test cases for teacher attendance API endpoints"""
    
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
        
        # Create another teacher
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
        
        # Create academic level
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
        
        # Create attendance record
        self.attendance = TeacherAttendance.objects.create(
            teacher=self.teacher,
            schedule=self.schedule,
            date=date.today(),
            jp_number=1,
            status='HADIR',
            recorded_by=self.admin_user
        )
        
        self.client = Client()
    
    # Attendance List/Create Tests
    
    def test_attendance_list_admin(self):
        """Test listing attendance as admin"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get('/api/teacher-attendance/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('attendances', data['data'])
        self.assertIn('pagination', data['data'])
    
    def test_attendance_list_teacher_own_only(self):
        """Test listing attendance as teacher (should only see own)"""
        self.client.login(username='teacher1', password='teacher123')
        
        response = self.client.get('/api/teacher-attendance/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        # Should only see own attendance
        for att in data['data']['attendances']:
            self.assertEqual(att['teacher']['id'], str(self.teacher.id))
    
    def test_attendance_list_with_filters(self):
        """Test listing attendance with filters"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get(
            f'/api/teacher-attendance/?teacher_id={self.teacher.id}&status=HADIR'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertGreater(len(data['data']['attendances']), 0)
    
    def test_attendance_create_admin(self):
        """Test creating attendance as admin"""
        self.client.login(username='admin', password='admin123')
        
        attendance_data = {
            'teacher_id': str(self.teacher.id),
            'date': date.today().isoformat(),
            'jp_number': 2,
            'status': 'HADIR',
            'schedule_id': str(self.schedule.id)
        }
        
        response = self.client.post(
            '/api/teacher-attendance/',
            data=json.dumps(attendance_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['status'], 'HADIR')
    
    def test_attendance_create_teacher_own_only(self):
        """Test creating attendance as teacher (only own)"""
        self.client.login(username='teacher1', password='teacher123')
        
        attendance_data = {
            'teacher_id': str(self.teacher.id),
            'date': date.today().isoformat(),
            'jp_number': 3,
            'status': 'HADIR'
        }
        
        response = self.client.post(
            '/api/teacher-attendance/',
            data=json.dumps(attendance_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
    
    def test_attendance_create_teacher_other_forbidden(self):
        """Test creating attendance for another teacher (should be forbidden)"""
        self.client.login(username='teacher1', password='teacher123')
        
        attendance_data = {
            'teacher_id': str(self.teacher2.id),
            'date': date.today().isoformat(),
            'jp_number': 3,
            'status': 'HADIR'
        }
        
        response = self.client.post(
            '/api/teacher-attendance/',
            data=json.dumps(attendance_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data['success'])
    
    # Attendance Detail/Update/Delete Tests
    
    def test_attendance_detail_admin(self):
        """Test getting attendance detail as admin"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get(f'/api/teacher-attendance/{self.attendance.id}/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['status'], 'HADIR')
    
    def test_attendance_detail_teacher_own_only(self):
        """Test getting attendance detail as teacher (only own)"""
        self.client.login(username='teacher1', password='teacher123')
        
        response = self.client.get(f'/api/teacher-attendance/{self.attendance.id}/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
    
    def test_attendance_update_admin(self):
        """Test updating attendance as admin"""
        self.client.login(username='admin', password='admin123')
        
        update_data = {
            'status': 'SAKIT',
            'notes': 'Demam tinggi'
        }
        
        response = self.client.put(
            f'/api/teacher-attendance/{self.attendance.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['status'], 'SAKIT')
    
    def test_attendance_update_teacher_own_only(self):
        """Test updating attendance as teacher (only own)"""
        self.client.login(username='teacher1', password='teacher123')
        
        update_data = {
            'notes': 'Updated notes'
        }
        
        response = self.client.put(
            f'/api/teacher-attendance/{self.attendance.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
    
    def test_attendance_delete_admin_only(self):
        """Test deleting attendance (admin only)"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.delete(f'/api/teacher-attendance/{self.attendance.id}/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
    
    def test_attendance_delete_teacher_forbidden(self):
        """Test deleting attendance as teacher (should be forbidden)"""
        self.client.login(username='teacher1', password='teacher123')
        
        response = self.client.delete(f'/api/teacher-attendance/{self.attendance.id}/')
        
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data['success'])
    
    # Location Validation Tests
    
    def test_validate_location_valid(self):
        """Test location validation with valid coordinates"""
        self.client.login(username='teacher1', password='teacher123')
        
        location_data = {
            'latitude': -7.7956,
            'longitude': 110.3695
        }
        
        response = self.client.post(
            '/api/teacher-attendance/validate-location/',
            data=json.dumps(location_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('is_valid', data['data'])
    
    def test_validate_location_missing_params(self):
        """Test location validation without required parameters"""
        self.client.login(username='teacher1', password='teacher123')
        
        location_data = {
            'latitude': -7.7956
            # Missing longitude
        }
        
        response = self.client.post(
            '/api/teacher-attendance/validate-location/',
            data=json.dumps(location_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    # Daily Attendance Tests
    
    def test_daily_attendance_authenticated(self):
        """Test getting daily attendance as authenticated user"""
        self.client.login(username='admin', password='admin123')
        
        today = date.today().isoformat()
        response = self.client.get(f'/api/teacher-attendance/daily/?date={today}')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('attendances', data['data'])
        self.assertIn('summary', data['data'])
    
    def test_daily_attendance_missing_date(self):
        """Test getting daily attendance without date parameter"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get('/api/teacher-attendance/daily/')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    # Absent Teachers Tests
    
    def test_absent_teachers_authenticated(self):
        """Test getting absent teachers as authenticated user"""
        self.client.login(username='admin', password='admin123')
        
        today = date.today().isoformat()
        response = self.client.get(
            f'/api/teacher-attendance/absent/?date={today}&jp_number=1'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('absent_teachers', data['data'])
        self.assertIn('total_absent', data['data'])
    
    def test_absent_teachers_missing_params(self):
        """Test getting absent teachers without required parameters"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.get('/api/teacher-attendance/absent/')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_absent_teachers_invalid_jp(self):
        """Test getting absent teachers with invalid JP number"""
        self.client.login(username='admin', password='admin123')
        
        today = date.today().isoformat()
        response = self.client.get(
            f'/api/teacher-attendance/absent/?date={today}&jp_number=15'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])


class APIAuthenticationTestCase(TestCase):
    """Test cases for API authentication and authorization"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
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
    
    def test_unauthenticated_access_forbidden(self):
        """Test that unauthenticated requests are rejected"""
        endpoints = [
            '/api/teachers/',
            '/api/schedules/',
            '/api/teacher-attendance/',
            '/api/reports/dashboard/',
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertIn(response.status_code, [302, 403], 
                         f"Endpoint {endpoint} should require authentication")
    
    def test_admin_access_all_endpoints(self):
        """Test that admin can access all endpoints"""
        self.client.login(username='admin', password='admin123')
        
        endpoints = [
            '/api/teachers/',
            '/api/schedules/',
            '/api/teacher-attendance/',
            '/api/reports/dashboard/',
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertIn(response.status_code, [200, 400], 
                         f"Admin should access {endpoint}")
    
    def test_teacher_limited_access(self):
        """Test that teachers have limited access"""
        self.client.login(username='teacher1', password='teacher123')
        
        # Should have access to these
        allowed_endpoints = [
            '/api/teachers/',
            '/api/teacher-attendance/',
            '/api/reports/dashboard/',
        ]
        
        for endpoint in allowed_endpoints:
            response = self.client.get(endpoint)
            self.assertIn(response.status_code, [200, 400, 403], 
                         f"Teacher should have some access to {endpoint}")


class APIResponseFormatTestCase(TestCase):
    """Test cases for API response format consistency"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        
        self.client = Client()
        self.client.login(username='admin', password='admin123')
    
    def test_success_response_format(self):
        """Test that success responses have consistent format"""
        response = self.client.get('/api/teachers/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check required fields
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
    
    def test_error_response_format(self):
        """Test that error responses have consistent format"""
        response = self.client.get('/api/teachers/invalid-uuid/')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        
        # Check required fields
        self.assertIn('success', data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_pagination_format(self):
        """Test that paginated responses have consistent format"""
        response = self.client.get('/api/teachers/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check pagination fields
        self.assertIn('pagination', data['data'])
        pagination = data['data']['pagination']
        self.assertIn('page', pagination)
        self.assertIn('page_size', pagination)
        self.assertIn('total', pagination)
        self.assertIn('total_pages', pagination)


class APIRequestValidationTestCase(TestCase):
    """Test cases for API request validation"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
        
        self.client = Client()
        self.client.login(username='admin', password='admin123')
    
    def test_invalid_json_rejected(self):
        """Test that invalid JSON is rejected"""
        response = self.client.post(
            '/api/teachers/',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_invalid_uuid_rejected(self):
        """Test that invalid UUIDs are rejected"""
        response = self.client.get('/api/teachers/not-a-uuid/')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_invalid_date_format_rejected(self):
        """Test that invalid date formats are rejected"""
        response = self.client.get('/api/teacher-attendance/daily/?date=invalid-date')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_missing_required_fields_rejected(self):
        """Test that requests with missing required fields are rejected"""
        # Try to create teacher without required fields
        response = self.client.post(
            '/api/teachers/',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_invalid_enum_values_rejected(self):
        """Test that invalid enum values are rejected"""
        response = self.client.get('/api/teacher-attendance/?status=INVALID_STATUS')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
