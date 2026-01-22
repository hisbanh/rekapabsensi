# Teacher Attendance API Reference

This document provides a comprehensive reference for the Teacher Attendance API endpoints.

## Base URL
All endpoints are prefixed with `/api/`

## Authentication
All endpoints require authentication. Include the session cookie or authentication token in your requests.

## Permission Model
- **Teachers**: Can only view and record their own attendance
- **Admin/Staff**: Can view and manage all teacher attendance records

---

## Endpoints

### 1. List/Create Attendance Records

#### GET `/api/teacher-attendance/`
List all attendance records with optional filters.

**Query Parameters:**
- `teacher_id` (UUID, optional): Filter by teacher
- `date` (YYYY-MM-DD, optional): Filter by specific date
- `start_date` (YYYY-MM-DD, optional): Filter by start date
- `end_date` (YYYY-MM-DD, optional): Filter by end date
- `jp_number` (1-10, optional): Filter by JP number
- `status` (string, optional): Filter by status (HADIR, SAKIT, IZIN, CUTI, DINAS, ALPA)
- `is_substitute` (boolean, optional): Filter substitute teaching
- `page` (integer, optional): Page number (default: 1)
- `page_size` (integer, optional): Items per page (default: 20, max: 100)

**Response:**
```json
{
  "success": true,
  "data": {
    "attendances": [
      {
        "id": "uuid",
        "date": "2024-01-20",
        "jp_number": 1,
        "status": "HADIR",
        "notes": "",
        "is_substitute": false,
        "is_location_valid": true,
        "recorded_at": "2024-01-20T08:00:00Z",
        "teacher": {
          "id": "uuid",
          "nip": "12345",
          "full_name": "Ahmad Yusuf",
          "photo_url": "/media/teachers/photo.jpg"
        },
        "schedule": {
          "id": "uuid",
          "subject": {
            "id": "uuid",
            "code": "MAT",
            "name": "Matematika"
          },
          "classroom": {
            "id": "uuid",
            "name": "8A",
            "grade": "8"
          },
          "room_number": "A101"
        },
        "substitute_for": null,
        "recorded_by": {
          "id": 1,
          "username": "admin",
          "full_name": "Admin User"
        },
        "latitude": -7.7956,
        "longitude": 110.3695,
        "created_at": "2024-01-20T08:00:00Z",
        "updated_at": "2024-01-20T08:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 50,
      "total_pages": 3
    }
  }
}
```

#### POST `/api/teacher-attendance/`
Record new attendance.

**Request Body:**
```json
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
```

**Response:**
```json
{
  "success": true,
  "message": "Attendance recorded successfully",
  "data": {
    // Same structure as GET response
  }
}
```

**Status Codes:**
- `201`: Created successfully
- `400`: Validation error
- `403`: Permission denied
- `500`: Server error

---

### 2. Get/Update/Delete Attendance Record

#### GET `/api/teacher-attendance/{id}/`
Get detailed information about a specific attendance record.

**Path Parameters:**
- `id` (UUID): Attendance record ID

**Response:**
```json
{
  "success": true,
  "data": {
    // Same structure as list endpoint
  }
}
```

#### PUT `/api/teacher-attendance/{id}/`
Update an existing attendance record.

**Path Parameters:**
- `id` (UUID): Attendance record ID

**Request Body:**
```json
{
  "status": "SAKIT",
  "notes": "Demam tinggi",
  // Any fields from the create endpoint
}
```

**Response:**
```json
{
  "success": true,
  "message": "Attendance updated successfully",
  "data": {
    // Updated attendance record
  }
}
```

#### DELETE `/api/teacher-attendance/{id}/`
Delete an attendance record (admin only).

**Path Parameters:**
- `id` (UUID): Attendance record ID

**Response:**
```json
{
  "success": true,
  "message": "Attendance deleted successfully"
}
```

**Status Codes:**
- `200`: Success
- `403`: Permission denied (admin only)
- `404`: Not found
- `500`: Server error

---

### 3. Validate Location

#### POST `/api/teacher-attendance/validate-location/`
Validate if coordinates are within school premises.

