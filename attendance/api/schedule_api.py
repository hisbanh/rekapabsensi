"""
Schedule API Endpoints
Provides RESTful API for teacher schedule management operations
"""
import json
from datetime import datetime, date
from uuid import UUID
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import transaction

from ..models import TeacherSchedule, Teacher, Subject, Classroom
from ..services.schedule_service import TeacherScheduleService


# Helper functions for serialization
def serialize_schedule(schedule, include_details=False):
    """
    Serialize a TeacherSchedule instance to a dictionary.
    
    Args:
        schedule: TeacherSchedule instance
        include_details: Whether to include detailed information
        
    Returns:
        Dictionary representation of the schedule
    """
    data = {
        'id': str(schedule.id),
        'day_of_week': schedule.day_of_week,
        'day_name': schedule.day_name,
        'jp_start': schedule.jp_start,
        'jp_end': schedule.jp_end,
        'jp_count': schedule.jp_count,
        'room_number': schedule.room_number,
        'notes': schedule.notes,
        'effective_date': schedule.effective_date.isoformat() if schedule.effective_date else None,
        'end_date': schedule.end_date.isoformat() if schedule.end_date else None,
        'is_active': schedule.is_active,
    }
    
    if include_details:
        # Add teacher details
        data['teacher'] = {
            'id': str(schedule.teacher.id),
            'nip': schedule.teacher.nip,
            'full_name': schedule.teacher.full_name,
            'photo_url': schedule.teacher.photo.url if schedule.teacher.photo else None,
        }
        
        # Add subject details
        data['subject'] = {
            'id': str(schedule.subject.id),
            'code': schedule.subject.code,
            'name': schedule.subject.name,
            'category': schedule.subject.category,
        }
        
        # Add classroom details
        data['classroom'] = {
            'id': str(schedule.classroom.id),
            'name': schedule.classroom.name,
            'grade': schedule.classroom.grade,
        }
        
        # Add timestamps
        data['created_at'] = schedule.created_at.isoformat() if schedule.created_at else None
        data['updated_at'] = schedule.updated_at.isoformat() if schedule.updated_at else None
    else:
        # Add minimal references
        data['teacher_id'] = str(schedule.teacher.id)
        data['teacher_name'] = schedule.teacher.full_name
        data['subject_id'] = str(schedule.subject.id)
        data['subject_name'] = schedule.subject.name
        data['classroom_id'] = str(schedule.classroom.id)
        data['classroom_name'] = schedule.classroom.name
    
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
def schedule_list_create(request):
    """
    GET /api/schedules/ - List all schedules with optional filters
    POST /api/schedules/ - Create a new schedule (admin only)
    
    Query Parameters (GET):
        - teacher_id: Filter by teacher UUID
        - subject_id: Filter by subject UUID
        - classroom_id: Filter by classroom UUID
        - day_of_week: Filter by day (0-6)
        - is_active: Filter by active status (true/false)
        - effective_date: Filter by effective date (YYYY-MM-DD)
        - page: Page number for pagination (default: 1)
        - page_size: Number of items per page (default: 20)
    
    Request Body (POST):
        {
            "teacher_id": "uuid",
            "subject_id": "uuid",
            "classroom_id": "uuid",
            "day_of_week": 0,
            "jp_start": 1,
            "jp_end": 2,
            "room_number": "A101",
            "notes": "Optional notes",
            "effective_date": "2024-01-01",
            "end_date": "2024-12-31",
            "is_active": true
        }
    
    Response (GET):
        {
            "success": true,
            "data": {
                "schedules": [...],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total": 50,
                    "total_pages": 3
                }
            }
        }
    
    Response (POST):
        {
            "success": true,
            "message": "Schedule created successfully",
            "data": {...}
        }
    """
    if request.method == 'GET':
        # Build query filters
        query = TeacherSchedule.objects.select_related('teacher', 'subject', 'classroom')
        
        if request.GET.get('teacher_id'):
            try:
                query = query.filter(teacher_id=UUID(request.GET.get('teacher_id')))
            except ValueError:
                return error_response("Invalid teacher_id format")
        
        if request.GET.get('subject_id'):
            try:
                query = query.filter(subject_id=UUID(request.GET.get('subject_id')))
            except ValueError:
                return error_response("Invalid subject_id format")
        
        if request.GET.get('classroom_id'):
            try:
                query = query.filter(classroom_id=UUID(request.GET.get('classroom_id')))
            except ValueError:
                return error_response("Invalid classroom_id format")
        
        if request.GET.get('day_of_week'):
            try:
                day = int(request.GET.get('day_of_week'))
                if 0 <= day <= 6:
                    query = query.filter(day_of_week=day)
                else:
                    return error_response("day_of_week must be between 0 and 6")
            except ValueError:
                return error_response("Invalid day_of_week format")
        
        if request.GET.get('is_active'):
            query = query.filter(is_active=request.GET.get('is_active').lower() == 'true')
        
        if request.GET.get('effective_date'):
            try:
                eff_date = datetime.strptime(request.GET.get('effective_date'), '%Y-%m-%d').date()
                query = query.filter(effective_date__lte=eff_date)
            except ValueError:
                return error_response("Invalid effective_date format. Use YYYY-MM-DD")
        
        # Order by day and JP
        query = query.order_by('day_of_week', 'jp_start')
        
        try:
            # Pagination
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            
            # Validate pagination parameters
            if page < 1:
                page = 1
            if page_size < 1 or page_size > 100:
                page_size = 20
            
            # Get total count
            total = query.count()
            total_pages = (total + page_size - 1) // page_size
            
            # Get page of schedules
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            schedules = list(query[start_idx:end_idx])
            
            # Serialize schedules
            serialized_schedules = [serialize_schedule(schedule, include_details=True) for schedule in schedules]
            
            return success_response({
                'schedules': serialized_schedules,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': total_pages,
                }
            })
            
        except Exception as e:
            return error_response(f"Error retrieving schedules: {str(e)}", status=500)
    
    elif request.method == 'POST':
        # Check admin permission
        if not request.user.is_staff:
            return error_response("Permission denied. Admin access required.", status=403)
        
        try:
            # Parse request body
            data = parse_request_body(request)
            
            # Convert date strings to date objects
            if 'effective_date' in data and isinstance(data['effective_date'], str):
                data['effective_date'] = datetime.strptime(data['effective_date'], '%Y-%m-%d').date()
            
            if 'end_date' in data and data['end_date'] and isinstance(data['end_date'], str):
                data['end_date'] = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            
            # Convert UUID strings to UUID objects
            if 'teacher_id' in data and isinstance(data['teacher_id'], str):
                data['teacher_id'] = UUID(data['teacher_id'])
            
            if 'subject_id' in data and isinstance(data['subject_id'], str):
                data['subject_id'] = UUID(data['subject_id'])
            
            if 'classroom_id' in data and isinstance(data['classroom_id'], str):
                data['classroom_id'] = UUID(data['classroom_id'])
            
            # Create schedule using service
            schedule = TeacherScheduleService.create_schedule(data)
            
            # Serialize and return
            return success_response(
                data=serialize_schedule(schedule, include_details=True),
                message="Schedule created successfully",
                status=201
            )
            
        except ValueError as e:
            return error_response(str(e), status=400)
        except ValidationError as e:
            return error_response(str(e), status=400)
        except ObjectDoesNotExist as e:
            return error_response(str(e), status=404)
        except Exception as e:
            return error_response(f"Error creating schedule: {str(e)}", status=500)


