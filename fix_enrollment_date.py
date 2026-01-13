#!/usr/bin/env python
"""
Script to fix enrollment date issues when populating students
"""
import os
import django
from datetime import date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sipa_yaumi.settings')
django.setup()

from attendance.models import AcademicLevel, Classroom, Student
from django.utils import timezone

def populate_students_with_valid_dates():
    """Populate students with valid enrollment dates"""
    
    # Ensure academic levels exist
    smp, _ = AcademicLevel.objects.get_or_create(
        code='SMP',
        defaults={
            'name': 'Sekolah Menengah Pertama',
            'level_type': 'SMP',
            'min_grade': 7,
            'max_grade': 9
        }
    )
    
    sma, _ = AcademicLevel.objects.get_or_create(
        code='SMA',
        defaults={
            'name': 'Sekolah Menengah Atas',
            'level_type': 'SMA',
            'min_grade': 10,
            'max_grade': 12
        }
    )
    
    # Ensure classrooms exist
    classrooms_data = [
        {'level': smp, 'grade': 7, 'section': 'A'},
        {'level': smp, 'grade': 7, 'section': 'B'},
        {'level': smp, 'grade': 8, 'section': 'A'},
        {'level': smp, 'grade': 8, 'section': 'B'},
        {'level': smp, 'grade': 9, 'section': 'A'},
        {'level': smp, 'grade': 9, 'section': 'B'},
        {'level': sma, 'grade': 10, 'section': 'A'},
        {'level': sma, 'grade': 10, 'section': 'B'},
        {'level': sma, 'grade': 11, 'section': ''},
        {'level': sma, 'grade': 12, 'section': ''},
    ]
    
    for data in classrooms_data:
        classroom, created = Classroom.objects.get_or_create(
            academic_level=data['level'],
            grade=data['grade'],
            section=data['section'],
            defaults={
                'academic_year': '2024/2025',
                'is_active': True
            }
        )
        if created:
            print(f"Created classroom: {classroom}")
    
    # Create classroom mapping
    classroom_mapping = {}
    for classroom in Classroom.objects.all():
        if classroom.section:
            key = f"{classroom.grade}-{classroom.section}"
        else:
            key = str(classroom.grade)
        classroom_mapping[key] = classroom
    
    # Sample students data (reduced for testing)
    students_data = [
        {'id': '7A01', 'nisn': '', 'name': 'Abdullah Muhammad Sadat', 'class': '7-A'},
        {'id': '7A02', 'nisn': '', 'name': 'Abdurrahman Sumardi', 'class': '7-A'},
        {'id': '7B01', 'nisn': '', 'name': 'Abdul Hakam As Syarif', 'class': '7-B'},
        {'id': '8A01', 'nisn': '0224010003', 'name': 'Abid Naqqi Alhakim', 'class': '8-A'},
        {'id': '9A01', 'nisn': '0223010001', 'name': 'Abdul Malik Al Atsary', 'class': '9-A'},
        {'id': '10A01', 'nisn': '', 'name': 'Anugerah Rajendra Aji Pawenang', 'class': '10-A'},
        {'id': '1101', 'nisn': '0324010001', 'name': 'Abdul Hamid', 'class': '11'},
        {'id': '1201', 'nisn': '0323010001', 'name': 'Abdul Aziz Risay Ar Royan', 'class': '12'},
    ]
    
    created_count = 0
    updated_count = 0
    error_count = 0
    
    # Use today's date for enrollment
    today = timezone.now().date()
    
    for student_data in students_data:
        try:
            # Get classroom
            class_key = student_data['class']
            if class_key not in classroom_mapping:
                print(f"Classroom not found for class: {class_key}")
                error_count += 1
                continue
            
            classroom = classroom_mapping[class_key]
            
            # Create student with explicit enrollment_date
            student, created = Student.objects.get_or_create(
                student_id=student_data['id'],
                defaults={
                    'nisn': student_data['nisn'],
                    'name': student_data['name'],
                    'classroom': classroom,
                    'enrollment_date': today,  # Explicitly set to today
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                print(f"Created: {student.name} ({student.classroom})")
            else:
                # Update existing student (don't change enrollment_date)
                student.nisn = student_data['nisn']
                student.name = student_data['name']
                student.classroom = classroom
                student.is_active = True
                # Skip validation by using update instead of save
                Student.objects.filter(id=student.id).update(
                    nisn=student.nisn,
                    name=student.name,
                    classroom=classroom,
                    is_active=True
                )
                updated_count += 1
                print(f"Updated: {student.name} ({student.classroom})")
                
        except Exception as e:
            print(f"Error processing student {student_data['id']}: {str(e)}")
            error_count += 1
    
    print(f"\nSummary:")
    print(f"Students: {created_count} created, {updated_count} updated, {error_count} errors")
    print(f"Total students in database: {Student.objects.count()}")

if __name__ == '__main__':
    populate_students_with_valid_dates()