from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('students/', views.student_list, name='student_list'),
    path('students/<str:student_id>/', views.student_detail, name='student_detail'),
    path('attendance/', views.take_attendance, name='take_attendance'),
    path('report/', views.attendance_report, name='attendance_report'),
    path('export/', views.export_csv, name='export_csv'),
    path('api/stats/', views.api_attendance_stats, name='api_attendance_stats'),
    path('search/', views.search, name='search'),  # Add search URL for Unfold
]