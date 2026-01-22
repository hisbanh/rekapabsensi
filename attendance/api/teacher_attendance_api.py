"""
Teacher Attendance API Endpoints
Provides RESTful API for teacher attendance recording and management operations
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

from ..models import TeacherAttendance, Teacher, TeacherSchedule
from ..services.teacher_attendance_service import TeacherAttendanceService, TeacherAttendanceServiceError


# Helper functions for serialization
def serialize_attendance(attendance, include_details=False):
    """
    Serialize a TeacherAttendance instance to a dictionary.
    
    Args:
        attendance: TeacherAttendance instance
        include_details: Whether to include detailed information
        
    Returns:
        Dictionary representation of the attendance
    """
    data = {
        'id': str(attendance.id),
        'date': attendance.date.isoformat(),
        'jp_number': attendance.jp_number,
        'status': attendance.status,
        'notes': attendance.notes,
        'is_substitute': attendance.is_substitute,
        'is_location_valid': attendance.is_location_valid,
        'recorded_at': attendance.recorded_at.isoformat() if attendance.recorded_at else None,
    }
    
    if include_details:
        # Add teacher details
        data['teacher'] = {
            'id': str(attendance.teacher.id),
            'nip': attendance.teacher.nip,
            'full_name': attendance.teacher.full_name,
            'photo_url': attendance.teacher.photo.url if attendance.teacher.photo else None,
        }
        
        # Add schedule details if exists
        if attendance.schedule:
            data['schedule'] = {
                'id': str(attendance.schedule.id),
                'subject': {
                    'id': str(attendance.schedule.subject.id),
                    'code': attendance.schedule.subject.code,
                    'name': attendance.schedule.subject.name,
                },
                'classroom': {
                    'id': str(attendance.schedule.classroom.id),
                    'name': attendance.schedule.classroom.name,
                    'grade': attendance.schedule.classroom.grade,
                },
                'room_number': attendance.schedule.room_number,
            }
        else:
            data['schedule'] = None
        
        # Add substitute_for details if exists
        if attendance.substitute_for:
            data['substitute_for'] = {
                'id': str(attendance.substitute_for.id),
                'nip': attendance.substitute_for.nip,
                'full_name': attendance.substitute_for.full_name,
            }
        else:
            data['substitute_for'] = None
        
        # Add recorded_by details if exists
        if attendance.recorded_by:
            data['recorded_by'] = {
                'id': attendance.recorded_by.id,
                'username': attendance.recorded_by.username,
                'full_name': attendance.recorded_by.get_full_name() or attendance.recorded_by.username,
            }
        else:
            data['recorded_by'] = None
        
        # Add location data
        data['latitude'] = float(attendance.latitude) if attendance.latitude else None
        data['longitude'] = float(attendance.longitude) if attendance.longitude else None
        
        # Add timestamps
        data['created_at'] = attendance.created_at.isoformat() if attendance.created_at else None
        data['updated_at'] = attendance.updated_at.isoformat() if attendance.updated_at else None
    else:
        # Add minimal references
        data['teacher_id'] = str(attendance.teacher.id)
        data['teacher_name'] = attendance.teacher.full_name
        
        if attendance.schedule:
            data['schedule_id'] = str(attendance.schedule.id)
            data['subject_name'] = attendance.schedule.subject.name
            data['classroom_name'] = attendance.schedule.classroom.name
        else:
            data['schedule_id'] = None
            data['subject_name'] = None
            data['classroom_name'] = None
    
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
def attendance_list_create(request):
    """
    GET /api/teacher-attendance/ - List all attendance records with optional filters
    POST /api/teacher-attendance/ - Record new attendance
    
    Query Parameters (GET):
        - teacher_id: Filter by teacher UUID
        - date: Filter by specific date (YYYY-MM-DD)
        - start_date: Filter by start date (YYYY-MM-DD)
        - end_date: Filter by end date (YYYY-MM-DD)
        - jp_number: Filter by JP number (1-10)
        - status: Filter by status (HADIR, SAKIT, IZIN, CUTI, DINAS, ALPA)
        - is_substitute: Filter substitute teaching (true/false)
        - page: Page number for pagination (default: 1)
        - page_size: Number of items per page (default: 20)
    
    Request Body (POST):
        {
            "teacher_id": "uuid",
            "date": "2024-01-20",
            "jp_number": 1,
            "status": "HADIR",
            "schedule_id": "uuid",  // optional
            "notes": "Optional notes",
            "is_substitute": false,
            "substitute_for": "uuid",  // optional, required if is_substitute=true
            "latitude": -7.7956,  // optional
            "longitude": 110.3695  // optional
        }
    
    Response (GET):
        {
            "success": true,
            "data": {
                "attendances": [...],
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
            "message": "Attendance recorded successfully",
            "data": {...}
        }
    """
    if request.method == 'GET':
        # Build query filters
        query = TeacherAttendance.objects.select_related(
            'teacher', 'schedule', 'schedule__subject', 'schedule__classroom', 
            'recorded_by', 'substitute_for'
        )
        
        # Apply filters
        if request.GET.get('teacher_id'):
            try:
                query = query.filter(teacher_id=UUID(request.GET.get('teacher_id')))
            except ValueError:
                return error_response("Invalid teacher_id format")
        
        if request.GET.get('date'):
            try:
                filter_date = datetime.strptime(request.GET.get('date'), '%Y-%m-%d').date()
                query = query.filter(date=filter_date)
            except ValueError:
                return error_response("Invalid date format. Use YYYY-MM-DD")
        
        if request.GET.get('start_date'):
            try:
                start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
                query = query.filter(date__gte=start_date)
            except ValueError:
                return error_response("Invalid start_date format. Use YYYY-MM-DD")
        
        if request.GET.get('end_date'):
            try:
                end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
                query = query.filter(date__lte=end_date)
            except ValueError:
                return error_response("Invalid end_date format. Use YYYY-MM-DD")
        
        if request.GET.get('jp_number'):
            try:
                jp_number = int(request.GET.get('jp_number'))
                if 1 <= jp_number <= 10:
                    query = query.filter(jp_number=jp_number)
                else:
                    return error_response("jp_number must be between 1 and 10")
            except ValueError:
                return error_response("Invalid jp_number format")
        
        if request.GET.get('status'):
            status = request.GET.get('status').upper()
            valid_statuses = ['HADIR', 'SAKIT', 'IZIN', 'CUTI', 'DINAS', 'ALPA']
            if status in valid_statuses:
                query = query.filter(status=status)
            else:
                return error_response(f"Invalid status. Valid values: {', '.join(valid_statuses)}")
        
        if request.GET.get('is_substitute'):
            query = query.filter(is_substitute=request.GET.get('is_substitute').lower() == 'true')
        
        # Permission check: teachers can only see their own attendance
        if not request.user.is_staff:
            # Get teacher associated with user
            try:
                teacher = Teacher.objects.get(user=request.user)
                query = query.filter(teacher=teacher)
            except Teacher.DoesNotExist:
                return error_response("No teacher profile associated with this user", status=403)
        
        # Order by date and JP
        query = query.order_by('-date', 'jp_number')
        
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
            
            # Get page of attendances
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            attendances = list(query[start_idx:end_idx])
            
            # Serialize attendances
            serialized_attendances = [serialize_attendance(att, include_details=True) for att in attendances]
            
            return success_response({
                'attendances': serialized_attendances,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': total_pages,
                }
            })
            
        except Exception as e:
            return error_response(f"Error retrieving attendance records: {str(e)}", status=500)
    
    elif request.method == 'POST':
        try:
            # Parse request body
            data = parse_request_body(request)
            
            # Convert date string to date object
            if 'date' in data and isinstance(data['date'], str):
                data['date'] = datetime.strptime(data['date'], '%Y-%m-%d').date()
            
            # Convert UUID strings to UUID objects
            if 'teacher_id' in data and isinstance(data['teacher_id'], str):
                data['teacher_id'] = UUID(data['teacher_id'])
            
            if 'schedule_id' in data and data['schedule_id'] and isinstance(data['schedule_id'], str):
                data['schedule_id'] = UUID(data['schedule_id'])
            
            if 'substitute_for' in data and data['substitute_for'] and isinstance(data['substitute_for'], str):
                data['substitute_for'] = UUID(data['substitute_for'])
            
            # Permission check: teachers can only record their own attendance
            if not request.user.is_staff:
                try:
                    teacher = Teacher.objects.get(user=request.user)
                    # Ensure teacher is recording their own attendance
                    if str(data.get('teacher_id')) != str(teacher.id):
                        return error_response("You can only record your own attendance", status=403)
                except Teacher.DoesNotExist:
                    return error_response("No teacher profile associated with this user", status=403)
            
            # Add recorded_by user
            data['recorded_by'] = request.user
            
            # Record attendance using service
            attendance = TeacherAttendanceService.record_attendance(data)
            
            # Serialize and return
            return success_response(
                data=serialize_attendance(attendance, include_details=True),
                message="Attendance recorded successfully",
                status=201
            )
            
        except ValueError as e:
            return error_response(str(e), status=400)
        except TeacherAttendanceServiceError as e:
            return error_response(str(e), status=400)
        except Exception as e:
            return error_response(f"Error recording attendance: {str(e)}", status=500)


@require_http_methods(["GET", "PUT", "DELETE"])
@login_required
def attendance_detail_update_delete(request, attendance_id):
    """
    GET /api/teacher-attendance/{id}/ - Get attendance detail
    PUT /api/teacher-attendance/{id}/ - Update attendance
    DELETE /api/teacher-attendance/{id}/ - Delete attendance
    
    Path Parameters:
        - attendance_id: UUID of the attendance record
    
    Request Body (PUT):
        {
            "status": "SAKIT",
            "notes": "Demam tinggi",
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
            "message": "Attendance updated successfully",
            "data": {...}
        }
    
    Response (DELETE):
        {
            "success": true,
            "message": "Attendance deleted successfully"
        }
    """
    try:
        attendance_uuid = UUID(attendance_id)
    except ValueError:
        return error_response("Invalid attendance ID format", status=400)
    
    if request.method == 'GET':
        try:
            # Get attendance
            attendance = TeacherAttendance.objects.select_related(
                'teacher', 'schedule', 'schedule__subject', 'schedule__classroom',
                'recorded_by', 'substitute_for'
            ).get(id=attendance_uuid)
            
            # Permission check: teachers can only view their own attendance
            if not request.user.is_staff:
                try:
                    teacher = Teacher.objects.get(user=request.user)
                    if attendance.teacher != teacher:
                        return error_response("You can only view your own attendance", status=403)
                except Teacher.DoesNotExist:
                    return error_response("No teacher profile associated with this user", status=403)
            
            # Serialize with full details
            data = serialize_attendance(attendance, include_details=True)
            
            return success_response(data)
            
        except TeacherAttendance.DoesNotExist:
            return error_response("Attendance record not found", status=404)
        except Exception as e:
            return error_response(f"Error retrieving attendance: {str(e)}", status=500)
    
    elif request.method == 'PUT':
        try:
            # Get attendance
            attendance = TeacherAttendance.objects.get(id=attendance_uuid)
            
            # Permission check: teachers can only update their own attendance, admin can update any
            if not request.user.is_staff:
                try:
                    teacher = Teacher.objects.get(user=request.user)
                    if attendance.teacher != teacher:
                        return error_response("You can only update your own attendance", status=403)
                except Teacher.DoesNotExist:
                    return error_response("No teacher profile associated with this user", status=403)
            
            # Parse request body
            data = parse_request_body(request)
            
            # Convert date string to date object if provided
            if 'date' in data and isinstance(data['date'], str):
                data['date'] = datetime.strptime(data['date'], '%Y-%m-%d').date()
            
            # Convert UUID strings to UUID objects if provided
            if 'schedule_id' in data and data['schedule_id'] and isinstance(data['schedule_id'], str):
                data['schedule_id'] = UUID(data['schedule_id'])
            
            if 'substitute_for' in data and data['substitute_for'] and isinstance(data['substitute_for'], str):
                data['substitute_for'] = UUID(data['substitute_for'])
            
            # Add recorded_by user
            data['recorded_by'] = request.user
            
            # Update attendance using service
            attendance = TeacherAttendanceService.update_attendance(attendance_uuid, data)
            
            # Serialize and return
            return success_response(
                data=serialize_attendance(attendance, include_details=True),
                message="Attendance updated successfully"
            )
            
        except TeacherAttendance.DoesNotExist:
            return error_response("Attendance record not found", status=404)
        except ValueError as e:
            return error_response(str(e), status=400)
        except TeacherAttendanceServiceError as e:
            return error_response(str(e), status=400)
        except Exception as e:
            return error_response(f"Error updating attendance: {str(e)}", status=500)
    
    elif request.method == 'DELETE':
        # Only admin can delete attendance
        if not request.user.is_staff:
            return error_response("Permission denied. Admin access required.", status=403)
        
        try:
            # Get and delete attendance
            attendance = TeacherAttendance.objects.get(id=attendance_uuid)
            attendance.delete()
            
            return success_response(message="Attendance deleted successfully")
            
        except TeacherAttendance.DoesNotExist:
            return error_response("Attendance record not found", status=404)
        except Exception as e:
            return error_response(f"Error deleting attendance: {str(e)}", status=500)


@require_http_methods(["POST"])
@login_required
def validate_location(request):
    """
    POST /api/teacher-attendance/validate-location/ - Validate if location is within school premises
    
    Request Body:
        {
            "latitude": -7.7956,
            "longitude": 110.3695
        }
    
    Response:
        {
            "success": true,
            "data": {
                "is_valid": true,
                "latitude": -7.7956,
                "longitude": 110.3695,
                "school_latitude": -7.7956,
                "school_longitude": 110.3695,
                "radius_meters": 150,
                "message": "Location is within school premises"
            }
        }
    """
    try:
        # Parse request body
        data = parse_request_body(request)
        
        # Validate required fields
        if 'latitude' not in data or 'longitude' not in data:
            return error_response("Both latitude and longitude are required", status=400)
        
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        except (ValueError, TypeError):
            return error_response("Invalid latitude or longitude value", status=400)
        
        # Validate location using service
        is_valid = TeacherAttendanceService.validate_location(latitude, longitude)
        
        # Build response
        response_data = {
            'is_valid': is_valid,
            'latitude': latitude,
            'longitude': longitude,
            'school_latitude': TeacherAttendanceService.SCHOOL_LATITUDE,
            'school_longitude': TeacherAttendanceService.SCHOOL_LONGITUDE,
            'radius_meters': TeacherAttendanceService.SCHOOL_RADIUS_METERS,
            'message': 'Location is within school premises' if is_valid else 'Location is outside school premises'
        }
        
        return success_response(response_data)
        
    except ValueError as e:
        return error_response(str(e), status=400)
    except TeacherAttendanceServiceError as e:
        return error_response(str(e), status=400)
    except Exception as e:
        return error_response(f"Error validating location: {str(e)}", status=500)


@require_http_methods(["GET"])
@login_required
def daily_attendance(request):
    """
    GET /api/teacher-attendance/daily/ - Get all attendance records for a specific date
    
    Query Parameters:
        - date: Date to get attendance for (YYYY-MM-DD, required)
    
    Response:
        {
            "success": true,
            "data": {
                "date": "2024-01-20",
                "attendances": [...],
                "summary": {
                    "total_teachers": 25,
                    "total_recorded": 20,
                    "total_hadir": 18,
                    "total_sakit": 1,
                    "total_izin": 1,
                    "total_cuti": 0,
                    "total_dinas": 0,
                    "total_alpa": 0,
                    "total_not_recorded": 5
                }
            }
        }
    """
    # Get date from query parameters
    if not request.GET.get('date'):
        return error_response("Date parameter is required", status=400)
    
    try:
        target_date = datetime.strptime(request.GET.get('date'), '%Y-%m-%d').date()
    except ValueError:
        return error_response("Invalid date format. Use YYYY-MM-DD", status=400)
    
    try:
        # Get daily attendance from service
        attendances = TeacherAttendanceService.get_daily_attendance(target_date)
        
        # Calculate summary
        total_recorded = len(attendances)
        total_hadir = sum(1 for att in attendances if att.status == 'HADIR')
        total_sakit = sum(1 for att in attendances if att.status == 'SAKIT')
        total_izin = sum(1 for att in attendances if att.status == 'IZIN')
        total_cuti = sum(1 for att in attendances if att.status == 'CUTI')
        total_dinas = sum(1 for att in attendances if att.status == 'DINAS')
        total_alpa = sum(1 for att in attendances if att.status == 'ALPA')
        
        # Get total active teachers
        total_teachers = Teacher.objects.filter(is_active=True).count()
        
        # Calculate not recorded (approximate - based on unique teachers)
        recorded_teachers = set(att.teacher_id for att in attendances)
        total_not_recorded = total_teachers - len(recorded_teachers)
        
        # Serialize attendances
        serialized_attendances = [serialize_attendance(att, include_details=True) for att in attendances]
        
        return success_response({
            'date': target_date.isoformat(),
            'attendances': serialized_attendances,
            'summary': {
                'total_teachers': total_teachers,
                'total_recorded': total_recorded,
                'total_hadir': total_hadir,
                'total_sakit': total_sakit,
                'total_izin': total_izin,
                'total_cuti': total_cuti,
                'total_dinas': total_dinas,
                'total_alpa': total_alpa,
                'total_not_recorded': total_not_recorded,
            }
        })
        
    except Exception as e:
        return error_response(f"Error retrieving daily attendance: {str(e)}", status=500)


@require_http_methods(["GET"])
@login_required
def absent_teachers(request):
    """
    GET /api/teacher-attendance/absent/ - Get list of teachers who are absent for a specific JP
    
    Query Parameters:
        - date: Date to check (YYYY-MM-DD, required)
        - jp_number: JP number to check (1-10, required)
    
    Response:
        {
            "success": true,
            "data": {
                "date": "2024-01-20",
                "jp_number": 1,
                "absent_teachers": [
                    {
                        "teacher": {...},
                        "schedule": {...},
                        "attendance": {...} or null,
                        "status": "SAKIT" or "NOT_RECORDED",
                        "subject": "Matematika",
                        "classroom": "8A"
                    }
                ],
                "total_absent": 3
            }
        }
    """
    # Get parameters
    if not request.GET.get('date'):
        return error_response("Date parameter is required", status=400)
    
    if not request.GET.get('jp_number'):
        return error_response("JP number parameter is required", status=400)
    
    try:
        target_date = datetime.strptime(request.GET.get('date'), '%Y-%m-%d').date()
    except ValueError:
        return error_response("Invalid date format. Use YYYY-MM-DD", status=400)
    
    try:
        jp_number = int(request.GET.get('jp_number'))
        if not (1 <= jp_number <= 10):
            return error_response("JP number must be between 1 and 10", status=400)
    except ValueError:
        return error_response("Invalid JP number format", status=400)
    
    try:
        # Get absent teachers from service
        absent = TeacherAttendanceService.get_absent_teachers(target_date, jp_number)
        
        # Serialize absent teachers
        serialized_absent = []
        for item in absent:
            serialized_item = {
                'teacher': {
                    'id': str(item['teacher'].id),
                    'nip': item['teacher'].nip,
                    'full_name': item['teacher'].full_name,
                    'photo_url': item['teacher'].photo.url if item['teacher'].photo else None,
                },
                'schedule': {
                    'id': str(item['schedule'].id),
                    'jp_start': item['schedule'].jp_start,
                    'jp_end': item['schedule'].jp_end,
                    'room_number': item['schedule'].room_number,
                },
                'attendance': serialize_attendance(item['attendance']) if item['attendance'] else None,
                'status': item['status'],
                'subject': item['subject'],
                'classroom': item['classroom'],
            }
            serialized_absent.append(serialized_item)
        
        return success_response({
            'date': target_date.isoformat(),
            'jp_number': jp_number,
            'absent_teachers': serialized_absent,
            'total_absent': len(serialized_absent),
        })
        
    except TeacherAttendanceServiceError as e:
        return error_response(str(e), status=400)
    except Exception as e:
        return error_response(f"Error retrieving absent teachers: {str(e)}", status=500)
