# Schedule API Reference

## Overview
RESTful API endpoints for managing teacher schedules with conflict detection and weekly schedule views.

## Authentication
All endpoints require authentication. Admin access is required for POST, PUT, and DELETE operations.

## Base URL
```
/api/schedules/
```

---

## Endpoints

### 1. List Schedules
**GET** `/api/schedules/`

List all teacher schedules with optional filtering and pagination.

**Query Parameters:**
- `teacher_id` (UUID): Filter by teacher
- `subject_id` (UUID): Filter by subject
- `classroom_id` (UUID): Filter by classroom
- `day_of_week` (0-6): Filter by day (0=Monday, 6=Sunday)
- `is_active` (boolean): Filter by active status
- `effective_date` (YYYY-MM-DD): Filter by effective date
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 20, max: 100)

**Response:**
```json
{
  "success": true,
  "data": {
    "schedules": [
      {
        "id": "uuid",
        "day_of_week": 0,
        "day_name": "Senin",
        "jp_start": 1,
        "jp_end": 2,
        "jp_count": 2,
        "room_number": "A101",
        "notes": "",
        "effective_date": "2024-01-01",
        "end_date": null,
        "is_active": true,
        "teacher": {
          "id": "uuid",
          "nip": "12345",
          "full_name": "Ahmad Yusuf",
          "photo_url": "/media/teachers/photo.jpg"
        },
        "subject": {
          "id": "uuid",
          "code": "MAT",
          "name": "Matematika",
          "category": "UMUM"
        },
        "classroom": {
          "id": "uuid",
          "name": "8A",
          "grade": 8
        },
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z"
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

---

### 2. Create Schedule
**POST** `/api/schedules/`

Create a new teacher schedule. Requires admin access.

**Request Body:**
```json
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
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Schedule created successfully",
  "data": {
    "id": "uuid",
    "day_of_week": 0,
    "day_name": "Senin",
    "jp_start": 1,
    "jp_end": 2,
    ...
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "Validation error message"
}
```

---

### 3. Get Schedule Detail
**GET** `/api/schedules/{id}/`

Get detailed information about a specific schedule.

**Path Parameters:**
- `id` (UUID): Schedule ID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "day_of_week": 0,
    "day_name": "Senin",
    "jp_start": 1,
    "jp_end": 2,
    "jp_count": 2,
    "teacher": {...},
    "subject": {...},
    "classroom": {...},
    ...
  }
}
```

---

### 4. Update Schedule
**PUT** `/api/schedules/{id}/`

Update an existing schedule. Requires admin access.

**Path Parameters:**
- `id` (UUID): Schedule ID

**Request Body:**
```json
{
  "jp_start": 3,
  "jp_end": 4,
  "room_number": "B202",
  "notes": "Updated notes"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Schedule updated successfully",
  "data": {...}
}
```

---

### 5. Delete Schedule
**DELETE** `/api/schedules/{id}/`

Soft delete a schedule (sets is_active to false). Requires admin access.

**Path Parameters:**
- `id` (UUID): Schedule ID

**Response:**
```json
{
  "success": true,
  "message": "Schedule deleted successfully"
}
```

---

### 6. Detect Conflicts
**POST** `/api/schedules/detect-conflicts/`

Check for scheduling conflicts before creating or updating a schedule. Requires admin access.

**Request Body:**
```json
{
  "teacher_id": "uuid",
  "day_of_week": 0,
  "jp_start": 1,
  "jp_end": 2,
  "effective_date": "2024-01-01",
  "end_date": "2024-12-31",
  "exclude_schedule_id": "uuid",
  "classroom_id": "uuid"
}
```

**Fields:**
- `teacher_id` (required): Teacher UUID
- `day_of_week` (required): Day (0-6)
- `jp_start` (required): Starting JP (1-10)
- `jp_end` (required): Ending JP (1-10)
- `effective_date` (optional): Effective date
- `end_date` (optional): End date
- `exclude_schedule_id` (optional): Schedule to exclude (for updates)
- `classroom_id` (optional): Check classroom conflicts too

