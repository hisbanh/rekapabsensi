# Implementation Plan: JP Attendance System

## Overview

Implementasi sistem rekap absensi per Jam Pelajaran (JP) dengan Custom Admin Panel yang modern dan mobile-responsive. Menggunakan Python/Django dengan tema putih dan coklat elegant.

## Tasks

- [x] 1. Setup New Models and Database Schema
  - [x] 1.1 Create DaySchedule model with day_of_week, day_name, default_jp_count, is_school_day fields
    - Add validators for jp_count (1-10 range)
    - Create migration file
    - _Requirements: 1.1, 1.3_
  - [x] 1.2 Create DailyAttendance model with student FK, date, jp_statuses JSONField, recorded_by FK
    - Add unique_together constraint for (student, date)
    - Add indexes for performance
    - _Requirements: 2.5, 10.3_
  - [x] 1.3 Create Holiday model with date, name, holiday_type, apply_to_all, classrooms M2M
    - Add HOLIDAY_TYPES choices
    - _Requirements: 3.1, 3.5_
  - [x] 1.4 Create initial data migration for DaySchedule (7 days with default JP counts)
    - Senin-Kamis: 6 JP, Jumat: 4 JP, Sabtu: 6 JP, Minggu: 0 JP (not school day)
    - _Requirements: 1.2_
  - [ ]* 1.5 Write property tests for model validation
    - **Property 1: DaySchedule JP Count Validation**
    - **Property 6: Attendance JSON Validation**
    - **Property 10: Holiday Type Validation**
    - **Validates: Requirements 1.1, 1.3, 2.5, 3.5, 10.1, 10.2**

- [x] 2. Implement Service Layer
  - [x] 2.1 Create ScheduleService with get_jp_count_for_date, get_day_schedule, update_schedule methods
    - _Requirements: 1.4, 1.5_
  - [x] 2.2 Create AttendanceService with get_attendance, save_attendance, save_bulk_attendance, get_missing_attendance methods
    - _Requirements: 2.1, 2.5, 2.6, 4.1_
  - [x] 2.3 Create HolidayService with is_holiday, get_holidays, create_holiday methods
    - _Requirements: 3.3, 3.6_
  - [ ]* 2.4 Write property tests for service methods
    - **Property 3: JP Count Determination**
    - **Property 9: Holiday Detection**
    - **Property 12: Missing Attendance Calculation**
    - **Validates: Requirements 1.5, 2.2, 2.9, 3.6, 4.1, 4.2, 4.3**

- [x] 3. Checkpoint - Ensure models and services work correctly
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Create Base Template Components
  - [x] 4.1 Create new base.html with sidebar layout and brown/white color theme
    - Include CSS variables for theme colors
    - Add Font Awesome CDN
    - _Requirements: 7.1, 7.2, 7.3_
  - [x] 4.2 Create _sidebar.html component with navigation menu
    - Dashboard, Input Absensi, Laporan sections
    - Management section (Students, Classrooms, Holidays, Settings, Users)
    - Role-based menu visibility
    - _Requirements: 7.1_
  - [x] 4.3 Create _data_table.html reusable component
    - Search input, column sorting, pagination
    - Bulk action checkboxes
    - Export buttons (CSV, Excel)
    - _Requirements: 7.6, 7.8_
  - [x] 4.4 Create _pagination.html, _modal.html, _form_field.html, _alert.html components
    - _Requirements: 7.5_
  - [x] 4.5 Create responsive CSS for mobile devices
    - Collapsible sidebar on mobile
    - Card layout for tables on small screens
    - _Requirements: 7.4_

- [x] 5. Implement Attendance Input Feature
  - [x] 5.1 Create attendance input select view (choose classroom and date)
    - Dropdown for classroom selection
    - Date picker for date selection
    - _Requirements: 2.1_
  - [x] 5.2 Create attendance input form view with dynamic JP columns
    - Load students for selected classroom
    - Display JP columns based on DaySchedule
    - Show holiday warning if applicable
    - _Requirements: 2.1, 2.2, 2.9_
  - [x] 5.3 Implement status toggle JavaScript (click to cycle H→S→I→A→H)
    - Color coding for each status
    - _Requirements: 2.3_
  - [x] 5.4 Implement Quick Fill buttons (Semua H, Semua S, Semua I, Semua A)
    - _Requirements: 2.4_
  - [x] 5.5 Create AJAX endpoint for saving attendance data
    - Validate and save jp_statuses JSON
    - Handle existing record updates
    - _Requirements: 2.5, 2.6_
  - [ ]* 5.6 Write property tests for attendance input
    - **Property 5: Status Toggle Cycle**
    - **Property 7: Attendance Persistence Round-Trip**
    - **Property 8: Past Date Acceptance**
    - **Validates: Requirements 2.3, 2.5, 2.6, 2.7**

- [x] 6. Checkpoint - Ensure attendance input works correctly
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement Dashboard with Missing Input Warning
  - [x] 7.1 Update dashboard view to calculate missing attendance per classroom
    - Get school days from DaySchedule
    - Exclude holidays
    - Compare against existing DailyAttendance records
    - _Requirements: 4.1, 4.2, 4.3_
  - [x] 7.2 Create dashboard template with warning section
    - Display classes with missing dates
    - Show success message when all complete
    - _Requirements: 4.4, 4.5_
  - [ ]* 7.3 Write property tests for missing attendance calculation
    - **Property 12: Missing Attendance Calculation**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

