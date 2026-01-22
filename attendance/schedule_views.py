"""
Teacher Schedule Management Views
Handles schedule CRUD operations with conflict detection

Authorization:
- Admin: Full access to all schedule management
- Teacher: Read-only access to own schedule
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.utils import timezone
import json
import logging

from .models import Teacher, Subject, Classroom, TeacherSchedule
from .forms import TeacherScheduleForm
from .services.schedule_service import ScheduleService, TeacherScheduleService
from .decorators import admin_required

logger = logging.getLogger(__name__)


@login_required
def schedule_management(request):
    """
    Main schedule management page with weekly grid view
    
    Features:
    - Display weekly schedule grid (days x JP)
    - Filter by teacher
    - Add/Edit/Delete schedule via modal
    - Conflict detection
    
    Access:
    - Admin: Can manage all schedules
    - Teacher: Can view own schedule only
    """
    # Get filter parameters
    teacher_id = request.GET.get('teacher')
    
    # Determine which teacher to show
    if request.user.is_superuser:
        # Admin can view any teacher
        if teacher_id:
            try:
                selected_teacher = Teacher.objects.get(id=teacher_id)
            except Teacher.DoesNotExist:
                messages.error(request, "Ustadz tidak ditemukan")
                selected_teacher = None
        else:
            # Default to first active teacher
            selected_teacher = Teacher.objects.filter(is_active=True).first()
    else:
        # Regular user can only view own schedule
        if hasattr(request.user, 'teacher_profile'):
            selected_teacher = request.user.teacher_profile
        else:
            messages.error(request, "Anda tidak memiliki profil ustadz")
            return redirect('dashboard')
    
    # Get weekly schedule if teacher is selected
    weekly_schedule = {}
    total_jp = 0
    if selected_teacher:
        try:
            weekly_schedule = TeacherScheduleService.get_weekly_schedule(selected_teacher.id)
            # Calculate total JP
            for day_schedules in weekly_schedule.values():
                for schedule in day_schedules:
                    total_jp += schedule.jp_count
        except Exception as e:
            logger.error(f"Error getting weekly schedule: {str(e)}")
            messages.error(request, "Terjadi kesalahan saat memuat jadwal")
    
    # Get all active teachers for filter (admin only)
    teachers = []
    if request.user.is_superuser:
        teachers = Teacher.objects.filter(is_active=True).order_by('full_name')
    
    # Get subjects and classrooms for form
    subjects = Subject.objects.filter(is_active=True).order_by('name')
    classrooms = Classroom.objects.filter(is_active=True).select_related('academic_level').order_by('name')
    
    # Days configuration
    days = [
        {'value': 0, 'name': 'Senin'},
        {'value': 1, 'name': 'Selasa'},
        {'value': 2, 'name': 'Rabu'},
        {'value': 3, 'name': 'Kamis'},
        {'value': 4, 'name': 'Jumat'},
        {'value': 5, 'name': 'Sabtu'},
    ]
    
    # JP slots (1-10)
    jp_slots = list(range(1, 11))
    
    context = {
        'selected_teacher': selected_teacher,
        'teachers': teachers,
        'weekly_schedule': weekly_schedule,
        'total_jp': total_jp,
        'subjects': subjects,
        'classrooms': classrooms,
        'days': days,
        'jp_slots': jp_slots,
        'is_admin': request.user.is_superuser,
    }
    
    return render(request, 'teacher/schedule_management.html', context)


@login_required
@admin_required
@require_http_methods(["POST"])
def schedule_create(request):
    """
    Create new schedule via AJAX
    
    Returns JSON with success/error message
    """
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['teacher_id', 'subject_id', 'classroom_id', 'day_of_week', 'jp_start', 'jp_end']
        for field in required_fields:
            if field not in data:
                return JsonResponse({
                    'success': False,
                    'error': f'Field {field} diperlukan'
                }, status=400)
        
        # Get related objects
        teacher = get_object_or_404(Teacher, id=data['teacher_id'])
        subject = get_object_or_404(Subject, id=data['subject_id'])
        classroom = get_object_or_404(Classroom, id=data['classroom_id'])
        
        # Check for conflicts
        conflicts = ScheduleService.detect_conflicts(
            teacher_id=teacher.id,
            day=int(data['day_of_week']),
            jp_start=int(data['jp_start']),
            jp_end=int(data['jp_end']),
            effective_date=timezone.now().date()
        )
        
        if conflicts:
            conflict_messages = []
            for conflict in conflicts:
                if conflict['type'] == 'teacher':
                    msg = f"Ustadz sudah memiliki jadwal pada {conflict['day_name']} JP {conflict['jp_start']}-{conflict['jp_end']}"
                elif conflict['type'] == 'classroom':
                    msg = f"Kelas {conflict['classroom_name']} sudah dijadwalkan pada {conflict['day_name']} JP {conflict['jp_start']}-{conflict['jp_end']}"
                conflict_messages.append(msg)
            
            return JsonResponse({
                'success': False,
                'error': 'Konflik jadwal ditemukan',
                'conflicts': conflict_messages
            }, status=400)
        
        # Create schedule
        schedule = TeacherSchedule.objects.create(
            teacher=teacher,
            subject=subject,
            classroom=classroom,
            day_of_week=int(data['day_of_week']),
            jp_start=int(data['jp_start']),
            jp_end=int(data['jp_end']),
            room_number=data.get('room_number', ''),
            notes=data.get('notes', ''),
            effective_date=timezone.now().date(),
            is_active=True,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Jadwal berhasil ditambahkan',
            'schedule': {
                'id': str(schedule.id),
                'subject': schedule.subject.name,
                'classroom': schedule.classroom.name,
                'day_name': schedule.day_name,
                'jp_range': f"JP {schedule.jp_start}-{schedule.jp_end}",
                'room_number': schedule.room_number,
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Format JSON tidak valid'
        }, status=400)
    except Exception as e:
        logger.error(f"Error creating schedule: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Terjadi kesalahan: {str(e)}'
        }, status=500)


@login_required
@admin_required
@require_http_methods(["POST"])
def schedule_update(request, pk):
    """
    Update existing schedule via AJAX
    
    Returns JSON with success/error message
    """
    try:
        schedule = get_object_or_404(TeacherSchedule, id=pk)
        data = json.loads(request.body)
        
        # Get related objects if provided
        if 'subject_id' in data:
            schedule.subject = get_object_or_404(Subject, id=data['subject_id'])
        if 'classroom_id' in data:
            schedule.classroom = get_object_or_404(Classroom, id=data['classroom_id'])
        
        # Update time if provided
        day_changed = False
        time_changed = False
        
        if 'day_of_week' in data:
            new_day = int(data['day_of_week'])
            if new_day != schedule.day_of_week:
                day_changed = True
                schedule.day_of_week = new_day
        
        if 'jp_start' in data or 'jp_end' in data:
            new_jp_start = int(data.get('jp_start', schedule.jp_start))
            new_jp_end = int(data.get('jp_end', schedule.jp_end))
            
            if new_jp_start != schedule.jp_start or new_jp_end != schedule.jp_end:
                time_changed = True
                schedule.jp_start = new_jp_start
                schedule.jp_end = new_jp_end
        
        # Check for conflicts if day or time changed
        if day_changed or time_changed:
            conflicts = ScheduleService.detect_conflicts(
                teacher_id=schedule.teacher.id,
                day=schedule.day_of_week,
                jp_start=schedule.jp_start,
                jp_end=schedule.jp_end,
                effective_date=schedule.effective_date,
                exclude_schedule_id=schedule.id
            )
            
            if conflicts:
                conflict_messages = []
                for conflict in conflicts:
                    if conflict['type'] == 'teacher':
                        msg = f"Ustadz sudah memiliki jadwal pada {conflict['day_name']} JP {conflict['jp_start']}-{conflict['jp_end']}"
                    elif conflict['type'] == 'classroom':
                        msg = f"Kelas {conflict['classroom_name']} sudah dijadwalkan pada {conflict['day_name']} JP {conflict['jp_start']}-{conflict['jp_end']}"
                    conflict_messages.append(msg)
                
                return JsonResponse({
                    'success': False,
                    'error': 'Konflik jadwal ditemukan',
                    'conflicts': conflict_messages
                }, status=400)
        
        # Update other fields
        if 'room_number' in data:
            schedule.room_number = data['room_number']
        if 'notes' in data:
            schedule.notes = data['notes']
        if 'is_active' in data:
            schedule.is_active = data['is_active']
        
        schedule.updated_by = request.user
        schedule.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Jadwal berhasil diperbarui',
            'schedule': {
                'id': str(schedule.id),
                'subject': schedule.subject.name,
                'classroom': schedule.classroom.name,
                'day_name': schedule.day_name,
                'jp_range': f"JP {schedule.jp_start}-{schedule.jp_end}",
                'room_number': schedule.room_number,
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Format JSON tidak valid'
        }, status=400)
    except Exception as e:
        logger.error(f"Error updating schedule: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Terjadi kesalahan: {str(e)}'
        }, status=500)


@login_required
@admin_required
@require_http_methods(["POST"])
def schedule_delete(request, pk):
    """
    Delete schedule via AJAX
    
    Returns JSON with success/error message
    """
    try:
        schedule = get_object_or_404(TeacherSchedule, id=pk)
        
        # Soft delete by setting is_active to False
        schedule.is_active = False
        schedule.updated_by = request.user
        schedule.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Jadwal berhasil dihapus'
        })
        
    except Exception as e:
        logger.error(f"Error deleting schedule: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Terjadi kesalahan: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def schedule_detail(request, pk):
    """
    Get schedule detail via AJAX
    
    Returns JSON with schedule data
    """
    try:
        schedule = get_object_or_404(TeacherSchedule, id=pk)
        
        # Check permission
        if not request.user.is_superuser:
            if not hasattr(request.user, 'teacher_profile') or request.user.teacher_profile != schedule.teacher:
                return JsonResponse({
                    'success': False,
                    'error': 'Anda tidak memiliki akses ke jadwal ini'
                }, status=403)
        
        return JsonResponse({
            'success': True,
            'schedule': {
                'id': str(schedule.id),
                'teacher_id': str(schedule.teacher.id),
                'teacher_name': schedule.teacher.full_name,
                'subject_id': str(schedule.subject.id),
                'subject_name': schedule.subject.name,
                'classroom_id': str(schedule.classroom.id),
                'classroom_name': schedule.classroom.name,
                'day_of_week': schedule.day_of_week,
                'day_name': schedule.day_name,
                'jp_start': schedule.jp_start,
                'jp_end': schedule.jp_end,
                'jp_count': schedule.jp_count,
                'room_number': schedule.room_number,
                'notes': schedule.notes,
                'is_active': schedule.is_active,
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting schedule detail: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Terjadi kesalahan: {str(e)}'
        }, status=500)
