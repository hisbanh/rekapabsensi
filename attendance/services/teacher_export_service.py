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

# PDF imports
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)


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
        Export teacher attendance report to PDF
        
        Args:
            teachers_data: List of dicts with teacher and summary
            start_date: Start date for report
            end_date: End date for report
            
        Returns:
            HttpResponse with PDF file
        """
        try:
            # Create PDF response
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            
            # Set up styles
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#1F4788'),
                spaceAfter=6,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            subtitle_style = ParagraphStyle(
                'Subtitle',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.HexColor('#555555'),
                spaceAfter=12,
                alignment=TA_CENTER,
                fontName='Helvetica'
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor('#1F4788'),
                spaceAfter=6,
                spaceBefore=6,
                fontName='Helvetica-Bold'
            )
            
            # Container for elements
            elements = []
            
            # Title
            elements.append(Paragraph("LAPORAN ABSENSI USTADZ", title_style))
            
            # Date range
            if start_date and end_date:
                date_text = f"Periode: {start_date.strftime('%d %B %Y')} - {end_date.strftime('%d %B %Y')}"
            else:
                date_text = f"Tanggal: {timezone.now().strftime('%d %B %Y')}"
            
            elements.append(Paragraph(date_text, subtitle_style))
            elements.append(Spacer(1, 0.3*cm))
            
            # Prepare table data
            table_data = [[
                'No',
                'ID Ustadz',
                'Nama',
                'Mata Pelajaran',
                'Hari',
                'JP',
                'Hadir',
                'Sakit',
                'Izin',
                'Alpa',
                'Lainnya',
                '%'
            ]]
            
            # Add data rows
            for idx, item in enumerate(teachers_data, 1):
                teacher = item['teacher']
                summary = item['summary']
                
                lainnya = (
                    summary.get('tidak_ada_jadwal', 0) +
                    summary.get('dinas_luar', 0) +
                    summary.get('cuti', 0) +
                    summary.get('terlambat', 0)
                )
                
                table_data.append([
                    str(idx),
                    str(teacher.teacher_id),
                    teacher.name[:20],  # Truncate long names
                    teacher.subjects[:15] if teacher.subjects else '-',
                    str(summary['total_days']),
                    str(summary['total_jp']),
                    str(summary['hadir']),
                    str(summary['sakit']),
                    str(summary['izin']),
                    str(summary['alpa']),
                    str(lainnya),
                    f"{summary['attendance_rate']:.1f}%"
                ])
            
            # Add total row
            if teachers_data:
                total_days = sum(item['summary']['total_days'] for item in teachers_data)
                total_jp = sum(item['summary']['total_jp'] for item in teachers_data)
                total_hadir = sum(item['summary']['hadir'] for item in teachers_data)
                total_sakit = sum(item['summary']['sakit'] for item in teachers_data)
                total_izin = sum(item['summary']['izin'] for item in teachers_data)
                total_alpa = sum(item['summary']['alpa'] for item in teachers_data)
                avg_percentage = (
                    sum(item['summary']['attendance_rate'] for item in teachers_data) / len(teachers_data)
                ) if teachers_data else 0
                
                table_data.append([
                    '',
                    '',
                    'TOTAL',
                    '',
                    str(total_days),
                    str(total_jp),
                    str(total_hadir),
                    str(total_sakit),
                    str(total_izin),
                    str(total_alpa),
                    '',
                    f"{avg_percentage:.1f}%"
                ])
            
            # Create table
            table = Table(table_data, colWidths=[0.5*cm, 1.2*cm, 2*cm, 1.8*cm, 0.6*cm, 0.6*cm, 0.7*cm, 0.7*cm, 0.7*cm, 0.7*cm, 0.7*cm, 0.7*cm])
            
            # Style table
            table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                
                # Data rows
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 8),
                ('ALIGN', (0, 1), (-1, -2), 'CENTER'),
                ('ALIGN', (2, 1), (2, -2), 'LEFT'),
                ('ALIGN', (3, 1), (3, -2), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -2), 1, colors.grey),
                
                # Alternating row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F5F5F5')]),
                
                # Total row
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8E8E8')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 9),
                ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
                ('TOPPADDING', (0, -1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
            ]))
            
            elements.append(table)
            
            # Footer info
            elements.append(Spacer(1, 0.5*cm))
            footer_text = f"Generated: {timezone.now().strftime('%d %B %Y at %H:%M')}"
            elements.append(Paragraph(footer_text, ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER
            )))
            
            # Build PDF
            doc.build(elements)
            
            # Return PDF response
            buffer.seek(0)
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="laporan_absensi_ustadz_{timezone.now().strftime("%Y%m%d")}.pdf"'
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}")
            raise Exception(f"Gagal export ke PDF: {str(e)}")
    
    @staticmethod
    def export_teacher_individual_pdf(teacher, start_date=None, end_date=None):
        """
        Export individual teacher attendance report to PDF
        
        Args:
            teacher: Teacher instance
            start_date: Start date
            end_date: End date
            
        Returns:
            HttpResponse with PDF file
        """
        try:
            from attendance.services.teacher_service import TeacherService
            
            # Get summary
            summary = TeacherService.get_teacher_attendance_summary(
                teacher, start_date=start_date, end_date=end_date
            )
            
            # Create PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor('#1F4788'),
                spaceAfter=6,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            elements = []
            
            # School name
            elements.append(Paragraph("LAPORAN KEHADIRAN USTADZ", title_style))
            
            # Teacher info
            elements.append(Spacer(1, 0.3*cm))
            teacher_info = f"""
            <b>Nama:</b> {teacher.name}<br/>
            <b>ID Ustadz:</b> {teacher.teacher_id}<br/>
            <b>NIP:</b> {teacher.nip or '-'}<br/>
            <b>Mata Pelajaran:</b> {teacher.subjects or '-'}
            """
            elements.append(Paragraph(teacher_info, styles['Normal']))
            
            # Date range
            if start_date and end_date:
                period = f"Periode: {start_date.strftime('%d %B %Y')} - {end_date.strftime('%d %B %Y')}"
            else:
                period = f"Tanggal Cetak: {timezone.now().strftime('%d %B %Y')}"
            
            elements.append(Spacer(1, 0.2*cm))
            elements.append(Paragraph(f"<b>{period}</b>", styles['Normal']))
            
            # Summary section
            elements.append(Spacer(1, 0.4*cm))
            elements.append(Paragraph("RINGKASAN KEHADIRAN", ParagraphStyle(
                'SectionTitle',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor('#1F4788'),
                fontName='Helvetica-Bold'
            )))
            
            # Summary table
            summary_data = [
                ['Statistik', 'Jumlah'],
                ['Total Hari Kerja', str(summary['total_days'])],
                ['Total JP', str(summary['total_jp'])],
                ['Hadir', f"{summary['hadir']} ({summary.get('hadir_rate', 0):.1f}%)"],
                ['Sakit', f"{summary['sakit']} ({summary.get('sakit_rate', 0):.1f}%)"],
                ['Izin', f"{summary['izin']} ({summary.get('izin_rate', 0):.1f}%)"],
                ['Alpa', f"{summary['alpa']} ({summary.get('alpa_rate', 0):.1f}%)"],
                ['<b>Persentase Kehadiran</b>', f"<b>{summary['attendance_rate']:.2f}%</b>"],
            ]
            
            summary_table = Table(summary_data, colWidths=[4*cm, 3*cm])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F5F5F5')]),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8E8E8')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ]))
            
            elements.append(summary_table)
            
            # Recent records
            elements.append(Spacer(1, 0.4*cm))
            elements.append(Paragraph("CATATAN KEHADIRAN TERBARU", ParagraphStyle(
                'SectionTitle',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor('#1F4788'),
                fontName='Helvetica-Bold'
            )))
            
            recent_data = [['Tanggal', 'Status JP', 'Catatan']]
            
            for record in summary['recent_records'][:10]:  # Last 10 records
                date_str = record.date.strftime('%d/%m/%Y')
                
                statuses = []
                if record.jp_statuses:
                    for jp_num in sorted([int(k) for k in record.jp_statuses.keys()]):
                        status_map = {'H': '✓', 'S': 'S', 'I': 'I', 'A': 'A'}
                        status = status_map.get(record.jp_statuses.get(str(jp_num), ''), '?')
                        statuses.append(f"JP{jp_num}:{status}")
                
                status_str = ' | '.join(statuses) if statuses else '-'
                notes = record.notes[:30] if record.notes else '-'
                
                recent_data.append([date_str, status_str, notes])
            
            recent_table = Table(recent_data, colWidths=[2*cm, 4*cm, 3*cm])
            recent_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4788')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ('ALIGN', (2, 1), (2, -1), 'LEFT'),
            ]))
            
            elements.append(recent_table)
            
            # Footer
            elements.append(Spacer(1, 0.5*cm))
            footer_text = f"Dicetak pada: {timezone.now().strftime('%d %B %Y pukul %H:%M')}"
            elements.append(Paragraph(footer_text, ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER
            )))
            
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
