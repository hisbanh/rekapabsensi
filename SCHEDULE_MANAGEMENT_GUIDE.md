# Panduan Manajemen Jadwal Ustadz

## Cara Mengakses Halaman Jadwal Ustadz

Halaman manajemen jadwal ustadz sudah tersedia dan dapat diakses melalui beberapa cara:

### 1. Melalui Menu Navigasi (Sidebar)

Setelah login sebagai **Admin** atau **Staff**, Anda akan melihat menu baru di sidebar:

```
📚 Absensi Ustadz
  ├── 👨‍🏫 Dashboard Ustadz
  ├── 👔 Data Ustadz
  ├── 📅 Jadwal Ustadz  ← KLIK DI SINI
  ├── ✅ Input Absensi Ustadz
  └── 📊 Laporan Ustadz
```

### 2. Melalui URL Langsung

Akses langsung melalui browser:
```
http://localhost:8000/schedules/
```

Atau di production:
```
https://your-domain.com/schedules/
```

### 3. Melalui Halaman Data Ustadz

1. Buka menu **Data Ustadz**
2. Klik pada nama ustadz
3. Di halaman detail ustadz, klik tombol **"Lihat Jadwal"**

---

## Fitur Halaman Jadwal Ustadz

### 📋 Tampilan Grid Jadwal Mingguan

Halaman ini menampilkan jadwal dalam format grid yang mudah dibaca:

```
        Senin    Selasa   Rabu     Kamis    Jumat    Sabtu
JP 1-2  Mat 8A   -        Mat 8B   -        Mat 9A   -
JP 3-4  -        Fis 9A   -        Fis 9B   -        -
JP 5-6  Mat 9B   -        Mat 9A   -        -        -
```

### ✨ Fitur Utama

1. **Filter Ustadz** (Admin)
   - Pilih ustadz dari dropdown untuk melihat jadwal mereka
   - Default menampilkan ustadz pertama yang aktif

2. **Tambah Jadwal Baru**
   - Klik tombol **"+ Tambah Jadwal"**
   - Isi form:
     - Pilih Ustadz
     - Pilih Mata Pelajaran
     - Pilih Kelas
     - Pilih Hari (Senin-Sabtu)
     - Pilih JP Mulai dan JP Selesai (1-10)
     - Nomor Ruangan (opsional)
     - Catatan (opsional)
   - Klik **"Simpan"**

3. **Edit Jadwal**
   - Klik pada jadwal yang ingin diedit di grid
   - Ubah informasi yang diperlukan
   - Klik **"Update"**

4. **Hapus Jadwal**
   - Klik pada jadwal yang ingin dihapus
   - Klik tombol **"Hapus"**
   - Konfirmasi penghapusan

5. **Deteksi Konflik Otomatis** ⚠️
   - Sistem otomatis mendeteksi konflik jadwal:
     - ❌ Ustadz yang sama di waktu yang sama
     - ❌ Kelas yang sama di waktu yang sama
   - Peringatan akan muncul jika ada konflik

6. **Total JP per Minggu**
   - Menampilkan total JP yang dijadwalkan untuk ustadz terpilih

---

## Hak Akses

### 👨‍💼 Admin / Superuser
- ✅ Melihat jadwal semua ustadz
- ✅ Menambah jadwal baru
- ✅ Mengedit jadwal
- ✅ Menghapus jadwal
- ✅ Filter berdasarkan ustadz

### 👨‍🏫 Ustadz (Teacher)
- ✅ Melihat jadwal sendiri
- ❌ Tidak bisa mengedit jadwal
- ❌ Tidak bisa melihat jadwal ustadz lain

---

## Validasi Sistem

Sistem akan memvalidasi:

1. **JP Range**
   - JP Mulai harus antara 1-10
   - JP Selesai harus antara 1-10
   - JP Selesai harus ≥ JP Mulai

2. **Konflik Jadwal**
   - Tidak boleh ada 2 jadwal untuk ustadz yang sama di waktu yang sama
   - Tidak boleh ada 2 jadwal untuk kelas yang sama di waktu yang sama

3. **Data Wajib**
   - Ustadz harus dipilih
   - Mata pelajaran harus dipilih
   - Kelas harus dipilih
   - Hari harus dipilih
   - JP harus diisi

