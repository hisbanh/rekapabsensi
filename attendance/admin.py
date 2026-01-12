"""
Admin configuration for the attendance application
Enterprise-grade admin interface with advanced features
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import csv
from django.http import HttpResponse
from django.template.response import TemplateResponse

from .models import (
    AcademicLevel, Classroom, Student, AttendanceRecord, 
    AttendanceSummary, AuditLog, AttendanceStatus
)


class ExportCsvMixin:
    """Mixin to add CSV export functionality to admin"""
    
    def export_as_csv(self, request, queryset):
        """Export selected items as CSV"""
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={meta}.csv'
        
        writer = csv.writer(response)
        writer.writerow(field_names)
        
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])
        
        return response
    
    export_as_csv.short_description = "Export Selected as CSV"


@admin.register(AcademicLevel)
class AcademicLevelAdmin(admin.ModelAdmin, ExportCsvMixin):
    """Academic Level admin"""
    
    list_display = ['code', 'name', 'level_type', 'grade_range', 'classroom_count', 'is_active']
    list_filter = ['level_type', 'is_active']
    search_fields = ['code', 'name']
    ordering = ['level_type', 'code']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'level_type', 'description')
        }),
        ('Academic Settings', {
            'fields': ('min_grade', 'max_grade')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    actions = ['export_as_csv', 'activate_levels', 'deactivate_levels']
    
    def classroom_count(self, obj):
        """Display number of classrooms"""
        return obj.classroom_set.count()
    classroom_count.short_description = 'Classrooms'
    
    def activate_levels(self, request, queryset):
        """Bulk activate academic levels"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} academic levels activated.')
    activate_levels.short_description = "Activate selected levels"
    
    def deactivate_levels(self, request, queryset):
        """Bulk deactivate academic levels"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} academic levels deactivated.')
    deactivate_levels.short_description = "Deactivate selected levels"


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin, ExportCsvMixin):
    """Classroom admin with comprehensive features"""
    
    list_display = [
        'full_name', 'academic_level', 'grade', 'section', 
        'student_count_display', 'capacity', 'homeroom_teacher', 
        'is_active', 'academic_year'
    ]
    list_filter = [
        'academic_level', 'grade', 'is_active', 'academic_year',
        ('homeroom_teacher', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = ['name', 'academic_level__name', 'homeroom_teacher__username']
    ordering = ['academic_level', 'grade', 'section']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('academic_level', 'grade', 'section', 'name')
        }),
        ('Classroom Details', {
            'fields': ('capacity', 'room_number', 'homeroom_teacher')
        }),
        ('Academic Information', {
            'fields': ('academic_year', 'is_active')
        }),
    )
    
    actions = ['export_as_csv', 'activate_classrooms', 'deactivate_classrooms']
    
    def student_count_display(self, obj):
        """Display student count with capacity indicator"""
        count = obj.student_count
        capacity = obj.capacity
        percentage = (count / capacity * 100) if capacity > 0 else 0
        
        if percentage >= 90:
            color = 'red'
        elif percentage >= 75:
            color = 'orange'
        else:
            color = 'green'
        
        return format_html(
            '<span style="color: {};">{}/{} ({}%)</span>',
            color, count, capacity, round(percentage)
        )
    student_count_display.short_description = 'Students'
    
    def activate_classrooms(self, request, queryset):
        """Bulk activate classrooms"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} classrooms activated.')
    activate_classrooms.short_description = "Activate selected classrooms"
    
    def deactivate_classrooms(self, request, queryset):
        """Bulk deactivate classrooms"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} classrooms deactivated.')
    deactivate_classrooms.short_description = "Deactivate selected classrooms"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin, ExportCsvMixin):
    """Enhanced Student admin with comprehensive features"""
    
    list_display = [
        'student_id', 'name', 'classroom_link', 'academic_level_display', 
        'nisn', 'is_active', 'attendance_rate_display', 'total_records',
        'enrollment_date'
    ]
    list_filter = [
        'classroom__academic_level', 'classroom__grade', 'is_active', 
        'gender', 'enrollment_date',
        ('classroom', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = ['name', 'student_id', 'nisn', 'classroom__name']
    ordering = ['classroom__academic_level', 'classroom__grade', 'classroom__section', 'name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'attendance_rate_display']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('student_id', 'name', 'classroom', 'nisn')
        }),
        ('Personal Details', {
            'fields': ('date_of_birth', 'gender', 'address', 'parent_phone'),
            'classes': ('collapse',)
        }),
        ('Academic Information', {
            'fields': ('enrollment_date', 'graduation_date', 'student_number')
        }),
        ('System Information', {
            'fields': ('is_active', 'id', 'created_at', 'updated_at', 'attendance_rate_display'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['export_as_csv', 'activate_students', 'deactivate_students']
    
    def classroom_link(self, obj):
        """Create link to classroom"""
        url = reverse('admin:attendance_classroom_change', args=[obj.classroom.pk])
        return format_html('<a href="{}">{}</a>', url, obj.classroom)
    classroom_link.short_description = 'Classroom'
    classroom_link.admin_order_field = 'classroom'
    
    def academic_level_display(self, obj):
        """Display academic level"""
        return obj.classroom.academic_level.code
    academic_level_display.short_description = 'Level'
    academic_level_display.admin_order_field = 'classroom__academic_level'
    
    def attendance_rate_display(self, obj):
        """Display attendance rate with color coding"""
        rate = obj.attendance_rate
        if rate >= 90:
            color = 'green'
        elif rate >= 75:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{}</span>',
            color, f"{rate:.1f}%"
        )
    attendance_rate_display.short_description = 'Attendance Rate'
    attendance_rate_display.admin_order_field = 'attendance_rate'
    
    def total_records(self, obj):
        """Display total attendance records"""
        return obj.attendancerecord_set.count()
    total_records.short_description = 'Total Records'
    
    def activate_students(self, request, queryset):
        """Bulk activate students"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} students activated.')
    activate_students.short_description = "Activate selected students"
    
    def deactivate_students(self, request, queryset):
        """Bulk deactivate students"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} students deactivated.')
    deactivate_students.short_description = "Deactivate selected students"
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch_related"""
        return super().get_queryset(request).select_related(
            'classroom', 'classroom__academic_level'
        ).prefetch_related('attendancerecord_set')


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin, ExportCsvMixin):
    """Enhanced AttendanceRecord admin"""
    
    list_display = [
        'student_link', 'classroom_display', 'date', 'status_display', 
        'teacher', 'notes_preview', 'recorded_at'
    ]
    list_filter = [
        'status', 'date', 'student__classroom__academic_level', 
        'student__classroom__grade', 'teacher',
        ('date', admin.DateFieldListFilter),
        ('recorded_at', admin.DateFieldListFilter),
    ]
    search_fields = [
        'student__name', 'student__student_id', 'student__classroom__name',
        'teacher__username', 'teacher__first_name', 'teacher__last_name'
    ]
    date_hierarchy = 'date'
    ordering = ['-date', 'student__classroom__academic_level', 'student__classroom__grade', 'student__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'recorded_at']
    
    fieldsets = (
        ('Attendance Information', {
            'fields': ('student', 'date', 'status', 'teacher')
        }),
        ('Additional Details', {
            'fields': ('notes', 'ip_address'),
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at', 'recorded_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['export_as_csv', 'mark_as_present', 'mark_as_absent']
    
    def student_link(self, obj):
        """Create link to student detail"""
        url = reverse('admin:attendance_student_change', args=[obj.student.pk])
        return format_html('<a href="{}">{}</a>', url, obj.student.name)
    student_link.short_description = 'Student'
    student_link.admin_order_field = 'student__name'
    
    def classroom_display(self, obj):
        """Display classroom information"""
        return obj.student.classroom
    classroom_display.short_description = 'Classroom'
    classroom_display.admin_order_field = 'student__classroom'
    
    def status_display(self, obj):
        """Display status with color coding"""
        colors = {
            'HADIR': 'green',
            'SAKIT': 'orange',
            'IZIN': 'blue',
            'ALPA': 'red'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status'
    
    def notes_preview(self, obj):
        """Show preview of notes"""
        if obj.notes:
            return obj.notes[:50] + '...' if len(obj.notes) > 50 else obj.notes
        return '-'
    notes_preview.short_description = 'Notes'
    
    def mark_as_present(self, request, queryset):
        """Bulk mark as present"""
        updated = queryset.update(status=AttendanceStatus.HADIR)
        self.message_user(request, f'{updated} records marked as present.')
    mark_as_present.short_description = "Mark selected as Present"
    
    def mark_as_absent(self, request, queryset):
        """Bulk mark as absent"""
        updated = queryset.update(status=AttendanceStatus.ALPA)
        self.message_user(request, f'{updated} records marked as absent.')
    mark_as_absent.short_description = "Mark selected as Absent"
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related(
            'student', 'student__classroom', 'student__classroom__academic_level', 'teacher'
        )


@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin, ExportCsvMixin):
    """AttendanceSummary admin"""
    
    list_display = [
        'student', 'classroom_display', 'year', 'month', 'total_days', 
        'total_hadir', 'attendance_percentage_display'
    ]
    list_filter = [
        'year', 'month', 'student__classroom__academic_level', 
        'student__classroom__grade'
    ]
    search_fields = ['student__name', 'student__student_id']
    ordering = ['-year', '-month', 'student__classroom__academic_level', 'student__classroom__grade']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    actions = ['export_as_csv', 'recalculate_percentages']
    
    def classroom_display(self, obj):
        """Display classroom"""
        return obj.student.classroom
    classroom_display.short_description = 'Classroom'
    classroom_display.admin_order_field = 'student__classroom'
    
    def attendance_percentage_display(self, obj):
        """Display percentage with color coding"""
        percentage = obj.attendance_percentage
        if percentage >= 90:
            color = 'green'
        elif percentage >= 75:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, f"{percentage:.1f}%"
        )
    attendance_percentage_display.short_description = 'Attendance %'
    attendance_percentage_display.admin_order_field = 'attendance_percentage'
    
    def recalculate_percentages(self, request, queryset):
        """Recalculate attendance percentages"""
        for summary in queryset:
            summary.calculate_percentage()
            summary.save()
        self.message_user(request, f'Recalculated {queryset.count()} summaries.')
    recalculate_percentages.short_description = "Recalculate percentages"


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """AuditLog admin for system monitoring"""
    
    list_display = [
        'created_at', 'user', 'action', 'model_name', 
        'description_preview', 'ip_address'
    ]
    list_filter = [
        'action', 'model_name', 'created_at',
        ('created_at', admin.DateFieldListFilter),
    ]
    search_fields = ['user__username', 'description', 'ip_address']
    ordering = ['-created_at']
    readonly_fields = [
        'id', 'user', 'action', 'model_name', 'object_id',
        'description', 'ip_address', 'user_agent', 'created_at'
    ]
    
    def description_preview(self, obj):
        """Show preview of description"""
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    description_preview.short_description = 'Description'
    
    def has_add_permission(self, request):
        """Disable adding audit logs manually"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable changing audit logs"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete audit logs"""
        return request.user.is_superuser


# Customize the default admin site
admin.site.site_header = "SIPA Beta  Administration"
admin.site.site_title = "SIPA Beta  Admin"
admin.site.index_title = "Dashboard Administrasi SIPA Beta "

# Additional customizations
admin.site.site_url = "/"  # Link to main site


# Override the default admin index view to add dashboard context
from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse

original_index = AdminSite.index

def custom_index(self, request, extra_context=None):
    """Custom admin index with dashboard statistics"""
    extra_context = extra_context or {}
    
    # Get today's date
    today = timezone.now().date()
    
    # Calculate statistics
    total_students = Student.objects.filter(is_active=True).count()
    
    # Today's attendance statistics
    today_records = AttendanceRecord.objects.filter(date=today)
    present_today = today_records.filter(status=AttendanceStatus.HADIR).count()
    absent_today = today_records.exclude(status=AttendanceStatus.HADIR).count()
    
    # If no records for today, use yesterday's data as fallback
    if today_records.count() == 0:
        yesterday = today - timedelta(days=1)
        yesterday_records = AttendanceRecord.objects.filter(date=yesterday)
        present_today = yesterday_records.filter(status=AttendanceStatus.HADIR).count()
        absent_today = yesterday_records.exclude(status=AttendanceStatus.HADIR).count()
    
    # Weekly attendance data for chart
    week_data = []
    for i in range(7):
        date = today - timedelta(days=6-i)
        day_records = AttendanceRecord.objects.filter(date=date)
        present = day_records.filter(status=AttendanceStatus.HADIR).count()
        total = day_records.count()
        percentage = (present / total * 100) if total > 0 else 0
        week_data.append({
            'date': date,
            'present': present,
            'total': total,
            'percentage': round(percentage, 1)
        })
    
    # Class statistics
    classrooms = Classroom.objects.filter(is_active=True).select_related('academic_level')
    class_stats = []
    for classroom in classrooms[:10]:  # Limit to 10 for display
        students_in_class = classroom.students.filter(is_active=True).count()
        present_in_class = AttendanceRecord.objects.filter(
            student__classroom=classroom,
            date=today,
            status=AttendanceStatus.HADIR
        ).count()
        
        if students_in_class > 0:
            percentage = (present_in_class / students_in_class) * 100
        else:
            percentage = 0
            
        class_stats.append({
            'classroom': classroom,
            'present': present_in_class,
            'total': students_in_class,
            'percentage': round(percentage, 1)
        })
    
    # Recent activity (last 10 attendance records)
    recent_activity = AttendanceRecord.objects.select_related(
        'student', 'student__classroom', 'teacher'
    ).order_by('-recorded_at')[:10]
    
    # System status
    last_backup = "2 jam lalu"  # This would come from actual backup system
    
    extra_context.update({
        'total_students': total_students,
        'present_today': present_today,
        'absent_today': absent_today,
        'week_data': week_data,
        'class_stats': class_stats,
        'recent_activity': recent_activity,
        'last_backup': last_backup,
        'dashboard_date': today,
    })
    
    return original_index(self, request, extra_context)

# Monkey patch the admin site
AdminSite.index = custom_index