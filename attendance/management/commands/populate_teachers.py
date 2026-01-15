"""
Management command to populate sample teacher data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from attendance.models import Teacher, TeacherSchedule
import random


class Command(BaseCommand):
    help = 'Populate sample teacher data for testing'
    
    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample teachers...')
        
        # Sample data
        teachers_data = [
            {
                'teacher_id': 'U001',
                'name': 'Ustadz Ahmad Fauzi',
                'subjects': 'Bahasa Arab, Tahfidz',
                'schedules': [
                    {'day': 0, 'jp': [1, 2, 3], 'subject': 'Bahasa Arab'},
                    {'day': 2, 'jp': [4, 5], 'subject': 'Tahfidz'},
                    {'day': 4, 'jp': [1, 2], 'subject': 'Bahasa Arab', 'piket': True},
                ]
            },
            {
                'teacher_id': 'U002',
                'name': 'Ustadzah Fatimah Zahra',
                'subjects': 'Fiqih, Akhlak',
                'schedules': [
                    {'day': 1, 'jp': [1, 2, 3], 'subject': 'Fiqih'},
                    {'day': 3, 'jp': [4, 5, 6], 'subject': 'Akhlak'},
                ]
            },
            {
                'teacher_id': 'U003',
                'name': 'Ustadz Muhammad Ridwan',
                'subjects': 'Tafsir, Hadits',
                'schedules': [
                    {'day': 0, 'jp': [4, 5], 'subject': 'Tafsir'},
                    {'day': 2, 'jp': [1, 2, 3], 'subject': 'Hadits'},
                    {'day': 4, 'jp': [6, 7], 'subject': 'Tafsir'},
                ]
            },
            {
                'teacher_id': 'U004',
                'name': 'Ustadzah Aisyah Nur',
                'subjects': 'Tajwid, Qiroah',
                'schedules': [
                    {'day': 1, 'jp': [4, 5], 'subject': 'Tajwid'},
                    {'day': 3, 'jp': [1, 2], 'subject': 'Qiroah'},
                ]
            },
            {
                'teacher_id': 'U005',
                'name': 'Ustadz Abdullah Hasan',
                'subjects': 'Aqidah, Sirah',
                'schedules': [
                    {'day': 0, 'jp': [6, 7], 'subject': 'Aqidah'},
                    {'day': 2, 'jp': [6, 7, 8], 'subject': 'Sirah', 'piket': True},
                ]
            },
        ]
        
        academic_year = '2024/2025'
        created_count = 0
        
        for data in teachers_data:
            # Check if teacher already exists
            teacher, created = Teacher.objects.get_or_create(
                teacher_id=data['teacher_id'],
                defaults={
                    'name': data['name'],
                    'subjects': data['subjects'],
                    'academic_year': academic_year,
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  Created: {teacher.name}')
                
                # Create schedules
                for schedule_data in data['schedules']:
                    schedule = TeacherSchedule.objects.create(
                        teacher=teacher,
                        day_of_week=schedule_data['day'],
                        jp_numbers=schedule_data['jp'],
                        subject=schedule_data['subject'],
                        is_piket=schedule_data.get('piket', False),
                        academic_year=academic_year,
                    )
                    day_name = dict(TeacherSchedule.DAY_CHOICES)[schedule_data['day']]
                    self.stdout.write(f'    - Schedule: {day_name}, JP {schedule_data["jp"]}')
            else:
                self.stdout.write(f'  Exists: {teacher.name}')
        
        self.stdout.write(self.style.SUCCESS(f'\nDone! Created {created_count} teachers'))
        self.stdout.write(f'Total teachers: {Teacher.objects.count()}')
