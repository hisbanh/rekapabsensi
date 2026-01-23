"""
Performance tests for teacher attendance system.

Tests database query performance for:
- Schedule retrieval with large datasets
- Attendance report generation with date ranges
- Dashboard statistics calculation
- Query optimization with indexes and select_related
"""

import time
from django.test import TestCase
from django.contrib.auth.models import User
from django.db import connection
from django.test.utils import override_settings
from datetime import date, timedelta
from decimal import Decimal

from attendance.models import (
    Subject,
    Teacher,
    TeacherSchedule,
    TeacherAttendance,
    Classroom,
    AcademicLevel
)
from attendance.services.schedule_service import TeacherScheduleService
from attendance.services.teacher_attendance_service import TeacherAttendanceService
from attendance.services.teacher_report_service import TeacherReportService


class PerformanceTestCase(TestCase):
    """Base class for performance tests with helper methods."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_staff=True
        )
        
        # Create academic level
        self.academic_level, _ = AcademicLevel.objects.get_or_create(
            code='SMP',
            defaults={
                'name': 'Sekolah Menengah Pertama',
                'level_type': 'SMP',
                'min_grade': 7,
                'max_grade': 9
            }
        )
        
        # Create classrooms
        self.classrooms = []
        for grade in [7, 8, 9]:
            for section in ['A', 'B', 'C']:
                classroom, _ = Classroom.objects.get_or_create(
                    academic_level=self.academic_level,
                    grade=grade,
                    section=section,
                    academic_year='2024/2025',
                    defaults={'name': f'Kelas {grade}-{section}'}
                )
                self.classrooms.append(classroom)
        
        # Create subjects
        self.subjects = []
        subject_data = [
            ('MAT01', 'Matematika', 'UMUM'),
            ('FIS01', 'Fisika', 'UMUM'),
            ('KIM01', 'Kimia', 'UMUM'),
            ('BIO01', 'Biologi', 'UMUM'),
            ('ING01', 'Bahasa Inggris', 'UMUM'),
            ('ARB01', 'Bahasa Arab', 'AGAMA'),
            ('QUR01', 'Al-Quran', 'AGAMA'),
            ('FIQ01', 'Fiqih', 'AGAMA'),
            ('AKH01', 'Akhlak', 'AGAMA'),
            ('TAR01', 'Tarikh', 'AGAMA'),
        ]
        
        for code, name, category in subject_data:
            subject = Subject.objects.create(
                code=code,
                name=name,
                category=category
            )
            self.subjects.append(subject)
    
    def create_teachers(self, count=30):
        """Create multiple teachers for testing."""
        teachers = []
        teacher_names = [
            'Ahmad Yusuf', 'Fatimah Zahra', 'Muhammad Ali', 'Khadijah Binti', 'Umar Faruq',
            'Aisyah Rahmah', 'Hasan Basri', 'Zainab Kubra', 'Husain Syahid', 'Maryam Qibtiyah',
            'Abdullah Rahman', 'Ruqayyah Zahra', 'Ja\'far Shadiq', 'Ummu Kulthum', 'Ali Zainal',
            'Hafsah Umar', 'Zaid Haritsah', 'Asma Bakr', 'Bilal Habsyi', 'Sumayyah Yasir',
            'Salman Farisi', 'Safiyyah Huyay', 'Abu Bakar Siddiq', 'Sawdah Zamah', 'Usman Affan',
            'Hafshah Umar', 'Talhah Ubaidillah', 'Zubair Awwam', 'Abdurrahman Auf', 'Saad Waqqas'
        ]
        
        for i in range(count):
            teacher = Teacher.objects.create(
                nip=f'NIP{i:05d}',
                full_name=teacher_names[i % len(teacher_names)] + f' {chr(65 + i // len(teacher_names))}',
                employment_date=date(2020, 1, 1),
                employment_status='ACTIVE'
            )
            # Assign 2-3 subjects to each teacher
            subjects_to_assign = self.subjects[i % len(self.subjects):(i % len(self.subjects)) + 3]
            teacher.subjects.add(*subjects_to_assign)
            teachers.append(teacher)
        return teachers
    
    def create_schedules_for_teachers(self, teachers):
        """Create weekly schedules for all teachers."""
        schedules = []
        classroom_schedule_tracker = {}  # Track which classrooms are used when
        
        for teacher_idx, teacher in enumerate(teachers):
            # Create 2-4 schedules per teacher (different days and times)
            schedules_created = 0
            for day in range(5):  # Monday to Friday
                if schedules_created >= 4:
                    break
                    
                for jp_slot in [(1, 2), (3, 4), (5, 6), (7, 8)]:
                    if schedules_created >= 4:
                        break
                        
                    # Use a distribution pattern to avoid conflicts
                    if (teacher_idx + day + jp_slot[0]) % 4 != 0:
                        continue
                    
                    subject = teacher.subjects.first()
                    if not subject:
                        continue
                    
                    # Find an available classroom for this day/time
                    classroom_found = False
                    for classroom in self.classrooms:
                        key = (classroom.id, day, jp_slot[0], jp_slot[1])
                        if key not in classroom_schedule_tracker:
                            classroom_schedule_tracker[key] = True
                            classroom_found = True
                            
                            schedule = TeacherSchedule.objects.create(
                                teacher=teacher,
                                subject=subject,
                                classroom=classroom,
                                day_of_week=day,
                                jp_start=jp_slot[0],
                                jp_end=jp_slot[1],
                                effective_date=date(2024, 1, 1)
                            )
                            schedules.append(schedule)
                            schedules_created += 1
                            break
                    
                    if classroom_found:
                        break
        
        return schedules
    
    def create_attendance_records(self, teachers, days=30):
        """Create attendance records for multiple days."""
        attendances = []
        start_date = date.today() - timedelta(days=days)
        
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            day_of_week = current_date.weekday()
            
            # Get schedules for this day
            day_schedules = TeacherSchedule.objects.filter(
                day_of_week=day_of_week,
                is_active=True
            ).select_related('teacher')
            
            for schedule in day_schedules:
                # Create attendance for each JP in the schedule
                for jp in range(schedule.jp_start, schedule.jp_end + 1):
                    # 85% attendance rate
                    if (schedule.teacher.id.int + day_offset + jp) % 100 < 85:
                        status = 'HADIR'
                    elif (schedule.teacher.id.int + day_offset + jp) % 100 < 90:
                        status = 'SAKIT'
                    elif (schedule.teacher.id.int + day_offset + jp) % 100 < 95:
                        status = 'IZIN'
                    else:
                        status = 'ALPA'
                    
                    attendance = TeacherAttendance.objects.create(
                        teacher=schedule.teacher,
                        schedule=schedule,
                        date=current_date,
                        jp_number=jp,
                        status=status,
                        recorded_by=self.user
                    )
                    attendances.append(attendance)
        
        return attendances
    
    def measure_query_time(self, func, *args, **kwargs):
        """Measure execution time and query count for a function."""
        # Reset query log
        connection.queries_log.clear()
        
        # Measure time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        query_count = len(connection.queries)
        
        return {
            'result': result,
            'execution_time': execution_time,
            'query_count': query_count,
            'queries': connection.queries if query_count < 20 else []
        }


@override_settings(DEBUG=True)  # Enable query logging
class ScheduleRetrievalPerformanceTest(PerformanceTestCase):
    """Test schedule retrieval performance with large datasets."""
    
    def test_weekly_schedule_retrieval_performance(self):
        """Test performance of retrieving weekly schedule for a teacher."""
        # Create large dataset
        teachers = self.create_teachers(count=30)
        self.create_schedules_for_teachers(teachers)
        
        # Test with first teacher
        teacher = teachers[0]
        
        # Measure performance
        metrics = self.measure_query_time(
            TeacherScheduleService.get_weekly_schedule,
            teacher.id
        )
        
        print(f"\n=== Weekly Schedule Retrieval Performance ===")
        print(f"Execution time: {metrics['execution_time']:.4f} seconds")
        print(f"Query count: {metrics['query_count']}")
        print(f"Result: {len([s for day_schedules in metrics['result'].values() for s in day_schedules])} schedules")
        
        # Performance assertions
        self.assertLess(metrics['execution_time'], 0.5, "Weekly schedule retrieval should complete in < 0.5s")
        self.assertLess(metrics['query_count'], 5, "Should use minimal queries with select_related")
    
    def test_classroom_schedule_retrieval_performance(self):
        """Test performance of retrieving classroom schedule."""
        # Create large dataset
        teachers = self.create_teachers(count=30)
        self.create_schedules_for_teachers(teachers)
        
        classroom = self.classrooms[0]
        
        # Measure performance
        metrics = self.measure_query_time(
            TeacherScheduleService.get_classroom_schedule,
            classroom.id,
            0  # Monday
        )
        
        print(f"\n=== Classroom Schedule Retrieval Performance ===")
        print(f"Execution time: {metrics['execution_time']:.4f} seconds")
        print(f"Query count: {metrics['query_count']}")
        print(f"Result: {len(metrics['result'])} schedules")
        
        # Performance assertions
        self.assertLess(metrics['execution_time'], 0.3, "Classroom schedule retrieval should complete in < 0.3s")
        self.assertLess(metrics['query_count'], 3, "Should use minimal queries")
    
    def test_conflict_detection_performance(self):
        """Test performance of schedule conflict detection."""
        # Create large dataset
        teachers = self.create_teachers(count=30)
        self.create_schedules_for_teachers(teachers)
        
        teacher = teachers[0]
        
        # Measure performance
        metrics = self.measure_query_time(
            TeacherScheduleService.detect_conflicts,
            teacher.id,
            0,  # Monday
            3,  # JP start
            4,  # JP end
            date(2024, 1, 1)
        )
        
        print(f"\n=== Conflict Detection Performance ===")
        print(f"Execution time: {metrics['execution_time']:.4f} seconds")
        print(f"Query count: {metrics['query_count']}")
        print(f"Conflicts found: {len(metrics['result'])}")
        
        # Performance assertions
        self.assertLess(metrics['execution_time'], 0.2, "Conflict detection should complete in < 0.2s")
        self.assertLess(metrics['query_count'], 4, "Should use indexed queries")
    
    def test_teaching_load_calculation_performance(self):
        """Test performance of calculating teacher teaching load."""
        # Create large dataset
        teachers = self.create_teachers(count=30)
        self.create_schedules_for_teachers(teachers)
        
        teacher = teachers[0]
        
        # Measure performance
        metrics = self.measure_query_time(
            TeacherScheduleService.get_teacher_teaching_load,
            teacher.id
        )
        
        print(f"\n=== Teaching Load Calculation Performance ===")
        print(f"Execution time: {metrics['execution_time']:.4f} seconds")
        print(f"Query count: {metrics['query_count']}")
        print(f"Total JP/week: {metrics['result']['total_jp_per_week']}")
        
        # Performance assertions
        self.assertLess(metrics['execution_time'], 0.3, "Teaching load calculation should complete in < 0.3s")
        self.assertLess(metrics['query_count'], 3, "Should use efficient queries")


@override_settings(DEBUG=True)
class AttendanceReportPerformanceTest(PerformanceTestCase):
    """Test attendance report generation performance with date ranges."""
    
    def test_daily_attendance_retrieval_performance(self):
        """Test performance of retrieving daily attendance."""
        # Create large dataset
        teachers = self.create_teachers(count=30)
        self.create_schedules_for_teachers(teachers)
        self.create_attendance_records(teachers, days=30)
        
        # Measure performance
        metrics = self.measure_query_time(
            TeacherAttendanceService.get_daily_attendance,
            date.today()
        )
        
        print(f"\n=== Daily Attendance Retrieval Performance ===")
        print(f"Execution time: {metrics['execution_time']:.4f} seconds")
        print(f"Query count: {metrics['query_count']}")
        print(f"Records retrieved: {len(metrics['result'])}")
        
        # Performance assertions
        self.assertLess(metrics['execution_time'], 0.5, "Daily attendance retrieval should complete in < 0.5s")
        self.assertLess(metrics['query_count'], 3, "Should use select_related efficiently")
    
    def test_attendance_history_retrieval_performance(self):
        """Test performance of retrieving attendance history."""
        # Create large dataset
        teachers = self.create_teachers(count=30)
        self.create_schedules_for_teachers(teachers)
        self.create_attendance_records(teachers, days=30)
        
        teacher = teachers[0]
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        # Measure performance
        metrics = self.measure_query_time(
            TeacherAttendanceService.get_teacher_attendance_history,
            teacher.id,
            start_date,
            end_date
        )
        
        print(f"\n=== Attendance History Retrieval Performance ===")
        print(f"Execution time: {metrics['execution_time']:.4f} seconds")
        print(f"Query count: {metrics['query_count']}")
        print(f"Records retrieved: {len(metrics['result'])}")
        
        # Performance assertions
        self.assertLess(metrics['execution_time'], 0.5, "Attendance history retrieval should complete in < 0.5s")
        self.assertLess(metrics['query_count'], 3, "Should use indexed date range queries")
    
    def test_monthly_summary_calculation_performance(self):
        """Test performance of calculating monthly summary."""
        # Create large dataset
        teachers = self.create_teachers(count=30)
        self.create_schedules_for_teachers(teachers)
        self.create_attendance_records(teachers, days=30)
        
        teacher = teachers[0]
        today = date.today()
        
        # Measure performance
        metrics = self.measure_query_time(
            TeacherAttendanceService.calculate_monthly_summary,
            teacher.id,
            today.year,
            today.month
        )
        
        print(f"\n=== Monthly Summary Calculation Performance ===")
        print(f"Execution time: {metrics['execution_time']:.4f} seconds")
        print(f"Query count: {metrics['query_count']}")
        print(f"Attendance percentage: {metrics['result']['attendance_percentage']}%")
        
        # Performance assertions
        self.assertLess(metrics['execution_time'], 1.0, "Monthly summary calculation should complete in < 1s")
        self.assertLess(metrics['query_count'], 50, "Should use efficient aggregation queries")
    
    def test_analytics_generation_performance(self):
        """Test performance of generating attendance analytics."""
        # Create large dataset
        teachers = self.create_teachers(count=30)
        self.create_schedules_for_teachers(teachers)
        self.create_attendance_records(teachers, days=30)
        
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        # Measure performance
        metrics = self.measure_query_time(
            TeacherReportService.get_attendance_analytics,
            start_date,
            end_date
        )
        
        print(f"\n=== Analytics Generation Performance ===")
        print(f"Execution time: {metrics['execution_time']:.4f} seconds")
        print(f"Query count: {metrics['query_count']}")
        print(f"Teachers analyzed: {len(metrics['result']['teacher_stats'])}")
        print(f"Overall attendance: {metrics['result']['overall_stats']['attendance_percentage']}%")
        
        # Performance assertions
        self.assertLess(metrics['execution_time'], 3.0, "Analytics generation should complete in < 3s")
        # Note: This will have more queries due to per-teacher calculations
    
    def test_pdf_report_generation_performance(self):
        """Test performance of PDF report generation."""
        # Create moderate dataset
        teachers = self.create_teachers(count=10)
        self.create_schedules_for_teachers(teachers)
        self.create_attendance_records(teachers, days=30)
        
        teacher = teachers[0]
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        # Measure performance
        metrics = self.measure_query_time(
            TeacherReportService.generate_teacher_report_pdf,
            teacher.id,
            start_date,
            end_date
        )
        
        print(f"\n=== PDF Report Generation Performance ===")
        print(f"Execution time: {metrics['execution_time']:.4f} seconds")
        print(f"Query count: {metrics['query_count']}")
        print(f"PDF size: {len(metrics['result'])} bytes")
        
        # Performance assertions
        self.assertLess(metrics['execution_time'], 5.0, "PDF generation should complete in < 5s")
        self.assertGreater(len(metrics['result']), 0, "PDF should be generated")
    
    def test_excel_export_performance(self):
        """Test performance of Excel export."""
        # Create moderate dataset
        teachers = self.create_teachers(count=10)
        self.create_schedules_for_teachers(teachers)
        self.create_attendance_records(teachers, days=30)
        
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        # Measure performance
        metrics = self.measure_query_time(
            TeacherReportService.export_attendance_excel,
            start_date,
            end_date
        )
        
        print(f"\n=== Excel Export Performance ===")
        print(f"Execution time: {metrics['execution_time']:.4f} seconds")
        print(f"Query count: {metrics['query_count']}")
        print(f"Excel size: {len(metrics['result'])} bytes")
        
        # Performance assertions
        self.assertLess(metrics['execution_time'], 5.0, "Excel export should complete in < 5s")
        self.assertGreater(len(metrics['result']), 0, "Excel file should be generated")


@override_settings(DEBUG=True)
class PDFExcelPerformanceTest(PerformanceTestCase):
    """Comprehensive performance tests for PDF and Excel generation with large datasets."""
    
    def test_pdf_generation_with_large_date_range(self):
        """Test PDF generation performance with large date range (90 days)."""
        print("\n" + "="*70)
        print("PDF GENERATION - LARGE DATE RANGE TEST (90 days)")
        print("="*70)
        
        # Create dataset
        teachers = self.create_teachers(count=10)
        self.create_schedules_for_teachers(teachers)
        self.create_attendance_records(teachers, days=90)
        
        teacher = teachers[0]
        start_date = date.today() - timedelta(days=90)
        end_date = date.today()
        
        # Measure performance
        metrics = self.measure_query_time(
            TeacherReportService.generate_teacher_report_pdf,
            teacher.id,
            start_date,
            end_date
        )
        
        print(f"\nTest Configuration:")
        print(f"  - Date range: 90 days")
        print(f"  - Teacher: {teacher.full_name}")
        print(f"  - Expected records: ~{90 * 4} JP (assuming 4 JP/day average)")
        
        print(f"\nPerformance Metrics:")
        print(f"  - Execution time: {metrics['execution_time']:.4f} seconds")
        print(f"  - Query count: {metrics['query_count']}")
        print(f"  - PDF size: {len(metrics['result']):,} bytes ({len(metrics['result'])/1024:.2f} KB)")
        
        # Performance assertions
        self.assertLess(metrics['execution_time'], 5.0, 
                       f"PDF generation with 90-day range should complete in < 5s (took {metrics['execution_time']:.4f}s)")
        self.assertGreater(len(metrics['result']), 0, "PDF should be generated")
        
        # Verify PDF is valid (starts with PDF header)
        self.assertTrue(metrics['result'].startswith(b'%PDF'), "Generated file should be a valid PDF")
        
        print(f"\n✓ Test PASSED - PDF generated in {metrics['execution_time']:.4f}s")
        print("="*70)
    
    def test_pdf_generation_with_very_large_date_range(self):
        """Test PDF generation performance with very large date range (180 days)."""
        print("\n" + "="*70)
        print("PDF GENERATION - VERY LARGE DATE RANGE TEST (180 days)")
        print("="*70)
        
        # Create dataset
        teachers = self.create_teachers(count=5)
        self.create_schedules_for_teachers(teachers)
        self.create_attendance_records(teachers, days=180)
        
        teacher = teachers[0]
        start_date = date.today() - timedelta(days=180)
        end_date = date.today()
        
        # Measure performance
        metrics = self.measure_query_time(
            TeacherReportService.generate_teacher_report_pdf,
            teacher.id,
            start_date,
            end_date
        )
        
        print(f"\nTest Configuration:")
        print(f"  - Date range: 180 days (6 months)")
        print(f"  - Teacher: {teacher.full_name}")
        print(f"  - Expected records: ~{180 * 4} JP")
        
        print(f"\nPerformance Metrics:")
        print(f"  - Execution time: {metrics['execution_time']:.4f} seconds")
        print(f"  - Query count: {metrics['query_count']}")
        print(f"  - PDF size: {len(metrics['result']):,} bytes ({len(metrics['result'])/1024:.2f} KB)")
        
        # Performance assertions - allow slightly more time for very large datasets
        self.assertLess(metrics['execution_time'], 8.0, 
                       f"PDF generation with 180-day range should complete in < 8s (took {metrics['execution_time']:.4f}s)")
        self.assertGreater(len(metrics['result']), 0, "PDF should be generated")
        self.assertTrue(metrics['result'].startswith(b'%PDF'), "Generated file should be a valid PDF")
        
        # Warn if approaching limit
        if metrics['execution_time'] > 5.0:
            print(f"\n⚠ WARNING: Generation time ({metrics['execution_time']:.4f}s) exceeds 5s threshold")
            print("  Consider optimization for very large date ranges")
        else:
            print(f"\n✓ Test PASSED - PDF generated in {metrics['execution_time']:.4f}s")
        
        print("="*70)
    
    def test_excel_export_with_large_date_range(self):
        """Test Excel export performance with large date range (90 days)."""
        print("\n" + "="*70)
        print("EXCEL EXPORT - LARGE DATE RANGE TEST (90 days)")
        print("="*70)
        
        # Create dataset
        teachers = self.create_teachers(count=10)
        self.create_schedules_for_teachers(teachers)
        self.create_attendance_records(teachers, days=90)
        
        start_date = date.today() - timedelta(days=90)
        end_date = date.today()
        
        # Measure performance
        metrics = self.measure_query_time(
            TeacherReportService.export_attendance_excel,
            start_date,
            end_date
        )
        
        print(f"\nTest Configuration:")
        print(f"  - Date range: 90 days")
        print(f"  - Teachers: {len(teachers)}")
        print(f"  - Expected records: ~{90 * len(teachers) * 4} JP")
        
        print(f"\nPerformance Metrics:")
        print(f"  - Execution time: {metrics['execution_time']:.4f} seconds")
        print(f"  - Query count: {metrics['query_count']}")
        print(f"  - Excel size: {len(metrics['result']):,} bytes ({len(metrics['result'])/1024:.2f} KB)")
        
        # Performance assertions
        self.assertLess(metrics['execution_time'], 5.0, 
                       f"Excel export with 90-day range should complete in < 5s (took {metrics['execution_time']:.4f}s)")
        self.assertGreater(len(metrics['result']), 0, "Excel file should be generated")
        
        # Verify Excel is valid (starts with PK for ZIP format)
        self.assertTrue(metrics['result'].startswith(b'PK'), "Generated file should be a valid Excel file (ZIP format)")
        
        print(f"\n✓ Test PASSED - Excel exported in {metrics['execution_time']:.4f}s")
        print("="*70)
    
    def test_excel_export_with_very_large_date_range(self):
        """Test Excel export performance with very large date range (180 days)."""
        print("\n" + "="*70)
        print("EXCEL EXPORT - VERY LARGE DATE RANGE TEST (180 days)")
        print("="*70)
        
        # Create dataset
        teachers = self.create_teachers(count=10)
        self.create_schedules_for_teachers(teachers)
        self.create_attendance_records(teachers, days=180)
        
        start_date = date.today() - timedelta(days=180)
        end_date = date.today()
        
        # Measure performance
        metrics = self.measure_query_time(
            TeacherReportService.export_attendance_excel,
            start_date,
            end_date
        )
        
        print(f"\nTest Configuration:")
        print(f"  - Date range: 180 days (6 months)")
        print(f"  - Teachers: {len(teachers)}")
        print(f"  - Expected records: ~{180 * len(teachers) * 4} JP")
        
        print(f"\nPerformance Metrics:")
        print(f"  - Execution time: {metrics['execution_time']:.4f} seconds")
        print(f"  - Query count: {metrics['query_count']}")
        print(f"  - Excel size: {len(metrics['result']):,} bytes ({len(metrics['result'])/1024:.2f} KB)")
        
        # Performance assertions - allow slightly more time for very large datasets
        self.assertLess(metrics['execution_time'], 8.0, 
                       f"Excel export with 180-day range should complete in < 8s (took {metrics['execution_time']:.4f}s)")
        self.assertGreater(len(metrics['result']), 0, "Excel file should be generated")
        self.assertTrue(metrics['result'].startswith(b'PK'), "Generated file should be a valid Excel file")
        
        # Warn if approaching limit
        if metrics['execution_time'] > 5.0:
            print(f"\n⚠ WARNING: Export time ({metrics['execution_time']:.4f}s) exceeds 5s threshold")
            print("  Consider optimization for very large date ranges")
        else:
            print(f"\n✓ Test PASSED - Excel exported in {metrics['execution_time']:.4f}s")
        
        print("="*70)
    
    def test_excel_export_with_multiple_teachers(self):
        """Test Excel export performance with multiple teachers (30 teachers)."""
        print("\n" + "="*70)
        print("EXCEL EXPORT - MULTIPLE TEACHERS TEST (30 teachers)")
        print("="*70)
        
        # Create large dataset
        teachers = self.create_teachers(count=30)
        self.create_schedules_for_teachers(teachers)
        self.create_attendance_records(teachers, days=30)
        
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        # Measure performance
        metrics = self.measure_query_time(
            TeacherReportService.export_attendance_excel,
            start_date,
            end_date
        )
        
        print(f"\nTest Configuration:")
        print(f"  - Date range: 30 days")
        print(f"  - Teachers: {len(teachers)}")
        print(f"  - Expected records: ~{30 * len(teachers) * 4} JP")
        
        print(f"\nPerformance Metrics:")
        print(f"  - Execution time: {metrics['execution_time']:.4f} seconds")
        print(f"  - Query count: {metrics['query_count']}")
        print(f"  - Excel size: {len(metrics['result']):,} bytes ({len(metrics['result'])/1024:.2f} KB)")
        
        # Performance assertions
        self.assertLess(metrics['execution_time'], 5.0, 
                       f"Excel export with 30 teachers should complete in < 5s (took {metrics['execution_time']:.4f}s)")
        self.assertGreater(len(metrics['result']), 0, "Excel file should be generated")
        self.assertTrue(metrics['result'].startswith(b'PK'), "Generated file should be a valid Excel file")
        
        print(f"\n✓ Test PASSED - Excel exported in {metrics['execution_time']:.4f}s")
        print("="*70)
    
    def test_excel_export_with_per_teacher_sheets(self):
        """Test Excel export performance with per-teacher sheets (10 teachers)."""
        print("\n" + "="*70)
        print("EXCEL EXPORT - PER-TEACHER SHEETS TEST (10 teachers)")
        print("="*70)
        
        # Create dataset
        teachers = self.create_teachers(count=10)
        self.create_schedules_for_teachers(teachers)
        self.create_attendance_records(teachers, days=30)
        
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        # Get teacher IDs for per-teacher sheets
        teacher_ids = [t.id for t in teachers]
        
        # Measure performance
        metrics = self.measure_query_time(
            TeacherReportService.export_attendance_excel,
            start_date,
            end_date,
            teacher_ids
        )
        
        print(f"\nTest Configuration:")
        print(f"  - Date range: 30 days")
        print(f"  - Teachers: {len(teachers)}")
        print(f"  - Per-teacher sheets: Yes")
        print(f"  - Expected sheets: 2 (Summary + Detail) + {len(teachers)} (per-teacher)")
        
        print(f"\nPerformance Metrics:")
        print(f"  - Execution time: {metrics['execution_time']:.4f} seconds")
        print(f"  - Query count: {metrics['query_count']}")
        print(f"  - Excel size: {len(metrics['result']):,} bytes ({len(metrics['result'])/1024:.2f} KB)")
        
        # Performance assertions - allow more time for per-teacher sheets
        self.assertLess(metrics['execution_time'], 8.0, 
                       f"Excel export with per-teacher sheets should complete in < 8s (took {metrics['execution_time']:.4f}s)")
        self.assertGreater(len(metrics['result']), 0, "Excel file should be generated")
        self.assertTrue(metrics['result'].startswith(b'PK'), "Generated file should be a valid Excel file")
        
        # Warn if approaching limit
        if metrics['execution_time'] > 5.0:
            print(f"\n⚠ WARNING: Export time ({metrics['execution_time']:.4f}s) exceeds 5s threshold")
            print("  Per-teacher sheets add overhead - this is expected")
        else:
            print(f"\n✓ Test PASSED - Excel exported in {metrics['execution_time']:.4f}s")
        
        print("="*70)
    
    def test_pdf_generation_stress_test(self):
        """Stress test: PDF generation with maximum realistic load."""
        print("\n" + "="*70)
        print("PDF GENERATION - STRESS TEST (365 days, high activity)")
        print("="*70)
        
        # Create dataset with high activity
        teachers = self.create_teachers(count=5)
        self.create_schedules_for_teachers(teachers)
        
        # Create full year of attendance data
        print("\nCreating 365 days of attendance data...")
        self.create_attendance_records(teachers, days=365)
        
        teacher = teachers[0]
        start_date = date.today() - timedelta(days=365)
        end_date = date.today()
        
        # Measure performance
        print("Generating PDF report...")
        metrics = self.measure_query_time(
            TeacherReportService.generate_teacher_report_pdf,
            teacher.id,
            start_date,
            end_date
        )
        
        print(f"\nTest Configuration:")
        print(f"  - Date range: 365 days (1 year)")
        print(f"  - Teacher: {teacher.full_name}")
        print(f"  - Expected records: ~{365 * 4} JP")
        
        print(f"\nPerformance Metrics:")
        print(f"  - Execution time: {metrics['execution_time']:.4f} seconds")
        print(f"  - Query count: {metrics['query_count']}")
        print(f"  - PDF size: {len(metrics['result']):,} bytes ({len(metrics['result'])/1024:.2f} KB)")
        
        # Performance assertions - allow more time for full year
        self.assertLess(metrics['execution_time'], 10.0, 
                       f"PDF generation with 1-year range should complete in < 10s (took {metrics['execution_time']:.4f}s)")
        self.assertGreater(len(metrics['result']), 0, "PDF should be generated")
        self.assertTrue(metrics['result'].startswith(b'%PDF'), "Generated file should be a valid PDF")
        
        # Provide optimization recommendations if slow
        if metrics['execution_time'] > 5.0:
            print(f"\n⚠ PERFORMANCE NOTICE:")
            print(f"  - Generation time: {metrics['execution_time']:.4f}s")
            print(f"  - Recommendation: Consider pagination or date range limits for very large reports")
            print(f"  - Alternative: Generate reports in background tasks for date ranges > 90 days")
        else:
            print(f"\n✓ EXCELLENT - PDF generated in {metrics['execution_time']:.4f}s even with 1 year of data")
        
        print("="*70)
    
    def test_excel_export_stress_test(self):
        """Stress test: Excel export with maximum realistic load."""
        print("\n" + "="*70)
        print("EXCEL EXPORT - STRESS TEST (180 days, 30 teachers)")
        print("="*70)
        
        # Create large dataset
        teachers = self.create_teachers(count=30)
        self.create_schedules_for_teachers(teachers)
        
        print("\nCreating 180 days of attendance data for 30 teachers...")
        self.create_attendance_records(teachers, days=180)
        
        start_date = date.today() - timedelta(days=180)
        end_date = date.today()
        
        # Measure performance
        print("Generating Excel export...")
        metrics = self.measure_query_time(
            TeacherReportService.export_attendance_excel,
            start_date,
            end_date
        )
        
        print(f"\nTest Configuration:")
        print(f"  - Date range: 180 days (6 months)")
        print(f"  - Teachers: {len(teachers)}")
        print(f"  - Expected records: ~{180 * len(teachers) * 4} JP")
        
        print(f"\nPerformance Metrics:")
        print(f"  - Execution time: {metrics['execution_time']:.4f} seconds")
        print(f"  - Query count: {metrics['query_count']}")
        print(f"  - Excel size: {len(metrics['result']):,} bytes ({len(metrics['result'])/1024:.2f} KB)")
        
        # Performance assertions - allow more time for stress test
        self.assertLess(metrics['execution_time'], 10.0, 
                       f"Excel export stress test should complete in < 10s (took {metrics['execution_time']:.4f}s)")
        self.assertGreater(len(metrics['result']), 0, "Excel file should be generated")
        self.assertTrue(metrics['result'].startswith(b'PK'), "Generated file should be a valid Excel file")
        
        # Provide optimization recommendations if slow
        if metrics['execution_time'] > 5.0:
            print(f"\n⚠ PERFORMANCE NOTICE:")
            print(f"  - Export time: {metrics['execution_time']:.4f}s")
            print(f"  - Recommendation: Consider background task processing for large exports")
            print(f"  - Alternative: Implement pagination or streaming for very large datasets")
        else:
            print(f"\n✓ EXCELLENT - Excel exported in {metrics['execution_time']:.4f}s with large dataset")
        
        print("="*70)


@override_settings(DEBUG=True)
class DashboardStatisticsPerformanceTest(PerformanceTestCase):
    """Test dashboard statistics calculation performance."""
    
    def test_dashboard_statistics_performance(self):
        """Test performance of dashboard statistics calculation."""
        # Create large dataset
        teachers = self.create_teachers(count=30)
        self.create_schedules_for_teachers(teachers)
        self.create_attendance_records(teachers, days=7)
        
        # Measure performance
        metrics = self.measure_query_time(
            TeacherReportService.get_dashboard_statistics
        )
        
        print(f"\n=== Dashboard Statistics Performance ===")
        print(f"Execution time: {metrics['execution_time']:.4f} seconds")
        print(f"Query count: {metrics['query_count']}")
        print(f"Today's attendance: {metrics['result']['today_stats']['attendance_percentage']}%")
        print(f"Absent today: {len(metrics['result']['absent_today'])}")
        print(f"Notifications: {len(metrics['result']['notifications'])}")
        
        # Performance assertions
        self.assertLess(metrics['execution_time'], 2.0, "Dashboard statistics should complete in < 2s")
        # Dashboard needs multiple queries for different sections
    
    def test_absent_teachers_detection_performance(self):
        """Test performance of detecting absent teachers."""
        # Create large dataset
        teachers = self.create_teachers(count=30)
        self.create_schedules_for_teachers(teachers)
        self.create_attendance_records(teachers, days=1)
        
        # Measure performance
        metrics = self.measure_query_time(
            TeacherAttendanceService.get_absent_teachers,
            date.today(),
            1  # JP 1
        )
        
        print(f"\n=== Absent Teachers Detection Performance ===")
        print(f"Execution time: {metrics['execution_time']:.4f} seconds")
        print(f"Query count: {metrics['query_count']}")
        print(f"Absent teachers found: {len(metrics['result'])}")
        
        # Performance assertions
        self.assertLess(metrics['execution_time'], 1.0, "Absent teacher detection should complete in < 1s")
        self.assertLess(metrics['query_count'], 10, "Should use efficient queries")


@override_settings(DEBUG=True)
class QueryOptimizationTest(PerformanceTestCase):
    """Test query optimization with indexes and select_related."""
    
    def test_schedule_query_uses_select_related(self):
        """Verify that schedule queries use select_related for optimization."""
        # Create dataset
        teachers = self.create_teachers(count=10)
        self.create_schedules_for_teachers(teachers)
        
        teacher = teachers[0]
        
        # Get weekly schedule
        connection.queries_log.clear()
        weekly_schedule = TeacherScheduleService.get_weekly_schedule(teacher.id)
        queries = connection.queries
        
        print(f"\n=== Schedule Query Optimization ===")
        print(f"Total queries: {len(queries)}")
        
        # Check that we're using select_related (should be 1-2 queries max)
        self.assertLessEqual(len(queries), 2, "Should use select_related to minimize queries")
        
        # Verify we can access related objects without additional queries
        connection.queries_log.clear()
        for day_schedules in weekly_schedule.values():
            for schedule in day_schedules:
                _ = schedule.subject.name
                _ = schedule.classroom.name
        
        # Should be 0 additional queries if select_related worked
        self.assertEqual(len(connection.queries), 0, "Related objects should be prefetched")
    
    def test_attendance_query_uses_select_related(self):
        """Verify that attendance queries use select_related for optimization."""
        # Create dataset
        teachers = self.create_teachers(count=10)
        self.create_schedules_for_teachers(teachers)
        self.create_attendance_records(teachers, days=7)
        
        # Get daily attendance
        connection.queries_log.clear()
        attendances = TeacherAttendanceService.get_daily_attendance(date.today())
        queries = connection.queries
        
        print(f"\n=== Attendance Query Optimization ===")
        print(f"Total queries: {len(queries)}")
        
        # Should use select_related
        self.assertLessEqual(len(queries), 2, "Should use select_related to minimize queries")
        
        # Verify we can access related objects without additional queries
        connection.queries_log.clear()
        for attendance in attendances:
            _ = attendance.teacher.full_name
            if attendance.schedule:
                _ = attendance.schedule.subject.name
                _ = attendance.schedule.classroom.name
        
        # Should be 0 additional queries
        self.assertEqual(len(connection.queries), 0, "Related objects should be prefetched")
    
    def test_index_usage_for_date_range_queries(self):
        """Test that date range queries use indexes efficiently."""
        # Create large dataset
        teachers = self.create_teachers(count=30)
        self.create_schedules_for_teachers(teachers)
        self.create_attendance_records(teachers, days=30)
        
        teacher = teachers[0]
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
        
        # Measure query performance
        start_time = time.time()
        history = TeacherAttendanceService.get_teacher_attendance_history(
            teacher.id,
            start_date,
            end_date
        )
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        print(f"\n=== Date Range Query Index Usage ===")
        print(f"Execution time: {execution_time:.4f} seconds")
        print(f"Records retrieved: {len(history)}")
        
        # With proper indexes, this should be fast even with large datasets
        self.assertLess(execution_time, 0.5, "Date range queries should use indexes efficiently")
    
    def test_bulk_operations_performance(self):
        """Test performance of bulk attendance recording."""
        # Create dataset
        teachers = self.create_teachers(count=10)
        self.create_schedules_for_teachers(teachers)
        
        # Prepare bulk attendance data
        bulk_data = []
        for teacher in teachers[:5]:
            for jp in range(1, 5):
                bulk_data.append({
                    'teacher_id': teacher.id,
                    'date': date.today(),
                    'jp_number': jp,
                    'status': 'HADIR'
                })
        
        # Measure performance
        start_time = time.time()
        created, errors = TeacherAttendanceService.bulk_record_attendance(
            bulk_data,
            self.user
        )
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        print(f"\n=== Bulk Operations Performance ===")
        print(f"Execution time: {execution_time:.4f} seconds")
        print(f"Records created: {len(created)}")
        print(f"Errors: {len(errors)}")
        print(f"Average time per record: {execution_time / len(bulk_data):.4f} seconds")
        
        # Bulk operations should be reasonably fast
        self.assertLess(execution_time, 2.0, "Bulk operations should complete in < 2s")
        self.assertEqual(len(created), len(bulk_data), "All records should be created")
        self.assertEqual(len(errors), 0, "No errors should occur")


class PerformanceSummaryTest(PerformanceTestCase):
    """Generate a summary of all performance metrics."""
    
    def test_generate_performance_summary(self):
        """Generate a comprehensive performance summary."""
        print("\n" + "="*70)
        print("PERFORMANCE TEST SUMMARY")
        print("="*70)
        
        # Create full dataset
        print("\nCreating test dataset...")
        teachers = self.create_teachers(count=30)
        schedules = self.create_schedules_for_teachers(teachers)
        attendances = self.create_attendance_records(teachers, days=30)
        
        print(f"Dataset created:")
        print(f"  - Teachers: {len(teachers)}")
        print(f"  - Schedules: {len(schedules)}")
        print(f"  - Attendance records: {len(attendances)}")
        
        # Test key operations
        operations = [
            ("Weekly Schedule Retrieval", lambda: TeacherScheduleService.get_weekly_schedule(teachers[0].id)),
            ("Daily Attendance Retrieval", lambda: TeacherAttendanceService.get_daily_attendance(date.today())),
            ("Monthly Summary Calculation", lambda: TeacherAttendanceService.calculate_monthly_summary(teachers[0].id, date.today().year, date.today().month)),
            ("Dashboard Statistics", lambda: TeacherReportService.get_dashboard_statistics()),
            ("Attendance Analytics", lambda: TeacherReportService.get_attendance_analytics(date.today() - timedelta(days=30), date.today())),
        ]
        
        print("\n" + "-"*70)
        print("OPERATION PERFORMANCE METRICS")
        print("-"*70)
        print(f"{'Operation':<35} {'Time (s)':<12} {'Queries':<10} {'Status'}")
        print("-"*70)
        
        for operation_name, operation_func in operations:
            metrics = self.measure_query_time(operation_func)
            status = "✓ PASS" if metrics['execution_time'] < 2.0 else "✗ SLOW"
            print(f"{operation_name:<35} {metrics['execution_time']:<12.4f} {metrics['query_count']:<10} {status}")
        
        print("-"*70)
        print("\nPerformance test completed successfully!")
        print("="*70)
