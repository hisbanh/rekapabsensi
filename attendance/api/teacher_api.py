"""
Teacher API Endpoints
Provides RESTful API for teacher management operations
"""
import json
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction

from ..models import Teacher, Subject, Classroom
from ..services.teacher_service import TeacherService, TeacherServiceError
from ..services.schedule_service import TeacherScheduleService
from ..decorators import admin_required


# Helper functions for serialization
def serialize_teacher(teacher, include_details=False):
    """
    Serialize a Teacher instance to a dictionary.
    
    Args:
        teacher: Teacher instance
        include_details: Whether to include detailed information
        
    Returns:
        Dictionary representation of the teacher
    """
    data = {
        'id': str(teacher.id),
        'nip': teacher.nip,
        'full_name': teacher.full_name,
        'email': teacher.email,
        'phone': teacher.phone,
        'employment_status': teacher.employment_status,
        'employment_date': teacher.employment_date.isoformat() if teacher.employment_date else None,
        'is_homeroom_teacher': teacher.is_homeroom_teacher,
        'is_active': teacher.is_active,
        'photo_url': teacher.photo.url if teacher.photo else None,
    }
    
    if include_details:
        # Add subjects
        data['subjects'] = [
            {
                'id': str(subject.id),
                'code': subject.code,
                'name': subject.name,
                'category': subject.category,
            }
            for subject in teacher.subjects.filter(is_active=True)
        ]
        
        # Add homeroom class
        if teacher.is_homeroom_teacher and teacher.homeroom_class:
            data['homeroom_class'] = {
                'id': str(teacher.homeroom_class.id),
                'name': teacher.homeroom_class.name,
                'grade': teacher.homeroom_class.grade,
            }
        else:
            data['homeroom_class'] = None
        
        # Add teaching load
        data['teaching_load'] = teacher.teaching_load
        
        # Add timestamps
        data['created_at'] = teacher.created_at.isoformat() if teacher.created_at else None
        data['updated_at'] = teacher.updated_at.isoformat() if teacher.updated_at else None
    
    return data


def parse_request_body(request):
    """
    Parse JSON request body.
    
    Args:
        request: Django request object
        
    Returns:
        Parsed JSON data as dictionary
        
    Raises:
        ValueError: If JSON is invalid
    """
    try:
        return json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {str(e)}")


def error_response(message, status=400, errors=None):
    """
    Create an error response.
    
    Args:
        message: Error message
        status: HTTP status code
        errors: Additional error details (optional)
        
    Returns:
        JsonResponse with error information
    """
    response_data = {
        'success': False,
        'error': message,
    }
    
    if errors:
        response_data['errors'] = errors
    
    return JsonResponse(response_data, status=status)


def success_response(data=None, message=None, status=200):
    """
    Create a success response.
    
    Args:
        data: Response data
        message: Success message (optional)
        status: HTTP status code
        
    Returns:
        JsonResponse with success information
    """
    response_data = {
        'success': True,
    }
    
    if message:
        response_data['message'] = message
    
    if data is not None:
        response_data['data'] = data
    
    return JsonResponse(response_data, status=status)


# API Endpoints

