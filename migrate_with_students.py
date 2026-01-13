#!/usr/bin/env python
"""
Script untuk menjalankan migrasi dengan data siswa
Mengatasi masalah enrollment_date validation
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sipa_yaumi.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from attendance.models import AcademicLevel, Classroom, Student

def check_current_status():
    """Cek status database saat ini"""
    print("=== CURRENT DATABASE STATUS ===")
    
    try:
        academic_levels = AcademicLevel.objects.count()
        classrooms = Classroom.objects.count()
        students = Student.objects.count()
        
        print(f"📚 Academic Levels: {academic_levels}")
        print(f"🏫 Classrooms: {classrooms}")
        print(f"👥 Students: {students}")
        
        return {
            'academic_levels': academic_levels,
            'classrooms': classrooms,
            'students': students
        }
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return None

def run_migrations():
    """Jalankan migrasi dengan aman"""
    print("\n=== RUNNING MIGRATIONS ===")
    
    try:
        # Jalankan migrasi
        print("🔄 Running migrations...")
        call_command('migrate', verbosity=2)
        print("✅ Migrations completed successfully!")
        
        return True
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False

def verify_data():
    """Verifikasi data setelah migrasi"""
    print("\n=== VERIFYING DATA ===")
    
    try:
        academic_levels = AcademicLevel.objects.count()
        classrooms = Classroom.objects.count()
        students = Student.objects.count()
        
        print(f"📚 Academic Levels: {academic_levels}")
        print(f"🏫 Classrooms: {classrooms}")
        print(f"👥 Students: {students}")
        
        if students > 0:
            print("\n📋 Sample students:")
            for student in Student.objects.all()[:5]:
                print(f"   - {student.student_id}: {student.name} ({student.classroom})")
        
        # Cek enrollment dates
        future_dates = Student.objects.filter(enrollment_date__gt=django.utils.timezone.now().date()).count()
        if future_dates > 0:
            print(f"⚠️  Warning: {future_dates} students have future enrollment dates")
        else:
            print("✅ All enrollment dates are valid")
        
        return True
    except Exception as e:
        print(f"❌ Error verifying data: {e}")
        return False

def fix_enrollment_dates():
    """Fix enrollment dates jika masih ada yang bermasalah"""
    print("\n=== FIXING ENROLLMENT DATES ===")
    
    try:
        from django.utils import timezone
        today = timezone.now().date()
        
        # Update students dengan enrollment_date yang bermasalah
        updated = Student.objects.filter(
            enrollment_date__gt=today
        ).update(enrollment_date=today)
        
        if updated > 0:
            print(f"🔧 Fixed {updated} students with future enrollment dates")
        else:
            print("✅ No enrollment dates need fixing")
        
        return True
    except Exception as e:
        print(f"❌ Error fixing enrollment dates: {e}")
        return False

def main():
    """Main function"""
    print("🚀 MIGRATION WITH STUDENT DATA")
    print("=" * 50)
    
    # Cek status awal
    initial_status = check_current_status()
    
    # Jalankan migrasi
    if run_migrations():
        # Verifikasi data
        if verify_data():
            # Fix enrollment dates jika perlu
            fix_enrollment_dates()
            
            print("\n" + "=" * 50)
            print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
            print("\nNext steps:")
            print("1. Check admin panel: /admin/attendance/student/")
            print("2. Test attendance functionality")
            print("3. Reload web app in PythonAnywhere dashboard")
        else:
            print("\n❌ Data verification failed")
    else:
        print("\n❌ Migration failed")
        print("\nTroubleshooting:")
        print("1. Check database permissions")
        print("2. Ensure all dependencies are installed")
        print("3. Check for conflicting migrations")

if __name__ == "__main__":
    main()