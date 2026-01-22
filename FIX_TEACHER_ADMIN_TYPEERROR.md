# Fix: TypeError di Django Admin Teacher Edit

## Problem
Ketika mencoba edit teacher di Django admin panel (`/admin/attendance/teacher/{id}/change/`), muncul error:
```
TypeError: args or kwargs must be provided.
```

## Root Cause
Error terjadi di method `photo_preview_large` dalam `TeacherAdmin`. Masalahnya adalah penggunaan `format_html()` tanpa placeholder `{}` untuk string HTML statis.

Django's `format_html()` function memerlukan:
- Format string dengan placeholder `{}`
- Argumen untuk mengisi placeholder tersebut

Ketika tidak ada placeholder (HTML statis), `format_html()` akan throw error "args or kwargs must be provided."

Contoh yang salah:
```python
return format_html('<div>Static HTML</div>')  # ERROR!
```

Contoh yang benar:
```python
return format_html('<div>{}</div>', 'content')  # OK
# atau
return mark_safe('<div>Static HTML</div>')  # OK
```

## Solution
Mengubah `format_html()` menjadi `mark_safe()` untuk HTML statis yang tidak memiliki placeholder di method `photo_preview` dan `photo_preview_large`:

```python
def photo_preview_large(self, obj):
    """Display larger photo preview in detail view"""
    from django.utils.safestring import mark_safe
    if obj and obj.photo:
        return format_html(
            '<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 8px; object-fit: cover;" />',
            obj.photo.url
        )
    # Use mark_safe for static HTML without placeholders
    return mark_safe('<div style="width: 200px; height: 200px; border-radius: 8px; background: #e5e7eb; display: flex; align-items: center; justify-content: center; color: #6b7280; font-size: 48px;">👤</div>')
```

### Additional Fixes:
1. **Added null check**: `if obj and obj.photo` untuk mencegah error jika obj adalah None
2. **Improved error handling**: Added try-except di `teaching_load_display`
3. **Added formfield_for_foreignkey**: Filter queryset untuk field `user` agar hanya menampilkan user yang available

## Files Modified
- `attendance/admin.py` - Updated `TeacherAdmin` class methods

## Benefits
1. ✓ Admin panel teacher edit page berfungsi tanpa error
2. ✓ Photo preview ditampilkan dengan benar (atau placeholder jika tidak ada foto)
3. ✓ Field user hanya menampilkan user yang available
4. ✓ Semua display methods handle edge cases dengan baik

## Testing
Verified dengan:
1. ✓ Django system check passes
2. ✓ All admin display methods work correctly
3. ✓ Admin change page returns 200 status
4. ✓ Photo preview displays correctly for teachers with/without photos

## Status
**FIXED** - Django admin teacher edit page sekarang berfungsi dengan sempurna.

## How to Test
1. Login sebagai superuser
2. Buka http://127.0.0.1:8001/admin/attendance/teacher/
3. Klik salah satu teacher untuk edit
4. Form edit teacher akan muncul tanpa error
5. Photo preview akan muncul (atau placeholder jika tidak ada foto)
6. Semua field dapat diedit dengan normal

## Technical Notes
- `format_html()` digunakan untuk HTML dengan dynamic content (ada placeholder)
- `mark_safe()` digunakan untuk HTML statis tanpa placeholder
- Kedua function sama-sama aman dari XSS karena tidak menerima user input langsung
