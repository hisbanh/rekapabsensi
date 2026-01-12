# Design Document: JP Attendance System

## Overview

Sistem rekap absensi per Jam Pelajaran (JP) untuk Pesantren Yaumi dengan Custom Admin Panel yang modern dan mobile-responsive. Sistem ini menggantikan Django Admin dengan interface custom yang user-friendly, menggunakan tema putih dengan aksen coklat elegant.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Templates  │  │   Static    │  │    JavaScript (AJAX)    │ │
│  │  (Jinja2)   │  │  (CSS/JS)   │  │   (Inline Edit, etc)    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        View Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Dashboard  │  │  Attendance │  │      Management         │ │
│  │   Views     │  │    Views    │  │        Views            │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Service Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Attendance  │  │   Report    │  │       Schedule          │ │
│  │  Service    │  │   Service   │  │       Service           │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Model Layer                              │
│  ┌──────────┐ ┌───────────┐ ┌─────────┐ ┌────────┐ ┌─────────┐ │
│  │DaySchedule│ │DailyAttend│ │ Holiday │ │Student │ │Classroom│ │
│  └──────────┘ └───────────┘ └─────────┘ └────────┘ └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Database (SQLite/PostgreSQL)               │
└─────────────────────────────────────────────────────────────────┘
```

### URL Structure

```
/                           → Redirect to /attendance/
/attendance/                → Dashboard
/attendance/input/          → Input Absensi (select class & date)
/attendance/input/<class>/<date>/  → Input form for specific class/date
/attendance/report/         → Report page with filters
/attendance/export/pdf/     → PDF export endpoint
/attendance/export/excel/   → Excel export endpoint
/attendance/export/csv/     → CSV export endpoint

/manage/                    → Management Dashboard
/manage/students/           → Student list
/manage/students/create/    → Create student
/manage/students/<id>/      → Edit student
/manage/students/<id>/delete/ → Delete student
/manage/classrooms/         → Classroom list (same pattern)
/manage/holidays/           → Holiday list (same pattern)
/manage/settings/           → Settings (Day Schedule, etc)
/manage/users/              → User management (Admin only)

/api/attendance/save/       → AJAX endpoint for saving attendance
/api/attendance/inline-edit/ → AJAX endpoint for inline edit
/api/export/                → AJAX endpoint for exports
```

## Components and Interfaces

### Template Components (Reusable)

```
templates/
├── base.html                    # Base layout with sidebar
├── components/
│   ├── _sidebar.html            # Sidebar navigation
│   ├── _navbar.html             # Top navbar
│   ├── _breadcrumb.html         # Breadcrumb navigation
│   ├── _data_table.html         # Reusable data table
│   ├── _pagination.html         # Pagination component
│   ├── _modal.html              # Modal dialog
│   ├── _form_field.html         # Form field wrapper
│   ├── _alert.html              # Alert/notification
│   ├── _card.html               # Card component
│   └── _filters.html            # Filter bar component
├── attendance/
│   ├── dashboard.html           # Main dashboard
│   ├── input_select.html        # Select class & date
│   ├── input_form.html          # Attendance input grid
│   └── report.html              # Report with export options
└── manage/
    ├── base_list.html           # Base list template
    ├── base_form.html           # Base form template
    ├── students/
    │   ├── list.html
    │   └── form.html
    ├── classrooms/
    │   ├── list.html
    │   └── form.html
    ├── holidays/
    │   ├── list.html
    │   └── form.html
    ├── settings/
    │   └── day_schedule.html
    └── users/
        ├── list.html
        └── form.html
```

### Service Interfaces

```python
# attendance/services/schedule_service.py
class ScheduleService:
    def get_jp_count_for_date(date: date) -> int
    def get_day_schedule(day_of_week: int) -> DaySchedule
    def get_all_schedules() -> List[DaySchedule]
    def update_schedule(day_of_week: int, jp_count: int) -> DaySchedule
    def is_school_day(date: date) -> bool

# attendance/services/attendance_service.py
class AttendanceService:
    def get_attendance(student: Student, date: date) -> Optional[DailyAttendance]
    def get_class_attendance(classroom: Classroom, date: date) -> List[DailyAttendance]
    def save_attendance(student: Student, date: date, jp_statuses: dict, user: User) -> DailyAttendance
    def save_bulk_attendance(classroom: Classroom, date: date, data: List[dict], user: User) -> int
    def get_missing_attendance(classroom: Classroom, start_date: date, end_date: date) -> List[date]