---

## Contoh Penggunaan

### Menambah Jadwal Matematika untuk Ustadz Ahmad

1. Buka halaman **Jadwal Ustadz** dari menu sidebar
2. Pilih **Ustadz Ahmad** dari dropdown (jika admin)
3. Klik tombol **"+ Tambah Jadwal"**
4. Isi form:
   - Ustadz: Ahmad Yusuf
   - Mata Pelajaran: Matematika
   - Kelas: 8A
   - Hari: Senin
   - JP Mulai: 1
   - JP Selesai: 2
   - Ruangan: R-101
5. Klik **"Simpan"**
6. Jadwal akan muncul di grid pada kolom Senin, baris JP 1-2

### Mengedit Jadwal yang Sudah Ada

1. Klik pada jadwal di grid (misalnya "Mat 8A" di Senin JP 1-2)
2. Modal edit akan muncul dengan data jadwal
3. Ubah informasi yang diperlukan (misalnya ganti ruangan)
4. Klik **"Update"**
5. Jadwal akan diperbarui di grid

---

## Troubleshooting

### Jadwal tidak muncul di grid?
- Pastikan ustadz yang dipilih memiliki jadwal aktif
- Cek apakah jadwal memiliki status `is_active = True`
- Refresh halaman

### Tidak bisa menambah jadwal?
- Pastikan Anda login sebagai Admin atau Staff
- Cek apakah ada konflik jadwal
- Pastikan semua field wajib sudah diisi

### Pesan error "Konflik jadwal ditemukan"?
- Cek apakah ustadz sudah memiliki jadwal di waktu yang sama
- Cek apakah kelas sudah dijadwalkan di waktu yang sama
- Ubah hari atau JP untuk menghindari konflik

---

## URL Endpoints

Berikut adalah URL endpoints yang tersedia:

| URL | Fungsi | Akses |
|-----|--------|-------|
| `/schedules/` | Halaman utama manajemen jadwal | Admin/Staff |
| `/schedules/create/` | Tambah jadwal baru (AJAX) | Admin |
| `/schedules/<id>/update/` | Update jadwal (AJAX) | Admin |
| `/schedules/<id>/delete/` | Hapus jadwal (AJAX) | Admin |
| `/schedules/<id>/detail/` | Detail jadwal (AJAX) | Admin/Teacher |
| `/teachers/<id>/schedule/` | Jadwal per ustadz | Admin/Teacher |

---

## Tips & Best Practices

1. **Rencanakan Jadwal Mingguan**
   - Buat jadwal untuk semua ustadz di awal semester
   - Pastikan tidak ada konflik sebelum semester dimulai

2. **Gunakan Nomor Ruangan**
   - Isi nomor ruangan untuk memudahkan koordinasi
   - Hindari double booking ruangan

3. **Tambahkan Catatan**
   - Gunakan field catatan untuk informasi tambahan
   - Misalnya: "Lab Komputer", "Outdoor", "Praktikum"

4. **Review Berkala**
   - Cek jadwal secara berkala untuk memastikan akurasi
   - Update jadwal jika ada perubahan

5. **Backup Data**
   - Export jadwal ke Excel secara berkala
   - Simpan sebagai backup

---

## Integrasi dengan Fitur Lain

Jadwal ustadz terintegrasi dengan:

1. **Absensi Ustadz**
   - Jadwal digunakan untuk validasi absensi
   - Ustadz hanya bisa absen sesuai jadwal mereka

2. **Dashboard Ustadz**
   - Menampilkan jadwal hari ini
   - Menampilkan total JP per minggu

3. **Laporan Ustadz**
   - Jadwal digunakan untuk menghitung kehadiran
   - Persentase kehadiran dihitung berdasarkan JP terjadwal

---

## Dukungan

Jika mengalami masalah atau memiliki pertanyaan:

1. Cek dokumentasi ini terlebih dahulu
2. Hubungi administrator sistem
3. Laporkan bug atau request fitur baru

---

**Terakhir Diperbarui**: 22 Januari 2026
**Versi**: 1.0
**Status**: ✅ Aktif dan Siap Digunakan
