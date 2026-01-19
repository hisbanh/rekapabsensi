from django.urls import path
from . import views
from . import views_teacher

urlpatterns = [
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
    
    # ============================================
    # Teacher/Ustadz URLs
    # ============================================
    
    # Teacher Dashboard
    path('teacher/', views_teacher.teacher_dashboard, name='teacher_dashboard'),
    
    # Teacher Management
    path('teacher/list/', views_teacher.teacher_list, name='teacher_list'),
    path('teacher/create/', views_teacher.teacher_create, name='teacher_create'),
    path('teacher/<uuid:pk>/', views_teacher.teacher_detail, name='teacher_detail'),
    path('teacher/<uuid:pk>/edit/', views_teacher.teacher_edit, name='teacher_edit'),
    path('teacher/<uuid:pk>/delete/', views_teacher.teacher_delete, name='teacher_delete'),
    
    # Teacher Schedule Management
    path('teacher/<uuid:teacher_id>/schedule/', views_teacher.teacher_schedule_manage, name='teacher_schedule_manage'),
    path('teacher/<uuid:teacher_id>/schedule/<int:day_of_week>/edit/', views_teacher.teacher_schedule_edit, name='teacher_schedule_edit'),
    path('teacher/schedule/<uuid:schedule_id>/delete/', views_teacher.teacher_schedule_delete, name='teacher_schedule_delete'),
    
    # Teacher Attendance Input
    path('teacher/attendance/', views_teacher.teacher_attendance_input, name='teacher_attendance_input'),
    path('teacher/attendance/<str:date_str>/', views_teacher.teacher_attendance_form, name='teacher_attendance_form'),
    path('api/teacher/attendance/save/', views_teacher.api_save_teacher_attendance, name='api_save_teacher_attendance'),
    path('api/teacher/attendance/reset/', views_teacher.api_reset_teacher_attendance_form, name='api_reset_teacher_attendance'),
    path('api/teacher/attendance/mark-all-present/', views_teacher.api_mark_all_teachers_present, name='api_mark_all_teachers_present'),
    
    # Teacher Attendance Reports
    path('teacher/report/', views_teacher.teacher_attendance_report, name='teacher_attendance_report'),
    
    # Teacher Export
    path('teacher/export/excel/', views_teacher.teacher_export_excel, name='teacher_export_excel'),
    path('teacher/export/csv/', views_teacher.teacher_export_csv, name='teacher_export_csv'),
    path('teacher/export/pdf/', views_teacher.teacher_export_pdf, name='teacher_export_pdf'),
    path('teacher/<uuid:teacher_id>/export/pdf/', views_teacher.teacher_export_individual_pdf, name='teacher_export_individual_pdf'),
    
    # Teacher Export - HTML/PDF dengan template modern
    path('teacher/<uuid:teacher_id>/export/html-pdf/', views_teacher.teacher_export_html_pdf, name='teacher_export_html_pdf'),
    path('teacher/export/all-html-pdf/', views_teacher.teacher_export_all_pdf_html, name='teacher_export_all_pdf_html'),
]