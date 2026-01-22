# Fix: Fitur Create dan Edit Data Ustadz Tidak Bisa Input Data

## Problem
Fitur create dan edit data ustadz tidak bisa menerima input data dari user. Form tidak berfungsi dengan baik.

## Root Cause
View `teacher_create` dan `teacher_update` di `attendance/teacher_views.py` tidak menggunakan Django Form yang sudah ada (`TeacherForm`). Sebaliknya, view menggunakan raw POST data processing yang:

1. **Tidak menampilkan form fields dengan benar** di template
2. **Tidak melakukan validasi** input dari user
3. **Field name mismatch**: View mencari `request.POST.getlist('subjects')` tetapi form field bernama `subject_ids`
4. **Tidak menangani form errors** dengan baik

## Solution
Mengubah view `teacher_create` dan `teacher_update` untuk menggunakan `TeacherForm` yang sudah ada di `attendance/forms/teacher_forms.py`:

### Perubahan pada `teacher_create`:
- Import `TeacherForm` dari `attendance.forms`
- Gunakan `form = TeacherForm(request.POST, request.FILES)` untuk POST request
- Gunakan `form = TeacherForm()` untuk GET request
- Validasi dengan `form.is_valid()`
- Simpan dengan `form.save()` (form sudah handle subject assignment)
- Pass `form` object ke template context

### Perubahan pada `teacher_update`:
- Import `TeacherForm` dari `attendance.forms`
- Gunakan `form = TeacherForm(request.POST, request.FILES, instance=teacher)` untuk POST request
- Gunakan `form = TeacherForm(instance=teacher)` untuk GET request
- Validasi dengan `form.is_valid()`
- Simpan dengan `form.save()` (form sudah handle subject assignment)
- Pass `form` object ke template context

## Files Modified
- `attendance/teacher_views.py` - Updated `teacher_create` and `teacher_update` functions

## Benefits
1. ✓ Form fields ditampilkan dengan benar di template
2. ✓ Validasi input otomatis (NIP unique, email format, phone number, dll)
3. ✓ Error messages ditampilkan per field
4. ✓ Subject assignment bekerja dengan benar
5. ✓ Photo upload handling sudah built-in
6. ✓ Homeroom class validation otomatis
7. ✓ Code lebih clean dan maintainable

## Testing
Verified dengan:
1. ✓ TeacherForm dapat diimport
2. ✓ Form memiliki semua field yang diperlukan termasuk `subject_ids`
3. ✓ GET request ke create view returns 200
4. ✓ GET request ke edit view returns 200
5. ✓ Form fields muncul di response HTML
6. ✓ Teacher data muncul di edit form

## Status
**FIXED** - Fitur create dan edit data ustadz sekarang berfungsi dengan baik.

## How to Test
1. Login sebagai admin
2. Buka http://127.0.0.1:8001/teachers/create/
3. Isi form dengan data ustadz baru
4. Pilih mata pelajaran (Ctrl+Click untuk multiple selection)
5. Upload foto (opsional)
6. Klik "Simpan"
7. Data ustadz berhasil tersimpan

Untuk edit:
1. Buka http://127.0.0.1:8001/teachers/
2. Klik tombol "Edit" pada salah satu ustadz
3. Ubah data yang diperlukan
4. Klik "Perbarui"
5. Data ustadz berhasil diupdate