@require_http_methods(["GET", "PUT", "DELETE"])
@login_required
def schedule_detail_update_delete(request, schedule_id):
    """
    GET /api/schedules/{id}/ - Get schedule detail
    PUT /api/schedules/{id}/ - Update schedule (admin only)
    DELETE /api/schedules/{id}/ - Delete schedule (admin only)
    
    Path Parameters:
        - schedule_id: UUID of the schedule
    
    Request Body (PUT):
        {
            "day_of_week": 1,
            "jp_start": 3,
            "jp_end": 4,
            "room_number": "B202",
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
            "message": "Schedule updated successfully",
            "data": {...}
        }
    
    Response (DELETE):
        {
            "success": true,
            "message": "Schedule deleted successfully"
        }
    """
    try:
        schedule_uuid = UUID(schedule_id)
    except ValueError:
        return error_response("Invalid schedule ID format", status=400)
    
    if request.method == 'GET':
        try:
            # Get schedule
            schedule = TeacherSchedule.objects.select_related(
                'teacher', 'subject', 'classroom'
            ).get(id=schedule_uuid)
            
            # Serialize with full details
            data = serialize_schedule(schedule, include_details=True)
            
            return success_response(data)
            
        except TeacherSchedule.DoesNotExist:
            return error_response("Schedule not found", status=404)
        except Exception as e:
            return error_response(f"Error retrieving schedule: {str(e)}", status=500)
    
    elif request.method == 'PUT':
        # Check admin permission
        if not request.user.is_staff:
            return error_response("Permission denied. Admin access required.", status=403)
        
        try:
            # Parse request body
            data = parse_request_body(request)
            
            # Convert date strings to date objects if provided
            if 'effective_date' in data and isinstance(data['effective_date'], str):
                data['effective_date'] = datetime.strptime(data['effective_date'], '%Y-%m-%d').date()
            
            if 'end_date' in data and data['end_date'] and isinstance(data['end_date'], str):
                data['end_date'] = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            
            # Convert UUID strings to UUID objects if provided
            if 'teacher_id' in data and isinstance(data['teacher_id'], str):
                data['teacher_id'] = UUID(data['teacher_id'])
            
            if 'subject_id' in data and isinstance(data['subject_id'], str):
                data['subject_id'] = UUID(data['subject_id'])
            
            if 'classroom_id' in data and isinstance(data['classroom_id'], str):
                data['classroom_id'] = UUID(data['classroom_id'])
            
            # Update schedule using service
            schedule = TeacherScheduleService.update_schedule(schedule_uuid, data)
            
            # Serialize and return
            return success_response(
                data=serialize_schedule(schedule, include_details=True),
                message="Schedule updated successfully"
            )
            
        except ValueError as e:
            return error_response(str(e), status=400)
        except ValidationError as e:
            return error_response(str(e), status=400)
        except ObjectDoesNotExist as e:
            return error_response(str(e), status=404)
        except Exception as e:
            return error_response(f"Error updating schedule: {str(e)}", status=500)
    
    elif request.method == 'DELETE':
        # Check admin permission
        if not request.user.is_staff:
            return error_response("Permission denied. Admin access required.", status=403)
        
        try:
            # Delete schedule using service (soft delete)
            TeacherScheduleService.delete_schedule(schedule_uuid)
            
            return success_response(message="Schedule deleted successfully")
            
        except ObjectDoesNotExist as e:
            return error_response(str(e), status=404)
        except Exception as e:
            return error_response(f"Error deleting schedule: {str(e)}", status=500)