# attendance/services/holiday_service.py
class HolidayService:
    def is_holiday(date: date, classroom: Classroom = None) -> bool
    def get_holidays(start_date: date, end_date: date) -> List[Holiday]
    def create_holiday(data: dict, user: User) -> Holiday
    def get_holidays_for_classroom(classroom: Classroom, start_date: date, end_date: date) -> List[Holiday]

# attendance/services/report_service.py
class ReportService:
    def generate_class_report(classroom: Classroom, start_date: date, end_date: date) -> dict
    def generate_student_report(student: Student, start_date: date, end_date: date) -> dict
    def export_pdf_class(classroom: Classroom, start_date: date, end_date: date) -> bytes
    def export_pdf_student(student: Student, start_date: date, end_date: date) -> bytes
    def export_excel(classrooms: List[Classroom], start_date: date, end_date: date) -> bytes
    def export_csv(classroom: Classroom, start_date: date, end_date: date) -> str
```

## Data Models

### New Models

```python
class DaySchedule(models.Model):
    """Configuration for JP count per day of week"""
    DAY_CHOICES = [
        (0, 'Senin'),
        (1, 'Selasa'),
        (2, 'Rabu'),
        (3, 'Kamis'),
        (4, 'Jumat'),
        (5, 'Sabtu'),
        (6, 'Minggu'),
    ]
    
    day_of_week = models.IntegerField(choices=DAY_CHOICES, unique=True, primary_key=True)
    day_name = models.CharField(max_length=10)
    default_jp_count = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    is_school_day = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)


