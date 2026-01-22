# Teacher Report API Reference

This document provides comprehensive documentation for the Teacher Report API endpoints.

## Base URL

All endpoints are prefixed with `/api/`

## Authentication

All endpoints require authentication. Use Django's session authentication or token authentication.

## Endpoints

### 1. Generate Teacher PDF Report

Generate a comprehensive PDF report for a specific teacher's attendance.

**Endpoint:** `GET /api/reports/teacher/{teacher_id}/pdf/`

**Path Parameters:**
- `teacher_id` (UUID, required): The UUID of the teacher

**Query Parameters:**
- `start_date` (string, required): Start date in YYYY-MM-DD format
- `end_date` (string, required): End date in YYYY-MM-DD format

**Permissions:**
- Teachers can only generate their own reports
- Admin can generate reports for any teacher

**Response:**
- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename="laporan_absensi_{teacher_name}_{dates}.pdf"`

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/reports/teacher/123e4567-e89b-12d3-a456-426614174000/pdf/?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Token your-auth-token" \
  --output report.pdf
```

**Error Responses:**
- `400 Bad Request`: Invalid teacher ID or missing/invalid date parameters
- `403 Forbidden`: User doesn't have permission to access this report
- `404 Not Found`: Teacher not found

---

### 2. Get Attendance Analytics

Get comprehensive attendance analytics for all teachers within a date range.

**Endpoint:** `GET /api/reports/analytics/`

**Query Parameters:**
- `start_date` (string, required): Start date in YYYY-MM-DD format
- `end_date` (string, required): End date in YYYY-MM-DD format

**Permissions:**
- Only admin users can access analytics

**Response:**
```json
{
  "success": true,
  "data": {
    "period": {
      "start_date": "2024-01-01",
      "end_date": "2024-01-31",
      "total_days": 31
    },
    "overall_stats": {
      "total_teachers": 25,
      "total_records": 500,
      "total_hadir": 425,
      "total_sakit": 30,
      "total_izin": 25,
      "total_cuti": 10,
      "total_dinas": 5,
      "total_alpa": 5,
      "attendance_percentage": 85.0
    },
    "teacher_stats": [
      {
        "teacher_id": "123e4567-e89b-12d3-a456-426614174000",
        "teacher_name": "Ahmad Yusuf",
        "nip": "12345",
        "total_jp": 80,
        "total_hadir": 68,
        "total_sakit": 4,
        "total_izin": 6,
        "total_cuti": 0,
        "total_dinas": 2,
        "total_alpa": 0,
        "attendance_percentage": 85.0
      }
    ],
    "daily_trends": [
      {
        "date": "2024-01-01",
        "day_name": "Monday",
        "total_jp": 100,
        "total_hadir": 85,
        "total_absent": 15,
        "attendance_percentage": 85.0
      }
    ],
    "subject_stats": [
      {
        "subject_name": "Matematika",
        "subject_code": "MAT",
        "total_jp": 120,
        "total_hadir": 102,
        "attendance_percentage": 85.0
      }
    ],
    "top_performers": [
      {
        "teacher_id": "...",
        "teacher_name": "Ahmad Yusuf",
        "nip": "12345",
        "attendance_percentage": 95.0
      }
    ],
    "needs_attention": [
      {
        "teacher_id": "...",
        "teacher_name": "Fatimah Zahra",
        "nip": "67890",
        "attendance_percentage": 75.0
      }
    ]
  }
}
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/reports/analytics/?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Token your-auth-token"
```

**Error Responses:**
- `400 Bad Request`: Missing or invalid date parameters
- `403 Forbidden`: User is not an admin

---

### 3. Export Attendance to Excel

Export attendance data to Excel format with multiple sheets and advanced formatting.

**Endpoint:** `GET /api/reports/export/excel/`

**Query Parameters:**
- `start_date` (string, required): Start date in YYYY-MM-DD format
- `end_date` (string, required): End date in YYYY-MM-DD format
- `teacher_ids` (string, optional): Comma-separated list of teacher UUIDs for individual sheets

**Permissions:**
- Only admin users can export attendance data

**Response:**
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Content-Disposition: `attachment; filename="absensi_ustadz_{dates}.xlsx"`

**Excel File Structure:**
- **Summary Sheet**: Overall statistics and teacher performance
- **Detail Sheet**: Complete attendance records with color-coded statuses
- **Per-Teacher Sheets** (if teacher_ids provided): Individual sheets for each teacher

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/reports/export/excel/?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Token your-auth-token" \
  --output attendance.xlsx

# With specific teachers
curl -X GET "http://localhost:8000/api/reports/export/excel/?start_date=2024-01-01&end_date=2024-01-31&teacher_ids=123e4567-e89b-12d3-a456-426614174000,987fcdeb-51a2-43f7-b890-123456789abc" \
  -H "Authorization: Token your-auth-token" \
  --output attendance.xlsx