@require_http_methods(["POST"])
@login_required
def detect_conflicts(request):
    """
    POST /api/schedules/detect-conflicts/ - Check for scheduling conflicts
    
    Request Body:
        {
            "teacher_id": "uuid",
            "day_of_week": 0,
            "jp_start": 1,
            "jp_end": 2,
            "effective_date": "2024-01-01",
            "end_date": "2024-12-31",
            "exclude_schedule_id": "uuid",  // optional, for updates
            "classroom_id": "uuid"  // optional, to check classroom conflicts
        }
    
    Response:
        {
            "success": true,
            "data": {
                "has_conflicts": true,
                "conflicts": [
                    {
                        "type": "teacher",
                        "message": "Teacher already has a schedule...",
                        "schedule": {...}
                    }
                ]
            }
        }
    """
    # Check admin permission
    if not request.user.is_staff:
        return error_response("Permission denied. Admin access required.", status=403)
    
    try:
        # Parse request body
        data = parse_request_body(request)
        
        # Validate required fields
        required_fields = ['teacher_id', 'day_of_week', 'jp_start', 'jp_end']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return error_response(f"Missing required fields: {', '.join(missing_fields)}", status=400)
        
        # Convert UUID strings to UUID objects
        teacher_id = UUID(data['teacher_id'])
        
        # Convert date strings to date objects if provided
        effective_date = None
        if 'effective_date' in data and data['effective_date']:
            effective_date = datetime.strptime(data['effective_date'], '%Y-%m-%d').date()
        
        end_date = None
        if 'end_date' in data and data['end_date']:
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        # Get optional parameters
        exclude_schedule_id = None
        if 'exclude_schedule_id' in data and data['exclude_schedule_id']:
            exclude_schedule_id = UUID(data['exclude_schedule_id'])
        
        classroom_id = None
        if 'classroom_id' in data and data['classroom_id']:
            classroom_id = UUID(data['classroom_id'])
        
        # Detect conflicts using service
        conflicts = TeacherScheduleService.detect_conflicts(
            teacher_id=teacher_id,
            day=int(data['day_of_week']),
            jp_start=int(data['jp_start']),
            jp_end=int(data['jp_end']),
            effective_date=effective_date,
            end_date=end_date,
            exclude_schedule_id=exclude_schedule_id,
            classroom_id=classroom_id
        )
        
        # Serialize conflicts
        serialized_conflicts = []
        for conflict in conflicts:
            serialized_conflicts.append({
                'type': conflict['type'],
                'message': conflict['message'],
                'schedule': serialize_schedule(conflict['schedule'], include_details=True)
            })
        
        return success_response({
            'has_conflicts': len(conflicts) > 0,
            'conflicts': serialized_conflicts
        })
        
    except ValueError as e:
        return error_response(str(e), status=400)
    except Exception as e:
        return error_response(f"Error detecting conflicts: {str(e)}", status=500)


@require_http_methods(["GET"])
@login_required
def weekly_schedule(request, teacher_id):
    """
    GET /api/schedules/weekly/{teacher}/ - Get teacher's weekly schedule
    
    Path Parameters:
        - teacher_id: UUID of the teacher
    
    Response:
        {
            "success": true,
            "data": {
                "teacher_id": "uuid",
                "teacher_name": "Ahmad Yusuf",
                "total_jp_per_week": 18,
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
        
        # Calculate total JP per week
        total_jp = 0
        
        # Serialize schedule
        serialized_schedule = {}
        for day, schedules in weekly_schedule.items():
            serialized_schedule[str(day)] = []
            for schedule in schedules:
                serialized_schedule[str(day)].append(serialize_schedule(schedule, include_details=True))
                total_jp += (schedule.jp_end - schedule.jp_start + 1)
        
        return success_response({
            'teacher_id': str(teacher.id),
            'teacher_name': teacher.full_name,
            'total_jp_per_week': total_jp,
            'weekly_schedule': serialized_schedule,
        })
        
    except ObjectDoesNotExist as e:
        return error_response(str(e), status=404)
    except Exception as e:
        return error_response(f"Error retrieving weekly schedule: {str(e)}", status=500)
