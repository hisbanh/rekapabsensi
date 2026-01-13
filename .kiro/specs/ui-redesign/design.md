# Design Document: UI Redesign

## Overview

Redesign UI/UX aplikasi SIPA Yaumi dengan design modern, minimalis, dan user-friendly. Menggunakan color scheme biru/indigo, font Inter, ApexCharts untuk grafik interaktif, dan avatar component untuk identifikasi visual siswa.

## Architecture

### File Structure

```
static/
├── css/
│   ├── main.css              # Main stylesheet (new)
│   ├── components.css        # Reusable components
│   └── responsive.css        # Mobile responsive (update)
├── js/
│   └── app.js                # Main JavaScript (new)
templates/
├── base_new.html             # New base template
├── components/
│   ├── _sidebar_new.html     # New sidebar
│   ├── _avatar.html          # Avatar component (new)
│   ├── _stat_card.html       # Stat card component (new)
│   ├── _filter_bar.html      # Filter bar component (new)
│   └── _status_badge.html    # Status badge component (new)
├── attendance/
│   ├── dashboard_new.html    # Redesigned dashboard
│   ├── input_form_new.html   # Redesigned input form
│   ├── report_new.html       # Redesigned report
│   └── students_new.html     # Redesigned student list
```

### External Dependencies

```html
<!-- Google Fonts - Inter -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

<!-- ApexCharts -->
<script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>

<!-- Heroicons (for icons) -->
<!-- Using inline SVG or icon font -->
```

## Components and Interfaces

### Color Variables (CSS Custom Properties)

```css
:root {
  /* Primary */
  --primary-50: #EEF2FF;
  --primary-100: #E0E7FF;
  --primary-500: #6366F1;
  --primary-600: #4F46E5;
  --primary-700: #4338CA;
  
  /* Gray/Slate */
  --slate-50: #F8FAFC;
  --slate-100: #F1F5F9;
  --slate-200: #E2E8F0;
  --slate-300: #CBD5E1;
  --slate-400: #94A3B8;
  --slate-500: #64748B;
  --slate-600: #475569;
  --slate-700: #334155;
  --slate-800: #1E293B;
  --slate-900: #0F172A;
  
  /* Status Colors */
  --status-hadir: #22C55E;
  --status-hadir-bg: #DCFCE7;
  --status-sakit: #EAB308;
  --status-sakit-bg: #FEF9C3;
  --status-izin: #3B82F6;
  --status-izin-bg: #DBEAFE;
  --status-alpa: #EF4444;
  --status-alpa-bg: #FEE2E2;
  
  /* Spacing */
  --spacing-1: 0.25rem;
  --spacing-2: 0.5rem;
  --spacing-3: 0.75rem;
  --spacing-4: 1rem;
  --spacing-5: 1.25rem;
  --spacing-6: 1.5rem;
  --spacing-8: 2rem;
  
  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  --radius-full: 9999px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  
  /* Sidebar */
  --sidebar-width: 260px;
  --sidebar-collapsed-width: 64px;
}
```

### Component Templates

#### Avatar Component (_avatar.html)
```html
{% load attendance_extras %}
<div class="avatar" style="background-color: {{ name|avatar_color }}">
  {{ name|avatar_initials }}
</div>
```

#### Stat Card Component (_stat_card.html)
```html
<div class="stat-card">
  <div class="stat-icon" style="background-color: {{ icon_bg }}">
    {{ icon_svg|safe }}
  </div>
  <div class="stat-content">
    <span class="stat-label">{{ label }}</span>
    <span class="stat-value">{{ value }}</span>
  </div>
</div>
```

#### Status Badge Component (_status_badge.html)
```html
<button class="status-badge status-{{ status|lower }}" 
        data-student="{{ student_id }}" 
        data-status="{{ status }}">
  {{ status }}
</button>
```

### Template Tags (attendance_extras.py additions)

```python
@register.filter
def avatar_initials(name):
    """Generate 2-letter initials from name"""
    words = name.split()
    if len(words) >= 2:
        return (words[0][0] + words[1][0]).upper()
    return name[:2].upper()

@register.filter
def avatar_color(name):
    """Generate consistent color based on name hash"""
    colors = [
        '#6366F1', '#8B5CF6', '#EC4899', '#EF4444',
        '#F97316', '#EAB308', '#22C55E', '#14B8A6',
        '#06B6D4', '#3B82F6'
    ]
    hash_val = sum(ord(c) for c in name)
    return colors[hash_val % len(colors)]
```

## Data Models

Tidak ada perubahan model database. Redesign ini hanya mengubah tampilan frontend.

## UI/UX Design

### Layout Structure

