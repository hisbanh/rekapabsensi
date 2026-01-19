# 📊 PANDUAN MENGGUNAKAN LAPORAN KEHADIRAN GURU YANG BARU

## 🎯 FITUR YANG TERSEDIA

Sistem SIPA Yaumi sekarang memiliki **2 jenis laporan PDF profesional** untuk kehadiran guru:

### 1️⃣ **Laporan Individual Guru** (Modern HTML Design)
- **Tujuan**: Evaluasi, presentasi, dan monitoring kehadiran guru individual
- **Isi**: 
  - Cover page dengan info guru (Nama, ID, NIP, periode)
  - Performance badge (Sangat Baik/Baik/Cukup/Kurang)
  - 4 KPI cards: Hadir, Sakit, Izin, Alpa (dengan persentase)
  - Progress bar tingkat kehadiran
  - Placeholder charts (pie chart, trend chart)
  - Detail kehadiran harian per JP
- **Format**: PDF atau HTML (tergantung system capabilities)
- **Design**: Modern, clean, minimalist dengan color-coding

### 2️⃣ **Laporan Summary Semua Guru** (Ringkasan Executive)
- **Tujuan**: Oversight umum dan perbandingan antar guru
- **Isi**:
  - Tabel ringkasan semua guru aktif
  - Kolom: No, ID Guru, Nama, Hadir, Sakit, Izin, Alpa, Persentase, Status
  - Performance badge untuk setiap guru
- **Format**: PDF atau HTML
- **Design**: Profesional dan mudah dibaca

---

## 🔗 CARA MENGAKSES

### VIA ADMIN PANEL
1. Login ke `/admin/`
2. Navigasi ke **Attendance → Teacher Management**
3. Cari guru yang ingin dilaporkan
4. Klik **"Lapor PDF (Modern)"** button → Download PDF

*(Button akan ditambahkan di admin template)*

### VIA URL LANGSUNG

#### Laporan Individual Guru:
```
http://localhost:8000/teacher/{teacher_id}/export/html-pdf/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
```

**Contoh:**
```
http://localhost:8000/teacher/1b9d89e6-87e2-4c45-9945-a06161d58673/export/html-pdf/?start_date=2026-01-01&end_date=2026-01-31
```

**Parameters:**
- `teacher_id`: UUID dari guru (REQUIRED)
- `start_date`: Tanggal mulai (format: YYYY-MM-DD, OPTIONAL)
- `end_date`: Tanggal akhir (format: YYYY-MM-DD, OPTIONAL)

#### Laporan Summary Semua Guru:
```
http://localhost:8000/teacher/export/all-html-pdf/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
```

**Contoh:**
```
http://localhost:8000/teacher/export/all-html-pdf/?start_date=2026-01-01&end_date=2026-01-31
```

---

## 📋 PERFORMA LEVEL OTOMATIS

Sistem otomatis menilai performa guru berdasarkan tingkat kehadiran:

| Level | Criteria | Color | Badge |
|-------|----------|-------|-------|
| 🟢 **Sangat Baik** | ≥ 90% | Green | SANGAT BAIK |
| 🔵 **Baik** | 80-89% | Blue | BAIK |
| 🟠 **Cukup** | 70-79% | Orange | CUKUP |
| 🔴 **Kurang** | < 70% | Red | KURANG |

*Otomatis dihitung dari `total_hadir / total_jp * 100`*

---

## 🎨 DESAIN LAPORAN

