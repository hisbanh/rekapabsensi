#!/usr/bin/env python
"""
Script to create a teacher profile for admin user
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sipa_yaumi.settings')
django.setup()

from django.contrib.auth.models import User
from attendance.models import Teacher, Subject
from datetime import date

def create_admin_teacher():
    """Create teacher profile for admin user"""
    try:
        # Get admin user
        username = input("Enter username to create teacher profile for (default: admin): ").strip() or "admin"
        
        try:
            user = User.objects.get(username=username)
            print(f"✓ Found user: {user.username}")
        except User.DoesNotExist:
            print(f"✗ User '{username}' not found!")
            return False
        
        # Check if user already has teacher profile
        if hasattr(user, 'teacher_profile'):
            print(f"✗ User already has a teacher profile: {user.teacher_profile.full_name}")
            return False
        
        # Get teacher details
        print("\n" + "=" * 60)
        print("CREATE TEACHER PROFILE")
        print("=" * 60)
        
        nip = input("Enter NIP (e.g., ADM001): ").strip()
        if not nip:
            print("✗ NIP is required!")
            return False
        
        # Check if NIP already exists
        if Teacher.objects.filter(nip=nip).exists():
            print(f"✗ Teacher with NIP '{nip}' already exists!")
            return False
        
        full_name = input(f"Enter full name (default: {user.get_full_name() or user.username}): ").strip()
        if not full_name:
            full_name = user.get_full_name() or user.username
        
        email = input(f"Enter email (default: {user.email or 'N/A'}): ").strip()
        if not email:
            email = user.email or ''
        
        phone = input("Enter phone number (optional): ").strip()
        
        # Create teacher
        teacher = Teacher.objects.create(
            nip=nip,
            user=user,
            full_name=full_name,
            email=email,
            phone=phone,
            employment_date=date.today(),
            employment_status='ACTIVE',
            is_active=True
        )
        
        print("\n" + "=" * 60)
        print("✓ SUCCESS! Teacher profile created")
        print("=" * 60)
        print(f"User: {user.username}")
        print(f"Teacher: {teacher.full_name}")
        print(f"NIP: {teacher.nip}")
        print(f"Email: {teacher.email or 'N/A'}")
        print(f"Phone: {teacher.phone or 'N/A'}")
        print("\nThe user can now access teacher attendance features!")
        
        # Ask if want to assign subjects
        assign_subjects = input("\nDo you want to assign subjects to this teacher? (yes/no): ").strip().lower()
        if assign_subjects == 'yes':
            subjects = Subject.objects.filter(is_active=True)
            if subjects.exists():
                print("\nAvailable subjects:")
                for i, subject in enumerate(subjects, 1):
                    print(f"{i}. {subject.name} ({subject.get_category_display()})")
                
                subject_ids = input("\nEnter subject numbers separated by comma (e.g., 1,3,5): ").strip()
                if subject_ids:
                    try:
                        indices = [int(x.strip()) - 1 for x in subject_ids.split(',')]
                        selected_subjects = [list(subjects)[i] for i in indices if 0 <= i < len(subjects)]
                        teacher.subjects.set(selected_subjects)
                        print(f"✓ Assigned {len(selected_subjects)} subject(s) to teacher")
                    except (ValueError, IndexError) as e:
                        print(f"✗ Invalid subject selection: {str(e)}")
            else:
                print("No subjects available")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    create_admin_teacher()