- [x] 8. Implement Management CRUD Pages
  - [x] 8.1 Create base_list.html and base_form.html templates for management pages
    - Extend from base.html
    - Include breadcrumb navigation
    - _Requirements: 8.7_
  - [x] 8.2 Implement Student management (list, create, edit, delete)
    - Search by name, NIS
    - Filter by classroom, status
    - Inline edit for quick updates
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  - [x] 8.3 Implement Classroom management (list, create, edit, delete)
    - _Requirements: 8.1_
  - [x] 8.4 Implement Holiday management (list, create, edit, delete)
    - Dropdown for "Semua Kelas" / "Pilih Kelas Tertentu"
    - Multi-select for classrooms
    - _Requirements: 3.2, 3.4, 8.1_
  - [x] 8.5 Implement Day Schedule settings page
    - Display all 7 days with JP count inputs
    - Save button to update all schedules
    - _Requirements: 1.2, 1.4_
  - [x] 8.6 Implement User management (Admin only)
    - List users with role display
    - Create/edit user with role assignment
    - _Requirements: 8.1, 8.6_
  - [x] 8.7 Implement bulk actions (delete, activate, deactivate)
    - Transaction-based processing
    - _Requirements: 8.5_
  - [ ]* 8.8 Write property tests for CRUD operations
    - **Property 16: Search Filter Correctness**
    - **Property 17: Bulk Action Atomicity**
    - **Property 19: Attendance Uniqueness**
    - **Validates: Requirements 8.2, 8.5, 10.3, 10.5**

- [x] 9. Checkpoint - Ensure management pages work correctly
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement Authorization
  - [x] 10.1 Create custom permission decorators for Admin and Guru roles
    - @admin_required decorator
    - @login_required decorator (existing Django)
    - _Requirements: 9.1_
  - [x] 10.2 Apply permission checks to all views
    - Guru: Dashboard, Input, Report, read-only management
    - Admin: Full access including Settings and Users
    - _Requirements: 9.2, 9.3_
  - [x] 10.3 Implement redirect with permission denied message
    - _Requirements: 9.4_
  - [ ]* 10.4 Write property tests for authorization
    - **Property 18: Role-Based Authorization**
    - **Validates: Requirements 8.6, 9.2, 9.3, 9.4**

- [ ] 11. Implement Report Service
  - [ ] 11.1 Create ReportService with generate_class_report and generate_student_report methods
    - Calculate totals and percentages
    - _Requirements: 5.3, 5.4, 5.6_
  - [ ] 11.2 Create report page with date range filter and export options
    - Select classroom or student
    - Date range picker
    - Export buttons (PDF, Excel, CSV)
    - _Requirements: 5.1, 6.1_
  - [ ]* 11.3 Write property tests for report calculations
    - **Property 13: Attendance Summary Calculation**
    - **Property 14: Attendance Percentage Calculation**
    - **Validates: Requirements 5.3, 5.4, 5.6**

- [ ] 12. Implement PDF Export
  - [ ] 12.1 Install and configure ReportLab or WeasyPrint for PDF generation
    - Add to requirements.txt
    - _Requirements: 5.1_
  - [ ] 12.2 Implement export_pdf_class method
    - Table with students as rows, dates as columns
    - Summary section with H/S/I/A totals per student
    - Class summary with average percentage
    - _Requirements: 5.2, 5.3, 5.4_
  - [ ] 12.3 Implement export_pdf_student method
    - Detailed view with dates as rows, JP columns
    - Summary with totals and percentages
    - _Requirements: 5.5, 5.6_
  - [ ] 12.4 Create PDF export endpoint
    - _Requirements: 5.7_

- [ ] 13. Implement Excel/CSV Export
  - [ ] 13.1 Install and configure openpyxl for Excel generation
    - Add to requirements.txt
    - _Requirements: 6.1_
  - [ ] 13.2 Implement export_excel method
    - Separate sheets per classroom
    - SUM and COUNTIF formulas
    - Conditional formatting (red=Alpa, orange=Sakit, blue=Izin)
    - _Requirements: 6.2, 6.3, 6.4, 6.5_
  - [ ] 13.3 Implement export_csv method
    - Simple CSV format
    - _Requirements: 6.6_
  - [ ] 13.4 Create export endpoints and integrate with report page
    - _Requirements: 6.1_
  - [ ]* 13.5 Write property tests for Excel export
    - **Property 15: Excel Sheet Count**
    - **Validates: Requirements 6.2**

- [ ] 14. Implement Inline Edit Feature
  - [ ] 14.1 Create AJAX endpoint for inline edit
    - Accept field name and new value
    - Validate and save
    - Return updated value
    - _Requirements: 7.7_
  - [ ] 14.2 Add JavaScript for inline edit in DataTable
    - Double-click to edit
    - Enter to save, Escape to cancel
    - _Requirements: 7.7_

- [ ] 15. Implement Audit Fields
  - [ ] 15.1 Update BaseModel to auto-populate created_by, updated_by fields
    - Use middleware or signal to get current user
    - _Requirements: 10.4_
  - [ ]* 15.2 Write property tests for audit fields
    - **Property 20: Audit Field Population**
    - **Validates: Requirements 10.4**

- [ ] 16. Final Checkpoint - Full System Testing
  - Ensure all tests pass, ask the user if questions arise.
  - Manual testing of all features
  - Mobile responsiveness testing

## Notes

- Tasks marked with `*` are optional property-based tests that can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Use Python's `hypothesis` library for property-based testing
- Use `factory_boy` for test data generation
