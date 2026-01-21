# Panduan Input Absensi Ustadz

## Masalah yang Diperbaiki

Fitur input absensi ustadz sekarang sudah berfungsi dengan baik. Masalah sebelumnya adalah tidak ada user account yang terhubung dengan data ustadz.

## Solusi yang Diterapkan

Script `fix_teacher_user_link.py` telah dijalankan untuk:
1. Membuat user account untuk setiap ustadz yang belum memiliki account
2. Menghubungkan user account dengan data ustadz
3. Mengatur password default untuk semua user baru

## Informasi Login

### Untuk Ustadz/Ustadzah

**Format Username:** `teacher_<NIP>`

**Contoh:**
- NIP: UST001 → Username: `teacher_UST001`
- NIP: UST002 → Username: `teacher_UST002`

**Password Default:** `password123`

⚠️ **PENTING:** Harap ganti password setelah login pertama kali!

### Untuk Admin

**Username:** `admin`
**Password:** `admin123`

## Cara Menggunakan Fitur Input Absensi

### A. Input Absensi Mandiri (Untuk Ustadz)

1. **Login ke Sistem**
   - Buka browser dan akses aplikasi
   - Login dengan username dan password Anda
   - Format username: `teacher_<NIP>`

2. **Akses Halaman Input Absensi**
   - Klik menu "Absensi Ustadz" atau
   - Akses URL: `/teacher-attendance/`

3. **Pilih Tanggal**
   - Secara default menampilkan tanggal hari ini
   - Anda dapat memilih tanggal lain (maksimal 7 hari ke belakang)
   - Gunakan date picker untuk memilih tanggal

4. **Deteksi Lokasi**
   - Klik tombol "Deteksi Lokasi"
   - Izinkan browser untuk mengakses lokasi Anda
   - Sistem akan memvalidasi apakah Anda berada di area sekolah (radius 150m)
   - Status lokasi akan ditampilkan:
     - ✓ Hijau: Lokasi valid (dalam area sekolah)
     - ✗ Merah: Lokasi di luar area sekolah (tetap bisa submit dengan peringatan)

5. **Isi Status Kehadiran**
   - Sistem menampilkan jadwal mengajar Anda untuk tanggal yang dipilih
   - Untuk setiap JP, pilih status kehadiran:
     - **Hadir**: Anda mengajar sesuai jadwal
     - **Sakit**: Tidak hadir karena sakit
     - **Izin**: Tidak hadir dengan izin
     - **Cuti**: Sedang cuti
     - **Dinas**: Tugas dinas di luar
     - **Alpa**: Tidak hadir tanpa keterangan
   - Tambahkan catatan jika diperlukan (opsional)

6. **Simpan Absensi**
   - Klik tombol "Simpan Absensi"
   - Sistem akan menyimpan absensi untuk semua JP yang Anda isi
   - Anda akan melihat notifikasi sukses atau error

### B. Input Absensi oleh Admin

1. **Login sebagai Admin**
   - Username: `admin`
   - Password: `admin123`

2. **Akses Halaman Admin Input**
   - Akses URL: `/teacher-attendance/admin/`

3. **Pilih Ustadz dan Tanggal**
   - Pilih ustadz dari dropdown
   - Pilih tanggal (tidak ada batasan 7 hari untuk admin)
   - Sistem akan menampilkan jadwal ustadz tersebut

4. **Isi Status Kehadiran**
   - Pilih status untuk setiap JP
   - Tambahkan catatan jika diperlukan
   - Tidak perlu validasi lokasi untuk input admin

5. **Simpan Absensi**
   - Klik "Simpan Absensi"
   - Sistem akan menyimpan data

### C. Melihat Riwayat Absensi

1. **Akses Halaman Riwayat**
   - URL: `/teacher-attendance/history/`

2. **Filter Data**
   - Filter berdasarkan tanggal (range)
   - Filter berdasarkan status kehadiran
   - Cari berdasarkan nama atau catatan

3. **Edit/Hapus Absensi**
   - Ustadz: Dapat edit/hapus absensi sendiri dalam 7 hari
   - Admin: Dapat edit/hapus semua absensi tanpa batasan waktu

## Fitur Validasi Lokasi

