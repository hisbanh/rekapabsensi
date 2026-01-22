#!/usr/bin/env python
"""
Script to automatically create teacher profile for admin user
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sipa_yaumi.settings')
django.setup()

from django.contrib.auth.models import User
from attendance.models import Teacher, Subject
from datetime import date

def setup_admin_teacher():
    """Create teacher profile for admin user automatically"""
    try:
        print("=" * 60)
        print("SETUP ADMIN TEACHER PROFILE")
        print("=" * 60)
        
        # Get admin user
        try:
            user = User.objects.get(username='admin')
            print(f"\n✓ Found user: {user.username}")
            print(f"  Email: {user.email or 'N/A'}")
            print(f"  Is Superuser: {user.is_superuser}")
        except User.DoesNotExist:
            print("\n✗ Admin user not found!")
            return False
        
        # Check if user already has teacher profile
        if hasattr(user, 'teacher_profile'):
            teacher = user.teacher_profile
            print(f"\n✓ Admin already has a teacher profile:")
            print(f"  Name: {teacher.full_name}")
            print(f"  NIP: {teacher.nip}")
            print(f"  Status: {teacher.get_employment_status_display()}")
            print("\nNo action needed. Admin can already access teacher attendance features!")
            return True
        
        print("\n→ Creating teacher profile for admin...")
        
        # Create teacher profile
        teacher = Teacher.objects.create(
            nip='ADM001',
            user=user,
            full_name='Administrator',
            email=user.email or 'admin@yaumi.sch.id',
            phone='081234567890',
            employment_date=date.today(),
            employment_status='ACTIVE',
            is_active=True,
            is_homeroom_teacher=False
        )
        
        print("\n✓ Teacher profile created successfully!")
        print(f"  Name: {teacher.full_name}")
        print(f"  NIP: {teacher.nip}")
        print(f"  Email: {teacher.email}")
        
        # Assign some subjects
        subjects = Subject.objects.filter(is_active=True)[:3]  # Get first 3 subjects
        if subjects.exists():
            teacher.subjects.set(subjects)
            print(f"\n✓ Assigned {subjects.count()} subject(s):")
            for subject in subjects:
                print(f"  - {subject.name} ({subject.get_category_display()})")
        
        print("\n" + "=" * 60)
        print("✓ SUCCESS!")
        print("=" * 60)
        print("\nAdmin user can now:")
        print("  1. Access 'Input Absensi Ustadz' menu")
        print("  2. Record attendance as a teacher")
        print("  3. View teacher dashboard")
        print("  4. Generate teacher reports")
        print("\nPlease refresh your browser and try again!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = setup_admin_teacher()
    
    if success:
        print("\n✓ Setup completed successfully!")
        print("\nNext steps:")
        print("  1. Refresh your browser")
        print("  2. Click 'Input Absensi Ustadz' menu")
        print("  3. You should now see the attendance input form")
    else:
        print("\n✗ Setup failed. Please check the error messages above.")
    
    import sys
    sys.exit(0 if success else 1)
