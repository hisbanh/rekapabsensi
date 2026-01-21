# Teacher API Documentation

## Overview

The Teacher API provides RESTful endpoints for managing teacher data, schedules, and statistics. All endpoints require authentication and some require admin privileges.

## Base URL

```
/api/teachers/
```

## Authentication

All API endpoints require authentication. Users must be logged in to access the API.

- **Admin-only endpoints**: POST, PUT, DELETE operations require `is_staff=True`
- **Read-only endpoints**: GET operations are available to all authenticated users

## Endpoints

### 1. List Teachers

**Endpoint:** `GET /api/teachers/`

**Description:** Retrieve a paginated list of teachers with optional filtering.

**Query Parameters:**
- `employment_status` (string, optional): Filter by employment status (ACTIVE, LEAVE, INACTIVE)
- `is_active` (boolean, optional): Filter by active status (true/false)
- `subject_id` (UUID, optional): Filter by subject UUID
- `is_homeroom_teacher` (boolean, optional): Filter homeroom teachers (true/false)
- `search` (string, optional): Search by name, NIP, or email
- `order_by` (string, optional): Field to order by (default: full_name)
- `page` (integer, optional): Page number for pagination (default: 1)
- `page_size` (integer, optional): Number of items per page (default: 20, max: 100)

**Response:**
```json
{
  "success": true,
  "data": {
    "teachers": [
      {
        "id": "uuid",
        "nip": "12345",
        "full_name": "Ahmad Yusuf",
        "email": "ahmad@example.com",
        "phone": "081234567890",
        "employment_status": "ACTIVE",
        "employment_date": "2024-01-01",
        "is_homeroom_teacher": false,
        "is_active": true,
        "photo_url": "/media/teachers/photo.jpg"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 25,
      "total_pages": 2
    }
  }
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/teachers/?employment_status=ACTIVE&page=1&page_size=10" \
  -H "Cookie: sessionid=your_session_id"
```

---

### 2. Create Teacher

**Endpoint:** `POST /api/teachers/`

**Description:** Create a new teacher (admin only).

**Request Body:**
```json
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
```

**Response:**
```json
{
  "success": true,
  "message": "Teacher created successfully",
  "data": {
    "id": "uuid",
    "nip": "12345",
    "full_name": "Ahmad Yusuf",
    "email": "ahmad@example.com",
    "phone": "081234567890",
    "employment_status": "ACTIVE",
    "employment_date": "2024-01-01",
    "is_homeroom_teacher": false,
    "is_active": true,
    "photo_url": null,
    "subjects": [],
    "homeroom_class": null,
    "teaching_load": 0,
    "created_at": "2024-01-21T10:00:00Z",
    "updated_at": "2024-01-21T10:00:00Z"
  }
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/teachers/" \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=your_session_id" \
  -d '{
    "nip": "12345",
    "full_name": "Ahmad Yusuf",
    "employment_date": "2024-01-01",
    "employment_status": "ACTIVE",
    "email": "ahmad@example.com"
  }'
```

---

### 3. Get Teacher Detail

**Endpoint:** `GET /api/teachers/{id}/`

**Description:** Retrieve detailed information about a specific teacher.

**Path Parameters:**
- `id` (UUID, required): Teacher UUID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "nip": "12345",
    "full_name": "Ahmad Yusuf",
    "email": "ahmad@example.com",
    "phone": "081234567890",
    "employment_status": "ACTIVE",
    "employment_date": "2024-01-01",
    "is_homeroom_teacher": false,
    "is_active": true,
    "photo_url": "/media/teachers/photo.jpg",
    "subjects": [
      {
        "id": "uuid",
        "code": "MAT",
        "name": "Matematika",
        "category": "UMUM"
      }
    ],
    "homeroom_class": null,
    "teaching_load": 18,
    "total_schedules": 6,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-21T10:00:00Z"
  }
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/teachers/uuid/" \
  -H "Cookie: sessionid=your_session_id"
```

---

### 4. Update Teacher

**Endpoint:** `PUT /api/teachers/{id}/`

**Description:** Update an existing teacher (admin only).

**Path Parameters:**
- `id` (UUID, required): Teacher UUID

**Request Body:**
```json
{
  "full_name": "Ahmad Yusuf Updated",
  "email": "newemail@example.com",
  "phone": "089999999999"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Teacher updated successfully",
  "data": {
    "id": "uuid",
    "nip": "12345",
    "full_name": "Ahmad Yusuf Updated",
    "email": "newemail@example.com",
    "phone": "089999999999",
    ...
  }
}
```

**Example:**
```bash
curl -X PUT "http://localhost:8000/api/teachers/uuid/" \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=your_session_id" \
  -d '{
    "phone": "089999999999",
    "email": "updated@example.com"
  }'
```

---

### 5. Delete Teacher

**Endpoint:** `DELETE /api/teachers/{id}/`

**Description:** Soft delete a teacher by setting is_active to False (admin only).

**Path Parameters:**
- `id` (UUID, required): Teacher UUID

**Response:**
```json
{
  "success": true,
  "message": "Teacher deleted successfully"
}
```

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/teachers/uuid/" \
  -H "Cookie: sessionid=your_session_id"
```

---

### 6. Get Teacher Schedule

**Endpoint:** `GET /api/teachers/{id}/schedule/`

**Description:** Retrieve a teacher's complete weekly schedule.

**Path Parameters:**
- `id` (UUID, required): Teacher UUID