### Konfigurasi Lokasi Sekolah

Lokasi sekolah dikonfigurasi di file `.env`:

```env
SCHOOL_LATITUDE=-7.7956
SCHOOL_LONGITUDE=110.3695
SCHOOL_RADIUS_METERS=150
```

### Cara Kerja Validasi

1. Sistem menggunakan Geolocation API browser untuk mendapatkan koordinat GPS
2. Menghitung jarak antara lokasi user dengan lokasi sekolah menggunakan Haversine formula
3. Jika jarak ≤ 150 meter: Lokasi valid ✓
4. Jika jarak > 150 meter: Lokasi tidak valid ✗ (tetap bisa submit dengan peringatan)

### Troubleshooting Lokasi

**Masalah:** Browser tidak bisa mendeteksi lokasi
- **Solusi:** 
  - Pastikan GPS/Location Services aktif di device
  - Izinkan browser mengakses lokasi
  - Coba refresh halaman dan deteksi ulang

**Masalah:** Lokasi terdeteksi tapi tidak valid
- **Solusi:**
  - Pastikan Anda berada di area sekolah
  - Tunggu beberapa saat agar GPS lebih akurat
  - Jika yakin sudah di sekolah, Anda tetap bisa submit (akan dicatat sebagai lokasi tidak valid)

## Batasan dan Aturan

### Untuk Ustadz:
- ✓ Dapat mengisi absensi sendiri
- ✓ Dapat mengisi absensi untuk 7 hari terakhir
- ✓ Dapat edit/hapus absensi sendiri dalam 7 hari
- ✓ Harus menggunakan validasi lokasi
- ✗ Tidak dapat mengisi absensi untuk tanggal masa depan
- ✗ Tidak dapat melihat absensi ustadz lain

### Untuk Admin:
- ✓ Dapat mengisi absensi untuk semua ustadz
- ✓ Dapat mengisi absensi untuk semua tanggal (tidak ada batasan 7 hari)
- ✓ Dapat edit/hapus semua absensi
- ✓ Tidak perlu validasi lokasi
- ✓ Dapat melihat semua riwayat absensi

## URL Endpoints

| Halaman | URL | Akses |
|---------|-----|-------|
| Input Absensi Mandiri | `/teacher-attendance/` | Ustadz |
| Input Absensi Admin | `/teacher-attendance/admin/` | Admin |
| Riwayat Absensi | `/teacher-attendance/history/` | Semua |
| Edit Absensi | `/teacher-attendance/<id>/edit/` | Ustadz (7 hari), Admin (semua) |
| Hapus Absensi | `/teacher-attendance/<id>/delete/` | Ustadz (7 hari), Admin (semua) |

## Keamanan

1. **Autentikasi:** Semua halaman memerlukan login
2. **Otorisasi:** 
   - Ustadz hanya bisa akses data sendiri
   - Admin bisa akses semua data
3. **Validasi Lokasi:** Mencegah absensi dari luar area sekolah
4. **Audit Trail:** Semua perubahan dicatat dengan user dan timestamp
5. **Batasan Waktu:** Ustadz hanya bisa edit data 7 hari terakhir

## Troubleshooting Umum

### 1. Tidak bisa login
- Pastikan username format: `teacher_<NIP>`
- Password default: `password123`
- Jika lupa password, hubungi admin

### 2. Halaman error "Anda tidak memiliki profil ustadz"
- Hubungi admin untuk menghubungkan user account dengan data ustadz
- Admin dapat menjalankan script: `python fix_teacher_user_link.py`

### 3. Tidak ada jadwal yang muncul
- Pastikan jadwal sudah diinput oleh admin
- Periksa apakah tanggal yang dipilih adalah hari kerja
- Hubungi admin jika jadwal belum diatur

### 4. Tombol "Simpan Absensi" disabled
- Pastikan sudah klik "Deteksi Lokasi" terlebih dahulu
- Tunggu hingga lokasi terdeteksi
- Jika lokasi tidak valid, Anda tetap bisa submit dengan konfirmasi

## Kontak Support

Jika mengalami masalah teknis, hubungi:
- Admin Sistem
- IT Support Sekolah

---

**Terakhir diupdate:** 21 Januari 2026
**Versi:** 1.0
