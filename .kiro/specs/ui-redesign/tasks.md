# Implementation Plan: UI Redesign

## Overview

Implementasi redesign UI/UX aplikasi SIPA Yaumi dengan design modern menggunakan color scheme biru/indigo, font Inter, ApexCharts, dan avatar component.

## Tasks

- [x] 1. Setup Design System Foundation
  - [x] 1.1 Create main.css with CSS custom properties (colors, spacing, shadows)
    - Define all color variables
    - Define spacing and border-radius variables
    - Define shadow variables
    - _Requirements: 1.1-1.10_
  - [x] 1.2 Add Google Fonts (Inter) to base template
    - _Requirements: 1.1_
  - [x] 1.3 Create components.css for reusable component styles
    - Button styles
    - Card styles
    - Input styles
    - Table styles
    - _Requirements: 1.9, 10.1-10.6_

- [x] 2. Implement Template Tags for Avatar
  - [x] 2.1 Add avatar_initials filter to attendance_extras.py
    - Generate 2-letter initials from name
    - _Requirements: 7.1, 7.4, 7.5_
  - [x] 2.2 Add avatar_color filter to attendance_extras.py
    - Generate consistent color based on name hash
    - _Requirements: 7.2, 7.3_
  - [ ]* 2.3 Write property tests for avatar filters
    - **Property 1: Avatar Initials Consistency**
    - **Property 2: Avatar Color Consistency**
    - **Validates: Requirements 7.1, 7.2**

- [x] 3. Create New Base Template
  - [x] 3.1 Create base_new.html with new layout structure
    - Include Inter font
    - Include ApexCharts CDN
    - Sidebar + main content layout
    - _Requirements: 2.1, 2.2_
  - [x] 3.2 Create _sidebar_new.html component
    - Logo section with "SY" badge
    - Navigation menu with icons
    - Active state highlighting
    - User profile section
    - _Requirements: 2.1-2.7_
  - [x] 3.3 Update responsive.css for new layout
    - Sidebar collapse on mobile
    - Hamburger menu toggle
    - _Requirements: 8.1-8.6_

- [x] 4. Checkpoint - Verify base layout works
  - Ensure base template renders correctly
  - Test sidebar navigation
  - Test responsive behavior

- [x] 5. Create Reusable Components
  - [x] 5.1 Create _avatar.html component
    - Circle with initials
    - Colored background
    - _Requirements: 7.1-7.5_
  - [x] 5.2 Create _stat_card.html component
    - Icon with colored background
    - Label and value
    - _Requirements: 3.3, 3.4_
  - [x] 5.3 Create _status_badge.html component
    - H/S/I/A buttons with colors
    - Click to select functionality
    - _Requirements: 4.5, 4.6, 4.7_
  - [x] 5.4 Create _filter_bar.html component
    - Date pickers
    - Dropdown filters
    - Action buttons
    - _Requirements: 3.2, 4.1, 5.1, 5.2_

- [x] 6. Redesign Dashboard/Analisis Page
  - [x] 6.1 Create dashboard_new.html template
    - Page title and date range picker
    - 3 stat cards row
    - _Requirements: 3.1-3.4_
  - [x] 6.2 Implement ApexCharts donut chart for attendance proportion
    - H/S/I/A breakdown
    - Animated on load
    - _Requirements: 3.5, 9.1-9.5_
  - [x] 6.3 Implement ApexCharts bar chart for per-class percentage
    - Class names on x-axis
    - Percentage on y-axis
    - _Requirements: 3.6, 9.1-9.5_
  - [x] 6.4 Implement student search with personal stats
    - Search dropdown
    - Individual attendance display
    - _Requirements: 3.7, 3.8_
  - [x] 6.5 Update dashboard view to provide chart data as JSON
    - _Requirements: 3.5, 3.6_

- [x] 7. Checkpoint - Verify dashboard works
  - Test stat cards display
  - Test charts render correctly
  - Test student search functionality

- [x] 8. Redesign Input Absensi Page
  - [x] 8.1 Create input_form_new.html template
    - Filter bar with date, class, JP selector
    - Simpan button
    - _Requirements: 4.1, 4.2_
  - [x] 8.2 Implement attendance table with avatars
    - Student rows with avatar initials
    - Status badge buttons
    - Notes input field
    - _Requirements: 4.3-4.8_
  - [x] 8.3 Implement JavaScript for status toggle
    - Click to select status
    - Visual feedback on selection
    - _Requirements: 4.6, 4.7_
  - [x] 8.4 Update input view to use new template
    - _Requirements: 4.1-4.8_

- [x] 9. Redesign Laporan Page
  - [x] 9.1 Create report_new.html template
    - Filter bar with date range and class filter
    - PDF and Excel export buttons
    - _Requirements: 5.1, 5.2_
  - [x] 9.2 Implement rekapitulasi table
    - Columns: No, NIS, Nama, Kelas, H, S, I, A, %
    - Colored status counts
    - Progress bar for percentage
    - _Requirements: 5.3-5.7_
  - [x] 9.3 Update report view to use new template
    - _Requirements: 5.1-5.7_

- [x] 10. Redesign Data Santri Page
  - [x] 10.1 Create students_new.html template
    - Page title and Tambah Santri button
    - Search input and class filter
    - _Requirements: 6.1-6.4_
  - [x] 10.2 Implement student table with avatars
    - Avatar with initials
    - Edit and delete action icons
    - _Requirements: 6.5-6.9_
  - [x] 10.3 Update student list view to use new template
    - _Requirements: 6.1-6.9_

- [ ] 11. Checkpoint - Verify all pages work
  - Test all page navigation
  - Test all interactive elements
  - Test form submissions

- [ ] 12. Implement JavaScript Interactions
  - [ ] 12.1 Create app.js with utility functions
    - Sidebar toggle for mobile
    - Status badge click handlers
    - _Requirements: 2.5, 4.6_
  - [ ] 12.2 Implement chart initialization functions
    - Donut chart config
    - Bar chart config
    - _Requirements: 9.1-9.6_
  - [ ] 12.3 Implement form enhancements
    - Date picker styling
    - Dropdown styling
    - _Requirements: 10.1-10.6_

- [ ] 13. Final Polish and Testing
  - [ ] 13.1 Test responsive design on all breakpoints
    - Mobile (320px-767px)
    - Tablet (768px-1023px)
    - Desktop (1024px+)
    - _Requirements: 8.1-8.6_
  - [ ] 13.2 Test cross-browser compatibility
    - Chrome, Firefox, Safari
  - [ ] 13.3 Verify color contrast accessibility
    - _Requirements: 1.2-1.8_

- [ ] 14. Switch to New Templates
  - [ ] 14.1 Update URL routing to use new templates
    - Update views to render new templates
  - [ ] 14.2 Remove or archive old templates
  - [ ] 14.3 Final testing of complete flow

- [ ] 15. Final Checkpoint
  - Ensure all pages render correctly
  - Ensure all functionality works
  - Manual testing of complete user flow

## Notes

- Tasks marked with `*` are optional property-based tests
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- New templates use `_new` suffix during development, then replace originals
- ApexCharts loaded from CDN for simplicity