@require_http_methods(["GET", "POST"])
@login_required
def teacher_list_create(request):
    """
    GET /api/teachers/ - List all teachers with optional filters
    POST /api/teachers/ - Create a new teacher (admin only)
    
    Query Parameters (GET):
        - employment_status: Filter by employment status (ACTIVE, LEAVE, INACTIVE)
        - is_active: Filter by active status (true/false)
        - subject_id: Filter by subject UUID
        - is_homeroom_teacher: Filter homeroom teachers (true/false)
        - search: Search by name, NIP, or email
        - order_by: Field to order by (default: full_name)
        - page: Page number for pagination (default: 1)
        - page_size: Number of items per page (default: 20)
    
    Request Body (POST):
        {
            "nip": "12345",
            "full_name": "Ahmad Yusuf",
            "employment_date": "2024-01-01",
            "employment_status": "ACTIVE",
            "email": "ahmad@example.com",
            "phone": "081234567890",
            "address": "Yogyakarta",
            "is_homeroom_teacher": false,
            "homeroom_class": null,
            "is_active": true
        }
    
    Response (GET):
        {
            "success": true,
            "data": {
                "teachers": [...],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total": 25,
                    "total_pages": 2
                }
            }
        }
    
    Response (POST):
        {
            "success": true,
            "message": "Teacher created successfully",
            "data": {...}
        }
    """
    if request.method == 'GET':
        # Build filters from query parameters
        filters = {}
        
        if request.GET.get('employment_status'):
            filters['employment_status'] = request.GET.get('employment_status')
        
        if request.GET.get('is_active'):
            filters['is_active'] = request.GET.get('is_active').lower() == 'true'
        
        if request.GET.get('subject_id'):
            try:
                filters['subject_id'] = UUID(request.GET.get('subject_id'))
            except ValueError:
                return error_response("Invalid subject_id format")
        
        if request.GET.get('is_homeroom_teacher'):
            filters['is_homeroom_teacher'] = request.GET.get('is_homeroom_teacher').lower() == 'true'
        
        if request.GET.get('search'):
            filters['search_query'] = request.GET.get('search')
        
        if request.GET.get('order_by'):
            filters['order_by'] = request.GET.get('order_by')
        
        try:
            # Get teachers from service
            teachers = TeacherService.get_teachers_with_filters(filters)
            
            # Pagination
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            
            # Validate pagination parameters
            if page < 1:
                page = 1
            if page_size < 1 or page_size > 100:
                page_size = 20
            
            # Calculate pagination
            total = len(teachers)
            total_pages = (total + page_size - 1) // page_size
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            
            # Get page of teachers
            page_teachers = teachers[start_idx:end_idx]
            
            # Serialize teachers
            serialized_teachers = [serialize_teacher(teacher) for teacher in page_teachers]
            
            return success_response({
                'teachers': serialized_teachers,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': total_pages,
                }
            })
            
        except Exception as e:
            return error_response(f"Error retrieving teachers: {str(e)}", status=500)
    
    elif request.method == 'POST':
        # Check admin permission
        if not request.user.is_staff:
            return error_response("Permission denied. Admin access required.", status=403)
        
        try:
            # Parse request body
            data = parse_request_body(request)
            
            # Convert date string to date object
            if 'employment_date' in data and isinstance(data['employment_date'], str):
                data['employment_date'] = datetime.strptime(data['employment_date'], '%Y-%m-%d').date()
            
            # Convert homeroom_class UUID string to UUID object
            if 'homeroom_class' in data and data['homeroom_class']:
                try:
                    classroom = Classroom.objects.get(id=UUID(data['homeroom_class']))
                    data['homeroom_class'] = classroom
                except (ValueError, Classroom.DoesNotExist):
                    return error_response("Invalid homeroom_class ID")
            
            # Create teacher using service
            teacher = TeacherService.create_teacher(data)
            
            # Serialize and return
            return success_response(
                data=serialize_teacher(teacher, include_details=True),
                message="Teacher created successfully",
                status=201
            )
            
        except ValueError as e:
            return error_response(str(e), status=400)
        except TeacherServiceError as e:
            return error_response(str(e), status=400)
        except Exception as e:
            return error_response(f"Error creating teacher: {str(e)}", status=500)


@require_http_methods(["GET", "PUT", "DELETE"])
@login_required
def teacher_detail_update_delete(request, teacher_id):
    """
    GET /api/teachers/{id}/ - Get teacher detail
    PUT /api/teachers/{id}/ - Update teacher (admin only)
    DELETE /api/teachers/{id}/ - Delete teacher (admin only)
    
    Path Parameters:
        - teacher_id: UUID of the teacher
    
    Request Body (PUT):
        {
            "full_name": "Ahmad Yusuf Updated",
            "email": "newemail@example.com",
            "phone": "081234567890",
            ...
        }
    
    Response (GET):
        {
            "success": true,
            "data": {...}
        }
    
    Response (PUT):
        {
            "success": true,
            "message": "Teacher updated successfully",
            "data": {...}
        }
    
    Response (DELETE):
        {
            "success": true,
            "message": "Teacher deleted successfully"
        }
    """
    try:
        teacher_uuid = UUID(teacher_id)
    except ValueError:
        return error_response("Invalid teacher ID format", status=400)
    
    if request.method == 'GET':
        try:
            # Get teacher profile from service
            profile = TeacherService.get_teacher_profile(teacher_uuid)
            teacher = profile['teacher']
            
            # Serialize with full details
            data = serialize_teacher(teacher, include_details=True)
            
            # Add additional profile information
            data['total_schedules'] = profile['total_schedules']
            data['teaching_load'] = profile['teaching_load']
            
            return success_response(data)
            
        except TeacherServiceError as e:
            return error_response(str(e), status=404)
        except Exception as e:
            return error_response(f"Error retrieving teacher: {str(e)}", status=500)
    
    elif request.method == 'PUT':
        # Check admin permission
        if not request.user.is_staff:
            return error_response("Permission denied. Admin access required.", status=403)
        
        try:
            # Parse request body
            data = parse_request_body(request)
            
            # Convert date string to date object if provided
            if 'employment_date' in data and isinstance(data['employment_date'], str):
                data['employment_date'] = datetime.strptime(data['employment_date'], '%Y-%m-%d').date()
            
            # Convert homeroom_class UUID string to UUID object if provided
            if 'homeroom_class' in data and data['homeroom_class']:
                try:
                    classroom = Classroom.objects.get(id=UUID(data['homeroom_class']))
                    data['homeroom_class'] = classroom
                except (ValueError, Classroom.DoesNotExist):
                    return error_response("Invalid homeroom_class ID")
            
            # Update teacher using service
            teacher = TeacherService.update_teacher(teacher_uuid, data)
            
            # Serialize and return
            return success_response(
                data=serialize_teacher(teacher, include_details=True),
                message="Teacher updated successfully"
            )
            
        except ValueError as e:
            return error_response(str(e), status=400)
        except TeacherServiceError as e:
            return error_response(str(e), status=400)
        except Exception as e:
            return error_response(f"Error updating teacher: {str(e)}", status=500)
    
    elif request.method == 'DELETE':
        # Check admin permission
        if not request.user.is_staff:
            return error_response("Permission denied. Admin access required.", status=403)
        
        try:
            # Get teacher
            teacher = Teacher.objects.get(id=teacher_uuid)
            
            # Soft delete by setting is_active to False
            teacher.is_active = False
            teacher.save()
            
            return success_response(message="Teacher deleted successfully")
            
        except Teacher.DoesNotExist:
            return error_response("Teacher not found", status=404)
        except Exception as e:
            return error_response(f"Error deleting teacher: {str(e)}", status=500)


