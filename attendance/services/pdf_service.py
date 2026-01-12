"""
PDF Export Service Layer
Handles PDF generation for attendance reports using ReportLab

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7
"""
from typing import List, Dict, Optional
from datetime import date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from ..models import Student, Classroom
from .report_service import ReportService


class PDFService:
    """Service class for PDF generation"""
    
    # Color definitions matching the UI theme
    COLORS = {
        'primary': colors.HexColor('#8B7355'),      # Soft brown
        'primary_dark': colors.HexColor('#6B5344'), # Darker brown
        'header_bg': colors.HexColor('#F8F6F4'),    # Warm white
        'hadir': colors.HexColor('#4CAF50'),        # Green
        'sakit': colors.HexColor('#FF9800'),        # Orange
        'izin': colors.HexColor('#2196F3'),         # Blue
        'alpa': colors.HexColor('#F44336'),         # Red
        'border': colors.HexColor('#E8E4E0'),
        'text': colors.HexColor('#2D2A26'),
        'text_muted': colors.HexColor('#6B6560'),
    }
    
    @staticmethod
    def get_styles():
        """Get custom paragraph styles for PDF"""
        styles = getSampleStyleSheet()
        
        # Title style
        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=PDFService.COLORS['primary_dark'],
            alignment=TA_CENTER,
            spaceAfter=12,
        ))
        
        # Subtitle style
        styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=PDFService.COLORS['text_muted'],
            alignment=TA_CENTER,
            spaceAfter=20,
        ))
        
        # Section header style
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=PDFService.COLORS['primary'],
            spaceBefore=15,
            spaceAfter=8,
        ))
        
        return styles

    @staticmethod
    def export_pdf_class(
        classroom: Classroom,
        start_date: date,
        end_date: date
    ) -> bytes:
        """
        Generate PDF report for a classroom.
        
        Creates a table with students as rows and dates as columns,
        showing daily attendance summary. Includes summary section with
        H/S/I/A totals per student and class summary with average percentage.
        
        Args:
            classroom: The classroom to generate report for
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            PDF file content as bytes
            
        Requirements: 5.2, 5.3, 5.4
        """
        # Generate report data
        report_data = ReportService.generate_class_report(
            classroom=classroom,
            start_date=start_date,
            end_date=end_date
        )
        
        # Create PDF buffer
        buffer = BytesIO()
        
        # Use landscape for more columns
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm,
        )
        
        # Build document elements
        elements = []
        styles = PDFService.get_styles()
        
        # Title
        title = Paragraph(
            f"Laporan Absensi Per JP - {classroom}",
            styles['ReportTitle']
        )
        elements.append(title)
        
        # Subtitle with date range
        subtitle = Paragraph(
            f"Periode: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
            styles['ReportSubtitle']
        )
        elements.append(subtitle)
        
        # Build main attendance table
        elements.extend(
            PDFService._build_class_attendance_table(report_data, styles)
        )
        
        # Add summary section
        elements.append(Spacer(1, 20))
        elements.extend(
            PDFService._build_class_summary_table(report_data, styles)
        )
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
    
    @staticmethod
    def _build_class_attendance_table(report_data: Dict, styles) -> List:
        """Build the main attendance table for class report"""
        elements = []
        
        # Section header
        elements.append(Paragraph("Detail Kehadiran", styles['SectionHeader']))
        
        dates = report_data['dates']
        students = report_data['students']
        
        if not students:
            elements.append(Paragraph(
                "Tidak ada data siswa untuk ditampilkan.",
                styles['Normal']
            ))
            return elements
        
        # Build header row
        header = ['No', 'NIS', 'Nama Siswa']
        for d in dates:
            header.append(d.strftime('%d/%m'))
        header.extend(['H', 'S', 'I', 'A', '%'])
        
        # Build data rows
        data = [header]
        
        for idx, student_data in enumerate(students, 1):
            student = student_data['student']
            row = [
                str(idx),
                student.student_id or '-',
                student.name[:20] + '...' if len(student.name) > 20 else student.name,
            ]
            
            # Add daily summaries
            for daily in student_data['daily_data']:
                if daily['has_record']:
                    # Show abbreviated summary
                    summary = f"H{daily['hadir']}"
                    if daily['sakit'] > 0:
                        summary += f"S{daily['sakit']}"
                    if daily['izin'] > 0:
                        summary += f"I{daily['izin']}"
                    if daily['alpa'] > 0:
                        summary += f"A{daily['alpa']}"
                    row.append(summary)
                else:
                    row.append('-')
            
            # Add totals
            row.extend([
                str(student_data['total_hadir']),
                str(student_data['total_sakit']),
                str(student_data['total_izin']),
                str(student_data['total_alpa']),
                f"{student_data['attendance_percentage']:.1f}%",
            ])
            
            data.append(row)
        
        # Calculate column widths
        num_date_cols = len(dates)
        available_width = landscape(A4)[0] - 2*cm  # Total width minus margins
        
        # Fixed widths for non-date columns
        fixed_widths = [0.8*cm, 1.5*cm, 4*cm]  # No, NIS, Name
        summary_widths = [0.8*cm, 0.8*cm, 0.8*cm, 0.8*cm, 1.2*cm]  # H, S, I, A, %
        
        fixed_total = sum(fixed_widths) + sum(summary_widths)
        remaining = available_width - fixed_total
        
        # Date column width (minimum 1.2cm)
        date_col_width = max(1.2*cm, remaining / max(num_date_cols, 1))
        
        col_widths = fixed_widths + [date_col_width] * num_date_cols + summary_widths
        
        # Create table
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        # Apply table style
        table_style = TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), PDFService.COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Data style
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # No column
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # NIS column
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),    # Name column
            ('ALIGN', (3, 1), (-1, -1), 'CENTER'), # Date and summary columns
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, PDFService.COLORS['border']),
            ('BOX', (0, 0), (-1, -1), 1, PDFService.COLORS['primary']),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFService.COLORS['header_bg']]),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ])
        
        table.setStyle(table_style)
        elements.append(table)
        
        return elements

    @staticmethod
    def _build_class_summary_table(report_data: Dict, styles) -> List:
        """Build the summary table for class report"""
        elements = []
        
        # Section header
        elements.append(Paragraph("Ringkasan Kelas", styles['SectionHeader']))
        
        summary = report_data['class_summary']
        
        # Summary data
        data = [
            ['Keterangan', 'Jumlah'],
            ['Total Siswa', str(summary['total_students'])],
            ['Total Hari Sekolah', str(report_data['total_school_days'])],
            ['Total JP Tercatat', str(summary['total_jp'])],
            ['Total Hadir (H)', str(summary['total_hadir'])],
            ['Total Sakit (S)', str(summary['total_sakit'])],
            ['Total Izin (I)', str(summary['total_izin'])],
            ['Total Alpa (A)', str(summary['total_alpa'])],
            ['Persentase Kehadiran', f"{summary['attendance_percentage']:.2f}%"],
        ]
        
        # Create table
        table = Table(data, colWidths=[6*cm, 4*cm])
        
        # Apply style
        table_style = TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), PDFService.COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, PDFService.COLORS['border']),
            ('BOX', (0, 0), (-1, -1), 1, PDFService.COLORS['primary']),
            
            # Alternating colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFService.COLORS['header_bg']]),
            
            # Highlight percentage row
            ('BACKGROUND', (0, -1), (-1, -1), PDFService.COLORS['header_bg']),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ])
        
        table.setStyle(table_style)
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
    def export_pdf_student(
        student: Student,
        start_date: date,
        end_date: date
    ) -> bytes:
        """
        Generate PDF report for a single student.
        
        Creates a detailed view with dates as rows and JP columns showing
        individual status. Includes summary with totals and percentages
        for each status type.
        
        Args:
            student: The student to generate report for
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            PDF file content as bytes
            
        Requirements: 5.5, 5.6
        """
        # Generate report data
        report_data = ReportService.generate_student_report(
            student=student,
            start_date=start_date,
            end_date=end_date
        )
        
        # Create PDF buffer
        buffer = BytesIO()
        
        # Use portrait for student report
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
        )
        
        # Build document elements
        elements = []
        styles = PDFService.get_styles()
        
        # Title
        title = Paragraph(
            "Laporan Absensi Per JP - Detail Siswa",
            styles['ReportTitle']
        )
        elements.append(title)
        
        # Student info
        student_info = Paragraph(
            f"<b>{student.name}</b><br/>"
            f"NIS: {student.student_id or '-'} | "
            f"Kelas: {student.classroom}",
            styles['ReportSubtitle']
        )
        elements.append(student_info)
        
        # Date range
        date_range = Paragraph(
            f"Periode: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
            styles['ReportSubtitle']
        )
        elements.append(date_range)
        
        # Build attendance detail table
        elements.extend(
            PDFService._build_student_attendance_table(report_data, styles)
        )
        
        # Add summary section
        elements.append(Spacer(1, 20))
        elements.extend(
            PDFService._build_student_summary_table(report_data, styles)
        )
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
    
    @staticmethod
    def _build_student_attendance_table(report_data: Dict, styles) -> List:
        """Build the attendance detail table for student report"""
        elements = []
        
        # Section header
        elements.append(Paragraph("Detail Kehadiran Per Hari", styles['SectionHeader']))
        
        daily_records = report_data['daily_records']
        max_jp = report_data['max_jp_count']
        
        if not daily_records:
            elements.append(Paragraph(
                "Tidak ada data kehadiran untuk ditampilkan.",
                styles['Normal']
            ))
            return elements
        
        # Build header row
        header = ['No', 'Tanggal', 'Hari']
        for jp_num in range(1, max_jp + 1):
            header.append(f'JP{jp_num}')
        header.extend(['H', 'S', 'I', 'A'])
        
        # Build data rows
        data = [header]
        
        for idx, record in enumerate(daily_records, 1):
            row = [
                str(idx),
                record['date'].strftime('%d/%m/%Y'),
                record['day_name'][:3],  # Abbreviated day name
            ]
            
            # Add JP statuses
            for jp_detail in record['jp_details']:
                status = jp_detail['status'] or '-'
                row.append(status)
            
            # Pad with empty cells if fewer JPs than max
            while len(row) < 3 + max_jp:
                row.append('-')
            
            # Add day summary
            day_sum = record['day_summary']
            row.extend([
                str(day_sum['hadir']),
                str(day_sum['sakit']),
                str(day_sum['izin']),
                str(day_sum['alpa']),
            ])
            
            data.append(row)
        
        # Calculate column widths
        available_width = A4[0] - 3*cm  # Total width minus margins
        
        # Fixed widths
        fixed_widths = [0.8*cm, 2.2*cm, 1.2*cm]  # No, Date, Day
        summary_widths = [0.8*cm, 0.8*cm, 0.8*cm, 0.8*cm]  # H, S, I, A
        
        fixed_total = sum(fixed_widths) + sum(summary_widths)
        remaining = available_width - fixed_total
        
        # JP column width
        jp_col_width = remaining / max_jp if max_jp > 0 else 1*cm
        
        col_widths = fixed_widths + [jp_col_width] * max_jp + summary_widths
        
        # Create table
        table = Table(data, colWidths=col_widths, repeatRows=1)
        
        # Apply table style with status coloring
        table_style = [
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), PDFService.COLORS['primary']),
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
            ('GRID', (0, 0), (-1, -1), 0.5, PDFService.COLORS['border']),
            ('BOX', (0, 0), (-1, -1), 1, PDFService.COLORS['primary']),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFService.COLORS['header_bg']]),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ]
        
        # Add status-based coloring for JP columns
        for row_idx, record in enumerate(daily_records, 1):
            for jp_idx, jp_detail in enumerate(record['jp_details']):
                col_idx = 3 + jp_idx  # Offset for No, Date, Day columns
                status = jp_detail['status']
                
                if status == 'H':
                    table_style.append(
                        ('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), PDFService.COLORS['hadir'])
                    )
                elif status == 'S':
                    table_style.append(
                        ('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), PDFService.COLORS['sakit'])
                    )
                elif status == 'I':
                    table_style.append(
                        ('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), PDFService.COLORS['izin'])
                    )
                elif status == 'A':
                    table_style.append(
                        ('TEXTCOLOR', (col_idx, row_idx), (col_idx, row_idx), PDFService.COLORS['alpa'])
                    )
        
        table.setStyle(TableStyle(table_style))
        elements.append(table)
        
        return elements

    @staticmethod
    def _build_student_summary_table(report_data: Dict, styles) -> List:
        """Build the summary table for student report"""
        elements = []
        
        # Section header
        elements.append(Paragraph("Ringkasan Kehadiran", styles['SectionHeader']))
        
        summary = report_data['summary']
        
        # Summary data with percentages
        data = [
            ['Status', 'Jumlah', 'Persentase'],
            ['Hadir (H)', str(summary['total_hadir']), f"{summary['attendance_percentage']:.2f}%"],
            ['Sakit (S)', str(summary['total_sakit']), f"{summary['sakit_percentage']:.2f}%"],
            ['Izin (I)', str(summary['total_izin']), f"{summary['izin_percentage']:.2f}%"],
            ['Alpa (A)', str(summary['total_alpa']), f"{summary['alpa_percentage']:.2f}%"],
            ['Total JP', str(summary['total_jp']), '100%'],
        ]
        
        # Create table
        table = Table(data, colWidths=[4*cm, 3*cm, 3*cm])
        
        # Apply style
        table_style = TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), PDFService.COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Status row colors
            ('TEXTCOLOR', (0, 1), (0, 1), PDFService.COLORS['hadir']),
            ('TEXTCOLOR', (0, 2), (0, 2), PDFService.COLORS['sakit']),
            ('TEXTCOLOR', (0, 3), (0, 3), PDFService.COLORS['izin']),
            ('TEXTCOLOR', (0, 4), (0, 4), PDFService.COLORS['alpa']),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, PDFService.COLORS['border']),
            ('BOX', (0, 0), (-1, -1), 1, PDFService.COLORS['primary']),
            
            # Alternating colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PDFService.COLORS['header_bg']]),
            
            # Total row highlight
            ('BACKGROUND', (0, -1), (-1, -1), PDFService.COLORS['header_bg']),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ])
        
        table.setStyle(table_style)
        elements.append(table)
        
        # Additional info
        elements.append(Spacer(1, 15))
        info = Paragraph(
            f"<b>Total Hari Sekolah:</b> {report_data['total_school_days']} hari<br/>"
            f"<b>Kelas:</b> {report_data['classroom']}",
            styles['Normal']
        )
        elements.append(info)
        
        return elements
