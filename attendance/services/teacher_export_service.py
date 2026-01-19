"""
Teacher Export Service
Handle export to Excel and PDF
"""
import io
from datetime import datetime
from django.http import HttpResponse
from django.utils import timezone
from django.template.loader import render_to_string
import logging

# PDF imports - ReportLab (untuk backward compatibility)
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

# WeasyPrint untuk HTML→PDF conversion
WEASYPRINT_AVAILABLE = False
try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    logger.debug(f"WeasyPrint not available: {str(e)}. HTML export will fallback to template preview.")


class TeacherExportService:
    """Service for exporting teacher attendance data"""
    
    @staticmethod
    def export_to_excel(teachers_data, start_date=None, end_date=None):
        """
        Export teacher attendance report to Excel
        
        Args:
            teachers_data: List of dicts with teacher and summary
            start_date: Start date for report
            end_date: End date for report
            
        Returns:
            HttpResponse with Excel file
        """
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
            from openpyxl.utils import get_column_letter
            
            # Create workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "Laporan Absensi Ustadz"
            
            # Title
            ws.merge_cells('A1:L1')
            title_cell = ws['A1']
            title_cell.value = "LAPORAN ABSENSI USTADZ"
            title_cell.font = Font(size=16, bold=True)
            title_cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # Date range
            if start_date and end_date:
                ws.merge_cells('A2:L2')
                date_cell = ws['A2']
                date_cell.value = f"Periode: {start_date.strftime('%d %B %Y')} - {end_date.strftime('%d %B %Y')}"
                date_cell.alignment = Alignment(horizontal='center')
            
            # Headers
            headers = [
                'No', 'ID Ustadz', 'Nama', 'Mata Pelajaran', 
                'Total Hari', 'Total JP', 'Hadir', 'Sakit', 'Izin', 'Alpa',
                'Lainnya', 'Persentase (%)'
            ]
            
            header_row = 4
            for col_num, header in enumerate(headers, 1):
                cell = ws.cell(row=header_row, column=col_num)
                cell.value = header
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
            
            # Data rows
            row_num = header_row + 1
            for idx, item in enumerate(teachers_data, 1):
                teacher = item['teacher']
                summary = item['summary']
                
                # Calculate "Lainnya" (other statuses)
                lainnya = (
                    summary.get('tidak_ada_jadwal', 0) +
                    summary.get('dinas_luar', 0) +
                    summary.get('cuti', 0) +
                    summary.get('terlambat', 0)
                )
                
                data = [
                    idx,
                    teacher.teacher_id,
                    teacher.name,
                    teacher.subjects or '-',
                    summary['total_days'],
                    summary['total_jp'],
                    summary['hadir'],
                    summary['sakit'],
                    summary['izin'],
                    summary['alpa'],
                    lainnya,
                    summary['attendance_rate']
                ]
                
                for col_num, value in enumerate(data, 1):
                    cell = ws.cell(row=row_num, column=col_num)
                    cell.value = value
                    cell.border = Border(
                        left=Side(style='thin'),
                        right=Side(style='thin'),
                        top=Side(style='thin'),
                        bottom=Side(style='thin')
                    )
                    
                    # Alignment
                    if col_num in [1, 5, 6, 7, 8, 9, 10, 11, 12]:  # Numbers
                        cell.alignment = Alignment(horizontal='center')
                    else:
                        cell.alignment = Alignment(horizontal='left')
                
                row_num += 1
            
            # Summary row
            if teachers_data:
                summary_row = row_num + 1
                ws.merge_cells(f'A{summary_row}:D{summary_row}')
                summary_cell = ws[f'A{summary_row}']
                summary_cell.value = "TOTAL"
                summary_cell.font = Font(bold=True)
                summary_cell.alignment = Alignment(horizontal='center')
                
                # Calculate totals
                total_days = sum(item['summary']['total_days'] for item in teachers_data)
                total_jp = sum(item['summary']['total_jp'] for item in teachers_data)
                total_hadir = sum(item['summary']['hadir'] for item in teachers_data)
                total_sakit = sum(item['summary']['sakit'] for item in teachers_data)
                total_izin = sum(item['summary']['izin'] for item in teachers_data)
                total_alpa = sum(item['summary']['alpa'] for item in teachers_data)
                
                avg_percentage = round(
                    sum(item['summary']['attendance_rate'] for item in teachers_data) / len(teachers_data),
                    2
                ) if teachers_data else 0
                
                totals = [total_days, total_jp, total_hadir, total_sakit, total_izin, total_alpa, '-', avg_percentage]
                
                for col_num, value in enumerate(totals, 5):
                    cell = ws.cell(row=summary_row, column=col_num)
                    cell.value = value
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal='center')
            
            # Adjust column widths
            column_widths = [5, 12, 25, 25, 12, 10, 10, 10, 10, 10, 10, 12]
            for i, width in enumerate(column_widths, 1):
                ws.column_dimensions[get_column_letter(i)].width = width
            
            # Save to BytesIO
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            
            # Create response
            filename = f"laporan_absensi_ustadz_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except ImportError:
            logger.error("openpyxl not installed")
            raise Exception("Library openpyxl tidak terinstall. Install dengan: pip install openpyxl")
        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}")
            raise Exception(f"Gagal export ke Excel: {str(e)}")
    
    @staticmethod
    def export_to_csv(teachers_data, start_date=None, end_date=None):
        """
        Export teacher attendance report to CSV
        
        Args:
            teachers_data: List of dicts with teacher and summary
            start_date: Start date for report
            end_date: End date for report
            
        Returns:
            HttpResponse with CSV file
        """
        import csv
        
        try:
            # Create response
            filename = f"laporan_absensi_ustadz_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            writer = csv.writer(response)
            
            # Title
            writer.writerow(['LAPORAN ABSENSI USTADZ'])
            if start_date and end_date:
                writer.writerow([f"Periode: {start_date.strftime('%d %B %Y')} - {end_date.strftime('%d %B %Y')}"])
            writer.writerow([])
            
            # Headers
            writer.writerow([
                'No', 'ID Ustadz', 'Nama', 'Mata Pelajaran',
                'Total Hari', 'Total JP', 'Hadir', 'Sakit', 'Izin', 'Alpa',
                'Lainnya', 'Persentase (%)'
            ])
            
            # Data
            for idx, item in enumerate(teachers_data, 1):
                teacher = item['teacher']
                summary = item['summary']
                
                lainnya = (
                    summary.get('tidak_ada_jadwal', 0) +
                    summary.get('dinas_luar', 0) +
                    summary.get('cuti', 0) +
                    summary.get('terlambat', 0)
                )
                
                writer.writerow([
                    idx,
                    teacher.teacher_id,
                    teacher.name,
                    teacher.subjects or '-',
                    summary['total_days'],
                    summary['total_jp'],
                    summary['hadir'],
                    summary['sakit'],
                    summary['izin'],
                    summary['alpa'],
                    lainnya,
                    summary['attendance_rate']
                ])
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            raise Exception(f"Gagal export ke CSV: {str(e)}")
    
    @staticmethod
    def export_to_pdf(teachers_data, start_date=None, end_date=None):
        """
        Export teacher attendance report to PDF using PROFESSIONAL ReportLab
        with A4 paper size, chart, KPI styling, and modern layout
        
        Args:
            teachers_data: List of dicts with teacher and summary
            start_date: Start date for report
            end_date: End date for report
            
        Returns:
            HttpResponse with PDF file
        """
        try:
            from reportlab.platypus import Image, SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            from reportlab.lib.units import cm
            import base64
            from io import BytesIO
            
            # Lazy load matplotlib
            MATPLOTLIB_AVAILABLE = False
            try:
                import matplotlib
                matplotlib.use('Agg')
                import matplotlib.pyplot as plt
                MATPLOTLIB_AVAILABLE = True
            except ImportError:
                logger.warning("Matplotlib not available. Charts will be skipped.")
            
            # Default dates
            if not start_date:
                start_date = timezone.now().date()
            if not end_date:
                end_date = timezone.now().date()
            
            # Create PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.8*cm, bottomMargin=0.8*cm, 
                                   leftMargin=1*cm, rightMargin=1*cm)
            
            # Setup styles
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1F4788'),
                spaceAfter=3,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.HexColor('#555555'),
                spaceAfter=12,
                alignment=TA_CENTER,
                fontName='Helvetica'
            )
            
            period_style = ParagraphStyle(
                'Period',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#666666'),
                spaceAfter=12,
                alignment=TA_CENTER,
                fontName='Helvetica-Oblique'
            )
            
            section_style = ParagraphStyle(
                'SectionTitle',
                parent=styles['Heading2'],
                fontSize=13,
                textColor=colors.HexColor('#1F4788'),
                spaceAfter=6,
                spaceBefore=8,
                fontName='Helvetica-Bold',
                borderColor=colors.HexColor('#1F4788'),
                borderWidth=2,
                borderPadding=4
            )
            
            # Container for elements
            elements = []
            
            # Header
            elements.append(Paragraph("PESANTREN YAUMI YOGYAKARTA", title_style))
            elements.append(Paragraph("Sistem Informasi Presensi (SIPA Beta)", subtitle_style))
            elements.append(Paragraph("LAPORAN KEHADIRAN GURU", ParagraphStyle(
                'ReportTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#2C3E50'),
                spaceAfter=3,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )))
            
            # Period
            if start_date and end_date:
                period_text = f"Periode: {start_date.strftime('%d %B %Y')} - {end_date.strftime('%d %B %Y')}"
            else:
                period_text = f"Tanggal: {timezone.now().strftime('%d %B %Y')}"
            elements.append(Paragraph(period_text, period_style))
            elements.append(Spacer(1, 0.3*cm))
            
            # Calculate summary statistics
            total_teachers = len(teachers_data)
            total_hadir = sum(item['summary']['hadir'] for item in teachers_data)
            total_sakit = sum(item['summary']['sakit'] for item in teachers_data)
            total_izin = sum(item['summary']['izin'] for item in teachers_data)
            total_alpa = sum(item['summary']['alpa'] for item in teachers_data)
            avg_attendance = (
                sum(item['summary']['attendance_rate'] for item in teachers_data) / total_teachers
            ) if total_teachers > 0 else 0
            
            # KPI Cards (simplified table-based approach)
            kpi_data = [
                [
                    'HADIR',
                    'SAKIT',
                    'IZIN',
                    'ALPA'
                ],
                [
                    str(total_hadir),
                    str(total_sakit),
                    str(total_izin),
                    str(total_alpa)
                ]
            ]
            
            kpi_table = Table(kpi_data, colWidths=[3*cm, 3*cm, 3*cm, 3*cm])
            kpi_table.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('PADDING', (0, 0), (-1, 0), 8),
                
                # Data rows
                ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#D5F4E6')),
                ('BACKGROUND', (1, 1), (1, 1), colors.HexColor('#FEF5E7')),
                ('BACKGROUND', (2, 1), (2, 1), colors.HexColor('#D6EAF8')),
                ('BACKGROUND', (3, 1), (3, 1), colors.HexColor('#FADBD8')),
                
                ('TEXTCOLOR', (0, 1), (0, 1), colors.HexColor('#27AE60')),
                ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#F39C12')),
                ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor('#2980B9')),
                ('TEXTCOLOR', (3, 1), (3, 1), colors.HexColor('#E74C3C')),
                
                ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, 1), 16),
                ('PADDING', (0, 1), (-1, 1), 12),
                
                ('GRID', (0, 0), (-1, -1), 1.5, colors.HexColor('#ECEFF1')),
            ]))
            
            elements.append(kpi_table)
            elements.append(Spacer(1, 0.4*cm))
            
            # Attendance percentage
            elements.append(Paragraph(f"Rata-rata Tingkat Kehadiran: <b>{avg_attendance:.1f}%</b>", ParagraphStyle(
                'Average',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#27AE60'),
                alignment=TA_CENTER,
                spaceAfter=6
            )))
            
            # Generate chart if matplotlib available
            chart_image = None
            if MATPLOTLIB_AVAILABLE:
                try:
                    fig, ax = plt.subplots(figsize=(5, 3.5), dpi=100)
                    labels = ['Hadir', 'Sakit', 'Izin', 'Alpa']
                    sizes = [total_hadir, total_sakit, total_izin, total_alpa]
                    colors_pie = ['#27ae60', '#f39c12', '#2980b9', '#e74c3c']
                    explode = (0.05, 0, 0, 0)
                    
                    ax.pie(sizes, explode=explode, labels=labels, colors=colors_pie, autopct='%1.1f%%',
                           shadow=True, startangle=90, textprops={'fontsize': 9, 'weight': 'bold'})
                    ax.axis('equal')
                    
                    chart_buffer = BytesIO()
                    plt.savefig(chart_buffer, format='png', bbox_inches='tight', dpi=100)
                    chart_buffer.seek(0)
                    plt.close(fig)
                    
                    chart_image = Image(chart_buffer, width=6*cm, height=4.5*cm)
                    elements.append(chart_image)
                    elements.append(Spacer(1, 0.3*cm))
                except Exception as chart_error:
                    logger.warning(f"Chart generation failed: {chart_error}")
            
            elements.append(Spacer(1, 0.3*cm))
            
            # Detail Table
            elements.append(Paragraph("DETAIL KEHADIRAN GURU", section_style))
            elements.append(Spacer(1, 0.2*cm))
            
            table_data = [[
                'No',
                'ID Guru',
                'Nama',
                'Hadir',
                'Sakit',
                'Izin',
                'Alpa',
                'Kehadiran (%)'
            ]]
            
            # Add data rows
            for idx, item in enumerate(teachers_data, 1):
                teacher = item['teacher']
                summary = item['summary']
                
                table_data.append([
                    str(idx),
                    str(teacher.teacher_id)[:8],
                    teacher.name[:20],
                    str(summary['hadir']),
                    str(summary['sakit']),
                    str(summary['izin']),
                    str(summary['alpa']),
                    f"{summary['attendance_rate']:.1f}%"
                ])
            
            # Add average row
            if teachers_data:
                table_data.append([
                    '',
                    '',
                    'RATA-RATA',
                    f"{total_hadir/total_teachers:.1f}" if total_teachers > 0 else '0',
                    f"{total_sakit/total_teachers:.1f}" if total_teachers > 0 else '0',
                    f"{total_izin/total_teachers:.1f}" if total_teachers > 0 else '0',
                    f"{total_alpa/total_teachers:.1f}" if total_teachers > 0 else '0',
                    f"{avg_attendance:.1f}%"
                ])
            
            # Create table
            table = Table(table_data, colWidths=[0.6*cm, 1.2*cm, 3*cm, 0.9*cm, 0.9*cm, 0.9*cm, 0.9*cm, 1.2*cm])
            
            # Style table
            table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('PADDING', (0, 0), (-1, 0), 6),
                
                # Data rows
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 8),
                ('ALIGN', (0, 1), (-1, -2), 'CENTER'),
                ('ALIGN', (2, 1), (2, -2), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ECEFF1')),
                
                # Alternating row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F5F8FA')]),
                
                # Average row
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8F0F7')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 9),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1F4788')),
                ('PADDING', (0, -1), (-1, -1), 6),
            ]))
            
            elements.append(table)
            
            # Footer
            elements.append(Spacer(1, 0.4*cm))
            footer_text = f"Generated: {timezone.now().strftime('%d %B %Y at %H:%M')} | Total Guru: {total_teachers}"
            elements.append(Paragraph(footer_text, ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#999999'),
                alignment=TA_CENTER
            )))
            
            # Build PDF
            doc.build(elements)
            
            # Return PDF response
            buffer.seek(0)
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="laporan_kehadiran_guru_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting teacher attendance PDF: {str(e)}")
            raise Exception(f"Gagal membuat laporan PDF guru: {str(e)}")
    
    @staticmethod
    def export_teacher_individual_pdf(teacher, start_date=None, end_date=None):
        """
        Export individual teacher attendance report to PDF
        Format sama seperti student report - dengan detail per JP per hari
        
        Args:
            teacher: Teacher instance
            start_date: Start date
            end_date: End date
            
        Returns:
            HttpResponse with PDF file
        """
        try:
            from attendance.services.teacher_service import TeacherService
            from attendance.models import TeacherDailyAttendance
            from django.utils import timezone
            
            # Get summary
            summary = TeacherService.get_teacher_attendance_summary(
                teacher, start_date=start_date, end_date=end_date
            )
            
            # Default dates
            if not start_date:
                start_date = timezone.now().date()
            if not end_date:
                end_date = timezone.now().date()
            
            # Create PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            
            # Custom styles (match student PDF style)
            title_style = ParagraphStyle(
                'ReportTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#6B5344'),
                alignment=TA_CENTER,
                spaceAfter=12,
                fontName='Helvetica-Bold'
            )
            
            subtitle_style = ParagraphStyle(
                'ReportSubtitle',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.HexColor('#6B6560'),
                alignment=TA_CENTER,
                spaceAfter=12,
                fontName='Helvetica'
            )
            
            section_header_style = ParagraphStyle(
                'SectionHeader',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor('#8B7355'),
                spaceBefore=15,
                spaceAfter=8,
                fontName='Helvetica-Bold'
            )
            
            elements = []
            
            # Title
            elements.append(Paragraph("Laporan Kehadiran Ustadz Per JP", title_style))
            
            # Teacher info
            teacher_info = f"<b>{teacher.name}</b><br/>ID: {teacher.teacher_id} | NIP: {teacher.nip or '-'} | Mata Pelajaran: {teacher.subjects or '-'}"
            elements.append(Paragraph(teacher_info, subtitle_style))
            
            # Date range
            date_range = f"Periode: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
            elements.append(Paragraph(date_range, subtitle_style))
            
            # Build attendance detail table (tanggal x JP format)
            elements.extend(
                TeacherExportService._build_teacher_attendance_detail(teacher, start_date, end_date, styles)
            )
            
            # Add summary section
            elements.append(Spacer(1, 20))
            elements.extend(
                TeacherExportService._build_teacher_summary_table(summary, section_header_style, styles)
            )
            
            # Build PDF
            doc.build(elements)
            
            # Return response
            buffer.seek(0)
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            filename = f"laporan_{teacher.teacher_id}_{timezone.now().strftime('%Y%m%d')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting individual teacher PDF: {str(e)}")
            raise Exception(f"Gagal export laporan ustadz: {str(e)}")
    
    @staticmethod
    def _build_teacher_attendance_detail(teacher, start_date, end_date, styles):
        """Build attendance detail table dengan format Tanggal x JP (sama seperti student)"""
        from attendance.models import TeacherDailyAttendance, TeacherSchedule
        from django.utils import timezone
        
        elements = []
        
        # Color definitions (matching student PDF style)
        COLORS = {
            'primary': colors.HexColor('#8B7355'),
            'header_bg': colors.HexColor('#F8F6F4'),
            'hadir': colors.HexColor('#4CAF50'),
            'sakit': colors.HexColor('#FF9800'),
            'izin': colors.HexColor('#2196F3'),
            'alpa': colors.HexColor('#F44336'),
            'border': colors.HexColor('#E8E4E0'),
        }
        
        # Section header
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=COLORS['primary'],
            spaceBefore=10,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph("Detail Kehadiran Per Hari", section_style))
        
        # Get all records dalam range
        daily_records = TeacherDailyAttendance.objects.filter(
            teacher=teacher,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        if not daily_records.exists():
            elements.append(Paragraph("Tidak ada data kehadiran untuk ditampilkan.", styles['Normal']))
            return elements
        
        # Find max JP count
        max_jp = 0
        for record in daily_records:
            if record.jp_statuses:
                max_jp = max(max_jp, max([int(k) for k in record.jp_statuses.keys()]))
        
        # Build header row
        header = ['No', 'Tanggal', 'Hari']
        for jp_num in range(1, max_jp + 1):
            header.append(f'JP{jp_num}')
        header.extend(['H', 'S', 'I', 'A'])
        
        # Build data rows
        data = [header]
        day_names = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
        
        for idx, record in enumerate(daily_records, 1):
            row = [
                str(idx),
                record.date.strftime('%d/%m/%Y'),
                day_names[record.date.weekday()][:3],
            ]
            
            # Add JP statuses
            for jp_num in range(1, max_jp + 1):
                status = record.jp_statuses.get(str(jp_num), '-') if record.jp_statuses else '-'
                row.append(status)
            
            # Add day summary
            day_sum = {
                'hadir': sum(1 for s in record.jp_statuses.values() if s == 'H') if record.jp_statuses else 0,
                'sakit': sum(1 for s in record.jp_statuses.values() if s == 'S') if record.jp_statuses else 0,
                'izin': sum(1 for s in record.jp_statuses.values() if s == 'I') if record.jp_statuses else 0,
                'alpa': sum(1 for s in record.jp_statuses.values() if s == 'A') if record.jp_statuses else 0,
            }
            row.extend([
                str(day_sum['hadir']),
                str(day_sum['sakit']),
                str(day_sum['izin']),
                str(day_sum['alpa']),
            ])
            
            data.append(row)
        
        # Calculate column widths (sama seperti student)
        available_width = A4[0] - 3*cm
        fixed_widths = [0.8*cm, 2.2*cm, 1.2*cm]
        summary_widths = [0.8*cm, 0.8*cm, 0.8*cm, 0.8*cm]
        fixed_total = sum(fixed_widths) + sum(summary_widths)
        remaining = available_width - fixed_total
        jp_col_width = remaining / max_jp if max_jp > 0 else 1*cm
        col_widths = fixed_widths + [jp_col_width] * max_jp + summary_widths
        
        # Create table
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        # Apply table style with status coloring (sama seperti student)
        table_style = [
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Data style
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, COLORS['border']),
            ('BOX', (0, 0), (-1, -1), 1, COLORS['primary']),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLORS['header_bg']]),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ]
        
        # Add status-based coloring for JP columns
        for row_idx, record in enumerate(daily_records, 1):
            for jp_num in range(1, max_jp + 1):
                col_idx = 3 + (jp_num - 1)
                status = record.jp_statuses.get(str(jp_num), '-') if record.jp_statuses else '-'
                
                if status == 'H':
                    table_style.append(
                        ('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), COLORS['hadir'])
                    )
                elif status == 'S':
                    table_style.append(
                        ('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), COLORS['sakit'])
                    )
                elif status == 'I':
                    table_style.append(
                        ('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), COLORS['izin'])
                    )
                elif status == 'A':
                    table_style.append(
                        ('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), COLORS['alpa'])
                    )
        
        table.setStyle(TableStyle(table_style))
        elements.append(table)
        
        # Add legend
        elements.append(Spacer(1, 15))
        legend = Paragraph(
            "<b>Keterangan Status:</b> H = Hadir, S = Sakit, I = Izin, A = Alpa",
            styles['Normal']
        )
        elements.append(legend)
        
        return elements
    
    @staticmethod
    def _build_teacher_summary_table(summary, section_header_style, styles):
        """Build summary statistics table (sama format seperti student PDF)"""
        from attendance.models import TeacherDailyAttendance
        
        elements = []
        
        # Color definitions (matching student PDF)
        COLORS = {
            'primary': colors.HexColor('#8B7355'),
            'header_bg': colors.HexColor('#F8F6F4'),
            'hadir': colors.HexColor('#4CAF50'),
            'sakit': colors.HexColor('#FF9800'),
            'izin': colors.HexColor('#2196F3'),
            'alpa': colors.HexColor('#F44336'),
            'border': colors.HexColor('#E8E4E0'),
        }
        
        # Section header (using provided style)
        elements.append(Paragraph("Statistik Kehadiran", section_header_style))
        
        # Build summary table (same structure as student PDF)
        data = [
            ['Status', 'Jumlah', 'Persentase'],
            ['Hadir', str(summary.get('hadir', 0)), f"{summary.get('hadir_rate', 0):.1f}%"],
            ['Sakit', str(summary.get('sakit', 0)), f"{summary.get('sakit_rate', 0):.1f}%"],
            ['Izin', str(summary.get('izin', 0)), f"{summary.get('izin_rate', 0):.1f}%"],
            ['Alpa', str(summary.get('alpa', 0)), f"{summary.get('alpa_rate', 0):.1f}%"],
        ]
        
        # Calculate widths
        available_width = A4[0] - 3*cm
        col_widths = [available_width * 0.4, available_width * 0.3, available_width * 0.3]
        
        # Create table
        table = Table(data, colWidths=col_widths)
        
        # Apply styling (exact same as student PDF)
        table_style = [
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            
            # Alternating backgrounds
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLORS['header_bg']]),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 0.5, COLORS['border']),
            ('BOX', (0, 0), (-1, -1), 1, COLORS['primary']),
        ]
        
        # Add status-based coloring untuk nilai
        status_colors = {
            'Hadir': COLORS['hadir'],
            'Sakit': COLORS['sakit'],
            'Izin': COLORS['izin'],
            'Alpa': COLORS['alpa'],
        }
        
        for row_idx in range(1, 5):
            status = data[row_idx][0]
            color = status_colors.get(status, COLORS['primary'])
            table_style.append(
                ('TEXTCOLOR', (1, row_idx), (2, row_idx), color)
            )
        
        table.setStyle(TableStyle(table_style))
        elements.append(table)
        
        return elements

    @staticmethod
    def export_teacher_attendance_pdf_html(teacher, start_date=None, end_date=None):
        """
        Export individual teacher attendance report to PDF menggunakan HTML+CSS template
        Menghasilkan desain modern, minimalis dengan better visual quality
        
        Args:
            teacher: Teacher instance
            start_date: Start date untuk report
            end_date: End date untuk report
            
        Returns:
            HttpResponse dengan PDF file atau HTML preview
        """
        from attendance.services.teacher_service import TeacherService
        from attendance.models import TeacherDailyAttendance
        
        try:
            # Default dates
            if not start_date:
                start_date = timezone.now().date()
            if not end_date:
                end_date = timezone.now().date()
            
            # Get teacher attendance data
            summary = TeacherService.get_teacher_attendance_summary(
                teacher, start_date=start_date, end_date=end_date
            )
            
            # Get daily records
            daily_records = TeacherDailyAttendance.objects.filter(
                teacher=teacher,
                date__gte=start_date,
                date__lte=end_date
            ).order_by('date')
            
            # Format daily records dengan detail
            formatted_records = []
            day_names = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
            
            status_map = {
                'H': 'Hadir',
                'S': 'Sakit',
                'I': 'Izin',
                'A': 'Alpa'
            }
            
            status_code_map = {
                'H': 'hadir',
                'S': 'sakit',
                'I': 'izin',
                'A': 'alpa'
            }
            
            for record in daily_records:
                # Determine primary status (most common on that day)
                if record.jp_statuses:
                    statuses = list(record.jp_statuses.values())
                    # Priority: A > I > S > H
                    if 'A' in statuses:
                        primary_status = 'A'
                    elif 'I' in statuses:
                        primary_status = 'I'
                    elif 'S' in statuses:
                        primary_status = 'S'
                    else:
                        primary_status = 'H'
                else:
                    primary_status = 'A'
                
                formatted_records.append({
                    'date': record.date,
                    'day_name': day_names[record.date.weekday()],
                    'status': status_map.get(primary_status, 'Alpa'),
                    'status_code': status_code_map.get(primary_status, 'alpa'),
                    'jp_details': {
                        f"JP{k}": status_map.get(v, v)
                        for k, v in (record.jp_statuses.items() if record.jp_statuses else {}).items()
                    },
                    'notes': getattr(record, 'notes', '')
                })
            
            # Determine performance level berdasarkan attendance rate
            attendance_rate = summary.get('hadir_rate', 0)
            if attendance_rate >= 90:
                performance_level = 'excellent'
                performance_label = 'SANGAT BAIK (90%+)'
            elif attendance_rate >= 80:
                performance_level = 'good'
                performance_label = 'BAIK (80-89%)'
            elif attendance_rate >= 70:
                performance_level = 'fair'
                performance_label = 'CUKUP (70-79%)'
            else:
                performance_level = 'poor'
                performance_label = 'KURANG (<70%)'
            
            # Context untuk template
            context = {
                'teacher': teacher,
                'start_date': start_date,
                'end_date': end_date,
                'print_date': timezone.now(),
                'stats': {
                    'total_hadir': summary.get('hadir', 0),
                    'total_sakit': summary.get('sakit', 0),
                    'total_izin': summary.get('izin', 0),
                    'total_alpa': summary.get('alpa', 0),
                    'hadir_percentage': summary.get('hadir_rate', 0),
                    'sakit_percentage': summary.get('sakit_rate', 0),
                    'izin_percentage': summary.get('izin_rate', 0),
                    'alpa_percentage': summary.get('alpa_rate', 0),
                    'attendance_rate': summary.get('hadir_rate', 0),
                    'total_working_days': (end_date - start_date).days + 1,
                },
                'performance_level': performance_level,
                'performance_label': performance_label,
                'daily_records': formatted_records,
            }
            
            # Render HTML template
            html_content = render_to_string('attendance/teacher/report_pdf.html', context)
            
            # Convert HTML to PDF menggunakan WeasyPrint
            if WEASYPRINT_AVAILABLE:
                try:
                    pdf_file = weasyprint.HTML(string=html_content, base_url='/static/')
                    pdf_bytes = pdf_file.write_pdf()
                    
                    # Return PDF response
                    response = HttpResponse(pdf_bytes, content_type='application/pdf')
                    filename = f"laporan_{teacher.teacher_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    response['Content-Disposition'] = f'attachment; filename="{filename}"'
                    
                    return response
                    
                except Exception as e:
                    logger.error(f"WeasyPrint conversion error: {str(e)}")
                    # Fall back to HTML preview
                    response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
                    response['Content-Disposition'] = f'inline; filename="laporan_{teacher.teacher_id}.html"'
                    return response
            else:
                # Return HTML untuk preview jika WeasyPrint tidak tersedia
                logger.info("WeasyPrint not available, returning HTML for preview")
                response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
                response['Content-Disposition'] = f'inline; filename="laporan_{teacher.teacher_id}.html"'
                return response
            
        except Exception as e:
            logger.error(f"Error exporting teacher attendance PDF: {str(e)}")
            raise Exception(f"Gagal export laporan ustadz: {str(e)}")
    
    @staticmethod
    def export_all_teachers_pdf_html(teachers=None, start_date=None, end_date=None):
        """
        Export laporan semua guru ke PDF menggunakan HTML+CSS
        
        Args:
            teachers: List of Teacher instances (None = all teachers)
            start_date: Start date untuk report
            end_date: End date untuk report
            
        Returns:
            HttpResponse dengan PDF file
        """
        from attendance.models import Teacher
        from attendance.services.teacher_service import TeacherService
        
        try:
            # Default dates
            if not start_date:
                start_date = timezone.now().date()
            if not end_date:
                end_date = timezone.now().date()
            
            # Get all teachers jika tidak dispecify
            if not teachers:
                teachers = Teacher.objects.filter(is_active=True).order_by('name')
            
            # Siapkan context untuk template
            all_teachers_data = []
            
            for teacher in teachers:
                summary = TeacherService.get_teacher_attendance_summary(
                    teacher, start_date=start_date, end_date=end_date
                )
                
                all_teachers_data.append({
                    'teacher': teacher,
                    'summary': summary,
                })
            
            # Context
            context = {
                'teachers': all_teachers_data,
                'start_date': start_date,
                'end_date': end_date,
                'print_date': timezone.now(),
                'title': 'Laporan Kehadiran Semua Guru',
            }
            
            # Render HTML template
            html_content = render_to_string('attendance/teacher/report_summary_pdf.html', context)
            
            # Check WeasyPrint availability
            if WEASYPRINT_AVAILABLE:
                try:
                    pdf_file = weasyprint.HTML(string=html_content, base_url='/static/')
                    pdf_bytes = pdf_file.write_pdf()
                    
                    response = HttpResponse(pdf_bytes, content_type='application/pdf')
                    filename = f"laporan_semua_guru_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    response['Content-Disposition'] = f'attachment; filename="{filename}"'
                    
                    return response
                    
                except Exception as e:
                    logger.error(f"WeasyPrint conversion error: {str(e)}")
                    response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
                    response['Content-Disposition'] = f'inline; filename="laporan_semua_guru.html"'
                    return response
            else:
                response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
                response['Content-Disposition'] = f'inline; filename="laporan_semua_guru.html"'
                return response
            
        except Exception as e:
            logger.error(f"Error exporting all teachers PDF: {str(e)}")
            raise Exception(f"Gagal export laporan guru: {str(e)}")
