# Panduan Kelola Jadwal Mengajar

## Fitur Baru: Schedule Management UI

Halaman kelola jadwal mengajar telah ditambahkan ke interface utama (bukan Django admin panel).

### Akses

**URL**: http://127.0.0.1:8001/schedules/

**Permission**:
- **Admin**: Dapat melihat dan mengedit jadwal semua ustadz
- **Guru**: Dapat melihat jadwal sendiri (read-only)

### Fitur Utama

#### 1. **Grid Jadwal Mingguan**
- Tampilan grid dengan hari (Senin-Sabtu) di kolom dan JP (1-10) di baris
- Jadwal ditampilkan sebagai card berwarna dengan informasi:
  - Nama mata pelajaran
  - Nama kelas
  - Nomor ruangan (jika ada)

#### 2. **Statistik**
- Total JP per minggu
- Jumlah mata pelajaran yang diajarkan
- Status beban mengajar (terpenuhi jika ≥18 JP)

#### 3. **Tambah Jadwal** (Admin only)
- Klik tombol "Tambah Jadwal" atau klik cell kosong di grid
- Isi form:
  - Hari
  - JP Mulai dan JP Selesai
  - Mata Pelajaran
  - Kelas
  - Nomor Ruangan (opsional)
  - Catatan (opsional)
- Sistem akan otomatis mendeteksi konflik jadwal

#### 4. **Edit Jadwal** (Admin only)
- Klik pada jadwal yang ada di grid
- Modal edit akan muncul dengan data jadwal
- Ubah data yang diperlukan
- Klik "Simpan" untuk menyimpan perubahan

#### 5. **Hapus Jadwal** (Admin only)
- Buka modal edit jadwal
- Klik tombol "Hapus"
- Konfirmasi penghapusan
- Jadwal akan di-soft delete (is_active = False)

#### 6. **Deteksi Konflik**
Sistem akan mendeteksi dan mencegah:
- **Konflik Ustadz**: Ustadz sudah memiliki jadwal di waktu yang sama
- **Konflik Kelas**: Kelas sudah dijadwalkan dengan ustadz lain di waktu yang sama

### Cara Penggunaan

#### Untuk Admin:

1. **Melihat Jadwal Ustadz**
   - Akses `/schedules/`
   - Pilih ustadz dari dropdown
   - Jadwal mingguan akan ditampilkan

2. **Menambah Jadwal**
   - Klik "Tambah Jadwal" atau klik cell kosong
   - Isi form yang muncul
   - Klik "Simpan"
   - Jika ada konflik, sistem akan menampilkan peringatan

3. **Mengedit Jadwal**
   - Klik pada jadwal di grid
   - Ubah data di modal yang muncul
   - Klik "Simpan"

4. **Menghapus Jadwal**
   - Klik pada jadwal di grid
   - Klik tombol "Hapus" di modal
   - Konfirmasi penghapusan

#### Untuk Guru:

1. **Melihat Jadwal Sendiri**
   - Akses `/schedules/`
   - Jadwal mingguan Anda akan ditampilkan otomatis
   - Anda dapat melihat detail jadwal dengan klik pada card

### API Endpoints

Untuk integrasi atau pengembangan lebih lanjut:

- `GET /schedules/` - Halaman utama schedule management
- `POST /schedules/create/` - Create new schedule (Admin only)
- `POST /schedules/<id>/update/` - Update schedule (Admin only)
- `POST /schedules/<id>/delete/` - Delete schedule (Admin only)
- `GET /schedules/<id>/detail/` - Get schedule detail

### Technical Details

**Files Created:**
- `attendance/schedule_views.py` - View functions
- `templates/teacher/schedule_management.html` - Template
- Updated `attendance/urls.py` - URL routing
- Updated `attendance/templatetags/attendance_extras.py` - Template filters

**Services Used:**
- `TeacherScheduleService.get_weekly_schedule()` - Get weekly schedule
- `ScheduleService.detect_conflicts()` - Detect scheduling conflicts

### Responsive Design

Halaman ini fully responsive:
- **Desktop**: Grid penuh dengan semua informasi
- **Tablet**: Grid dengan scroll horizontal
- **Mobile**: Grid compact dengan informasi minimal

### Tips

1. **Beban Mengajar**: Pastikan setiap ustadz memiliki minimal 18 JP per minggu
2. **Konflik**: Sistem akan otomatis mencegah konflik, tapi tetap periksa jadwal secara manual
3. **Ruangan**: Isi nomor ruangan untuk memudahkan koordinasi
4. **Catatan**: Gunakan field catatan untuk informasi tambahan (misal: lab, outdoor, dll)

### Troubleshooting

**Jadwal tidak muncul:**
- Pastikan ustadz sudah dipilih (untuk admin)
- Pastikan jadwal memiliki `is_active=True`
- Periksa tanggal efektif jadwal

**Tidak bisa menambah jadwal:**
- Pastikan Anda login sebagai admin
- Periksa apakah ada konflik dengan jadwal lain

**Error saat menyimpan:**
- Periksa semua field required sudah diisi
- Pastikan JP Selesai >= JP Mulai
- Periksa pesan error untuk detail

### Future Enhancements

Fitur yang bisa ditambahkan di masa depan:
- Export jadwal ke PDF/Excel
- Copy jadwal dari minggu/semester sebelumnya
- Bulk edit untuk multiple schedules
- Notifikasi perubahan jadwal
- Integration dengan Google Calendar
- Drag & drop untuk reschedule