**Response:**
```json
{
  "success": true,
  "data": {
    "teacher_id": "uuid",
    "teacher_name": "Ahmad Yusuf",
    "weekly_schedule": {
      "0": [
        {
          "id": "uuid",
          "day_of_week": 0,
          "day_name": "Senin",
          "jp_start": 1,
          "jp_end": 2,
          "jp_count": 2,
          "subject": {
            "id": "uuid",
            "code": "MAT",
            "name": "Matematika"
          },
          "classroom": {
            "id": "uuid",
            "name": "Kelas 8-A",
            "grade": 8
          },
          "room_number": "R101",
          "notes": "",
          "effective_date": "2024-01-01",
          "end_date": null
        }
      ],
      "1": [],
      "2": [],
      ...
    }
  }
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/teachers/uuid/schedule/" \
  -H "Cookie: sessionid=your_session_id"
```

---

### 7. Get Teacher Statistics

**Endpoint:** `GET /api/teachers/{id}/statistics/`

**Description:** Retrieve attendance statistics for a teacher for a specific month.

**Path Parameters:**
- `id` (UUID, required): Teacher UUID

**Query Parameters:**
- `year` (integer, required): Year (e.g., 2024)
- `month` (integer, required): Month (1-12)

**Response:**
```json
{
  "success": true,
  "data": {
    "teacher": {
      "id": "uuid",
      "nip": "12345",
      "full_name": "Ahmad Yusuf"
    },
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
```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/teachers/uuid/statistics/?year=2024&month=1" \
  -H "Cookie: sessionid=your_session_id"
```

---

## Error Responses

All endpoints return error responses in the following format:

```json
{
  "success": false,
  "error": "Error message description"
}
```

### Common HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data or validation error
- `403 Forbidden`: Permission denied (admin access required)
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

### Example Error Response

```json
{
  "success": false,
  "error": "Validation errors: Field 'nip' is required, Full name must be at least 3 characters"
}
```

---

## Request Validation

### Teacher Creation/Update Validation Rules

- **nip**: Required (creation only), max 20 characters, alphanumeric, unique
- **full_name**: Required (creation only), min 3 characters, no numbers
- **employment_date**: Required (creation only), cannot be in future, format: YYYY-MM-DD
- **employment_status**: Required (creation only), must be ACTIVE, LEAVE, or INACTIVE
- **email**: Optional, must be valid email format
- **phone**: Optional, max 15 characters
- **is_homeroom_teacher**: Optional, boolean
- **homeroom_class**: Required if is_homeroom_teacher is true, must be valid classroom UUID
- **is_active**: Optional, boolean (default: true)

---

## Pagination

List endpoints support pagination with the following parameters:

- **page**: Page number (default: 1, min: 1)
- **page_size**: Items per page (default: 20, min: 1, max: 100)

Pagination information is returned in the response:

```json
{
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 25,
    "total_pages": 2
  }
}
```

---

## Filtering and Searching

The list endpoint supports multiple filters:

### Filter by Employment Status
```
GET /api/teachers/?employment_status=ACTIVE
```

### Filter by Active Status
```
GET /api/teachers/?is_active=true
```

### Filter by Subject
```
GET /api/teachers/?subject_id=uuid
```

### Filter Homeroom Teachers
```
GET /api/teachers/?is_homeroom_teacher=true
```

### Search by Name, NIP, or Email
```
GET /api/teachers/?search=Ahmad
```

### Combine Multiple Filters
```
GET /api/teachers/?employment_status=ACTIVE&is_active=true&search=Ahmad&page_size=10
```

---

## Testing

A test script is provided to verify all API endpoints:

```bash
python test_teacher_api.py
```

This script tests:
1. List teachers with pagination
2. Create teacher
3. Get teacher detail
4. Update teacher
5. Get teacher schedule
6. Get teacher statistics
7. Delete teacher
8. Filtering and searching
9. Authentication requirements

---

## Integration Examples

### JavaScript (Fetch API)

```javascript
// List teachers
fetch('/api/teachers/?page=1&page_size=10', {
  method: 'GET',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
  }
})
.then(response => response.json())
.then(data => {
  console.log('Teachers:', data.data.teachers);
});

// Create teacher
fetch('/api/teachers/', {
  method: 'POST',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCookie('csrftoken'),
  },
  body: JSON.stringify({
    nip: '12345',
    full_name: 'Ahmad Yusuf',
    employment_date: '2024-01-01',
    employment_status: 'ACTIVE',
    email: 'ahmad@example.com'
  })
})
.then(response => response.json())
.then(data => {
  console.log('Created teacher:', data.data);
});
```

### Python (Requests)

```python
import requests

# Login first
session = requests.Session()
session.post('http://localhost:8000/login/', data={
    'username': 'admin',
    'password': 'password'
})

# List teachers
response = session.get('http://localhost:8000/api/teachers/')
data = response.json()
print('Teachers:', data['data']['teachers'])

# Create teacher
response = session.post('http://localhost:8000/api/teachers/', json={
    'nip': '12345',
    'full_name': 'Ahmad Yusuf',
    'employment_date': '2024-01-01',
    'employment_status': 'ACTIVE',
    'email': 'ahmad@example.com'
})
data = response.json()
print('Created teacher:', data['data'])
```

---

## Notes

- All date fields use ISO 8601 format (YYYY-MM-DD)
- All datetime fields use ISO 8601 format with timezone (YYYY-MM-DDTHH:MM:SSZ)
- UUIDs are returned as strings
- Photo URLs are relative to the media root
- Soft delete is used (is_active=False) instead of hard delete
- All endpoints require CSRF token for POST, PUT, DELETE operations when using session authentication

---

## Support

For issues or questions about the API, please contact the development team or refer to the main project documentation.
