# Cara Mengakses Halaman Input Absensi Ustadz

## 📍 Lokasi Menu

Halaman input absensi ustadz dapat diakses melalui beberapa cara:

### 1. **Melalui Sidebar/Menu Navigasi**

Menu "Absensi Ustadz" tersedia di sidebar dengan syarat:
- ✅ User harus login sebagai **Admin** atau **Staff**
- ✅ Menu berada di section "Absensi Ustadz"

**Lokasi Menu:**
```
Sidebar → Absensi Ustadz → Input Absensi Ustadz
```

**Icon:** 📋 (Clipboard Check)

### 2. **Melalui URL Langsung**

Anda dapat mengakses langsung melalui URL:
```
http://your-domain.com/teacher-attendance/
```

Atau jika menggunakan localhost:
```
http://localhost:8000/teacher-attendance/
```

### 3. **Melalui Dashboard Ustadz**

Dari Dashboard Ustadz, klik tombol "Input Absensi"

---

## 🔐 Persyaratan Akses

### Untuk Melihat Menu:
- User harus memiliki status **is_staff=True** atau **is_superuser=True**
- User harus sudah login

### Untuk Input Absensi Mandiri (Self-Service):
- User harus memiliki profil Teacher yang terhubung
- User harus memiliki jadwal mengajar untuk hari tersebut

### Untuk Input Absensi Admin:
- User harus memiliki status **is_superuser=True**
- Dapat menginput absensi untuk ustadz manapun
- Dapat menginput untuk tanggal manapun (tidak terbatas 7 hari)

---

## 🛠️ Troubleshooting

### Menu Tidak Muncul?

**Penyebab 1: User bukan Staff/Admin**
```python
# Cek status user di Django Admin atau shell
python manage.py shell

from django.contrib.auth.models import User
user = User.objects.get(username='nama_user')
print(f"Is Staff: {user.is_staff}")
print(f"Is Superuser: {user.is_superuser}")
```

**Solusi:** Set user sebagai staff
```python
user.is_staff = True
user.save()
```

**Penyebab 2: Template yang digunakan tidak memiliki menu**
- Periksa apakah menggunakan `_sidebar.html` atau `_sidebar_new.html`
- Pastikan template yang digunakan sudah include menu ustadz

**Solusi:** Saya sudah menambahkan menu ke `_sidebar_new.html`

---

## 📋 Fitur Halaman Input Absensi Ustadz

### Absensi Mandiri (Self-Service)
1. **Deteksi Lokasi Otomatis**
   - Validasi lokasi dalam radius 150m dari sekolah
   - Menggunakan GPS browser

2. **Jadwal Hari Ini**
   - Menampilkan semua JP yang dijadwalkan
   - Pilih status per JP (Hadir, Sakit, Izin, Cuti, Dinas, Alpa)
   - Tambah catatan (opsional)

3. **Batasan Waktu**
   - Ustadz dapat input untuk 7 hari terakhir
   - Admin tidak ada batasan waktu

### Absensi Admin
1. **Pilih Ustadz**
   - Dropdown semua ustadz aktif

2. **Pilih Tanggal**
   - Bebas pilih tanggal manapun

3. **Input Absensi**
   - Input untuk semua JP yang dijadwalkan
   - Tidak perlu validasi lokasi

---

## 🔗 URL Terkait

| Halaman | URL | Akses |
|---------|-----|-------|
| Input Absensi Mandiri | `/teacher-attendance/` | Staff/Admin |
| Input Absensi Admin | `/teacher-attendance/admin/` | Admin Only |
| Riwayat Absensi | `/teacher-attendance/history/` | Staff/Admin |
| Dashboard Ustadz | `/teacher-dashboard/` | Staff/Admin |
| Data Ustadz | `/teachers/` | Staff/Admin |
| Laporan Ustadz | `/teacher-reports/` | Staff/Admin |

---

## 💡 Tips

1. **Untuk Ustadz:**
   - Pastikan sudah terhubung dengan user account
   - Pastikan jadwal mengajar sudah diatur
   - Aktifkan GPS/lokasi di browser

2. **Untuk Admin:**
   - Gunakan menu "Input Absensi Admin" untuk input manual
   - Dapat input untuk ustadz yang tidak hadir
   - Dapat koreksi absensi yang salah

3. **Untuk Developer:**
   - Periksa `attendance/teacher_attendance_views.py` untuk logika view
   - Template ada di `templates/teacher/attendance_input.html`
   - URL didefinisikan di `attendance/urls.py`

---

## 📞 Bantuan Lebih Lanjut

Jika masih mengalami masalah:
1. Periksa log Django: `logs/django.log`
2. Cek console browser untuk error JavaScript
3. Pastikan migrations sudah dijalankan: `python manage.py migrate`
4. Pastikan data ustadz dan jadwal sudah ada di database

---

**Terakhir diupdate:** 22 Januari 2026
