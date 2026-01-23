# Fitur Print Laporan Absensi Ustadz

## 📋 Overview
Fitur print telah ditambahkan ke halaman laporan absensi ustadz untuk memudahkan pencetakan dokumen laporan dengan format yang profesional dan terstandarisasi.

## ✨ Fitur

### 1. **Tombol Print**
- Lokasi: Di bagian action buttons, sejajar dengan tombol "Generate Report"
- Fungsi: Print langsung dari browser menggunakan `window.print()`
- Icon: 🖨️ Print

### 2. **Format Print**
- **Orientasi:** Landscape (mendatar)
- **Ukuran Kertas:** A4
- **Margin:** 1.5cm di semua sisi
- **Warna:** Full color dengan preserve colors untuk badges dan status

### 3. **Konten yang Di-print**

#### A. Header (Otomatis muncul saat print)
```
SIPA YAUMI
Sistem Informasi Presensi Pesantren Yaumi
─────────────────────────────────────────
LAPORAN ABSENSI USTADZ
Periode: [Tanggal Mulai] - [Tanggal Akhir]
```

#### B. Isi Laporan
- **Statistik Cards:** Total JP, Hadir, Sakit/Izin, Alpa
- **Grafik Breakdown:** Pie chart status kehadiran
- **Informasi Ustadz:** Foto, NIP, Nama, Mata Pelajaran
- **Tabel Detail Absensi:** Tanggal, JP, Mata Pelajaran, Kelas, Status, Keterangan

#### C. Footer (Otomatis muncul saat print)
- **Area Tanda Tangan:**
  - Kepala Sekolah (kiri)
  - Dicetak oleh: [Nama User] + Tanggal (tengah)
  - Bagian Kepegawaian (kanan)
  
- **QR Code Verifikasi:**
  - QR code untuk verifikasi dokumen
  - Document ID: TR-[Teacher ID]-[Start Date]-[End Date]
  - URL verifikasi: `/verify-report/[Document ID]`

### 4. **Elemen yang Disembunyikan Saat Print**
- Sidebar navigation
- Top navbar
- Breadcrumb
- Semua tombol dan form filter
- Alert messages
- Background colors halaman

### 5. **Optimasi Print**
- **Font Size:** 9-10pt untuk tabel, 11-18pt untuk header
- **Page Break:** Otomatis di tempat yang tepat
- **Color Preservation:** Warna badge dan status tetap muncul
- **Zebra Striping:** Baris tabel bergantian warna untuk readability
- **Border:** Tabel dengan border solid untuk clarity

## 🎨 Styling

### CSS Print File
File: `static/css/print-report.css`

Berisi semua styling khusus untuk print:
- Page setup (@page rules)
- Element visibility
- Layout adjustments
- Color preservation
- Typography optimization

### Cara Penggunaan di Template
```django
{% load static %}

{% block extra_css %}
{% if report_data %}
<link href="{% static 'css/print-report.css' %}" rel="stylesheet">
{% endif %}
{% endblock %}
```

## 🔧 Implementasi Teknis

### 1. Print Button
```html
<button type="button" class="btn btn-secondary" onclick="window.print()">
    <i class="fas fa-print me-2"></i>
    Print
</button>
```

### 2. Print Header
```html
<div class="print-header">
    <h2>SIPA YAUMI</h2>
    <h3>Sistem Informasi Presensi Pesantren Yaumi</h3>
    <div class="period">
        <strong>LAPORAN ABSENSI USTADZ</strong><br>
        Periode: {{ start_date|date:"d F Y" }} - {{ end_date|date:"d F Y" }}
    </div>
</div>
```

### 3. Print Footer dengan QR Code
```html
<div class="print-footer">
    <div class="signature-section">
        <!-- 3 signature boxes -->
    </div>
    <div class="qr-code-section">
        <div id="qrcode"></div>
        <div>Scan QR code untuk verifikasi dokumen</div>
    </div>
</div>
```

### 4. QR Code Generation
```javascript
// Library: qrcodejs
<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>

// Generate QR Code
new QRCode(document.getElementById('qrcode'), {
    text: verificationUrl,
    width: 80,
    height: 80,
    colorDark: "#000000",
    colorLight: "#ffffff",
    correctLevel: QRCode.CorrectLevel.M
});
```

## 📱 Browser Compatibility
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ Opera

## 🚀 Cara Menggunakan

### Untuk User:
1. Buka halaman "Laporan Ustadz"
2. Pilih ustadz dan rentang tanggal
3. Klik "Generate Report"
4. Klik tombol "Print" 🖨️
5. Dialog print browser akan muncul
6. Pilih printer atau "Save as PDF"
7. Klik "Print"

### Tips Print:
- **Preview:** Browser otomatis menampilkan preview sebelum print
- **Save as PDF:** Pilih "Save as PDF" di dialog print untuk menyimpan
- **Page Range:** Bisa pilih halaman tertentu jika dokumen panjang
- **Copies:** Bisa pilih jumlah copy yang diinginkan

## 📊 Halaman yang Sudah Mendukung Print

1. ✅ **Laporan Absensi Ustadz** (`/teacher-report/`)
   - Print individual teacher report
   - Dengan QR code dan tanda tangan

2. ✅ **Analytics Ustadz** (`/teacher-analytics/`)
   - Print analytics dengan grafik
   - Tombol print sudah ditambahkan

## 🔮 Future Enhancements

### Planned:
- [ ] Print preview modal sebelum print
- [ ] Custom print options (pilih apa yang di-print)
- [ ] Watermark untuk dokumen draft
- [ ] Multiple teacher report print (batch)
- [ ] Email report langsung dari sistem

### Under Consideration:
- [ ] Print template customization
- [ ] Logo pesantren di header
- [ ] Digital signature integration
- [ ] Automatic archiving of printed reports

## 📝 Notes

### Document ID Format:
```
TR-[8 digit Teacher ID]-[YYYYMMDD Start]-[YYYYMMDD End]
Example: TR-a1b2c3d4-20260101-20260131
```

### QR Code URL:
```
https://[domain]/verify-report/TR-a1b2c3d4-20260101-20260131
```

### Verification Endpoint:
**Note:** Endpoint `/verify-report/<doc_id>/` belum diimplementasikan.
Ini adalah placeholder untuk future feature.

## 🐛 Known Issues
- None at the moment

## 📞 Support
Jika ada masalah dengan fitur print, hubungi tim development.

---

**Last Updated:** 23 Januari 2026
**Version:** 1.0.0
**Author:** Kiro AI Assistant
