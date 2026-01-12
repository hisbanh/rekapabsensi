# Requirements Document

## Introduction

Sistem Rekap Absensi Per Jam Pelajaran (JP) untuk Pesantren Yaumi. Sistem ini menggantikan Django Admin dengan Custom Admin Panel yang modern, user-friendly, dan mobile responsive. Guru dapat menginput absensi per JP (Jam Pelajaran) dengan jumlah JP yang fleksibel per hari, serta mengekspor laporan dalam format PDF dan Excel.

## Glossary

- **System**: Aplikasi SIPA YAUMI (Sistem Informasi Presensi Absensi Yaumi)
- **Admin**: User dengan hak akses penuh untuk mengelola semua data dan pengaturan
- **Guru**: User yang dapat menginput absensi dan melihat laporan
- **JP**: Jam Pelajaran - slot waktu pembelajaran dalam sehari
- **DailyAttendance**: Record absensi harian per siswa dengan status per JP
- **DaySchedule**: Konfigurasi jumlah JP per hari dalam seminggu
- **Holiday**: Hari libur yang dikecualikan dari input absensi
- **Classroom**: Kelas tempat siswa belajar
- **Student**: Santri/siswa yang diabsen
- **AttendanceStatus**: Status kehadiran (H=Hadir, S=Sakit, I=Izin, A=Alpa)

## Requirements

### Requirement 1: Day Schedule Configuration

**User Story:** As an admin, I want to configure the number of JP per day of the week, so that the attendance input form dynamically adjusts to the correct number of JP slots.

#### Acceptance Criteria

1. THE System SHALL provide a DaySchedule model storing day_of_week (0-6), day_name, default_jp_count (1-10), and is_school_day flag
2. WHEN an admin accesses the settings page, THE System SHALL display all 7 days with their current JP configuration
3. WHEN an admin updates the JP count for a day, THE System SHALL validate that jp_count is between 1 and 10
4. WHEN an admin saves the day schedule, THE System SHALL persist the changes and reflect them in attendance input forms
5. THE System SHALL use the DaySchedule configuration to determine how many JP columns to display in the attendance input form

### Requirement 2: Daily Attendance Input

**User Story:** As a guru, I want to input attendance for all students in a class for a specific date with all JP slots at once, so that I can efficiently record attendance from paper sheets.

#### Acceptance Criteria

1. WHEN a guru selects a classroom and date, THE System SHALL load all active students in that classroom
2. WHEN the attendance form loads, THE System SHALL display JP columns based on the DaySchedule for that day of week
3. WHEN a guru clicks on a status cell, THE System SHALL toggle through statuses: H → S → I → A → H
4. WHEN a guru uses Quick Fill buttons, THE System SHALL set all visible cells to the selected status (H, S, I, or A)
5. WHEN a guru submits the attendance form, THE System SHALL save all attendance records with jp_statuses as JSON field
6. WHEN attendance already exists for a student on that date, THE System SHALL load existing data for editing
7. THE System SHALL allow input for any past date without restriction
8. THE System SHALL allow input on Sundays without warning
9. IF the selected date is marked as a holiday for the classroom, THEN THE System SHALL display a warning but still allow input

### Requirement 3: Holiday Management

**User Story:** As an admin, I want to mark specific dates as holidays for all or selected classrooms, so that the system can track non-school days.

#### Acceptance Criteria

1. THE System SHALL provide a Holiday model with date, name, holiday_type, apply_to_all flag, and optional classroom relations
2. WHEN an admin creates a holiday, THE System SHALL provide a dropdown to select "Semua Kelas" or "Pilih Kelas Tertentu"
3. WHEN "Semua Kelas" is selected, THE System SHALL set apply_to_all to True and clear classroom relations
4. WHEN "Pilih Kelas Tertentu" is selected, THE System SHALL allow multi-select of classrooms
5. THE System SHALL support holiday types: UAS, UN, PESANTREN, LAINNYA
6. WHEN checking if a date is a holiday for a classroom, THE System SHALL check both apply_to_all holidays and classroom-specific holidays

### Requirement 4: Dashboard with Missing Input Warning

**User Story:** As a guru, I want to see which classes have missing attendance input for the current week, so that I can prioritize data entry.

#### Acceptance Criteria

1. WHEN a user views the dashboard, THE System SHALL display a warning section showing classes with missing attendance this week
2. THE System SHALL calculate missing days by comparing school days (from DaySchedule) against existing DailyAttendance records
3. THE System SHALL exclude holidays when calculating missing days
4. WHEN a class has missing attendance, THE System SHALL display the class name and list of missing dates
5. WHEN all classes have complete attendance, THE System SHALL display a success message