@require_http_methods(["GET"])
@login_required
def teacher_schedule(request, teacher_id):
    """
    GET /api/teachers/{id}/schedule/ - Get teacher's weekly schedule
    
    Path Parameters:
        - teacher_id: UUID of the teacher
    
    Response:
        {
            "success": true,
            "data": {
                "teacher_id": "...",
                "teacher_name": "Ahmad Yusuf",
                "weekly_schedule": {
                    "0": [...],  // Monday
                    "1": [...],  // Tuesday
                    ...
                }
            }
        }
    """
    try:
        teacher_uuid = UUID(teacher_id)
    except ValueError:
        return error_response("Invalid teacher ID format", status=400)
    
    try:
        # Get weekly schedule from service
        weekly_schedule = TeacherScheduleService.get_weekly_schedule(teacher_uuid)
        
        # Get teacher
        teacher = Teacher.objects.get(id=teacher_uuid)
        
        # Serialize schedule
        serialized_schedule = {}
        for day, schedules in weekly_schedule.items():
            serialized_schedule[str(day)] = [
                {
                    'id': str(schedule.id),
                    'day_of_week': schedule.day_of_week,
                    'day_name': schedule.day_name,
                    'jp_start': schedule.jp_start,
                    'jp_end': schedule.jp_end,
                    'jp_count': schedule.jp_count,
                    'subject': {
                        'id': str(schedule.subject.id),
                        'code': schedule.subject.code,
                        'name': schedule.subject.name,
                    },
                    'classroom': {
                        'id': str(schedule.classroom.id),
                        'name': schedule.classroom.name,
                        'grade': schedule.classroom.grade,
                    },
                    'room_number': schedule.room_number,
                    'notes': schedule.notes,
                    'effective_date': schedule.effective_date.isoformat() if schedule.effective_date else None,
                    'end_date': schedule.end_date.isoformat() if schedule.end_date else None,
                }
                for schedule in schedules
            ]
        
        return success_response({
            'teacher_id': str(teacher.id),
            'teacher_name': teacher.full_name,
            'weekly_schedule': serialized_schedule,
        })
        
    except ObjectDoesNotExist:
        return error_response("Teacher not found", status=404)
    except Exception as e:
        return error_response(f"Error retrieving schedule: {str(e)}", status=500)


@require_http_methods(["GET"])
@login_required
def teacher_statistics(request, teacher_id):
    """
    GET /api/teachers/{id}/statistics/ - Get teacher attendance statistics
    
    Path Parameters:
        - teacher_id: UUID of the teacher
    
    Query Parameters:
        - year: Year (required)
        - month: Month 1-12 (required)
    
    Response:
        {
            "success": true,
            "data": {
                "teacher": {...},
                "year": 2024,
                "month": 1,
                "total_hadir": 68,
                "total_sakit": 4,
                "total_izin": 6,
                "total_cuti": 0,
                "total_dinas": 2,
                "total_alpa": 0,
                "total_jp_scheduled": 80,
                "attendance_percentage": 85.0,
                "summary_exists": true
            }
        }
    """
    try:
        teacher_uuid = UUID(teacher_id)
    except ValueError:
        return error_response("Invalid teacher ID format", status=400)
    
    # Get year and month from query parameters
    try:
        year = int(request.GET.get('year'))
        month = int(request.GET.get('month'))
    except (TypeError, ValueError):
        return error_response("Year and month parameters are required and must be integers", status=400)
    
    try:
        # Get statistics from service
        stats = TeacherService.get_teacher_statistics(teacher_uuid, year, month)
        
        # Serialize teacher info
        teacher_data = {
            'id': str(stats['teacher'].id),
            'nip': stats['teacher'].nip,
            'full_name': stats['teacher'].full_name,
        }
        
        # Build response
        response_data = {
            'teacher': teacher_data,
            'year': stats['year'],
            'month': stats['month'],
            'total_hadir': stats['total_hadir'],
            'total_sakit': stats['total_sakit'],
            'total_izin': stats['total_izin'],
            'total_cuti': stats['total_cuti'],
            'total_dinas': stats['total_dinas'],
            'total_alpa': stats['total_alpa'],
            'total_jp_scheduled': stats['total_jp_scheduled'],
            'attendance_percentage': stats['attendance_percentage'],
            'summary_exists': stats['summary_exists'],
        }
        
        return success_response(response_data)
        
    except TeacherServiceError as e:
        return error_response(str(e), status=400)
    except Exception as e:
        return error_response(f"Error retrieving statistics: {str(e)}", status=500)