```

**Error Responses:**
- `400 Bad Request`: Missing/invalid date parameters or invalid teacher_ids format
- `403 Forbidden`: User is not an admin

---

### 4. Get Dashboard Statistics

Get real-time statistics for the teacher attendance dashboard.

**Endpoint:** `GET /api/reports/dashboard/`

**Query Parameters:** None

**Permissions:**
- Admin can access all dashboard statistics
- Teachers can access limited dashboard statistics (their own data)

**Response:**
```json
{
  "success": true,
  "data": {
    "today": "2024-01-20",
    "today_stats": {
      "total_jp": 120,
      "total_hadir": 100,
      "total_sakit": 10,
      "total_izin": 5,
      "total_cuti": 2,
      "total_dinas": 2,
      "total_alpa": 1,
      "attendance_percentage": 83.33,
      "teachers_recorded": 20,
      "total_active_teachers": 25
    },
    "absent_today": [
      {
        "teacher_name": "Ahmad Yusuf",
        "nip": "12345",
        "status": "SAKIT",
        "schedule": {
          "id": "...",
          "subject": "Matematika",
          "classroom": "8A",
          "jp_start": 1,
          "jp_end": 2
        }
      }
    ],
    "recent_trends": [
      {
        "date": "2024-01-14",
        "day_name": "Sunday",
        "total_jp": 100,
        "total_hadir": 85,
        "total_absent": 15,
        "attendance_percentage": 85.0
      }
    ],
    "notifications": [
      {
        "type": "warning",
        "message": "5 ustadz belum mencatat kehadiran hari ini",
        "priority": "high"
      }
    ],
    "quick_stats": {
      "month_total_jp": 2400,
      "month_total_hadir": 2040,
      "month_attendance_percentage": 85.0,
      "total_active_teachers": 25
    }
  }
}
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/reports/dashboard/" \
  -H "Authorization: Token your-auth-token"
```

**Error Responses:**
- `403 Forbidden`: User without teacher profile trying to access (for non-admin users)
- `500 Internal Server Error`: Server error while retrieving statistics

---

## Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Attendance Status Values

- `HADIR`: Present
- `SAKIT`: Sick
- `IZIN`: Permission/Leave
- `CUTI`: Official Leave
- `DINAS`: Official Duty
- `ALPA`: Absent without notice

## Date Format

All dates must be in ISO 8601 format: `YYYY-MM-DD`

Example: `2024-01-20`

## Error Response Format

```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

## Notes

1. **PDF Reports**: Generated reports include:
   - School header with logo (if available)
   - Teacher photo and profile information
   - Attendance summary table
   - Bar chart visualization
   - Detailed attendance records
   - Page numbers and timestamps

2. **Excel Exports**: Excel files include:
   - Professional styling with indigo theme
   - Conditional formatting (color-coded statuses)
   - Formulas for automatic calculations
   - Frozen header rows
   - Multiple sheets for comprehensive data

3. **Analytics**: Provides insights including:
   - Overall attendance rates
   - Teacher-wise performance
   - Daily attendance trends
   - Subject-wise statistics
   - Top performers and teachers needing attention

4. **Dashboard**: Real-time statistics updated automatically, including:
   - Today's attendance summary
   - Absent teachers list
   - Recent 7-day trends
   - Important notifications
   - Monthly quick statistics

## Integration Examples

### Python (requests)

```python
import requests

# Get analytics
response = requests.get(
    'http://localhost:8000/api/reports/analytics/',
    params={
        'start_date': '2024-01-01',
        'end_date': '2024-01-31'
    },
    headers={'Authorization': 'Token your-auth-token'}
)
analytics = response.json()

# Download PDF report
response = requests.get(
    f'http://localhost:8000/api/reports/teacher/{teacher_id}/pdf/',
    params={
        'start_date': '2024-01-01',
        'end_date': '2024-01-31'
    },
    headers={'Authorization': 'Token your-auth-token'}
)
with open('report.pdf', 'wb') as f:
    f.write(response.content)
```

### JavaScript (fetch)

```javascript
// Get dashboard statistics
fetch('http://localhost:8000/api/reports/dashboard/', {
  headers: {
    'Authorization': 'Token your-auth-token'
  }
})
.then(response => response.json())
.then(data => {
  console.log('Dashboard stats:', data);
});

// Download Excel export
fetch('http://localhost:8000/api/reports/export/excel/?start_date=2024-01-01&end_date=2024-01-31', {
  headers: {
    'Authorization': 'Token your-auth-token'
  }
})
.then(response => response.blob())
.then(blob => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'attendance.xlsx';
  a.click();
});
```

## Support

For issues or questions, please contact the development team or refer to the main API documentation.
