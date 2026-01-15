# Analisis Fitur Kehadiran Guru & Rekomendasi Perbaikan

## 📊 Status Fitur Saat Ini

### ✅ Yang Sudah Ada
1. **Manajemen Guru (CRUD)**
   - Tambah, edit, hapus guru dengan validasi lengkap
   - Menyimpan NIP dan ID Guru unik
   - Status aktif/nonaktif

2. **Manajemen Jadwal Guru**
   - Jadwal mingguan per guru (Senin-Minggu)
   - Menyimpan JP (Jam Pelajaran) per hari
   - Mata pelajaran dan status piket
   - Validasi JP numbers (1-10)

3. **Input Absensi Guru**
   - Input per tanggal untuk multiple guru
   - Status: Hadir (H), Sakit (S), Izin (I), Alpa (A), Terlambat (L), Dinas Luar (D), Cuti (C)
   - Input JP statuses per JP slot
   - Catatan/notes untuk setiap absensi
   - Form dengan grid interaktif

4. **Laporan & Analytics**
   - Statistik kehadiran per guru
   - Persentase kehadiran
   - Export ke Excel

5. **Dashboard**
   - Ringkasan kehadiran 30 hari terakhir
   - Guru yang belum input hari ini
   - Record absensi terbaru

### ⚠️ Potensi Masalah & Kebutuhan Guru

---

## 🎯 REKOMENDASI FITUR YANG PERLU DITAMBAHKAN

### 1. **📱 Mobile-Friendly Interface untuk Input Cepat**
**Problem:** Guru biasanya input absensi di awal/akhir hari dari office yang sibuk
- Input butuh lebih cepat dengan interface minimal
- Butuh QR code scanning untuk konfirmasi kehadiran

**Solusi:**
```
a. Buat simplified mobile form untuk quick input
b. Input via QR code dengan default status "Hadir"
c. Allow one-tap status change (Hadir → Sakit → Izin → Alpa)
d. Offline capability untuk area dengan koneksi terbatas
```

**Prioritas:** ⭐⭐⭐⭐⭐ (SANGAT PENTING)

---

### 2. **📅 Self-Service untuk Guru (Input Sendiri)**
**Problem:** Guru harus menunggu admin untuk input absensi mereka
- Guru perlu autonomy untuk update status mereka
- Perlu pembatasan waktu input (hanya hari yang sama, max 24 jam setelah)

**Solusi:**
```
a. Dashboard guru untuk lihat jadwal hari ini
b. Quick button untuk "Hadir", "Sakit", "Izin", "Alpa"
c. Form untuk upload bukti sakit (foto surat/resep)
d. Approval flow: Guru input → Admin review → Finalisasi
e. Reminder notification 5 menit sebelum jam pertama
```

**Prioritas:** ⭐⭐⭐⭐⭐

---

### 3. **🔔 Notification System**
**Problem:** Guru tidak tahu kapan harus input atau jika ada yang terlewat

**Solusi:**
```
a. SMS/WhatsApp reminder 30 min sebelum jam mulai
b. Email recapitulation harian
c. Alert jika ada 3x tidak hadir berturut-turut
d. Push notification di dashboard
```

**Prioritas:** ⭐⭐⭐⭐

---

### 4. **📋 Attendance History dengan Filter Powerful**
**Problem:** Guru butuh lihat rekam jejak mereka dengan mudah

**Solusi:**
```
a. Calendar view dengan warna status (Hadir=green, Sakit=orange, etc)
b. Monthly summary card (e.g., "20/22 Hadir = 90.9%")
c. Filter by:
   - Date range
   - Status
   - Mata pelajaran
   - Replacement teaching status
d. Download laporan pribadi (Excel/PDF)
```

**Prioritas:** ⭐⭐⭐⭐

---

### 5. **🔄 Replacement Teaching Management**
**Problem:** Tidak ada tracking untuk guru pengganti

**Solusi:**
```
a. Dedicated form untuk "Mengajar Menggantikan"
b. Track: Guru asli → Guru pengganti → JP yang diambil
c. Verifikasi by guru asli
d. Report showing replacement history
e. Dashboard untuk guru: "Replacement teaching: 5 jam"
```

**Prioritas:** ⭐⭐⭐⭐

---

### 6. **📊 Advanced Reports & Analytics**
**Problem:** Laporan saat ini terbatas, guru butuh insights lebih

**Solusi:**
```
a. Attendance trend chart (6 bulan/1 tahun)
b. Comparison: "Rata-rata Anda 92%, Rata-rata sekolah 85%"
c. Attendance certificate generator (e.g., "100% Hadir Bulan Januari")
d. Individual report generator (guru bisa generate sendiri)
e. Export dalam berbagai format (Excel, PDF, CSV)
f. Print-ready format untuk dinas/dokumentasi
```

**Prioritas:** ⭐⭐⭐

---

### 7. **⏰ Leave/Cuti Management System**
**Problem:** Tidak ada workflow untuk permohonan cuti resmi

**Solusi:**
```
a. Guru bisa submit permohonan cuti dengan:
   - Tanggal mulai-akhir
   - Alasan (sakit, cuti, dinas)
   - Bukti (jika perlu)
b. Admin dashboard untuk approve/reject
c. Auto-mark attendance sebagai "Approved Leave"
d. Tidak dihitung dalam absensi negatif
e. Report: "Cuti Approved: 5 hari"
```

**Prioritas:** ⭐⭐⭐⭐

---

### 8. **👥 Bulk Import dari Staff Excel**
**Problem:** Input 100+ guru manual sangat memakan waktu

**Solusi:**
```
a. Template Excel untuk upload guru
b. Columns: ID, Nama, NIP, Mata Pelajaran, Jadwal (format standar)
c. Validation before import
d. Error reporting & fix guide
e. Auto-generate akun login dari template
```