### Requirement 5: PDF Export

**User Story:** As a guru, I want to export attendance reports as PDF in multiple formats, so that I can print and archive physical copies.

#### Acceptance Criteria

1. THE System SHALL provide PDF export with date range filter (start_date, end_date)
2. WHEN exporting per-class PDF, THE System SHALL generate a table with students as rows and dates as columns, showing daily attendance summary
3. WHEN exporting per-class PDF, THE System SHALL include a summary section with total H/S/I/A counts and percentage per student
4. WHEN exporting per-class PDF, THE System SHALL include a class summary with average attendance percentage
5. WHEN exporting per-student PDF, THE System SHALL generate a detailed view with dates as rows and JP columns showing individual status
6. WHEN exporting per-student PDF, THE System SHALL include a summary with total and percentage for each status type
7. THE System SHALL generate PDF without school letterhead (clean format)

### Requirement 6: Excel Export

**User Story:** As a guru, I want to export attendance data as Excel with advanced features, so that I can perform further analysis.

#### Acceptance Criteria

1. THE System SHALL provide Excel export with date range filter (start_date, end_date)
2. WHEN exporting Excel, THE System SHALL create separate sheets per classroom
3. WHEN exporting Excel, THE System SHALL include raw data suitable for pivot table analysis
4. WHEN exporting Excel, THE System SHALL include SUM and COUNTIF formulas for automatic totals
5. WHEN exporting Excel, THE System SHALL apply conditional formatting (red for Alpa, orange for Sakit, blue for Izin)
6. THE System SHALL also support CSV export for simple data extraction

### Requirement 7: Custom Admin Panel - Base Components

**User Story:** As a developer, I want reusable UI components for the custom admin panel, so that I can build consistent and maintainable management pages.

#### Acceptance Criteria

1. THE System SHALL provide a base layout template with sidebar navigation and content area
2. THE System SHALL use a color theme of white background with elegant soft brown accents
3. THE System SHALL use Font Awesome icons throughout the interface
4. THE System SHALL be fully responsive for mobile devices
5. THE System SHALL provide reusable template components: data table, form, modal, pagination, filters
6. THE System SHALL provide a reusable DataTable component with search, sort, filter, pagination, and bulk actions
7. THE System SHALL provide inline edit capability in DataTable for quick updates
8. THE System SHALL provide export buttons (CSV, Excel) in list views

### Requirement 8: Custom Admin Panel - CRUD Operations

**User Story:** As an admin, I want to manage all system entities through a modern custom admin interface, so that I don't need to use Django Admin.

#### Acceptance Criteria

1. THE System SHALL provide CRUD pages for: Students, Classrooms, Academic Levels, Holidays, Day Schedules, Users
2. WHEN viewing a list page, THE System SHALL display a searchable, sortable, filterable data table
3. WHEN creating or editing an entity, THE System SHALL display a clean form with validation
4. WHEN deleting an entity, THE System SHALL show a confirmation modal
5. WHEN performing bulk actions, THE System SHALL process selected items and show result feedback
6. THE System SHALL restrict User management to Admin role only
7. THE System SHALL provide breadcrumb navigation for all management pages

### Requirement 9: Authentication and Authorization

**User Story:** As a system administrator, I want role-based access control, so that users can only access features appropriate to their role.

#### Acceptance Criteria

1. THE System SHALL support two roles: Admin and Guru
2. WHEN a Guru logs in, THE System SHALL allow access to: Dashboard, Input Absensi, Laporan, and read-only management views
3. WHEN an Admin logs in, THE System SHALL allow full access to all features including Settings and User management
4. IF a user without Admin role attempts to access admin-only features, THEN THE System SHALL redirect to dashboard with permission denied message
5. THE System SHALL use Django's built-in authentication with custom permission checks

### Requirement 10: Data Persistence and Validation

**User Story:** As a system user, I want data to be properly validated and persisted, so that the system maintains data integrity.

#### Acceptance Criteria

1. WHEN saving DailyAttendance, THE System SHALL validate that jp_statuses JSON contains only valid status values (H, S, I, A)
2. WHEN saving DailyAttendance, THE System SHALL validate that the number of JP entries matches the DaySchedule for that day
3. THE System SHALL enforce unique constraint on DailyAttendance (student, date) combination
4. WHEN saving any record, THE System SHALL track created_by, updated_by, created_at, updated_at fields
5. THE System SHALL use database transactions for bulk operations to ensure atomicity
