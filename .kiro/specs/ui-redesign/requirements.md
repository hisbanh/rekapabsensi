# Requirements Document

## Introduction

Redesign UI/UX aplikasi SIPA Yaumi agar lebih modern, minimalis, dan user-friendly. Design mengacu pada referensi sipayaumi.vercel.app dengan warna biru/indigo, font Inter, dan komponen modern seperti ApexCharts untuk grafik interaktif.

## Glossary

- **System**: Aplikasi SIPA Yaumi (Sistem Informasi Presensi Absensi)
- **User**: Pengguna aplikasi (Admin/Guru)
- **Dashboard**: Halaman utama dengan statistik dan grafik
- **Sidebar**: Menu navigasi di sisi kiri
- **Card**: Komponen kotak dengan shadow untuk menampilkan informasi
- **Avatar**: Lingkaran dengan inisial nama untuk identifikasi visual
- **Badge**: Label kecil berwarna untuk status (H/S/I/A)
- **ApexCharts**: Library JavaScript untuk grafik interaktif

## Requirements

### Requirement 1: Design System & Color Scheme

**User Story:** As a user, I want a consistent and modern visual design, so that the application feels professional and easy to use.

#### Acceptance Criteria

1. THE System SHALL use Inter font family from Google Fonts for all text
2. THE System SHALL use indigo/blue (#4F46E5) as primary color
3. THE System SHALL use white (#FFFFFF) as main background color
4. THE System SHALL use slate gray (#64748B) for secondary text
5. THE System SHALL use green (#22C55E) for Hadir status
6. THE System SHALL use yellow (#EAB308) for Sakit status
7. THE System SHALL use blue (#3B82F6) for Izin status
8. THE System SHALL use red (#EF4444) for Alpa status
9. THE System SHALL apply consistent border-radius (8px for cards, 6px for buttons)
10. THE System SHALL use subtle box-shadow for card elevation

### Requirement 2: Sidebar Navigation

**User Story:** As a user, I want a clean sidebar navigation, so that I can easily access all features.

#### Acceptance Criteria

1. THE System SHALL display a vertical sidebar on the left side
2. THE System SHALL show logo "SY" with app name "SIPA YAUMI" at the top of sidebar
3. THE System SHALL display navigation items with icons: Absensi, Data Santri, Laporan, Analisis
4. THE System SHALL highlight active menu item with primary color background
5. THE System SHALL collapse sidebar on mobile devices with hamburger menu toggle
6. WHEN user clicks a menu item, THE System SHALL navigate to the corresponding page
7. THE System SHALL show user profile section at bottom of sidebar

### Requirement 3: Dashboard/Analisis Page

**User Story:** As a user, I want to see attendance analytics at a glance, so that I can monitor overall performance.

#### Acceptance Criteria

1. THE System SHALL display page title "Analisis Kehadiran" with subtitle
2. THE System SHALL provide date range picker (Dari Tanggal - Sampai Tanggal)
3. THE System SHALL display 3 stat cards: Santri Aktif, Rata-rata Kehadiran, Alasan Utama Absen
4. WHEN stat cards load, THE System SHALL show icon with colored background circle
5. THE System SHALL display "Proporsi Kehadiran" donut chart using ApexCharts
6. THE System SHALL display "Persentase Per Kelas" bar chart using ApexCharts
7. THE System SHALL display "Profil Kehadiran Personal" section with student search
8. WHEN user selects a student, THE System SHALL show individual attendance stats

### Requirement 4: Input Absensi Page

**User Story:** As a guru, I want a clean attendance input interface, so that I can quickly record attendance.

#### Acceptance Criteria

1. THE System SHALL display filter bar with: Tanggal, Kelas dropdown, JP selector (1-6 buttons)
2. THE System SHALL display "Simpan JP X" button with primary color
3. THE System SHALL display attendance table with columns: No, NIS, Nama Santri, Kehadiran (JP X), Catatan
4. WHEN displaying student name, THE System SHALL show avatar with initials and colored background
5. THE System SHALL display H/S/I/A buttons as colored badges for each student
6. WHEN user clicks a status badge, THE System SHALL toggle/select that status
7. THE System SHALL highlight selected status with darker shade
8. THE System SHALL provide optional notes input field per student

### Requirement 5: Laporan Page

**User Story:** As a user, I want to view and export attendance reports, so that I can analyze and share data.

#### Acceptance Criteria

1. THE System SHALL display filter bar with: Dari Tanggal, Sampai Tanggal, Filter Kelas dropdown
2. THE System SHALL display PDF export button (red) and Excel export button (green)
3. THE System SHALL display "Rekapitulasi Total JP" table
4. THE System SHALL show columns: No, NIS, Nama Santri, Kelas, H(JP), S(JP), I(JP), A(JP), %
5. THE System SHALL display attendance counts with colored text (green/yellow/blue/red)
6. THE System SHALL show percentage with progress bar indicator
7. THE System SHALL display total student count badge (e.g., "278 SANTRI")

### Requirement 6: Data Santri Page

**User Story:** As an admin, I want to manage student data with a modern interface, so that I can easily add, edit, and search students.

#### Acceptance Criteria

1. THE System SHALL display page title "Database Santri" with subtitle
2. THE System SHALL display "Tambah Santri" button with primary color
3. THE System SHALL provide search input with placeholder "Cari nama santri atau NISN..."
4. THE System SHALL provide class filter dropdown
5. THE System SHALL display student table with columns: No, Nama Lengkap, NISN, Kelas, Aksi
6. WHEN displaying student name, THE System SHALL show avatar with initials
7. THE System SHALL display edit (pencil) and delete (trash) action icons
8. WHEN user clicks edit, THE System SHALL open edit form/modal
9. WHEN user clicks delete, THE System SHALL show confirmation dialog

### Requirement 7: Avatar Component

**User Story:** As a user, I want visual identification for students, so that I can quickly recognize entries.

#### Acceptance Criteria

1. THE System SHALL generate avatar from first 2 letters of student name
2. THE System SHALL assign consistent color based on name hash
3. THE System SHALL display avatar as circle with 32px diameter
4. THE System SHALL use white text on colored background
5. THE System SHALL use font-weight 600 for avatar text

### Requirement 8: Responsive Design

**User Story:** As a user, I want to use the application on mobile devices, so that I can access it anywhere.

#### Acceptance Criteria

1. THE System SHALL be fully responsive for screens 320px and above
2. WHEN screen width is below 768px, THE System SHALL collapse sidebar
3. WHEN screen width is below 768px, THE System SHALL show hamburger menu icon
4. THE System SHALL stack filter inputs vertically on mobile
5. THE System SHALL make tables horizontally scrollable on mobile
6. THE System SHALL adjust card layouts to single column on mobile

### Requirement 9: Interactive Charts

**User Story:** As a user, I want interactive charts, so that I can explore data visually.

#### Acceptance Criteria

1. THE System SHALL use ApexCharts library for all charts
2. THE System SHALL display donut chart for attendance proportion (H/S/I/A)
3. THE System SHALL display bar chart for per-class attendance percentage
4. WHEN user hovers on chart, THE System SHALL show tooltip with details
5. THE System SHALL animate charts on initial load
6. THE System SHALL use consistent color scheme matching status colors

### Requirement 10: Form Components

**User Story:** As a user, I want modern form inputs, so that data entry feels smooth.

#### Acceptance Criteria

1. THE System SHALL style all inputs with border-radius 6px
2. THE System SHALL use subtle border color (#E2E8F0) for inputs
3. THE System SHALL show focus state with primary color border
4. THE System SHALL style dropdowns consistently with other inputs
5. THE System SHALL use modern date picker styling
6. THE System SHALL display form validation errors in red below inputs