**Response:**
```json
{
  "success": true,
  "data": {
    "has_conflicts": true,
    "conflicts": [
      {
        "type": "teacher",
        "message": "Teacher Ahmad Yusuf already has a schedule on Senin from JP 1 to 2 (Matematika in 8A)",
        "schedule": {...}
      },
      {
        "type": "classroom",
        "message": "Classroom 8A is already scheduled on Senin from JP 1 to 2 with Ahmad Yusuf (Matematika)",
        "schedule": {...}
      }
    ]
  }
}
```

---

### 7. Get Weekly Schedule
**GET** `/api/schedules/weekly/{teacher_id}/`

Get a teacher's complete weekly schedule organized by day.

**Path Parameters:**
- `teacher_id` (UUID): Teacher ID

**Response:**
```json
{
  "success": true,
  "data": {
    "teacher_id": "uuid",
    "teacher_name": "Ahmad Yusuf",
    "total_jp_per_week": 18,
    "weekly_schedule": {
      "0": [
        {
          "id": "uuid",
          "day_of_week": 0,
          "day_name": "Senin",
          "jp_start": 1,
          "jp_end": 2,
          "subject": {...},
          "classroom": {...},
          ...
        }
      ],
      "1": [...],
      "2": [...],
      "3": [...],
      "4": [...],
      "5": [],
      "6": []
    }
  }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

### 403 Forbidden
```json
{
  "success": false,
  "error": "Permission denied. Admin access required."
}
```

### 404 Not Found
```json
{
  "success": false,
  "error": "Schedule not found"
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "error": "Error message"
}
```

---

## Usage Examples

### Example 1: Create a schedule with conflict detection

```python
import requests

# First, check for conflicts
conflict_check = requests.post(
    'http://localhost:8000/api/schedules/detect-conflicts/',
    json={
        'teacher_id': 'teacher-uuid',
        'day_of_week': 0,
        'jp_start': 1,
        'jp_end': 2,
        'effective_date': '2024-01-01',
        'classroom_id': 'classroom-uuid'
    },
    headers={'Authorization': 'Bearer token'}
)

if not conflict_check.json()['data']['has_conflicts']:
    # No conflicts, create the schedule
    response = requests.post(
        'http://localhost:8000/api/schedules/',
        json={
            'teacher_id': 'teacher-uuid',
            'subject_id': 'subject-uuid',
            'classroom_id': 'classroom-uuid',
            'day_of_week': 0,
            'jp_start': 1,
            'jp_end': 2,
            'effective_date': '2024-01-01',
            'is_active': True
        },
        headers={'Authorization': 'Bearer token'}
    )
```

### Example 2: Get teacher's weekly schedule

```python
import requests

response = requests.get(
    'http://localhost:8000/api/schedules/weekly/teacher-uuid/',
    headers={'Authorization': 'Bearer token'}
)

data = response.json()['data']
print(f"Teacher: {data['teacher_name']}")
print(f"Total JP per week: {data['total_jp_per_week']}")

for day, schedules in data['weekly_schedule'].items():
    if schedules:
        print(f"\nDay {day}:")
        for schedule in schedules:
            print(f"  JP {schedule['jp_start']}-{schedule['jp_end']}: {schedule['subject']['name']}")
```

### Example 3: Filter schedules by teacher and day

```python
import requests

response = requests.get(
    'http://localhost:8000/api/schedules/',
    params={
        'teacher_id': 'teacher-uuid',
        'day_of_week': 0,  # Monday
        'is_active': 'true'
    },
    headers={'Authorization': 'Bearer token'}
)

schedules = response.json()['data']['schedules']
```

---

## Notes

- All date fields use ISO 8601 format (YYYY-MM-DD)
- All datetime fields use ISO 8601 format with timezone (YYYY-MM-DDTHH:MM:SSZ)
- UUIDs are represented as strings
- Day of week: 0=Monday (Senin), 1=Tuesday (Selasa), ..., 6=Sunday (Minggu)
- JP (Jam Pelajaran) numbers range from 1 to 10
- Schedules are soft-deleted (is_active set to false) rather than permanently removed
- Conflict detection checks both teacher and classroom availability
- Weekly schedule only returns active schedules within the current date range
