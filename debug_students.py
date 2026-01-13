#!/usr/bin/env python
"""
Script untuk debug masalah data siswa di PythonAnywhere
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sipa_yaumi.settings')
django.setup()

from attendance.models import AcademicLevel, Classroom, Student
from django.utils import timezone

def debug_database():
    """Debug status database"""
    print("=== DATABASE STATUS ===")
    print(f"Academic Levels: {AcademicLevel.objects.count()}")
    print(f"Classrooms: {Classroom.objects.count()}")
    print(f"Students: {Student.objects.count()}")
    
    if AcademicLevel.objects.exists():
        print("\nAcademic Levels:")
        for level in AcademicLevel.objects.all():
            print(f"  - {level.code}: {level.name}")
    
    if Classroom.objects.exists():
        print("\nClassrooms:")
        for classroom in Classroom.objects.all()[:5]:  # Show first 5
            print(f"  - {classroom}")
    
    if Student.objects.exists():
        print("\nStudents (first 5):")
        for student in Student.objects.all()[:5]:
            print(f"  - {student.student_id}: {student.name} ({student.classroom})")
    else:
        print("\n❌ No students found!")

def create_sample_data():
    """Buat data contoh jika kosong"""
    print("\n=== CREATING SAMPLE DATA ===")
    
    # Buat Academic Level
    smp, created = AcademicLevel.objects.get_or_create(
        code='SMP',
        defaults={
            'name': 'Sekolah Menengah Pertama',
            'level_type': 'SMP',
            'description': 'Tingkat pendidikan menengah pertama (kelas 7-9)',
            'min_grade': 7,
            'max_grade': 9,
        }
    )
    if created:
        print("✅ Created SMP Academic Level")
    
    # Buat Classroom
    classroom, created = Classroom.objects.get_or_create(
        academic_level=smp,
        grade=7,
        section='A',
        academic_year='2024/2025',
        defaults={'capacity': 35}
    )
    if created:
        print("✅ Created 7-A Classroom")
    
    # Buat beberapa siswa
    sample_students = [
        {'id': '7A01', 'name': 'Abdullah Muhammad Sadat'},
        {'id': '7A02', 'name': 'Abdurrahman Sumardi'},
        {'id': '7A03', 'name': 'Abidz Alvaro Bastian'},
    ]
    
    created_count = 0
    for student_data in sample_students:
        student, created = Student.objects.get_or_create(
            student_id=student_data['id'],
            defaults={
                'name': student_data['name'],
                'classroom': classroom,
                'enrollment_date': timezone.now().date()
            }
        )
        if created:
            created_count += 1
    
    print(f"✅ Created {created_count} sample students")

if __name__ == "__main__":
    print("🔍 DEBUGGING STUDENT DATA ISSUE")
    print("=" * 40)
    
    debug_database()
    
    if Student.objects.count() == 0:
        print("\n🔧 No students found. Creating sample data...")
        create_sample_data()
        print("\n📊 After creating sample data:")
        debug_database()
    
    print("\n✅ Debug completed!")
    print("\nNext steps:")
    print("1. Check admin panel: /admin/attendance/student/")
    print("2. If still empty, run: python manage.py populate_students --reset")
    print("3. Check error logs in PythonAnywhere")