**Request Body:**
```json
{
  "latitude": -7.7956,
  "longitude": 110.3695
}
```

**Response:**
```json
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
```

**Status Codes:**
- `200`: Success
- `400`: Invalid coordinates
- `500`: Server error

---

### 4. Daily Attendance

#### GET `/api/teacher-attendance/daily/`
Get all attendance records for a specific date with summary statistics.

**Query Parameters:**
- `date` (YYYY-MM-DD, required): Date to get attendance for

**Response:**
```json
{
  "success": true,
  "data": {
    "date": "2024-01-20",
    "attendances": [
      // Array of attendance records
    ],
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
```

**Status Codes:**
- `200`: Success
- `400`: Invalid date format
- `500`: Server error

---

### 5. Absent Teachers

#### GET `/api/teacher-attendance/absent/`
Get list of teachers who are absent for a specific JP on a date.

**Query Parameters:**
- `date` (YYYY-MM-DD, required): Date to check
- `jp_number` (1-10, required): JP number to check

**Response:**
```json
{
  "success": true,
  "data": {
    "date": "2024-01-20",
    "jp_number": 1,
    "absent_teachers": [
      {
        "teacher": {
          "id": "uuid",
          "nip": "12345",
          "full_name": "Ahmad Yusuf",
          "photo_url": "/media/teachers/photo.jpg"
        },
        "schedule": {
          "id": "uuid",
          "jp_start": 1,
          "jp_end": 2,
          "room_number": "A101"
        },
        "attendance": {
          // Attendance record if exists, null if not recorded
        },
        "status": "SAKIT",  // or "NOT_RECORDED"
        "subject": "Matematika",
        "classroom": "8A"
      }
    ],
    "total_absent": 3
  }
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid parameters
- `500`: Server error

---

## Status Values

Valid attendance status values:
- `HADIR`: Present
- `SAKIT`: Sick
- `IZIN`: Permission/Leave
- `CUTI`: Official Leave
- `DINAS`: Official Duty
- `ALPA`: Absent without notice

---

## Error Response Format

All error responses follow this format:

```json
{
  "success": false,
  "error": "Error message description",
  "errors": {
    // Optional additional error details
  }
}
```

---

## Examples

### Example 1: Record Attendance with Location

```bash
curl -X POST http://localhost:8000/api/teacher-attendance/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=..." \
  -d '{
    "teacher_id": "123e4567-e89b-12d3-a456-426614174000",
    "date": "2024-01-20",
    "jp_number": 1,
    "status": "HADIR",
    "latitude": -7.7956,
    "longitude": 110.3695
  }'
```

### Example 2: Get Daily Attendance

```bash
curl -X GET "http://localhost:8000/api/teacher-attendance/daily/?date=2024-01-20" \
  -H "Cookie: sessionid=..."
```

### Example 3: Validate Location

```bash
curl -X POST http://localhost:8000/api/teacher-attendance/validate-location/ \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=..." \
  -d '{
    "latitude": -7.7956,
    "longitude": 110.3695
  }'
```

### Example 4: Get Absent Teachers

```bash
curl -X GET "http://localhost:8000/api/teacher-attendance/absent/?date=2024-01-20&jp_number=1" \
  -H "Cookie: sessionid=..."
```

---

## Notes

1. **Date Format**: All dates must be in ISO format (YYYY-MM-DD)
2. **UUID Format**: All UUIDs must be valid UUID4 format
3. **JP Numbers**: Valid range is 1-10
4. **Location Validation**: Uses Haversine formula to calculate distance from school coordinates
5. **Permissions**: 
   - Teachers can only access their own attendance data
   - Admin/staff can access all attendance data
6. **Date Restrictions**:
   - Teachers can only record attendance for dates within the last 7 days
   - Admin can record attendance for any past date
7. **Duplicate Prevention**: System prevents duplicate attendance records for the same teacher, date, and JP

---

## Related Documentation

- [Teacher API Reference](./QUICK_REFERENCE.md)
- [Schedule API Reference](./SCHEDULE_API_REFERENCE.md)
- [Implementation Summary](./IMPLEMENTATION_SUMMARY.md)
