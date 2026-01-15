"""
Teacher Service Layer
Business logic for teacher management
"""
from django.db.models import Q, Count, Prefetch
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from attendance.models import Teacher, TeacherSchedule, TeacherDailyAttendance, TeacherStatus, DaySchedule
from attendance.exceptions import AttendanceServiceError

logger = logging.getLogger(__name__)


class TeacherService:
    """Service class for teacher-related operations"""
    
    @staticmethod
    def get_teachers_with_filters(search_query=None, is_active=None, page=1, per_page=20):
        """
        Get filtered list of teachers with pagination
        
        Args:
            search_query: Search by name or teacher_id
            is_active: Filter by active status
            page: Page number
            per_page: Items per page
            
        Returns:
            Dict with teachers and pagination info
        """
        try:
            queryset = Teacher.objects.select_related('user').all()
            
            # Apply filters
            if search_query:
                queryset = queryset.filter(
                    Q(name__icontains=search_query) |
                    Q(teacher_id__icontains=search_query) |
                    Q(nip__icontains=search_query)
                )
            
            if is_active is not None:
                queryset = queryset.filter(is_active=is_active)
            
            queryset = queryset.order_by('name')
            
            # Pagination
            paginator = Paginator(queryset, per_page)
            teachers = paginator.get_page(page)
            
            return {
                'teachers': teachers,
                'total': paginator.count,
                'pages': paginator.num_pages,
                'current_page': page,
                'has_next': teachers.has_next(),
                'has_previous': teachers.has_previous(),
            }
            
        except Exception as e:
            logger.error(f"Error getting teachers: {str(e)}")
            raise AttendanceServiceError(f"Failed to get teachers: {str(e)}")
    
    @staticmethod
    def get_teacher_detail(teacher_id):
        """Get teacher detail with related data"""
        try:
            teacher = Teacher.objects.select_related('user').get(id=teacher_id)
            return teacher
        except Teacher.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting teacher detail: {str(e)}")
            raise AttendanceServiceError(f"Failed to get teacher detail: {str(e)}")
    
    @staticmethod
    def get_teacher_schedule(teacher, day_of_week=None, academic_year=None):
        """
        Get teacher's schedule
        
        Args:
            teacher: Teacher instance
            day_of_week: Specific day (0-6), None for all days
            academic_year: Academic year filter
            
        Returns:
            QuerySet of TeacherSchedule
        """
        try:
            queryset = TeacherSchedule.objects.filter(teacher=teacher)
            
            if day_of_week is not None:
                queryset = queryset.filter(day_of_week=day_of_week)
            
            if academic_year:
                queryset = queryset.filter(academic_year=academic_year)
            
            return queryset.order_by('day_of_week')
            
        except Exception as e:
            logger.error(f"Error getting teacher schedule: {str(e)}")
            raise AttendanceServiceError(f"Failed to get teacher schedule: {str(e)}")
    
    @staticmethod
    def get_schedule_for_date(teacher, target_date):
        """
        Get teacher's schedule for a specific date
        
        Args:
            teacher: Teacher instance
            target_date: Date object
            
        Returns:
            TeacherSchedule instance or None
        """
        try:
            day_of_week = target_date.weekday()
            
            schedule = TeacherSchedule.objects.filter(
                teacher=teacher,
                day_of_week=day_of_week
            ).first()
            
            return schedule
            
        except Exception as e:
            logger.error(f"Error getting schedule for date: {str(e)}")
            return None
    
    @staticmethod
    def create_or_update_schedule(teacher, day_of_week, jp_numbers, subject='', 
                                   is_piket=False, academic_year='', notes='', user=None):
        """
        Create or update teacher schedule
        
        Args:
            teacher: Teacher instance
            day_of_week: Day of week (0-6)
            jp_numbers: List of JP numbers
            subject: Subject name
            is_piket: Is piket day
            academic_year: Academic year
            notes: Additional notes
            user: User creating/updating
            
        Returns:
            TeacherSchedule instance
        """
        try:
            schedule, created = TeacherSchedule.objects.update_or_create(
                teacher=teacher,
                day_of_week=day_of_week,
                academic_year=academic_year,
                defaults={
                    'jp_numbers': jp_numbers,
                    'subject': subject,
                    'is_piket': is_piket,
                    'notes': notes,
                }
            )
            
            if user:
                if created:
                    schedule.created_by = user
                schedule.updated_by = user
                schedule.save()
            
            return schedule
            
        except Exception as e:
            logger.error(f"Error creating/updating schedule: {str(e)}")
            raise AttendanceServiceError(f"Failed to save schedule: {str(e)}")
    
    @staticmethod
    def get_teachers_without_attendance_today():
        """
        Get list of teachers who haven't recorded attendance today
        
        Returns:
            QuerySet of Teacher
        """
        try:
            today = timezone.now().date()
            day_of_week = today.weekday()
            
            # Get teachers who have schedule today
            teachers_with_schedule = TeacherSchedule.objects.filter(
                day_of_week=day_of_week
            ).values_list('teacher_id', flat=True)
            
            # Get teachers who already recorded attendance today
            teachers_with_attendance = TeacherDailyAttendance.objects.filter(
                date=today
            ).values_list('teacher_id', flat=True)
            
            # Teachers with schedule but no attendance
            missing_teachers = Teacher.objects.filter(
                id__in=teachers_with_schedule,
                is_active=True
            ).exclude(
                id__in=teachers_with_attendance
            ).order_by('name')
            
            return missing_teachers
            
        except Exception as e:
            logger.error(f"Error getting teachers without attendance: {str(e)}")
            return Teacher.objects.none()
    
    @staticmethod
    def get_teacher_attendance_summary(teacher, start_date=None, end_date=None):
        """
        Get attendance summary for a teacher
        
        Args:
            teacher: Teacher instance
            start_date: Start date (optional)
            end_date: End date (optional)
            
        Returns:
            Dict with summary statistics
        """
        try:
            queryset = TeacherDailyAttendance.objects.filter(teacher=teacher)
            
            if start_date:
                queryset = queryset.filter(date__gte=start_date)
            if end_date:
                queryset = queryset.filter(date__lte=end_date)
            
            # Count JP statuses
            total_hadir = 0
            total_sakit = 0
            total_izin = 0
            total_alpa = 0
            total_tidak_ada_jadwal = 0
            total_dinas_luar = 0
            total_cuti = 0
            total_terlambat = 0
            total_jp = 0
            
            for attendance in queryset:
                for status in attendance.jp_statuses.values():
                    total_jp += 1
                    if status == 'H':
                        total_hadir += 1
                    elif status == 'S':
                        total_sakit += 1
                    elif status == 'I':
                        total_izin += 1
                    elif status == 'A':
                        total_alpa += 1
                    elif status == 'T':
                        total_tidak_ada_jadwal += 1
                    elif status == 'D':
                        total_dinas_luar += 1
                    elif status == 'C':
                        total_cuti += 1
                    elif status == 'L':
                        total_terlambat += 1
            
            # Calculate percentage
            attendance_rate = 0.0
            if total_jp > 0:
                attendance_rate = round((total_hadir / total_jp) * 100, 2)
            
            return {
                'total_days': queryset.count(),
                'total_jp': total_jp,
                'hadir': total_hadir,
                'sakit': total_sakit,
                'izin': total_izin,
                'alpa': total_alpa,
                'tidak_ada_jadwal': total_tidak_ada_jadwal,
                'dinas_luar': total_dinas_luar,
                'cuti': total_cuti,
                'terlambat': total_terlambat,
                'attendance_rate': attendance_rate,
                'recent_records': queryset.order_by('-date')[:20]
            }
            
        except Exception as e:
            logger.error(f"Error getting teacher attendance summary: {str(e)}")
            raise AttendanceServiceError(f"Failed to get attendance summary: {str(e)}")