**Prioritas:** ⭐⭐⭐

---

### 9. **📧 Email Digest & Summary**
**Problem:** Guru sering lupa tracking absensi mereka

**Solusi:**
```
a. Weekly recap email: Attendance summary + trends
b. Monthly certificate email (attendance record)
c. Alert email untuk anomali (3x absent, pattern aneh)
d. Customizable frequency (daily/weekly/monthly)
e. Unsubscribe option dengan approval
```

**Prioritas:** ⭐⭐⭐

---

### 10. **🔐 Access Control untuk Guru**
**Problem:** Semua guru melihat absensi guru lain (privacy issue)

**Solusi:**
```
a. Guru hanya lihat data diri sendiri (by default)
b. Supervisor/Admin lihat tim mereka
c. Audit log untuk semua akses data
d. Permission matrix: view, edit, export, approve
```

**Prioritas:** ⭐⭐⭐⭐

---

## 🛠️ Improvement Teknis

### A. **Database Optimization**
```
a. Tambah index pada:
   - (teacher_id, date) untuk query cepat
   - (teacher_id, date_range) untuk reports
   - (replaced_teacher, date) untuk replacement tracking
   
b. Cache attendance stats (refresh daily)
c. Partisi table TeacherDailyAttendance by year
```

### B. **API Endpoints yang Perlu**
```
GET    /api/teachers/me/                    # Profile guru
GET    /api/teachers/me/attendance/         # History guru
POST   /api/teachers/me/attendance/         # Quick input
GET    /api/teachers/me/schedule/today/     # Jadwal hari ini
POST   /api/teachers/leave-request/         # Submit cuti
GET    /api/teachers/me/stats/              # Stats pribadi
POST   /api/teachers/attendance/bulk/       # Bulk upload
```

### C. **Frontend Components yang Dibutuhkan**
```
1. TeacherDashboard 
   - Today schedule widget
   - Quick attendance button
   - Recent history card

2. AttendanceHistory Calendar
   - Month view dengan warna status
   - Click detail

3. ReplacementForm
   - Guru asli selector
   - JP selector
   - Verifikasi

4. ReportGenerator
   - Date range picker
   - Export format selector
```

---

## 📈 Implementation Priority

### Phase 1 (Critical - 2-3 weeks)
1. ✅ Self-service teacher input (guru input sendiri)
2. ✅ Mobile-friendly quick input
3. ✅ Notification system

### Phase 2 (Important - 1-2 weeks)
4. ✅ Replacement teaching management
5. ✅ Leave/cuti management

### Phase 3 (Nice to have - 1 week)
6. ✅ Advanced reports & analytics
7. ✅ Email digest system
8. ✅ Calendar history view

### Phase 4 (Optional - ongoing)
9. ✅ QR code integration
10. ✅ Offline mobile app

---

## 📋 User Stories untuk Developers

### US-1: Teacher Quick Attendance Input
```
AS A teacher
I WANT TO input my attendance quickly from mobile
SO THAT I don't need to wait for admin to record it

ACCEPTANCE CRITERIA:
✓ Load dalam <2 detik di mobile
✓ 1 klik untuk input status
✓ Auto-fill based on schedule
✓ Confirmation notification
✓ History visible immediately
```

### US-2: Attendance History Calendar
```
AS A teacher
I WANT TO see my attendance history in calendar view
SO THAT I can easily track my presence pattern

ACCEPTANCE CRITERIA:
✓ Month view dengan color-coded status
✓ Click untuk lihat detail JP
✓ Stats card (total hadir, rate %)
✓ Filter by month/year
✓ Export monthly report
```

### US-3: Leave Request Workflow
```
AS A teacher
I WANT TO submit leave request officially
SO THAT my absence is properly documented

ACCEPTANCE CRITERIA:
✓ Form untuk submit cuti + bukti
✓ Admin notification
✓ Status tracking (pending/approved/rejected)
✓ Auto-update attendance record
✓ History of all leaves
```

---

## 🎨 UI/UX Improvements

1. **Dashboard Guru**
   - Besar & jelas untuk quick reference
   - "Hadir" button prominent di tengah
   - Status drop-down untuk alternative

2. **Color Coding Konsisten**
   - H (Hadir) = 🟢 Green
   - S (Sakit) = 🟠 Orange
   - I (Izin) = 🔵 Blue
   - A (Alpa) = 🔴 Red

3. **Responsive Design**
   - Mobile-first approach
   - Touch-friendly buttons (min 44px)
   - Minimalist interface

---

## ✅ Validation Rules

Tambahkan validasi:
```
1. Guru hanya input untuk hari yang sama (T-1 maksimal)
2. Tidak boleh edit attendance lebih dari 24 jam
3. JP statuses harus sesuai schedule (jika ada)
4. Replacement harus verified by guru asli
5. Cuti harus approve sebelum count sebagai "approved"
```

---

## 📊 Suggested Metrics to Track

```
1. Input Timeliness: "90% guru input sebelum pukul 08:00"
2. Accuracy Rate: "% attendance records yang accurate"
3. Amendment Rate: "% yang perlu diperbaiki admin"
4. System Usage: "Average login per guru per minggu"
5. Support Requests: "# issues per 100 guru per bulan"
```

---

## 🚀 Next Steps

1. **Validasi dengan guru** - minta feedback tentang prioritas
2. **Create wireframes** untuk fitur priority 1
3. **Setup development environment** untuk Phase 1
4. **Start coding** self-service + notifications
5. **Beta testing** dengan guru selected

---

**Last Updated:** January 15, 2026
**Status:** Ready for Development
**Estimated Effort:** 4-6 weeks untuk semua fitur