```
┌─────────────────────────────────────────────────────────────────┐
│ ┌──────────┐ ┌────────────────────────────────────────────────┐ │
│ │          │ │  Header (optional - page title)                │ │
│ │          │ ├────────────────────────────────────────────────┤ │
│ │ SIDEBAR  │ │                                                │ │
│ │          │ │              MAIN CONTENT                      │ │
│ │ - Logo   │ │                                                │ │
│ │ - Menu   │ │  - Filter Bar                                  │ │
│ │ - User   │ │  - Cards / Tables / Charts                     │ │
│ │          │ │                                                │ │
│ └──────────┘ └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Sidebar Design

```
┌──────────────────┐
│  ┌──┐            │
│  │SY│ SIPA YAUMI │  <- Logo + App Name
│  └──┘            │
│  Sistem Informasi│  <- Subtitle (small)
├──────────────────┤
│                  │
│  📋 Absensi      │  <- Menu items with icons
│  👥 Data Santri  │
│  📊 Laporan      │  <- Active item highlighted
│  📈 Analisis     │
│                  │
├──────────────────┤
│  ⚙️ Pengaturan   │  <- Admin only
│  👤 Users        │
├──────────────────┤
│  ┌──┐            │
│  │AH│ Admin      │  <- User profile
│  └──┘ Logout     │
└──────────────────┘
```

### Dashboard Page

```
┌─────────────────────────────────────────────────────────────────┐
│  Analisis Kehadiran                    [📅 14/12/2025] → [📅]  │
│  Visualisasi performa berdasarkan rentang tanggal              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ 👥 278      │  │ 📈 85%      │  │ 🕐 Sakit    │             │
│  │ SANTRI AKTIF│  │ RATA-RATA   │  │ ALASAN UTAMA│             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────────────────┐  │
│  │ Proporsi Kehadiran  │  │ Persentase Per Kelas            │  │
│  │                     │  │                                 │  │
│  │    [DONUT CHART]    │  │      [BAR CHART]                │  │
│  │                     │  │                                 │  │
│  │  ● Hadir  ● Sakit   │  │  7-A  7-B  8-A  8-B  ...       │  │
│  │  ● Izin   ● Alpa    │  │                                 │  │
│  └─────────────────────┘  └─────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  Profil Kehadiran Personal          [🔍 Abdullah Muhammad...] │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  [HADIR] [SAKIT] [IZIN] [ALPA] [INDEKS]                 │   │
│  │    85%     5%     3%     7%     85%                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Input Absensi Page

```
┌─────────────────────────────────────────────────────────────────┐
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────────────────┐ │
│  │📅 TANGGAL    │ │🏫 KELAS      │ │⏰ JAM PELAJARAN (JP)    │ │
│  │ 13/01/2026   │ │ Kelas 7-A ▼  │ │ [1][2][3][4][5][6]     │ │
│  └──────────────┘ └──────────────┘ └─────────────────────────┘ │
│                                          [💾 Simpan JP 1]      │
├─────────────────────────────────────────────────────────────────┤
│  ⏱️ PRESENSI JAM PELAJARAN 1                   SELASA, 13 JAN  │
├─────────────────────────────────────────────────────────────────┤
│  NO │ NIS │ NAMA SANTRI              │ KEHADIRAN │ CATATAN     │
│  ───┼─────┼──────────────────────────┼───────────┼─────────────│
│  1  │  -  │ [A] Abdullah Muhammad    │ [H][S][I][A] │ [______] │
│  2  │  -  │ [A] Abdurrahman Sumardi  │ [H][S][I][A] │ [______] │
│  3  │  -  │ [A] Abidz Alvaro Bastian │ [H][S][I][A] │ [______] │
│  ...│ ... │ ...                      │ ...         │ ...       │
└─────────────────────────────────────────────────────────────────┘
```

### Laporan Page

```
┌─────────────────────────────────────────────────────────────────┐
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │📅 DARI       │ │📅 SAMPAI     │ │🏫 FILTER     │            │
│  │ 31/12/2025   │ │ 13/01/2026   │ │ Semua Kelas▼ │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                                    [📄 PDF] [📊 Excel]         │
├─────────────────────────────────────────────────────────────────┤
│  ⏱️ Rekapitulasi Total JP                        [278 SANTRI] │
├─────────────────────────────────────────────────────────────────┤
│  NO │ NIS        │ NAMA SANTRI          │KELAS│H(JP)│S│I│A│ % │
│  ───┼────────────┼──────────────────────┼─────┼─────┼─┼─┼─┼───│
│  1  │ 0323010001 │ Abdul Aziz Risay     │ 12  │  0  │0│0│0│ 0%│
│  2  │ -          │ Abdul Hakam As Syarif│ 7-B │  0  │0│0│0│ 0%│
│  3  │ 0323010002 │ Abdul Halim Mustaqim │ 12  │  0  │0│0│0│ 0%│
│  ...│ ...        │ ...                  │ ... │ ... │.│.│.│...│
└─────────────────────────────────────────────────────────────────┘
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system.*

### Property 1: Avatar Initials Consistency
*For any* student name, the avatar_initials filter should always return exactly 2 uppercase characters.
**Validates: Requirements 7.1, 7.2**

### Property 2: Avatar Color Consistency
*For any* student name, calling avatar_color multiple times should always return the same color.
**Validates: Requirements 7.2**

### Property 3: Status Badge State
*For any* attendance status selection, exactly one status (H, S, I, or A) should be active at a time per student per JP.
**Validates: Requirements 4.6, 4.7**

### Property 4: Responsive Breakpoint
*For any* screen width below 768px, the sidebar should be collapsed and hamburger menu visible.
**Validates: Requirements 8.2, 8.3**

### Property 5: Chart Data Consistency
*For any* date range filter, the chart data should match the table data totals.
**Validates: Requirements 3.5, 3.6, 9.2, 9.3**

## Error Handling

### UI Error States
- Empty data: Show "Tidak ada data" message with illustration
- Loading state: Show skeleton loaders for cards and tables
- Chart error: Show fallback message "Gagal memuat grafik"
- Form validation: Show inline error messages in red

### JavaScript Error Handling
- Wrap ApexCharts initialization in try-catch
- Graceful degradation if charts fail to load
- Console logging for debugging

## Testing Strategy

### Visual Testing
- Manual testing across different screen sizes
- Browser compatibility testing (Chrome, Firefox, Safari)
- Color contrast accessibility check

### Functional Testing
- Avatar generation with various name formats
- Status toggle functionality
- Chart rendering with different data sets
- Responsive behavior at breakpoints

### Unit Tests
- Template tag filters (avatar_initials, avatar_color)
- JavaScript utility functions

### Property-Based Tests
- Avatar initials always 2 characters
- Avatar color consistency
- Status badge mutual exclusivity