class DailyAttendance(BaseModel):
    """Daily attendance record with JP statuses stored as JSON"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    jp_statuses = models.JSONField(
        default=dict,
        help_text='{"1": "H", "2": "H", "3": "S", ...}'
    )
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['student', 'date']),
        ]


class Holiday(BaseModel):
    """Holiday/non-school day configuration"""
    HOLIDAY_TYPES = [
        ('UAS', 'Ujian Akhir Semester'),
        ('UN', 'Ujian Nasional'),
        ('PESANTREN', 'Libur Pesantren'),
        ('LAINNYA', 'Lainnya'),
    ]
    
    date = models.DateField()
    name = models.CharField(max_length=100)
    holiday_type = models.CharField(max_length=20, choices=HOLIDAY_TYPES)
    apply_to_all = models.BooleanField(default=True)
    classrooms = models.ManyToManyField(Classroom, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['apply_to_all']),
        ]
```

### Model Relationships

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────┐
│ DaySchedule │       │ DailyAttendance │       │   Holiday   │
├─────────────┤       ├─────────────────┤       ├─────────────┤
│ day_of_week │       │ student (FK)────┼──────►│ date        │
│ day_name    │       │ date            │       │ name        │
│ jp_count    │       │ jp_statuses{}   │       │ type        │
│ is_school   │       │ recorded_by(FK) │       │ apply_to_all│
└─────────────┘       └────────┬────────┘       │ classrooms  │
                               │                └──────┬──────┘
                               ▼                       │
                      ┌─────────────┐                  │
                      │   Student   │                  │
                      ├─────────────┤                  │
                      │ classroom───┼──────────────────┘
                      │ name        │         (M2M)
                      │ student_id  │
                      └─────────────┘
```

## UI/UX Design

### Color Theme

```css
:root {
    /* Primary Colors - Elegant Brown */
    --primary: #8B7355;           /* Soft brown */
    --primary-dark: #6B5344;      /* Darker brown */
    --primary-light: #A89078;     /* Lighter brown */
    
    /* Background Colors */
    --bg-white: #FFFFFF;
    --bg-light: #F8F6F4;          /* Warm white */
    --bg-sidebar: #FAF8F6;        /* Sidebar background */
    
    /* Text Colors */
    --text-primary: #2D2A26;      /* Dark brown-black */
    --text-secondary: #6B6560;    /* Muted brown */
    --text-muted: #9B9590;        /* Light muted */
    
    /* Status Colors */
    --status-hadir: #4CAF50;      /* Green */
    --status-sakit: #FF9800;      /* Orange */
    --status-izin: #2196F3;       /* Blue */
    --status-alpa: #F44336;       /* Red */
    
    /* Border & Shadow */
    --border-color: #E8E4E0;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
    --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
}
```

### Attendance Input Grid UI

```
┌──────────────────────────────────────────────────────────────────┐
│  Input Absensi                                                   │
├──────────────────────────────────────────────────────────────────┤
│  Kelas: [7A (SMP) ▼]    Tanggal: [📅 12 Jan 2026]    [Load]     │
├──────────────────────────────────────────────────────────────────┤
│  ⚠️ Tanggal ini adalah hari libur: Libur Pesantren              │
├──────────────────────────────────────────────────────────────────┤
│  Quick Fill: [Semua H] [Semua S] [Semua I] [Semua A] [Reset]    │
├──────────────────────────────────────────────────────────────────┤
│  No │ NIS  │ Nama Siswa      │ JP1 │ JP2 │ JP3 │ JP4 │ JP5 │JP6 │
│  ───┼──────┼─────────────────┼─────┼─────┼─────┼─────┼─────┼────│
│  1  │ 001  │ Ahmad bin Ali   │ [H] │ [H] │ [H] │ [H] │ [H] │[H] │
│  2  │ 002  │ Budi Santoso    │ [H] │ [S] │ [S] │ [S] │ [S] │[S] │
│  3  │ 003  │ Citra Dewi      │ [H] │ [H] │ [I] │ [I] │ [H] │[H] │
│  ...│ ...  │ ...             │ ... │ ... │ ... │ ... │ ... │... │
├──────────────────────────────────────────────────────────────────┤
│  Ringkasan: H=150 S=12 I=8 A=2                                   │
│                                              [💾 Simpan Absensi] │
└──────────────────────────────────────────────────────────────────┘

Status Toggle: Click cell to cycle H → S → I → A → H
Color coding: H=green, S=orange, I=blue, A=red
```

### DataTable Component Features

```
┌──────────────────────────────────────────────────────────────────┐
│  Siswa                                           [+ Tambah]      │
├──────────────────────────────────────────────────────────────────┤
│  🔍 [Search...          ]                                        │
│  Filter: [Kelas ▼] [Status ▼] [Level ▼]           [Clear All]   │
├──────────────────────────────────────────────────────────────────┤
│  □ │ NIS ↕ │ Nama ↕        │ Kelas ↕ │ Status │ Aksi           │
│  ──┼───────┼───────────────┼─────────┼────────┼────────────────│
│  □ │ 001   │ Ahmad         │ 7A      │ ● Aktif│ [✏️] [🗑️]      │
│  □ │ 002   │ Budi          │ 7A      │ ● Aktif│ [✏️] [🗑️]      │
│  □ │ 003   │ Citra         │ 7B      │ ○ Non  │ [✏️] [🗑️]      │
├──────────────────────────────────────────────────────────────────┤
│  With selected: [Delete ▼] [Apply]                               │
│  [📥 CSV] [📥 Excel]              ◀ 1 2 3 ... 10 ▶  10/page ▼   │
└──────────────────────────────────────────────────────────────────┘

Features:
- Click column header to sort (↕ indicator)
- Inline edit: double-click cell to edit
- Bulk select with checkbox
- Export buttons for CSV/Excel
- Responsive: cards on mobile
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: DaySchedule JP Count Validation
*For any* DaySchedule record, the default_jp_count value must be between 1 and 10 inclusive. Any attempt to save a value outside this range should be rejected with a validation error.
**Validates: Requirements 1.1, 1.3**

### Property 2: DaySchedule Completeness
*For any* call to get all day schedules, the system should return exactly 7 records (one for each day of the week, 0-6).
**Validates: Requirements 1.2, 1.5**

### Property 3: JP Count Determination
*For any* valid date, the system should return the correct JP count based on the day of week from DaySchedule configuration.
**Validates: Requirements 1.5, 2.2**

### Property 4: Active Students Filter
*For any* classroom, when loading students for attendance input, only students with is_active=True should be returned.
**Validates: Requirements 2.1**

### Property 5: Status Toggle Cycle
*For any* attendance status, toggling should cycle through H → S → I → A → H in that exact order.
**Validates: Requirements 2.3**

### Property 6: Attendance JSON Validation
*For any* DailyAttendance record, the jp_statuses JSON field must contain only valid status values ('H', 'S', 'I', 'A') and the number of entries must match the DaySchedule jp_count for that day of week.
**Validates: Requirements 2.5, 10.1, 10.2**

### Property 7: Attendance Persistence Round-Trip
*For any* valid attendance data saved to the system, retrieving it by student and date should return the exact same jp_statuses values.
**Validates: Requirements 2.5, 2.6**

### Property 8: Past Date Acceptance
*For any* date in the past (including dates years ago), the system should accept attendance input without restriction or error.
**Validates: Requirements 2.7**

### Property 9: Holiday Detection
*For any* date and classroom combination, the is_holiday check should return True if either (a) a holiday exists with apply_to_all=True for that date, or (b) a holiday exists for that date with the specific classroom in its classrooms relation.
**Validates: Requirements 2.9, 3.6**

### Property 10: Holiday Type Validation
*For any* Holiday record, the holiday_type must be one of the valid choices: 'UAS', 'UN', 'PESANTREN', 'LAINNYA'.
**Validates: Requirements 3.5**

### Property 11: Apply To All Holiday Logic
*For any* Holiday with apply_to_all=True, the classrooms relation should be empty. Conversely, if apply_to_all=False, at least one classroom should be in the relation.
**Validates: Requirements 3.3**

### Property 12: Missing Attendance Calculation
*For any* classroom and date range, the missing attendance calculation should return dates that are (a) school days according to DaySchedule, (b) not holidays for that classroom, and (c) have no DailyAttendance records for any student in that classroom.
**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

### Property 13: Attendance Summary Calculation
*For any* set of DailyAttendance records for a student in a date range, the summary totals (H, S, I, A counts) should equal the sum of each status across all JP slots in all records.
**Validates: Requirements 5.3, 5.6**

### Property 14: Attendance Percentage Calculation
*For any* attendance summary, the percentage should equal (total_hadir / total_jp_slots) * 100, where total_jp_slots is the sum of JP counts across all attendance records.
**Validates: Requirements 5.4**

### Property 15: Excel Sheet Count
*For any* Excel export with N classrooms selected, the generated file should contain exactly N sheets (one per classroom).
**Validates: Requirements 6.2**

### Property 16: Search Filter Correctness
*For any* search query on a list view, all returned records should contain the search term in at least one of the searchable fields.
**Validates: Requirements 8.2**

### Property 17: Bulk Action Atomicity
*For any* bulk action (delete, update) on N selected items, either all N items should be processed successfully, or none should be modified (transaction rollback on error).
**Validates: Requirements 8.5, 10.5**

### Property 18: Role-Based Authorization
*For any* user with Guru role attempting to access admin-only endpoints (User management, Settings), the system should deny access and redirect to dashboard.
**Validates: Requirements 8.6, 9.2, 9.3, 9.4**

### Property 19: Attendance Uniqueness
*For any* student and date combination, there should be at most one DailyAttendance record. Attempting to create a duplicate should raise a validation error.
**Validates: Requirements 10.3**

### Property 20: Audit Field Population
*For any* record saved through the system, the created_at, updated_at, created_by, and updated_by fields should be automatically populated with the current timestamp and user.
**Validates: Requirements 10.4**

## Error Handling

### Validation Errors
- Invalid JP count (outside 1-10 range): Return 400 with field-specific error message
- Invalid attendance status: Return 400 with "Status harus H, S, I, atau A"
- Duplicate attendance record: Return 400 with "Absensi untuk siswa ini pada tanggal tersebut sudah ada"
- Missing required fields: Return 400 with field-specific error messages

### Authorization Errors
- Unauthorized access to admin features: Redirect to dashboard with flash message "Anda tidak memiliki akses ke halaman ini"
- Session expired: Redirect to login page

### Data Errors
- Student not found: Return 404 with "Siswa tidak ditemukan"
- Classroom not found: Return 404 with "Kelas tidak ditemukan"
- Invalid date format: Return 400 with "Format tanggal tidak valid"

### Export Errors
- No data for export: Return empty file with header row only
- Export generation failure: Return 500 with "Gagal membuat file export"

## Testing Strategy

### Unit Tests
- Model validation tests for all new models
- Service method tests with mocked dependencies
- View tests for HTTP responses and redirects
- Form validation tests

### Property-Based Tests
Using `hypothesis` library for Python:
- DaySchedule JP count validation (Property 1)
- Attendance JSON validation (Property 6)
- Status toggle cycle (Property 5)
- Holiday detection logic (Property 9)
- Missing attendance calculation (Property 12)
- Authorization checks (Property 18)

### Integration Tests
- End-to-end attendance input flow
- Export generation with real data
- Bulk operations with database transactions

### Test Configuration
- Minimum 100 iterations per property test
- Use factory_boy for test data generation
- Use pytest-django for Django integration
