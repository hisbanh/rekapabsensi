"""
URL Configuration for Teacher API
"""
from django.urls import path
from . import teacher_api, schedule_api

app_name = 'teacher_api'

urlpatterns = [
    # Teacher CRUD endpoints
    path('teachers/', teacher_api.teacher_list_create, name='teacher_list_create'),
    path('teachers/<str:teacher_id>/', teacher_api.teacher_detail_update_delete, name='teacher_detail_update_delete'),
    
    # Teacher schedule endpoint
    path('teachers/<str:teacher_id>/schedule/', teacher_api.teacher_schedule, name='teacher_schedule'),
    
    # Teacher statistics endpoint
    path('teachers/<str:teacher_id>/statistics/', teacher_api.teacher_statistics, name='teacher_statistics'),
    
    # Schedule conflict detection (must be before detail pattern)
    path('schedules/detect-conflicts/', schedule_api.detect_conflicts, name='detect_conflicts'),
    
    # Weekly schedule endpoint (must be before detail pattern)
    path('schedules/weekly/<str:teacher_id>/', schedule_api.weekly_schedule, name='weekly_schedule'),
    
    # Schedule CRUD endpoints
    path('schedules/', schedule_api.schedule_list_create, name='schedule_list_create'),
    path('schedules/<str:schedule_id>/', schedule_api.schedule_detail_update_delete, name='schedule_detail_update_delete'),
]
