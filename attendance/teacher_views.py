"""
Teacher Management Views
Handles all views related to teacher CRUD operations and schedule management

Authorization:
- Admin: Full access to all teacher management features
- Teacher: Read-only access to own profile and schedule
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db import models
from django.utils import timezone
import logging

from .models import Teacher, Subject, Classroom, TeacherSchedule
from .services.teacher_service import TeacherService, TeacherServiceError
from .services.schedule_service import TeacherScheduleService, ScheduleService
from .decorators import admin_required

logger = logging.getLogger(__name__)


# ============================================
# Teacher Management Views
# Read: All authenticated users
# Write: Admin only
# ============================================

@login_required
def teacher_list(request):
    """
    Teacher list view with filtering, search, and pagination.
    
    Accessible by: All authenticated users
    
    Features:
    - Search by name, NIP, or email
    - Filter by employment status, subject, homeroom teacher status
    - Pagination (20 per page)
    - Display teacher photo, subjects, and statistics
    
    Requirements: FR-028, FR-029
    """
    try:
        # Get filter parameters
        search_query = request.GET.get('search', '').strip()
        employment_status = request.GET.get('employment_status', '')
        subject_id = request.GET.get('subject', '')
        is_homeroom = request.GET.get('is_homeroom', '')
        is_active = request.GET.get('is_active', '')
        
        # Build filters dictionary
        filters = {}
        
        if employment_status:
            filters['employment_status'] = employment_status
        
        if subject_id:
            filters['subject_id'] = subject_id
        
        if is_homeroom:
            filters['is_homeroom_teacher'] = is_homeroom == 'true'
        
        if is_active:
            filters['is_active'] = is_active == 'true'
        
        if search_query:
            filters['search_query'] = search_query
        
        # Get filtered teachers using service
        teachers = TeacherService.get_teachers_with_filters(filters)
        
        # Pagination
        paginator = Paginator(teachers, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Get filter options
        subjects = Subject.objects.filter(is_active=True).order_by('name')
        
        # Calculate statistics
        total_teachers = Teacher.objects.count()
        active_teachers = Teacher.objects.filter(is_active=True).count()
        homeroom_teachers = Teacher.objects.filter(is_homeroom_teacher=True, is_active=True).count()
        
        context = {
            'teachers': page_obj,
            'subjects': subjects,
            'total_teachers': total_teachers,
            'active_teachers': active_teachers,
            'homeroom_teachers': homeroom_teachers,
            # Preserve filter values
            'search_query': search_query,
            'current_employment_status': employment_status,
            'current_subject': subject_id,
            'current_is_homeroom': is_homeroom,
            'current_is_active': is_active,
        }
        
    except Exception as e:
        logger.error(f"Error loading teacher list: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat memuat data ustadz")
        context = {
            'teachers': [],
            'subjects': [],
            'total_teachers': 0,
            'active_teachers': 0,
            'homeroom_teachers': 0,
        }
    
    return render(request, 'teacher/teacher_list.html', context)


@login_required
@admin_required
def teacher_create(request):
    """
    Create new teacher view.
    
    Accessible by: Admin only
    
    Features:
    - Create teacher with complete profile
    - Photo upload
    - Subject assignment
    - Homeroom class assignment
    - Validation using TeacherForm
    
    Requirements: FR-001, FR-002, FR-004
    """
    from .forms import TeacherForm
    
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Save teacher (form handles subject assignment)
                teacher = form.save()
                
                messages.success(request, f'Ustadz "{teacher.full_name}" berhasil ditambahkan')
                return redirect('teacher_detail', pk=teacher.id)
                
            except Exception as e:
                logger.error(f"Error creating teacher: {str(e)}")
                messages.error(request, f"Terjadi kesalahan: {str(e)}")
        else:
            # Form validation failed
            messages.error(request, "Mohon perbaiki kesalahan pada form")
    else:
        # GET request - show empty form
        form = TeacherForm()
    
    context = {
        'form': form,
        'is_edit': False,
    }
    
    return render(request, 'teacher/teacher_form.html', context)


@login_required
def teacher_detail(request, pk):
    """
    Teacher detail view with complete profile and statistics.
    
    Accessible by: All authenticated users
    Teachers can only view their own profile (enforced in template)
    
    Features:
    - Display complete teacher profile
    - Show assigned subjects
    - Display weekly schedule
    - Show attendance statistics
    - Edit/Delete buttons (admin only)
    
    Requirements: FR-028, FR-029
    """
    try:
        # Get teacher profile using service
        profile = TeacherService.get_teacher_profile(pk)
        teacher = profile['teacher']
        
        # Check if current user is viewing their own profile
        is_own_profile = (
            request.user.is_authenticated and 
            hasattr(request.user, 'teacher_profile') and 
            request.user.teacher_profile.id == teacher.id
        )
        
        # Get attendance statistics for current month
        now = timezone.now()
        try:
            stats = TeacherService.get_teacher_statistics(
                teacher.id,
                now.year,
                now.month
            )
        except TeacherServiceError:
            stats = {
                'total_hadir': 0,
                'total_sakit': 0,
                'total_izin': 0,
                'total_alpa': 0,
                'attendance_percentage': 0.0,
            }
        
        # Get weekly schedule
        try:
            weekly_schedule = TeacherScheduleService.get_weekly_schedule(teacher.id)
        except Exception as e:
            logger.error(f"Error getting weekly schedule: {str(e)}")
            weekly_schedule = {}
        
        context = {
            'teacher': teacher,
            'subjects': profile['subjects'],
            'homeroom_class': profile['homeroom_class'],
            'total_schedules': profile['total_schedules'],
            'teaching_load': profile['teaching_load'],
            'stats': stats,
            'weekly_schedule': weekly_schedule,
            'is_own_profile': is_own_profile,
        }
        
    except TeacherServiceError as e:
        logger.error(f"Teacher service error: {str(e)}")
        messages.error(request, f"Ustadz tidak ditemukan: {str(e)}")
        return redirect('teacher_list')
    except Exception as e:
        logger.error(f"Error loading teacher detail: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat memuat detail ustadz")
        return redirect('teacher_list')
    
    return render(request, 'teacher/teacher_detail.html', context)


@login_required
@admin_required
def teacher_update(request, pk):
    """
    Update existing teacher view.
    
    Accessible by: Admin only
    
    Features:
    - Edit teacher profile
    - Update photo
    - Modify subject assignments
    - Change homeroom class
    - Validation using TeacherForm
    
    Requirements: FR-001, FR-002, FR-004
    """
    from .forms import TeacherForm
    
    try:
        # Optimized query with prefetch_related for subjects
        teacher = Teacher.objects.prefetch_related('subjects').select_related(
            'homeroom_class', 'homeroom_class__academic_level'
        ).get(id=pk)
    except Teacher.DoesNotExist:
        messages.error(request, "Ustadz tidak ditemukan")
        return redirect('teacher_list')
    
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            try:
                # Save teacher (form handles subject assignment)
                teacher = form.save()
                
                messages.success(request, f'Ustadz "{teacher.full_name}" berhasil diperbarui')
                return redirect('teacher_detail', pk=teacher.id)
                
            except Exception as e:
                logger.error(f"Error updating teacher: {str(e)}")
                messages.error(request, f"Terjadi kesalahan: {str(e)}")
        else:
            # Form validation failed
            messages.error(request, "Mohon perbaiki kesalahan pada form")
    else:
        # GET request - show form with existing data
        form = TeacherForm(instance=teacher)
    
    context = {
        'form': form,
        'teacher': teacher,
        'is_edit': True,
    }
    
    return render(request, 'teacher/teacher_form.html', context)


@login_required
@admin_required
@require_http_methods(["POST"])
def teacher_delete(request, pk):
    """
    Soft delete teacher (set is_active to False).
    
    Accessible by: Admin only
    
    Features:
    - Soft delete (preserves data)
    - Confirmation required
    - Cannot delete if teacher has active schedules
    
    Requirements: FR-029, FR-031
    """
    try:
        teacher = Teacher.objects.get(id=pk)
        
        # Check if teacher has active schedules
        active_schedules = TeacherSchedule.objects.filter(
            teacher=teacher,
            is_active=True
        ).count()
        
        if active_schedules > 0:
            messages.error(
                request,
                f'Tidak dapat menghapus ustadz "{teacher.full_name}" karena masih memiliki {active_schedules} jadwal aktif. '
                'Nonaktifkan jadwal terlebih dahulu.'
            )
            return redirect('teacher_detail', pk=pk)
        
        # Soft delete
        name = teacher.full_name
        teacher.is_active = False
        teacher.save()
        
        messages.success(request, f'Ustadz "{name}" berhasil dinonaktifkan')
        
    except Teacher.DoesNotExist:
        messages.error(request, "Ustadz tidak ditemukan")
    except Exception as e:
        logger.error(f"Error deleting teacher: {str(e)}")
        messages.error(request, f"Gagal menghapus ustadz: {str(e)}")
    
    return redirect('teacher_list')


@login_required
def teacher_schedule(request, pk):
    """
    View and manage teacher's weekly schedule.
    
    Accessible by: All authenticated users
    Admin can edit, teachers can only view
    
    Features:
    - Display weekly schedule grid
    - Show subject and classroom for each slot
    - Highlight scheduling conflicts
    - Add/Edit/Delete schedule (admin only)
    - Calculate total JP per week
    
    Requirements: FR-006, FR-007, FR-008, FR-009
    """
    try:
        teacher = Teacher.objects.get(id=pk)
        
        # Check if current user is viewing their own schedule
        is_own_schedule = (
            request.user.is_authenticated and 
            hasattr(request.user, 'teacher_profile') and 
            request.user.teacher_profile.id == teacher.id
        )
        
        # Get weekly schedule using service
        try:
            weekly_schedule = TeacherScheduleService.get_weekly_schedule(teacher.id)
        except Exception as e:
            logger.error(f"Error getting weekly schedule: {str(e)}")
            weekly_schedule = {}
            messages.error(request, "Terjadi kesalahan saat memuat jadwal")
        
        # Calculate total JP per week
        total_jp = 0
        for day_schedules in weekly_schedule.values():
            for schedule in day_schedules:
                total_jp += schedule.jp_count
        
        # Get subjects and classrooms for schedule creation (admin only)
        subjects = Subject.objects.filter(is_active=True).order_by('name')
        classrooms = Classroom.objects.filter(is_active=True).select_related('academic_level').order_by('name')
        
        context = {
            'teacher': teacher,
            'weekly_schedule': weekly_schedule,
            'total_jp': total_jp,
            'subjects': subjects,
            'classrooms': classrooms,
            'is_own_schedule': is_own_schedule,
            'days': [
                {'value': 0, 'name': 'Senin'},
                {'value': 1, 'name': 'Selasa'},
                {'value': 2, 'name': 'Rabu'},
                {'value': 3, 'name': 'Kamis'},
                {'value': 4, 'name': 'Jumat'},
                {'value': 5, 'name': 'Sabtu'},
                {'value': 6, 'name': 'Minggu'},
            ],
        }
        
    except Teacher.DoesNotExist:
        messages.error(request, "Ustadz tidak ditemukan")
        return redirect('teacher_list')
    except Exception as e:
        logger.error(f"Error loading teacher schedule: {str(e)}")
        messages.error(request, "Terjadi kesalahan saat memuat jadwal ustadz")
        return redirect('teacher_list')
    
    return render(request, 'teacher/teacher_schedule.html', context)


# ============================================
# AJAX API Endpoints
# ============================================

@login_required
@admin_required
@require_http_methods(["POST"])
def api_teacher_inline_edit(request):
    """
    AJAX endpoint for inline editing teacher fields.
    
    Accessible by: Admin only
    
    Accepts JSON payload:
    {
        "id": "<teacher_id>",
        "field": "<field_name>",
        "value": "<new_value>"
    }
    
    Returns JSON:
    {
        "success": true|false,
        "value": "<updated_value>",
        "message": "<success_message>",
        "error": "<error_message>"
    }
    
    Requirements: FR-029, FR-031
    """
    import json
    
    try:
        data = json.loads(request.body)
        teacher_id = data.get('id')
        field = data.get('field')
        value = data.get('value')
        
        if not all([teacher_id, field]):
            return JsonResponse({
                'success': False,
                'error': 'Parameter tidak lengkap'
            }, status=400)
        
        # Allowed fields for inline edit
        allowed_fields = ['full_name', 'email', 'phone', 'employment_status', 'is_active']
        if field not in allowed_fields:
            return JsonResponse({
                'success': False,
                'error': 'Field tidak diizinkan untuk inline edit'
            }, status=400)
        
        teacher = Teacher.objects.get(id=teacher_id)
        
        # Handle boolean fields
        if field == 'is_active':
            value = value in ['true', 'True', True, 1, '1']
        
        # Update using service
        update_data = {field: value}
        teacher = TeacherService.update_teacher(teacher_id, update_data)
        
        # Format display value
        display_value = getattr(teacher, field)
        if field == 'is_active':
            display_value = 'Aktif' if display_value else 'Nonaktif'
        elif field == 'employment_status':
            display_value = teacher.get_employment_status_display()
        
        return JsonResponse({
            'success': True,
            'value': getattr(teacher, field),
            'display_value': display_value,
            'message': 'Data berhasil diperbarui'
        })
        
    except Teacher.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Ustadz tidak ditemukan'
        }, status=404)
    except TeacherServiceError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Format JSON tidak valid'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in inline edit: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Terjadi kesalahan: {str(e)}'
        }, status=500)
