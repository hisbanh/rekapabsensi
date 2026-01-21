# Teacher API Quick Reference

## Endpoints Summary

| Method | Endpoint | Description | Auth | Admin |
|--------|----------|-------------|------|-------|
| GET | `/api/teachers/` | List teachers | ✓ | ✗ |
| POST | `/api/teachers/` | Create teacher | ✓ | ✓ |
| GET | `/api/teachers/{id}/` | Get teacher detail | ✓ | ✗ |
| PUT | `/api/teachers/{id}/` | Update teacher | ✓ | ✓ |
| DELETE | `/api/teachers/{id}/` | Delete teacher | ✓ | ✓ |
| GET | `/api/teachers/{id}/schedule/` | Get teacher schedule | ✓ | ✗ |
| GET | `/api/teachers/{id}/statistics/` | Get teacher statistics | ✓ | ✗ |

## Quick Examples

### List Teachers (with filters)
```bash
GET /api/teachers/?employment_status=ACTIVE&page=1&page_size=10
```

### Create Teacher
```json
POST /api/teachers/
{
  "nip": "12345",
  "full_name": "Ahmad Yusuf",
  "employment_date": "2024-01-01",
  "employment_status": "ACTIVE",
  "email": "ahmad@example.com"
}
```

### Get Teacher Detail
```bash
GET /api/teachers/{uuid}/
```

### Update Teacher
```json
PUT /api/teachers/{uuid}/
{
  "phone": "089999999999",
  "email": "updated@example.com"
}
```

### Delete Teacher
```bash
DELETE /api/teachers/{uuid}/
```

### Get Teacher Schedule
```bash
GET /api/teachers/{uuid}/schedule/
```

### Get Teacher Statistics
```bash
GET /api/teachers/{uuid}/statistics/?year=2024&month=1
```

## Response Format

### Success Response
```json
{
  "success": true,
  "data": {...},
  "message": "Optional message"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message"
}
```

## Common Status Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Validation error
- `403 Forbidden` - Permission denied
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Filter Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `employment_status` | string | ACTIVE, LEAVE, INACTIVE |
| `is_active` | boolean | true/false |
| `subject_id` | UUID | Filter by subject |
| `is_homeroom_teacher` | boolean | true/false |
| `search` | string | Search name, NIP, email |
| `order_by` | string | Field to order by |
| `page` | integer | Page number (default: 1) |
| `page_size` | integer | Items per page (default: 20, max: 100) |

## Validation Rules

### Teacher Fields
- **nip**: Required, max 20 chars, alphanumeric, unique
- **full_name**: Required, min 3 chars, no numbers
- **employment_date**: Required, YYYY-MM-DD, not future
- **employment_status**: Required, ACTIVE/LEAVE/INACTIVE
- **email**: Optional, valid email format
- **phone**: Optional, max 15 chars
- **is_homeroom_teacher**: Optional, boolean
- **homeroom_class**: Required if is_homeroom_teacher=true
- **is_active**: Optional, boolean (default: true)

## Testing

Run the test suite:
```bash
python manage.py test attendance.tests.test_teacher_api
```

Or use the provided test script:
```bash
python test_teacher_api.py
```

## Notes

- All endpoints require authentication
- Admin operations require `is_staff=True`
- Dates use ISO 8601 format (YYYY-MM-DD)
- UUIDs are returned as strings
- Soft delete is used (is_active=False)
- CSRF token required for POST/PUT/DELETE

## Support

For detailed documentation, see [README.md](README.md)
