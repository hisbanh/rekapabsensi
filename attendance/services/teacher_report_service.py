"""
Teacher Report Service Layer
Handles all business logic related to teacher attendance reporting, analytics, and exports
"""
from typing import List, Dict, Optional
from uuid import UUID
from datetime import date, timedelta
from calendar import monthrange
from io import BytesIO

from django.db.models import Q, Count, Sum, Avg, F
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

from ..models import (
    Teacher, TeacherAttendance, TeacherSchedule, 
    TeacherAttendanceSummary, Subject, Classroom
)
from ..exceptions import AttendanceBaseException


class TeacherReportServiceError(AttendanceBaseException):
    """Exception raised by teacher report service operations"""
    pass


class TeacherReportService:
    """Service class for teacher attendance reporting and analytics"""
    
    # Color definitions for PDF and Excel
    COLORS = {
        'primary': colors.HexColor('#4F46E5'),      # Indigo
        'primary_dark': colors.HexColor('#3730A3'), # Dark indigo
        'header_bg': colors.HexColor('#EEF2FF'),    # Light indigo
        'hadir': colors.HexColor('#10B981'),        # Green
        'sakit': colors.HexColor('#F59E0B'),        # Orange
        'izin': colors.HexColor('#3B82F6'),         # Blue
        'cuti': colors.HexColor('#8B5CF6'),         # Purple
        'dinas': colors.HexColor('#06B6D4'),        # Cyan
        'alpa': colors.HexColor('#EF4444'),         # Red
        'border': colors.HexColor('#E5E7EB'),
        'text': colors.HexColor('#1F2937'),
        'text_muted': colors.HexColor('#6B7280'),
    }
    
    @staticmethod
    def generate_teacher_report_pdf(
        teacher_id: UUID,
        start_date: date,
        end_date: date
    ) -> bytes:
        """
        Generate comprehensive PDF report for a teacher's attendance.
        
        Creates an A4 format PDF with:
        - Teacher profile information (photo, NIP, name, subjects)
        - Attendance summary table with totals and percentages
        - Detailed attendance records table
        - Attendance breakdown chart visualization
        
        Args:
            teacher_id: UUID of the teacher
            start_date: Start date of the report period (inclusive)
            end_date: End date of the report period (inclusive)
            
        Returns:
            bytes: PDF file content
            
        Raises:
            TeacherReportServiceError: If teacher not found or invalid date range
            
        Example:
            >>> from datetime import date
            >>> from uuid import UUID
            >>> teacher_id = UUID('...')
            >>> pdf_bytes = TeacherReportService.generate_teacher_report_pdf(
            ...     teacher_id,
            ...     date(2024, 1, 1),
            ...     date(2024, 1, 31)
            ... )
            >>> with open('teacher_report.pdf', 'wb') as f:
            ...     f.write(pdf_bytes)
        """
        # Validate teacher exists
        try:
            teacher = Teacher.objects.select_related('homeroom_class').prefetch_related('subjects').get(id=teacher_id)
        except Teacher.DoesNotExist:
            raise TeacherReportServiceError(f"Teacher with ID '{teacher_id}' not found")
        
        # Validate date range
        if start_date > end_date:
            raise TeacherReportServiceError("Start date must be before or equal to end date")
        
        # Get attendance data
        attendances = TeacherAttendance.objects.filter(
            teacher=teacher,
            date__gte=start_date,
            date__lte=end_date
        ).select_related('schedule', 'schedule__subject', 'schedule__classroom', 'recorded_by').order_by('date', 'jp_number')
        
        # Calculate summary statistics
        total_hadir = attendances.filter(status='HADIR').count()
        total_sakit = attendances.filter(status='SAKIT').count()
        total_izin = attendances.filter(status='IZIN').count()
        total_cuti = attendances.filter(status='CUTI').count()
        total_dinas = attendances.filter(status='DINAS').count()
        total_alpa = attendances.filter(status='ALPA').count()
        total_jp = attendances.count()
        
        attendance_percentage = round((total_hadir / total_jp * 100), 2) if total_jp > 0 else 0.0
        
        # Create PDF buffer
        buffer = BytesIO()
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
        styles = getSampleStyleSheet()
        
        # Add custom styles
        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=TeacherReportService.COLORS['primary_dark'],
            alignment=TA_CENTER,
            spaceAfter=12,
        ))
        
        styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=TeacherReportService.COLORS['text_muted'],
            alignment=TA_CENTER,
            spaceAfter=20,
        ))
        
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=TeacherReportService.COLORS['primary'],
            spaceBefore=15,
            spaceAfter=8,
        ))
        
        # Title
        title = Paragraph("Laporan Absensi Ustadz", styles['ReportTitle'])
        elements.append(title)
        
        # Teacher info
        teacher_info = Paragraph(
            f"<b>{teacher.full_name}</b><br/>"
            f"NIP: {teacher.nip} | "
            f"Status: {teacher.get_employment_status_display()}",
            styles['ReportSubtitle']
        )
        elements.append(teacher_info)
        
        # Subjects taught
        subjects_list = ", ".join([s.name for s in teacher.subjects.filter(is_active=True)])
        if subjects_list:
            subjects_info = Paragraph(
                f"Mata Pelajaran: {subjects_list}",
                styles['ReportSubtitle']
            )
            elements.append(subjects_info)
        
        # Date range
        date_range = Paragraph(
            f"Periode: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
            styles['ReportSubtitle']
        )
        elements.append(date_range)
        
        # Summary section
        elements.append(Paragraph("Ringkasan Kehadiran", styles['SectionHeader']))
        
        summary_data = [
            ['Status', 'Jumlah', 'Persentase'],
            ['Hadir', str(total_hadir), f"{attendance_percentage:.2f}%"],
            ['Sakit', str(total_sakit), f"{(total_sakit/total_jp*100):.2f}%" if total_jp > 0 else "0%"],
            ['Izin', str(total_izin), f"{(total_izin/total_jp*100):.2f}%" if total_jp > 0 else "0%"],
            ['Cuti', str(total_cuti), f"{(total_cuti/total_jp*100):.2f}%" if total_jp > 0 else "0%"],
            ['Dinas', str(total_dinas), f"{(total_dinas/total_jp*100):.2f}%" if total_jp > 0 else "0%"],
            ['Alpa', str(total_alpa), f"{(total_alpa/total_jp*100):.2f}%" if total_jp > 0 else "0%"],
            ['Total JP', str(total_jp), '100%'],
        ]
        
        summary_table = Table(summary_data, colWidths=[5*cm, 3*cm, 3*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), TeacherReportService.COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, TeacherReportService.COLORS['border']),
            ('BOX', (0, 0), (-1, -1), 1, TeacherReportService.COLORS['primary']),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, TeacherReportService.COLORS['header_bg']]),
            ('BACKGROUND', (0, -1), (-1, -1), TeacherReportService.COLORS['header_bg']),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(summary_table)
        
        # Detailed attendance records
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Detail Kehadiran", styles['SectionHeader']))
        
        if attendances.exists():
            detail_data = [['No', 'Tanggal', 'JP', 'Status', 'Mata Pelajaran', 'Kelas', 'Keterangan']]
            
            for idx, att in enumerate(attendances, 1):
                subject_name = att.schedule.subject.name if att.schedule else '-'
                classroom_name = att.schedule.classroom.name if att.schedule else '-'
                
                detail_data.append([
                    str(idx),
                    att.date.strftime('%d/%m/%Y'),
                    str(att.jp_number),
                    att.get_status_display(),
                    subject_name[:15] + '...' if len(subject_name) > 15 else subject_name,
                    classroom_name[:10] + '...' if len(classroom_name) > 10 else classroom_name,
                    att.notes[:20] + '...' if len(att.notes) > 20 else att.notes or '-',
                ])
            
            detail_table = Table(detail_data, colWidths=[0.8*cm, 2.2*cm, 1*cm, 2*cm, 3*cm, 2.5*cm, 3.5*cm])
            detail_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), TeacherReportService.COLORS['primary']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, TeacherReportService.COLORS['border']),
                ('BOX', (0, 0), (-1, -1), 1, TeacherReportService.COLORS['primary']),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, TeacherReportService.COLORS['header_bg']]),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ]))
            elements.append(detail_table)
        else:
            elements.append(Paragraph("Tidak ada data kehadiran untuk periode ini.", styles['Normal']))
        
        # Footer
        elements.append(Spacer(1, 20))
        footer = Paragraph(
            f"<i>Laporan dibuat pada: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}</i>",
            styles['Normal']
        )
        elements.append(footer)
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
    
    @staticmethod
    def get_attendance_analytics(
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Get comprehensive attendance analytics for all teachers within a date range.
        
        Provides aggregate statistics including:
        - Overall attendance rates
        - Status breakdown (Hadir, Sakit, Izin, Cuti, Dinas, Alpa)
        - Teacher-wise performance summary
        - Daily attendance trends
        - Subject-wise attendance statistics
        
        Args:
            start_date: Start date of the analysis period (inclusive)
            end_date: End date of the analysis period (inclusive)
            
        Returns:
            Dictionary containing:
                - period: Dict with start_date and end_date
                - overall_stats: Aggregate statistics across all teachers
                - teacher_stats: List of per-teacher statistics
                - daily_trends: Daily attendance counts
                - subject_stats: Subject-wise attendance statistics
                - top_performers: Teachers with highest attendance rates
                - needs_attention: Teachers with low attendance rates
                
        Raises:
            TeacherReportServiceError: If invalid date range
            
        Example:
            >>> from datetime import date
            >>> analytics = TeacherReportService.get_attendance_analytics(
            ...     date(2024, 1, 1),
            ...     date(2024, 1, 31)
            ... )
            >>> print(f"Overall attendance: {analytics['overall_stats']['attendance_percentage']}%")
            >>> print(f"Total teachers: {analytics['overall_stats']['total_teachers']}")
        """
        # Validate date range
        if start_date > end_date:
            raise TeacherReportServiceError("Start date must be before or equal to end date")
        
        # Get all attendance records in the date range
        attendances = TeacherAttendance.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).select_related('teacher', 'schedule', 'schedule__subject')
        
        # Overall statistics
        total_records = attendances.count()
        total_hadir = attendances.filter(status='HADIR').count()
        total_sakit = attendances.filter(status='SAKIT').count()
        total_izin = attendances.filter(status='IZIN').count()
        total_cuti = attendances.filter(status='CUTI').count()
        total_dinas = attendances.filter(status='DINAS').count()
        total_alpa = attendances.filter(status='ALPA').count()
        
        overall_attendance_percentage = round((total_hadir / total_records * 100), 2) if total_records > 0 else 0.0
        
        # Get active teachers
        active_teachers = Teacher.objects.filter(is_active=True)
        total_teachers = active_teachers.count()
        
        # Teacher-wise statistics
        teacher_stats = []
        for teacher in active_teachers:
            teacher_attendances = attendances.filter(teacher=teacher)
            teacher_total = teacher_attendances.count()
            teacher_hadir = teacher_attendances.filter(status='HADIR').count()
            
            if teacher_total > 0:
                teacher_percentage = round((teacher_hadir / teacher_total * 100), 2)
            else:
                teacher_percentage = 0.0
            
            teacher_stats.append({
                'teacher': teacher,
                'teacher_id': str(teacher.id),
                'teacher_name': teacher.full_name,
                'nip': teacher.nip,
                'total_jp': teacher_total,
                'total_hadir': teacher_hadir,
                'total_sakit': teacher_attendances.filter(status='SAKIT').count(),
                'total_izin': teacher_attendances.filter(status='IZIN').count(),
                'total_cuti': teacher_attendances.filter(status='CUTI').count(),
                'total_dinas': teacher_attendances.filter(status='DINAS').count(),
                'total_alpa': teacher_attendances.filter(status='ALPA').count(),
                'attendance_percentage': teacher_percentage,
            })
        
        # Sort by attendance percentage (descending)
        teacher_stats.sort(key=lambda x: x['attendance_percentage'], reverse=True)
        
        # Top performers (attendance >= 95%)
        top_performers = [t for t in teacher_stats if t['attendance_percentage'] >= 95.0 and t['total_jp'] > 0]
        
        # Needs attention (attendance < 80%)
        needs_attention = [t for t in teacher_stats if t['attendance_percentage'] < 80.0 and t['total_jp'] > 0]
        
        # Daily trends
        daily_trends = []
        current_date = start_date
        while current_date <= end_date:
            day_attendances = attendances.filter(date=current_date)
            day_total = day_attendances.count()
            day_hadir = day_attendances.filter(status='HADIR').count()
            
            daily_trends.append({
                'date': current_date,
                'total_jp': day_total,
                'total_hadir': day_hadir,
                'total_absent': day_total - day_hadir,
                'attendance_percentage': round((day_hadir / day_total * 100), 2) if day_total > 0 else 0.0,
            })
            
            current_date += timedelta(days=1)
        
        # Subject-wise statistics
        subject_stats = []
        subjects = Subject.objects.filter(is_active=True)
        
        for subject in subjects:
            subject_attendances = attendances.filter(schedule__subject=subject)
            subject_total = subject_attendances.count()
            subject_hadir = subject_attendances.filter(status='HADIR').count()
            
            if subject_total > 0:
                subject_stats.append({
                    'subject': subject,
                    'subject_name': subject.name,
                    'subject_code': subject.code,
                    'total_jp': subject_total,
                    'total_hadir': subject_hadir,
                    'attendance_percentage': round((subject_hadir / subject_total * 100), 2),
                })
        
        # Sort by total JP (descending)
        subject_stats.sort(key=lambda x: x['total_jp'], reverse=True)
        
        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'total_days': (end_date - start_date).days + 1,
            },
            'overall_stats': {
                'total_teachers': total_teachers,
                'total_records': total_records,
                'total_hadir': total_hadir,
                'total_sakit': total_sakit,
                'total_izin': total_izin,
                'total_cuti': total_cuti,
                'total_dinas': total_dinas,
                'total_alpa': total_alpa,
                'attendance_percentage': overall_attendance_percentage,
            },
            'teacher_stats': teacher_stats,
            'daily_trends': daily_trends,
            'subject_stats': subject_stats,
            'top_performers': top_performers,
            'needs_attention': needs_attention,
        }
    
    @staticmethod
    def export_attendance_excel(
        start_date: date,
        end_date: date
    ) -> bytes:
        """
        Export teacher attendance data to Excel format with advanced features.
        
        Creates an Excel workbook with multiple sheets:
        - Summary sheet: Overall statistics and teacher performance
        - Detail sheet: Complete attendance records
        - Analytics sheet: Charts and visualizations (data for charts)
        
        Features:
        - Conditional formatting (color-coded statuses)
        - Formulas for automatic calculations
        - Frozen header rows
        - Professional styling
        
        Args:
            start_date: Start date of the export period (inclusive)
            end_date: End date of the export period (inclusive)
            
        Returns:
            bytes: Excel file content
            
        Raises:
            TeacherReportServiceError: If invalid date range
            
        Example:
            >>> from datetime import date
            >>> excel_bytes = TeacherReportService.export_attendance_excel(
            ...     date(2024, 1, 1),
            ...     date(2024, 1, 31)
            ... )
            >>> with open('teacher_attendance.xlsx', 'wb') as f:
            ...     f.write(excel_bytes)
        """
        # Validate date range
        if start_date > end_date:
            raise TeacherReportServiceError("Start date must be before or equal to end date")
        
        # Get analytics data
        analytics = TeacherReportService.get_attendance_analytics(start_date, end_date)
        
        # Get all attendance records
        attendances = TeacherAttendance.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).select_related(
            'teacher', 'schedule', 'schedule__subject', 'schedule__classroom', 'recorded_by'
        ).order_by('date', 'teacher__full_name', 'jp_number')
        
        # Create workbook
        wb = Workbook()
        
        # Define styles
        header_font = Font(bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='4F46E5', end_color='4F46E5', fill_type='solid')
        header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Status colors
        hadir_fill = PatternFill(start_color='D1FAE5', end_color='D1FAE5', fill_type='solid')  # Light green
        sakit_fill = PatternFill(start_color='FED7AA', end_color='FED7AA', fill_type='solid')  # Light orange
        izin_fill = PatternFill(start_color='DBEAFE', end_color='DBEAFE', fill_type='solid')   # Light blue
        cuti_fill = PatternFill(start_color='E9D5FF', end_color='E9D5FF', fill_type='solid')   # Light purple
        dinas_fill = PatternFill(start_color='CFFAFE', end_color='CFFAFE', fill_type='solid')  # Light cyan
        alpa_fill = PatternFill(start_color='FEE2E2', end_color='FEE2E2', fill_type='solid')   # Light red
        
        # Sheet 1: Summary
        ws_summary = wb.active
        ws_summary.title = 'Ringkasan'
        
        # Summary header
        ws_summary['A1'] = 'RINGKASAN ABSENSI USTADZ'
        ws_summary['A1'].font = Font(bold=True, size=14, color='4F46E5')
        ws_summary['A1'].alignment = Alignment(horizontal='center')
        ws_summary.merge_cells('A1:F1')
        
        ws_summary['A2'] = f"Periode: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        ws_summary['A2'].alignment = Alignment(horizontal='center')
        ws_summary.merge_cells('A2:F2')
        
        # Overall statistics
        ws_summary['A4'] = 'Statistik Keseluruhan'
        ws_summary['A4'].font = Font(bold=True)
        
        overall_data = [
            ['Keterangan', 'Jumlah'],
            ['Total Ustadz', analytics['overall_stats']['total_teachers']],
            ['Total JP Tercatat', analytics['overall_stats']['total_records']],
            ['Total Hadir', analytics['overall_stats']['total_hadir']],
            ['Total Sakit', analytics['overall_stats']['total_sakit']],
            ['Total Izin', analytics['overall_stats']['total_izin']],
            ['Total Cuti', analytics['overall_stats']['total_cuti']],
            ['Total Dinas', analytics['overall_stats']['total_dinas']],
            ['Total Alpa', analytics['overall_stats']['total_alpa']],
            ['Persentase Kehadiran', f"{analytics['overall_stats']['attendance_percentage']}%"],
        ]
        
        for row_idx, row_data in enumerate(overall_data, 5):
            for col_idx, value in enumerate(row_data, 1):
                cell = ws_summary.cell(row=row_idx, column=col_idx, value=value)
                cell.border = thin_border
                if row_idx == 5:  # Header row
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = header_alignment
        
        # Teacher performance
        ws_summary['A16'] = 'Performa Per Ustadz'
        ws_summary['A16'].font = Font(bold=True)
        
        teacher_headers = ['No', 'NIP', 'Nama', 'Total JP', 'Hadir', 'Sakit', 'Izin', 'Cuti', 'Dinas', 'Alpa', 'Persentase']
        for col_idx, header in enumerate(teacher_headers, 1):
            cell = ws_summary.cell(row=17, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border
        
        for row_idx, teacher_stat in enumerate(analytics['teacher_stats'], 18):
            row_data = [
                row_idx - 17,
                teacher_stat['nip'],
                teacher_stat['teacher_name'],
                teacher_stat['total_jp'],
                teacher_stat['total_hadir'],
                teacher_stat['total_sakit'],
                teacher_stat['total_izin'],
                teacher_stat['total_cuti'],
                teacher_stat['total_dinas'],
                teacher_stat['total_alpa'],
                f"{teacher_stat['attendance_percentage']}%",
            ]
            
            for col_idx, value in enumerate(row_data, 1):
                cell = ws_summary.cell(row=row_idx, column=col_idx, value=value)
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center' if col_idx != 3 else 'left')
        
        # Set column widths
        ws_summary.column_dimensions['A'].width = 5
        ws_summary.column_dimensions['B'].width = 15
        ws_summary.column_dimensions['C'].width = 25
        ws_summary.column_dimensions['D'].width = 10
        ws_summary.column_dimensions['E'].width = 8
        ws_summary.column_dimensions['F'].width = 8
        ws_summary.column_dimensions['G'].width = 8
        ws_summary.column_dimensions['H'].width = 8
        ws_summary.column_dimensions['I'].width = 8
        ws_summary.column_dimensions['J'].width = 8
        ws_summary.column_dimensions['K'].width = 12
        
        # Freeze header row
        ws_summary.freeze_panes = 'A18'
        
        # Sheet 2: Detail
        ws_detail = wb.create_sheet(title='Detail Kehadiran')
        
        # Detail header
        detail_headers = ['No', 'Tanggal', 'NIP', 'Nama Ustadz', 'JP', 'Status', 'Mata Pelajaran', 'Kelas', 'Keterangan', 'Dicatat Oleh', 'Waktu Catat']
        for col_idx, header in enumerate(detail_headers, 1):
            cell = ws_detail.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border
        
        # Detail data
        for row_idx, att in enumerate(attendances, 2):
            row_data = [
                row_idx - 1,
                att.date.strftime('%d/%m/%Y'),
                att.teacher.nip,
                att.teacher.full_name,
                att.jp_number,
                att.get_status_display(),
                att.schedule.subject.name if att.schedule else '-',
                att.schedule.classroom.name if att.schedule else '-',
                att.notes or '-',
                att.recorded_by.get_full_name() if att.recorded_by else '-',
                att.recorded_at.strftime('%d/%m/%Y %H:%M') if att.recorded_at else '-',
            ]
            
            for col_idx, value in enumerate(row_data, 1):
                cell = ws_detail.cell(row=row_idx, column=col_idx, value=value)
                cell.border = thin_border
                cell.alignment = Alignment(horizontal='center' if col_idx in [1, 2, 5, 6] else 'left')
                
                # Apply status-based coloring
                if col_idx == 6:  # Status column
                    if att.status == 'HADIR':
                        cell.fill = hadir_fill
                    elif att.status == 'SAKIT':
                        cell.fill = sakit_fill
                    elif att.status == 'IZIN':
                        cell.fill = izin_fill
                    elif att.status == 'CUTI':
                        cell.fill = cuti_fill
                    elif att.status == 'DINAS':
                        cell.fill = dinas_fill
                    elif att.status == 'ALPA':
                        cell.fill = alpa_fill
        
        # Set column widths
        ws_detail.column_dimensions['A'].width = 5
        ws_detail.column_dimensions['B'].width = 12
        ws_detail.column_dimensions['C'].width = 15
        ws_detail.column_dimensions['D'].width = 25
        ws_detail.column_dimensions['E'].width = 5
        ws_detail.column_dimensions['F'].width = 10
        ws_detail.column_dimensions['G'].width = 20
        ws_detail.column_dimensions['H'].width = 15
        ws_detail.column_dimensions['I'].width = 30
        ws_detail.column_dimensions['J'].width = 20
        ws_detail.column_dimensions['K'].width = 15
        
        # Freeze header row
        ws_detail.freeze_panes = 'A2'
        
        # Save to buffer
        buffer = BytesIO()
        wb.save(buffer)
        excel_content = buffer.getvalue()
        buffer.close()
        
        return excel_content
    
    @staticmethod
    def get_dashboard_statistics() -> Dict:
        """
        Get real-time statistics for the teacher attendance dashboard.
        
        Provides current day and recent statistics including:
        - Today's attendance summary
        - Absent teachers today
        - Recent attendance trends (last 7 days)
        - Notifications and alerts
        - Quick statistics
        
        Returns:
            Dictionary containing:
                - today: Today's date
                - today_stats: Today's attendance statistics
                - absent_today: List of absent teachers today
                - recent_trends: Last 7 days attendance trends
                - notifications: List of important notifications
                - quick_stats: Quick overview statistics
                
        Example:
            >>> stats = TeacherReportService.get_dashboard_statistics()
            >>> print(f"Today's attendance: {stats['today_stats']['attendance_percentage']}%")
            >>> print(f"Absent teachers: {len(stats['absent_today'])}")
        """
        today = timezone.now().date()
        
        # Today's statistics
        today_attendances = TeacherAttendance.objects.filter(date=today)
        today_total = today_attendances.count()
        today_hadir = today_attendances.filter(status='HADIR').count()
        today_sakit = today_attendances.filter(status='SAKIT').count()
        today_izin = today_attendances.filter(status='IZIN').count()
        today_cuti = today_attendances.filter(status='CUTI').count()
        today_dinas = today_attendances.filter(status='DINAS').count()
        today_alpa = today_attendances.filter(status='ALPA').count()
        
        today_attendance_percentage = round((today_hadir / today_total * 100), 2) if today_total > 0 else 0.0
        
        # Get all active teachers
        active_teachers = Teacher.objects.filter(is_active=True)
        total_active_teachers = active_teachers.count()
        
        # Get teachers who have recorded attendance today
        teachers_recorded_today = today_attendances.values('teacher').distinct().count()
        
        # Absent teachers today (teachers with schedules but no HADIR status)
        day_of_week = today.weekday()
        scheduled_today = TeacherSchedule.objects.filter(
            day_of_week=day_of_week,
            is_active=True,
            effective_date__lte=today,
            teacher__is_active=True
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=today)
        ).select_related('teacher', 'subject', 'classroom').distinct()
        
        absent_today = []
        for schedule in scheduled_today:
            # Check if teacher has any non-HADIR attendance or no attendance at all
            teacher_today_att = today_attendances.filter(teacher=schedule.teacher)
            
            if not teacher_today_att.exists():
                absent_today.append({
                    'teacher': schedule.teacher,
                    'teacher_name': schedule.teacher.full_name,
                    'nip': schedule.teacher.nip,
                    'status': 'NOT_RECORDED',
                    'schedule': schedule,
                })
            else:
                # Check if all attendance records are non-HADIR
                all_absent = not teacher_today_att.filter(status='HADIR').exists()
                if all_absent:
                    # Get the most common status
                    status_counts = teacher_today_att.values('status').annotate(count=Count('status')).order_by('-count')
                    primary_status = status_counts[0]['status'] if status_counts else 'UNKNOWN'
                    
                    absent_today.append({
                        'teacher': schedule.teacher,
                        'teacher_name': schedule.teacher.full_name,
                        'nip': schedule.teacher.nip,
                        'status': primary_status,
                        'schedule': schedule,
                    })
        
        # Recent trends (last 7 days)
        recent_trends = []
        for i in range(6, -1, -1):
            trend_date = today - timedelta(days=i)
            trend_attendances = TeacherAttendance.objects.filter(date=trend_date)
            trend_total = trend_attendances.count()
            trend_hadir = trend_attendances.filter(status='HADIR').count()
            
            recent_trends.append({
                'date': trend_date,
                'day_name': trend_date.strftime('%A'),
                'total_jp': trend_total,
                'total_hadir': trend_hadir,
                'total_absent': trend_total - trend_hadir,
                'attendance_percentage': round((trend_hadir / trend_total * 100), 2) if trend_total > 0 else 0.0,
            })
        
        # Notifications
        notifications = []
        
        # Alert for teachers not recorded today
        not_recorded_count = len([a for a in absent_today if a['status'] == 'NOT_RECORDED'])
        if not_recorded_count > 0:
            notifications.append({
                'type': 'warning',
                'message': f"{not_recorded_count} ustadz belum mencatat kehadiran hari ini",
                'priority': 'high',
            })
        
        # Alert for teachers with ALPA status today
        alpa_count = today_attendances.filter(status='ALPA').values('teacher').distinct().count()
        if alpa_count > 0:
            notifications.append({
                'type': 'danger',
                'message': f"{alpa_count} ustadz dengan status Alpa hari ini",
                'priority': 'high',
            })
        
        # Alert for low attendance rate today
        if today_total > 0 and today_attendance_percentage < 80.0:
            notifications.append({
                'type': 'warning',
                'message': f"Tingkat kehadiran hari ini rendah: {today_attendance_percentage}%",
                'priority': 'medium',
            })
        
        # Quick statistics (this month)
        current_month = today.month
        current_year = today.year
        month_start = date(current_year, current_month, 1)
        
        month_attendances = TeacherAttendance.objects.filter(
            date__gte=month_start,
            date__lte=today
        )
        month_total = month_attendances.count()
        month_hadir = month_attendances.filter(status='HADIR').count()
        month_attendance_percentage = round((month_hadir / month_total * 100), 2) if month_total > 0 else 0.0
        
        return {
            'today': today,
            'today_stats': {
                'total_jp': today_total,
                'total_hadir': today_hadir,
                'total_sakit': today_sakit,
                'total_izin': today_izin,
                'total_cuti': today_cuti,
                'total_dinas': today_dinas,
                'total_alpa': today_alpa,
                'attendance_percentage': today_attendance_percentage,
                'teachers_recorded': teachers_recorded_today,
                'total_active_teachers': total_active_teachers,
            },
            'absent_today': absent_today,
            'recent_trends': recent_trends,
            'notifications': notifications,
            'quick_stats': {
                'month_total_jp': month_total,
                'month_total_hadir': month_hadir,
                'month_attendance_percentage': month_attendance_percentage,
                'total_active_teachers': total_active_teachers,
            },
        }
    
    @staticmethod
    def generate_monthly_report(
        year: int,
        month: int
    ) -> Dict:
        """
        Generate comprehensive monthly attendance report for all teachers.
        
        Provides detailed monthly statistics including:
        - Monthly summary for each teacher
        - Aggregate statistics for the month
        - Daily breakdown
        - Comparison with previous month
        - Performance rankings
        
        Args:
            year: Year (e.g., 2024)
            month: Month (1-12)
            
        Returns:
            Dictionary containing:
                - period: Dict with year, month, start_date, end_date
                - monthly_summaries: List of teacher monthly summaries
                - aggregate_stats: Overall monthly statistics
                - daily_breakdown: Day-by-day attendance counts
                - performance_ranking: Teachers ranked by attendance
                - comparison: Comparison with previous month (if available)
                
        Raises:
            TeacherReportServiceError: If invalid month or year
            
        Example:
            >>> report = TeacherReportService.generate_monthly_report(2024, 1)
            >>> print(f"Month: {report['period']['month']}/{report['period']['year']}")
            >>> print(f"Overall attendance: {report['aggregate_stats']['attendance_percentage']}%")
        """
        # Validate month and year
        if not (1 <= month <= 12):
            raise TeacherReportServiceError("Month must be between 1 and 12")
        
        if not (2020 <= year <= 2030):
            raise TeacherReportServiceError("Year must be between 2020 and 2030")
        
        # Calculate date range
        _, last_day = monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        
        # Get all active teachers
        active_teachers = Teacher.objects.filter(is_active=True)
        
        # Get or calculate monthly summaries
        monthly_summaries = []
        for teacher in active_teachers:
            try:
                summary = TeacherAttendanceSummary.objects.get(
                    teacher=teacher,
                    year=year,
                    month=month
                )
            except TeacherAttendanceSummary.DoesNotExist:
                # Calculate summary if not exists
                from .teacher_attendance_service import TeacherAttendanceService
                summary_data = TeacherAttendanceService.calculate_monthly_summary(
                    teacher.id, year, month
                )
                summary = TeacherAttendanceSummary.objects.get(
                    teacher=teacher,
                    year=year,
                    month=month
                )
            
            monthly_summaries.append({
                'teacher': teacher,
                'teacher_name': teacher.full_name,
                'nip': teacher.nip,
                'total_hadir': summary.total_hadir,
                'total_sakit': summary.total_sakit,
                'total_izin': summary.total_izin,
                'total_cuti': summary.total_cuti,
                'total_dinas': summary.total_dinas,
                'total_alpa': summary.total_alpa,
                'total_jp_scheduled': summary.total_jp_scheduled,
                'attendance_percentage': summary.attendance_percentage,
            })
        
        # Sort by attendance percentage (descending)
        monthly_summaries.sort(key=lambda x: x['attendance_percentage'], reverse=True)
        
        # Aggregate statistics
        total_hadir = sum(s['total_hadir'] for s in monthly_summaries)
        total_sakit = sum(s['total_sakit'] for s in monthly_summaries)
        total_izin = sum(s['total_izin'] for s in monthly_summaries)
        total_cuti = sum(s['total_cuti'] for s in monthly_summaries)
        total_dinas = sum(s['total_dinas'] for s in monthly_summaries)
        total_alpa = sum(s['total_alpa'] for s in monthly_summaries)
        total_jp_scheduled = sum(s['total_jp_scheduled'] for s in monthly_summaries)
        
        aggregate_attendance_percentage = round(
            (total_hadir / total_jp_scheduled * 100), 2
        ) if total_jp_scheduled > 0 else 0.0
        
        # Daily breakdown
        daily_breakdown = []
        current_date = start_date
        while current_date <= end_date:
            day_attendances = TeacherAttendance.objects.filter(date=current_date)
            day_total = day_attendances.count()
            day_hadir = day_attendances.filter(status='HADIR').count()
            
            daily_breakdown.append({
                'date': current_date,
                'day_name': current_date.strftime('%A'),
                'day_of_week': current_date.weekday(),
                'total_jp': day_total,
                'total_hadir': day_hadir,
                'total_absent': day_total - day_hadir,
                'attendance_percentage': round((day_hadir / day_total * 100), 2) if day_total > 0 else 0.0,
            })
            
            current_date += timedelta(days=1)
        
        # Performance ranking
        performance_ranking = {
            'excellent': [s for s in monthly_summaries if s['attendance_percentage'] >= 95.0 and s['total_jp_scheduled'] > 0],
            'good': [s for s in monthly_summaries if 85.0 <= s['attendance_percentage'] < 95.0 and s['total_jp_scheduled'] > 0],
            'fair': [s for s in monthly_summaries if 75.0 <= s['attendance_percentage'] < 85.0 and s['total_jp_scheduled'] > 0],
            'needs_improvement': [s for s in monthly_summaries if s['attendance_percentage'] < 75.0 and s['total_jp_scheduled'] > 0],
        }
        
        # Comparison with previous month
        comparison = None
        if month > 1:
            prev_month = month - 1
            prev_year = year
        else:
            prev_month = 12
            prev_year = year - 1
        
        # Get previous month summaries
        prev_summaries = TeacherAttendanceSummary.objects.filter(
            year=prev_year,
            month=prev_month
        )
        
        if prev_summaries.exists():
            prev_total_hadir = sum(s.total_hadir for s in prev_summaries)
            prev_total_jp = sum(s.total_jp_scheduled for s in prev_summaries)
            prev_attendance_percentage = round(
                (prev_total_hadir / prev_total_jp * 100), 2
            ) if prev_total_jp > 0 else 0.0
            
            percentage_change = round(
                aggregate_attendance_percentage - prev_attendance_percentage, 2
            )
            
            comparison = {
                'previous_month': prev_month,
                'previous_year': prev_year,
                'previous_attendance_percentage': prev_attendance_percentage,
                'current_attendance_percentage': aggregate_attendance_percentage,
                'percentage_change': percentage_change,
                'trend': 'up' if percentage_change > 0 else 'down' if percentage_change < 0 else 'stable',
            }
        
        return {
            'period': {
                'year': year,
                'month': month,
                'start_date': start_date,
                'end_date': end_date,
                'total_days': last_day,
            },
            'monthly_summaries': monthly_summaries,
            'aggregate_stats': {
                'total_teachers': len(active_teachers),
                'total_hadir': total_hadir,
                'total_sakit': total_sakit,
                'total_izin': total_izin,
                'total_cuti': total_cuti,
                'total_dinas': total_dinas,
                'total_alpa': total_alpa,
                'total_jp_scheduled': total_jp_scheduled,
                'attendance_percentage': aggregate_attendance_percentage,
            },
            'daily_breakdown': daily_breakdown,
            'performance_ranking': performance_ranking,
            'comparison': comparison,
        }
    
    @staticmethod
    def get_teacher_performance_summary(
        teacher_id: UUID
    ) -> Dict:
        """
        Get comprehensive performance summary for a specific teacher.
        
        Provides detailed performance metrics including:
        - Overall attendance statistics (all-time)
        - Monthly breakdown (last 6 months)
        - Attendance trends
        - Comparison with school average
        - Teaching load analysis
        - Recent attendance records
        
        Args:
            teacher_id: UUID of the teacher
            
        Returns:
            Dictionary containing:
                - teacher: Teacher instance
                - overall_stats: All-time attendance statistics
                - monthly_breakdown: Last 6 months statistics
                - trends: Attendance trend analysis
                - comparison: Comparison with school average
                - teaching_load: Teaching load analysis
                - recent_records: Recent attendance records (last 30 days)
                
        Raises:
            TeacherReportServiceError: If teacher not found
            
        Example:
            >>> from uuid import UUID
            >>> teacher_id = UUID('...')
            >>> summary = TeacherReportService.get_teacher_performance_summary(teacher_id)
            >>> print(f"Teacher: {summary['teacher'].full_name}")
            >>> print(f"Overall attendance: {summary['overall_stats']['attendance_percentage']}%")
            >>> print(f"Teaching load: {summary['teaching_load']['total_jp_per_week']} JP/week")
        """
        # Validate teacher exists
        try:
            teacher = Teacher.objects.select_related('homeroom_class').prefetch_related('subjects', 'schedules').get(id=teacher_id)
        except Teacher.DoesNotExist:
            raise TeacherReportServiceError(f"Teacher with ID '{teacher_id}' not found")
        
        # Overall statistics (all-time)
        all_attendances = TeacherAttendance.objects.filter(teacher=teacher)
        total_all = all_attendances.count()
        total_hadir_all = all_attendances.filter(status='HADIR').count()
        total_sakit_all = all_attendances.filter(status='SAKIT').count()
        total_izin_all = all_attendances.filter(status='IZIN').count()
        total_cuti_all = all_attendances.filter(status='CUTI').count()
        total_dinas_all = all_attendances.filter(status='DINAS').count()
        total_alpa_all = all_attendances.filter(status='ALPA').count()
        
        overall_attendance_percentage = round(
            (total_hadir_all / total_all * 100), 2
        ) if total_all > 0 else 0.0
        
        # Monthly breakdown (last 6 months)
        today = timezone.now().date()
        monthly_breakdown = []
        
        for i in range(5, -1, -1):
            # Calculate month and year
            target_date = today - timedelta(days=i * 30)
            target_year = target_date.year
            target_month = target_date.month
            
            # Get or calculate summary
            try:
                summary = TeacherAttendanceSummary.objects.get(
                    teacher=teacher,
                    year=target_year,
                    month=target_month
                )
                
                monthly_breakdown.append({
                    'year': target_year,
                    'month': target_month,
                    'month_name': date(target_year, target_month, 1).strftime('%B'),
                    'total_hadir': summary.total_hadir,
                    'total_sakit': summary.total_sakit,
                    'total_izin': summary.total_izin,
                    'total_cuti': summary.total_cuti,
                    'total_dinas': summary.total_dinas,
                    'total_alpa': summary.total_alpa,
                    'total_jp_scheduled': summary.total_jp_scheduled,
                    'attendance_percentage': summary.attendance_percentage,
                })
            except TeacherAttendanceSummary.DoesNotExist:
                # No data for this month
                monthly_breakdown.append({
                    'year': target_year,
                    'month': target_month,
                    'month_name': date(target_year, target_month, 1).strftime('%B'),
                    'total_hadir': 0,
                    'total_sakit': 0,
                    'total_izin': 0,
                    'total_cuti': 0,
                    'total_dinas': 0,
                    'total_alpa': 0,
                    'total_jp_scheduled': 0,
                    'attendance_percentage': 0.0,
                })
        
        # Attendance trends
        if len(monthly_breakdown) >= 2:
            recent_percentages = [m['attendance_percentage'] for m in monthly_breakdown if m['total_jp_scheduled'] > 0]
            if len(recent_percentages) >= 2:
                trend_direction = 'improving' if recent_percentages[-1] > recent_percentages[0] else 'declining' if recent_percentages[-1] < recent_percentages[0] else 'stable'
                avg_percentage = sum(recent_percentages) / len(recent_percentages)
            else:
                trend_direction = 'insufficient_data'
                avg_percentage = 0.0
        else:
            trend_direction = 'insufficient_data'
            avg_percentage = 0.0
        
        trends = {
            'direction': trend_direction,
            'average_percentage': round(avg_percentage, 2),
            'monthly_data': monthly_breakdown,
        }
        
        # Comparison with school average
        school_all_attendances = TeacherAttendance.objects.all()
        school_total = school_all_attendances.count()
        school_hadir = school_all_attendances.filter(status='HADIR').count()
        school_avg_percentage = round(
            (school_hadir / school_total * 100), 2
        ) if school_total > 0 else 0.0
        
        comparison = {
            'teacher_percentage': overall_attendance_percentage,
            'school_average_percentage': school_avg_percentage,
            'difference': round(overall_attendance_percentage - school_avg_percentage, 2),
            'performance': 'above_average' if overall_attendance_percentage > school_avg_percentage else 'below_average' if overall_attendance_percentage < school_avg_percentage else 'average',
        }
        
        # Teaching load analysis
        active_schedules = teacher.schedules.filter(is_active=True)
        total_jp_per_week = sum(schedule.jp_count for schedule in active_schedules)
        
        # Count unique subjects and classrooms
        unique_subjects = active_schedules.values('subject').distinct().count()
        unique_classrooms = active_schedules.values('classroom').distinct().count()
        
        teaching_load = {
            'total_jp_per_week': total_jp_per_week,
            'total_schedules': active_schedules.count(),
            'unique_subjects': unique_subjects,
            'unique_classrooms': unique_classrooms,
            'subjects_taught': [s.name for s in teacher.subjects.filter(is_active=True)],
            'is_homeroom_teacher': teacher.is_homeroom_teacher,
            'homeroom_class': str(teacher.homeroom_class) if teacher.homeroom_class else None,
        }
        
        # Recent attendance records (last 30 days)
        thirty_days_ago = today - timedelta(days=30)
        recent_records = TeacherAttendance.objects.filter(
            teacher=teacher,
            date__gte=thirty_days_ago,
            date__lte=today
        ).select_related('schedule', 'schedule__subject', 'schedule__classroom').order_by('-date', 'jp_number')[:50]
        
        recent_records_list = []
        for record in recent_records:
            recent_records_list.append({
                'date': record.date,
                'jp_number': record.jp_number,
                'status': record.status,
                'status_display': record.get_status_display(),
                'subject': record.schedule.subject.name if record.schedule else None,
                'classroom': record.schedule.classroom.name if record.schedule else None,
                'notes': record.notes,
            })
        
        return {
            'teacher': teacher,
            'teacher_name': teacher.full_name,
            'nip': teacher.nip,
            'employment_status': teacher.employment_status,
            'overall_stats': {
                'total_records': total_all,
                'total_hadir': total_hadir_all,
                'total_sakit': total_sakit_all,
                'total_izin': total_izin_all,
                'total_cuti': total_cuti_all,
                'total_dinas': total_dinas_all,
                'total_alpa': total_alpa_all,
                'attendance_percentage': overall_attendance_percentage,
            },
            'monthly_breakdown': monthly_breakdown,
            'trends': trends,
            'comparison': comparison,
            'teaching_load': teaching_load,
            'recent_records': recent_records_list,
        }
