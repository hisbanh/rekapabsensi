"""
Notification Service Layer
Handles all business logic related to teacher attendance notifications

This service provides notification functionality for:
- Absent teachers without attendance records
- Scheduling conflicts
- Missing attendance records
- General system notifications

Requirements: FR-021, FR-022
"""
from typing import List, Dict, Optional
from datetime import date, timedelta
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.models import User
import logging

from ..models import (
    Teacher, TeacherAttendance, TeacherSchedule
)
from ..exceptions import AttendanceBaseException

logger = logging.getLogger(__name__)


class NotificationServiceError(AttendanceBaseException):
    """Exception raised by notification service operations"""
    pass


class NotificationService:
    """Service class for notification-related business operations"""
    
    # Notification types
    TYPE_MISSING_ATTENDANCE = 'missing_attendance'
    TYPE_CONFLICT = 'conflict'
    TYPE_ABSENT = 'absent'
    TYPE_INFO = 'info'
    TYPE_WARNING = 'warning'
    TYPE_ERROR = 'error'
    
    # Priority levels
    PRIORITY_HIGH = 'high'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_LOW = 'low'
    
    @staticmethod
    def get_absent_teachers_notification(target_date: date) -> List[Dict]:
        """
        Get notifications for teachers who are absent on a specific date.
        
        This method identifies teachers who have schedules for the given date
        but have recorded non-HADIR status (SAKIT, IZIN, CUTI, DINAS, ALPA)
        or have not recorded attendance at all.
        
        Args:
            target_date: Date to check for absent teachers
            
        Returns:
            List of notification dictionaries containing:
                - type: Notification type (TYPE_ABSENT or TYPE_MISSING_ATTENDANCE)
                - message: Human-readable notification message
                - priority: Priority level (PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW)
                - date: Related date
                - teacher: Teacher instance
                - status: Attendance status or 'NOT_RECORDED'
                - jp_numbers: List of JP numbers where absent/not recorded
                - total_jp: Total number of JP affected
                
        Example:
            >>> from datetime import date
            >>> notifications = NotificationService.get_absent_teachers_notification(date(2024, 1, 20))
            >>> for notif in notifications:
            ...     print(f"{notif['message']} - Priority: {notif['priority']}")
        """
        notifications = []
        day_of_week = target_date.weekday()
        
        try:
            # Get all active teachers with schedules for this day
            teachers_with_schedules = Teacher.objects.filter(
                is_active=True,
                schedules__day_of_week=day_of_week,
                schedules__is_active=True,
                schedules__effective_date__lte=target_date
            ).filter(
                Q(schedules__end_date__isnull=True) | 
                Q(schedules__end_date__gte=target_date)
            ).distinct()
            
            for teacher in teachers_with_schedules:
                # Get schedules for this teacher on this day
                schedules = TeacherSchedule.objects.filter(
                    teacher=teacher,
                    day_of_week=day_of_week,
                    is_active=True,
                    effective_date__lte=target_date
                ).filter(
                    Q(end_date__isnull=True) | Q(end_date__gte=target_date)
                )
                
                # Get all scheduled JP numbers
                scheduled_jp_numbers = set()
                for schedule in schedules:
                    for jp_num in range(schedule.jp_start, schedule.jp_end + 1):
                        scheduled_jp_numbers.add(jp_num)
                
                # Get attendance records for this teacher on this date
                attendances = TeacherAttendance.objects.filter(
                    teacher=teacher,
                    date=target_date
                )
                
                # Build attendance status map
                attendance_map = {}
                for attendance in attendances:
                    attendance_map[attendance.jp_number] = attendance.status
                
                # Check for absent or missing attendance
                absent_jp = []
                missing_jp = []
                
                for jp_num in scheduled_jp_numbers:
                    status = attendance_map.get(jp_num)
                    
                    if status is None:
                        # No attendance record
                        missing_jp.append(jp_num)
                    elif status != 'HADIR':
                        # Absent (SAKIT, IZIN, CUTI, DINAS, ALPA)
                        absent_jp.append({
                            'jp_number': jp_num,
                            'status': status
                        })
                
                # Create notification for missing attendance
                if missing_jp:
                    jp_list = ', '.join([f'JP{jp}' for jp in sorted(missing_jp)])
                    notifications.append({
                        'type': NotificationService.TYPE_MISSING_ATTENDANCE,
                        'message': f'{teacher.full_name} belum mencatat absensi untuk {jp_list}',
                        'priority': NotificationService.PRIORITY_HIGH,
                        'date': target_date,
                        'teacher': teacher,
                        'status': 'NOT_RECORDED',
                        'jp_numbers': sorted(missing_jp),
                        'total_jp': len(missing_jp),
                    })
                
                # Create notification for absent teachers
                if absent_jp:
                    # Group by status
                    status_groups = {}
                    for jp_info in absent_jp:
                        status = jp_info['status']
                        if status not in status_groups:
                            status_groups[status] = []
                        status_groups[status].append(jp_info['jp_number'])
                    
                    # Create notification for each status
                    for status, jp_numbers in status_groups.items():
                        jp_list = ', '.join([f'JP{jp}' for jp in sorted(jp_numbers)])
                        
                        # Determine priority based on status
                        if status == 'ALPA':
                            priority = NotificationService.PRIORITY_HIGH
                        elif status in ['SAKIT', 'IZIN']:
                            priority = NotificationService.PRIORITY_MEDIUM
                        else:  # CUTI, DINAS
                            priority = NotificationService.PRIORITY_LOW
                        
                        # Get status display name
                        status_display = {
                            'SAKIT': 'sakit',
                            'IZIN': 'izin',
                            'CUTI': 'cuti',
                            'DINAS': 'dinas luar',
                            'ALPA': 'alpa'
                        }.get(status, status.lower())
                        
                        notifications.append({
                            'type': NotificationService.TYPE_ABSENT,
                            'message': f'{teacher.full_name} {status_display} pada {jp_list}',
                            'priority': priority,
                            'date': target_date,
                            'teacher': teacher,
                            'status': status,
                            'jp_numbers': sorted(jp_numbers),
                            'total_jp': len(jp_numbers),
                        })
            
            # Sort notifications by priority (high first) and then by teacher name
            priority_order = {
                NotificationService.PRIORITY_HIGH: 0,
                NotificationService.PRIORITY_MEDIUM: 1,
                NotificationService.PRIORITY_LOW: 2,
            }
            notifications.sort(key=lambda x: (
                priority_order.get(x['priority'], 3),
                x['teacher'].full_name
            ))
            
        except Exception as e:
            logger.error(f"Error getting absent teachers notification: {str(e)}")
            raise NotificationServiceError(f"Error getting absent teachers notification: {str(e)}")
        
        return notifications
    
    @staticmethod
    def get_scheduling_conflicts_notification() -> List[Dict]:
        """
        Get notifications for scheduling conflicts.
        
        This method detects two types of conflicts:
        1. Teacher conflicts: Same teacher scheduled at overlapping times
        2. Classroom conflicts: Same classroom scheduled with different teachers at overlapping times
        
        Returns:
            List of notification dictionaries containing:
                - type: Notification type (TYPE_CONFLICT)
                - message: Human-readable conflict description
                - priority: Priority level (PRIORITY_MEDIUM)
                - conflict_type: 'teacher_conflict' or 'classroom_conflict'
                - teacher: Teacher instance (for teacher conflicts)
                - classroom: Classroom instance (for classroom conflicts)
                - day_of_week: Day of week (0-6)
                - day_name: Day name in Indonesian
                - schedule1: First conflicting schedule
                - schedule2: Second conflicting schedule
                - jp_overlap: List of overlapping JP numbers
                
        Example:
            >>> conflicts = NotificationService.get_scheduling_conflicts_notification()
            >>> for conflict in conflicts:
            ...     print(f"{conflict['message']} - {conflict['day_name']}")
        """
        notifications = []
        today = timezone.now().date()
        
        try:
            # Get all active schedules
            schedules = TeacherSchedule.objects.filter(
                is_active=True,
                effective_date__lte=today
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=today)
            ).select_related('teacher', 'subject', 'classroom')
            
            # Day names for display
            day_names = {
                0: 'Senin', 1: 'Selasa', 2: 'Rabu',
                3: 'Kamis', 4: 'Jumat', 5: 'Sabtu', 6: 'Minggu'
            }
            
            # Check for teacher conflicts
            teacher_schedules = {}
            for schedule in schedules:
                key = (schedule.teacher_id, schedule.day_of_week)
                if key not in teacher_schedules:
                    teacher_schedules[key] = []
                teacher_schedules[key].append(schedule)
            
            for (teacher_id, day), schedule_list in teacher_schedules.items():
                for i, schedule1 in enumerate(schedule_list):
                    for schedule2 in schedule_list[i+1:]:
                        # Check for JP overlap
                        overlap_start = max(schedule1.jp_start, schedule2.jp_start)
                        overlap_end = min(schedule1.jp_end, schedule2.jp_end)
                        
                        if overlap_start <= overlap_end:
                            # There is an overlap
                            jp_overlap = list(range(overlap_start, overlap_end + 1))
                            jp_list = ', '.join([f'JP{jp}' for jp in jp_overlap])
                            
                            notifications.append({
                                'type': NotificationService.TYPE_CONFLICT,
                                'message': (
                                    f'Konflik jadwal: {schedule1.teacher.full_name} mengajar '
                                    f'{schedule1.subject.name} dan {schedule2.subject.name} '
                                    f'pada {day_names[day]} {jp_list}'
                                ),
                                'priority': NotificationService.PRIORITY_MEDIUM,
                                'conflict_type': 'teacher_conflict',
                                'teacher': schedule1.teacher,
                                'day_of_week': day,
                                'day_name': day_names[day],
                                'schedule1': schedule1,
                                'schedule2': schedule2,
                                'jp_overlap': jp_overlap,
                            })
            
            # Check for classroom conflicts
            classroom_schedules = {}
            for schedule in schedules:
                key = (schedule.classroom_id, schedule.day_of_week)
                if key not in classroom_schedules:
                    classroom_schedules[key] = []
                classroom_schedules[key].append(schedule)
            
            for (classroom_id, day), schedule_list in classroom_schedules.items():
                for i, schedule1 in enumerate(schedule_list):
                    for schedule2 in schedule_list[i+1:]:
                        # Check for JP overlap
                        overlap_start = max(schedule1.jp_start, schedule2.jp_start)
                        overlap_end = min(schedule1.jp_end, schedule2.jp_end)
                        
                        if overlap_start <= overlap_end:
                            # There is an overlap
                            jp_overlap = list(range(overlap_start, overlap_end + 1))
                            jp_list = ', '.join([f'JP{jp}' for jp in jp_overlap])
                            
                            notifications.append({
                                'type': NotificationService.TYPE_CONFLICT,
                                'message': (
                                    f'Konflik ruangan: {schedule1.classroom.name} digunakan oleh '
                                    f'{schedule1.teacher.full_name} dan {schedule2.teacher.full_name} '
                                    f'pada {day_names[day]} {jp_list}'
                                ),
                                'priority': NotificationService.PRIORITY_MEDIUM,
                                'conflict_type': 'classroom_conflict',
                                'classroom': schedule1.classroom,
                                'day_of_week': day,
                                'day_name': day_names[day],
                                'schedule1': schedule1,
                                'schedule2': schedule2,
                                'jp_overlap': jp_overlap,
                            })
            
            # Sort by day of week and then by teacher/classroom name
            notifications.sort(key=lambda x: (
                x['day_of_week'],
                x.get('teacher', x.get('classroom')).full_name if hasattr(x.get('teacher', x.get('classroom')), 'full_name') 
                else x.get('classroom').name
            ))
            
        except Exception as e:
            logger.error(f"Error getting scheduling conflicts notification: {str(e)}")
            raise NotificationServiceError(f"Error getting scheduling conflicts notification: {str(e)}")
        
        return notifications
    
    @staticmethod
    def get_missing_attendance_notification(target_date: date) -> List[Dict]:
        """
        Get notifications for teachers who have not recorded attendance.
        
        This method identifies teachers who have schedules for the given date
        but have not recorded any attendance at all.
        
        Args:
            target_date: Date to check for missing attendance
            
        Returns:
            List of notification dictionaries containing:
                - type: Notification type (TYPE_MISSING_ATTENDANCE)
                - message: Human-readable notification message
                - priority: Priority level (PRIORITY_HIGH)
                - date: Related date
                - teacher: Teacher instance
                - scheduled_jp: List of scheduled JP numbers
                - total_jp: Total number of JP scheduled
                
        Example:
            >>> from datetime import date
            >>> notifications = NotificationService.get_missing_attendance_notification(date(2024, 1, 20))
            >>> for notif in notifications:
            ...     print(f"{notif['message']}")
        """
        notifications = []
        day_of_week = target_date.weekday()
        
        try:
            # Get all active teachers with schedules for this day
            teachers_with_schedules = Teacher.objects.filter(
                is_active=True,
                schedules__day_of_week=day_of_week,
                schedules__is_active=True,
                schedules__effective_date__lte=target_date
            ).filter(
                Q(schedules__end_date__isnull=True) | 
                Q(schedules__end_date__gte=target_date)
            ).distinct()
            
            for teacher in teachers_with_schedules:
                # Check if teacher has any attendance record for this date
                has_attendance = TeacherAttendance.objects.filter(
                    teacher=teacher,
                    date=target_date
                ).exists()
                
                if not has_attendance:
                    # Get all scheduled JP for this teacher
                    schedules = TeacherSchedule.objects.filter(
                        teacher=teacher,
                        day_of_week=day_of_week,
                        is_active=True,
                        effective_date__lte=target_date
                    ).filter(
                        Q(end_date__isnull=True) | Q(end_date__gte=target_date)
                    )
                    
                    scheduled_jp = set()
                    for schedule in schedules:
                        for jp_num in range(schedule.jp_start, schedule.jp_end + 1):
                            scheduled_jp.add(jp_num)
                    
                    if scheduled_jp:
                        jp_list = ', '.join([f'JP{jp}' for jp in sorted(scheduled_jp)])
                        
                        notifications.append({
                            'type': NotificationService.TYPE_MISSING_ATTENDANCE,
                            'message': f'{teacher.full_name} belum mencatat absensi sama sekali ({jp_list})',
                            'priority': NotificationService.PRIORITY_HIGH,
                            'date': target_date,
                            'teacher': teacher,
                            'scheduled_jp': sorted(scheduled_jp),
                            'total_jp': len(scheduled_jp),
                        })
            
            # Sort by teacher name
            notifications.sort(key=lambda x: x['teacher'].full_name)
            
        except Exception as e:
            logger.error(f"Error getting missing attendance notification: {str(e)}")
            raise NotificationServiceError(f"Error getting missing attendance notification: {str(e)}")
        
        return notifications
    
    @staticmethod
    def send_notification(user: User, message: str, notification_type: str) -> None:
        """
        Send a notification to a user.
        
        This is a placeholder method for future notification delivery implementation.
        In a full implementation, this could:
        - Store notifications in a database table
        - Send email notifications
        - Send push notifications
        - Display in-app notifications
        
        Args:
            user: User to send notification to
            message: Notification message
            notification_type: Type of notification (TYPE_* constants)
            
        Raises:
            NotificationServiceError: If notification sending fails
            
        Example:
            >>> from django.contrib.auth.models import User
            >>> user = User.objects.get(username='admin')
            >>> NotificationService.send_notification(
            ...     user,
            ...     'Teacher attendance reminder',
            ...     NotificationService.TYPE_INFO
            ... )
        """
        try:
            # Log the notification
            logger.info(f"Notification for {user.username}: [{notification_type}] {message}")
            
            # TODO: Implement actual notification delivery
            # Options:
            # 1. Store in database (create Notification model)
            # 2. Send email using Django's email backend
            # 3. Send push notification using a service like Firebase
            # 4. Display as Django messages framework message
            
            # For now, just log it
            # In a real implementation, you might do:
            # - Notification.objects.create(user=user, message=message, type=notification_type)
            # - send_mail(subject, message, from_email, [user.email])
            # - send_push_notification(user, message)
            
        except Exception as e:
            logger.error(f"Error sending notification to {user.username}: {str(e)}")
            raise NotificationServiceError(f"Error sending notification: {str(e)}")
    
    @staticmethod
    def get_all_notifications(target_date: Optional[date] = None) -> Dict[str, List[Dict]]:
        """
        Get all notifications for a specific date.
        
        This is a convenience method that combines all notification types.
        
        Args:
            target_date: Date to check (defaults to today)
            
        Returns:
            Dictionary containing:
                - absent_teachers: List of absent teacher notifications
                - missing_attendance: List of missing attendance notifications
                - scheduling_conflicts: List of scheduling conflict notifications
                - total_count: Total number of notifications
                - high_priority_count: Count of high priority notifications
                
        Example:
            >>> from datetime import date
            >>> all_notifs = NotificationService.get_all_notifications(date(2024, 1, 20))
            >>> print(f"Total notifications: {all_notifs['total_count']}")
            >>> print(f"High priority: {all_notifs['high_priority_count']}")
        """
        if target_date is None:
            target_date = timezone.now().date()
        
        try:
            # Get all notification types
            absent_teachers = NotificationService.get_absent_teachers_notification(target_date)
            missing_attendance = NotificationService.get_missing_attendance_notification(target_date)
            scheduling_conflicts = NotificationService.get_scheduling_conflicts_notification()
            
            # Combine all notifications
            all_notifications = absent_teachers + missing_attendance + scheduling_conflicts
            
            # Count high priority notifications
            high_priority_count = sum(
                1 for notif in all_notifications 
                if notif['priority'] == NotificationService.PRIORITY_HIGH
            )
            
            return {
                'absent_teachers': absent_teachers,
                'missing_attendance': missing_attendance,
                'scheduling_conflicts': scheduling_conflicts,
                'all_notifications': all_notifications,
                'total_count': len(all_notifications),
                'high_priority_count': high_priority_count,
            }
            
        except Exception as e:
            logger.error(f"Error getting all notifications: {str(e)}")
            raise NotificationServiceError(f"Error getting all notifications: {str(e)}")