### Warna-Warna yang Digunakan:
- **Hadir**: 🟢 Green (#27ae60)
- **Sakit**: 🟠 Orange (#f39c12)
- **Izin**: 🔵 Blue (#2980b9)
- **Alpa**: 🔴 Red (#e74c3c)
- **Header**: Dark Grey (#34495e)

### Layout:
- **Responsive**: Works di semua screen sizes
- **Print-friendly**: Optimized untuk print ke PDF
- **Multi-page**: Automatic page breaks
- **Professional**: Clean typography, proper spacing

---

## 💻 TECHNICAL DETAILS

### File-File yang Dimodifikasi:

1. **Templates** (New):
   - `templates/attendance/teacher/report_pdf.html` - Laporan individual
   - `templates/attendance/teacher/report_summary_pdf.html` - Laporan summary

2. **Services**:
   - `attendance/services/teacher_export_service.py` - Export logic
   - `attendance/services/teacher_service.py` - Summary calculation

3. **Views**:
   - `attendance/views_teacher.py` - Export endpoints

4. **URLs**:
   - `attendance/urls.py` - Route definitions

### Dependencies:
- **WeasyPrint**: HTML → PDF conversion (optional)
- **Django**: Web framework (existing)
- **Python**: 3.13.7 (existing)

### Fallback Behavior:
```
Jika WeasyPrint tidak tersedia:
┌─────────────────────────────────────────┐
│ Template HTML rendered (preview mode)   │
│ User dapat print langsung dari browser   │
│ Hasil: PDF-equivalent quality           │
└─────────────────────────────────────────┘
```

---

## 🚀 NEXT FEATURES (Future Roadmap)

Fitur yang bisa ditambahkan di masa depan:

- [ ] **Add Actual Charts**: Pie chart untuk distribusi status
- [ ] **Trend Analysis**: Line chart untuk kehadiran mingguan
- [ ] **Email Integration**: Kirim PDF langsung via email
- [ ] **Scheduled Reports**: Auto-generate reports setiap akhir bulan
- [ ] **Archive**: Store PDFs untuk historical reference
- [ ] **Comparison**: Side-by-side comparison antar guru
- [ ] **Department Reports**: Laporan per departemen/kelas
- [ ] **Custom Templates**: Template selector di admin

---

## ❓ FAQ

### Q: Bagaimana kalau WeasyPrint tidak terinstall?
**A**: System akan otomatis fallback ke HTML preview yang bisa di-print dari browser. Hasilnya sama bagus dengan PDF.

### Q: Bisa ganti warna/design laporan?
**A**: Ya! Edit CSS di file template (`report_pdf.html` atau `report_summary_pdf.html`). Server akan auto-reload, refresh browser untuk preview.

### Q: Data dari mana untuk charts?
**A**: Chart placeholder sudah ada di template. Untuk actual charts, bisa integrate matplotlib atau chart library lainnya.

### Q: Bisa schedule auto-generate laporan?
**A**: Bisa! Buat Celery task atau cronjob yang call endpoint secara otomatis. Template sudah siap.

### Q: Laporan bisa email ke admin?
**A**: Bisa! Buat view tambahan yang generate PDF, lalu kirim via Django mail backend.

### Q: Performa level 'Sangat Baik' threshold 90% bisa diubah?
**A**: Ya, edit di `teacher_service.py` fungsi `get_teacher_attendance_summary()`:
```python
if hadir_rate >= 90:  # Ubah angka ini
    performance_level = 'excellent'
```

---

## 📞 TROUBLESHOOTING

### Error: "Template not found"
- Check path: `templates/attendance/teacher/report_pdf.html` harus ada
- Verify TEMPLATES setting di `settings.py`

### Error: "WeasyPrint not available"
- Ini **bukan error**, sistem akan fallback ke HTML
- Jika ingin PDF, install: `pip install weasyprint`

### PDF tidak terdownload, hanya preview HTML
- Normal kalau WeasyPrint tidak tersedia
- Browser print (Cmd+P / Ctrl+P) kemudian save sebagai PDF

### Performance badge tidak muncul
- Check data: guru harus punya attendance records
- Check date range: pastikan start_date < end_date

---

## 📊 CONTOH DATA YANG DITAMPILKAN

```
Laporan Kehadiran Ustadz Abdullah Hasan
Periode: 1 Januari 2026 - 31 Januari 2026

┌─────────────────────────────────────┐
│  Nama Guru: Ustadz Abdullah Hasan   │
│  ID Guru: UST001                    │
│  NIP: 000000000000000001            │
│  Tanggal Cetak: 19 Jan 2026 14:09   │
└─────────────────────────────────────┘

PERFORMANCE: [🟢 SANGAT BAIK]

┌──────────────────────────────────────────┐
│ Hadir: 85 (90.5%)  │ Sakit: 5 (5.3%)    │
│ Izin: 3 (3.2%)     │ Alpa: 1 (1.0%)     │
└──────────────────────────────────────────┘

Tingkat Kehadiran: ████████░ 90.5% (Target: 90%)

[Pie Chart Placeholder]   [Trend Chart Placeholder]

─── DETAIL KEHADIRAN HARIAN ───
Tanggal     | Hari  | Status | JP Detail | Keterangan
2026-01-01  | Sel   | Hadir  | JP1:H JP2:H| -
2026-01-02  | Rab   | Hadir  | JP1:H JP2:S| Sakit pagi
...
```

---

**Last Updated**: January 19, 2026
**Status**: ✅ Ready for Production
