from django.urls import path, include
from . import views
from . import teacher_views
from . import teacher_attendance_views
from . import teacher_dashboard_views
from . import teacher_report_views

urlpatterns = [
    # Teacher API endpoints
    path('api/', include('attendance.api.urls')),
    
    path('', views.dashboard, name='dashboard'),
    path('students/', views.student_list, name='student_list'),
    path('students/new/', views.student_list_new, name='student_list_new'),
    path('students/<str:student_id>/', views.student_detail, name='student_detail'),
    path('attendance/', views.take_attendance, name='take_attendance'),
    path('report/', views.attendance_report, name='attendance_report'),
    path('report/new/', views.attendance_report_new, name='attendance_report_new'),
    path('export/', views.export_csv, name='export_csv'),
    path('api/stats/', views.api_attendance_stats, name='api_attendance_stats'),
    path('api/students/search/', views.api_student_search, name='api_student_search'),
    path('api/students/<uuid:student_id>/stats/', views.api_student_stats, name='api_student_stats'),
    path('search/', views.search, name='search'),  # Add search URL for Unfold
    
    # JP-Based Attendance Input URLs
    path('input/', views.attendance_input_select, name='attendance_input'),
    path('input/<uuid:classroom_id>/<str:date_str>/', views.attendance_input_form, name='attendance_input_form'),
    path('api/attendance/save/', views.api_save_attendance, name='api_save_attendance'),
    
    # Management CRUD URLs
    # Student Management
    path('manage/students/', views.manage_student_list, name='manage_student_list'),
    path('manage/students/create/', views.manage_student_create, name='manage_student_create'),
    path('manage/students/<uuid:pk>/edit/', views.manage_student_edit, name='manage_student_edit'),
    path('manage/students/<uuid:pk>/delete/', views.manage_student_delete, name='manage_student_delete'),
    path('api/students/inline-edit/', views.api_student_inline_edit, name='api_student_inline_edit'),
    
    # Classroom Management
    path('manage/classrooms/', views.manage_classroom_list, name='manage_classroom_list'),
    path('manage/classrooms/create/', views.manage_classroom_create, name='manage_classroom_create'),
    path('manage/classrooms/<uuid:pk>/edit/', views.manage_classroom_edit, name='manage_classroom_edit'),
    path('manage/classrooms/<uuid:pk>/delete/', views.manage_classroom_delete, name='manage_classroom_delete'),
    
    # Holiday Management
    path('manage/holidays/', views.manage_holiday_list, name='manage_holiday_list'),
    path('manage/holidays/create/', views.manage_holiday_create, name='manage_holiday_create'),
    path('manage/holidays/<uuid:pk>/edit/', views.manage_holiday_edit, name='manage_holiday_edit'),
    path('manage/holidays/<uuid:pk>/delete/', views.manage_holiday_delete, name='manage_holiday_delete'),
    
    # Day Schedule Settings
    path('manage/settings/schedule/', views.manage_day_schedule, name='manage_day_schedule'),
    
    # User Management (Admin Only)
    path('manage/users/', views.manage_user_list, name='manage_user_list'),
    path('manage/users/create/', views.manage_user_create, name='manage_user_create'),
    path('manage/users/<int:pk>/edit/', views.manage_user_edit, name='manage_user_edit'),
    path('manage/users/<int:pk>/delete/', views.manage_user_delete, name='manage_user_delete'),
    
    # Bulk Actions
    path('manage/bulk-action/', views.bulk_action, name='bulk_action'),
    
    # Generic Inline Edit API
    path('api/inline-edit/', views.api_inline_edit, name='api_inline_edit'),
    
    # JP-Based Report URLs
    path('jp-report/', views.jp_report, name='jp_report'),
    path('export/jp-csv/', views.export_jp_csv, name='export_jp_csv'),
    path('export/pdf/class/', views.export_pdf_class, name='export_pdf_class'),
    path('export/pdf/student/', views.export_pdf_student, name='export_pdf_student'),
    path('export/excel/class/', views.export_excel_class, name='export_excel_class'),
    path('export/excel/all/', views.export_excel_all, name='export_excel_all'),
    path('api/students-by-classroom/', views.api_get_students_by_classroom, name='api_students_by_classroom'),
    
    # Teacher Management URLs
    path('teachers/', teacher_views.teacher_list, name='teacher_list'),
    path('teachers/create/', teacher_views.teacher_create, name='teacher_create'),
    path('teachers/<uuid:pk>/', teacher_views.teacher_detail, name='teacher_detail'),
    path('teachers/<uuid:pk>/edit/', teacher_views.teacher_update, name='teacher_update'),
    path('teachers/<uuid:pk>/delete/', teacher_views.teacher_delete, name='teacher_delete'),
    path('teachers/<uuid:pk>/schedule/', teacher_views.teacher_schedule, name='teacher_schedule'),
    path('api/teachers/inline-edit/', teacher_views.api_teacher_inline_edit, name='api_teacher_inline_edit'),
    
    # Teacher Attendance URLs
    path('teacher-attendance/', teacher_attendance_views.attendance_input, name='teacher_attendance_input'),
    path('teacher-attendance/admin/', teacher_attendance_views.attendance_admin_input, name='teacher_attendance_admin'),
    path('teacher-attendance/history/', teacher_attendance_views.attendance_history, name='teacher_attendance_history'),
    path('teacher-attendance/<uuid:pk>/edit/', teacher_attendance_views.attendance_update, name='teacher_attendance_update'),
    path('teacher-attendance/<uuid:pk>/delete/', teacher_attendance_views.attendance_delete, name='teacher_attendance_delete'),
    
    # Teacher Attendance API URLs
    path('api/teacher-attendance/validate-location/', teacher_attendance_views.api_validate_location, name='api_validate_location'),
    path('api/teacher-attendance/schedule/', teacher_attendance_views.api_teacher_schedule, name='api_teacher_schedule'),
    
    # Teacher Dashboard URLs
    path('teacher-dashboard/', teacher_dashboard_views.teacher_dashboard, name='teacher_dashboard'),
    path('api/teacher-dashboard/', teacher_dashboard_views.teacher_dashboard_api, name='teacher_dashboard_api'),
    
    # Teacher Report URLs
    path('teacher-reports/', teacher_report_views.teacher_report, name='teacher_report'),
    path('teacher-reports/pdf/<uuid:teacher_id>/', teacher_report_views.teacher_report_pdf, name='teacher_report_pdf'),
    path('teacher-reports/excel/', teacher_report_views.teacher_report_excel, name='teacher_report_excel'),
    path('teacher-analytics/', teacher_report_views.teacher_analytics, name='teacher_analytics'),
    path('api/teacher-report-data/', teacher_report_views.api_teacher_report_data, name='api_teacher_report_data'),
]