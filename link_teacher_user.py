#!/usr/bin/env python
"""
Script to link a Teacher profile to a User account
Usage: python link_teacher_user.py <username> <teacher_nip>
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sipa_yaumi.settings')
django.setup()

from django.contrib.auth.models import User
from attendance.models import Teacher

def link_teacher_to_user(username, teacher_nip):
    """Link a teacher profile to a user account"""
    try:
        # Get user
        try:
            user = User.objects.get(username=username)
            print(f"✓ Found user: {user.username} ({user.get_full_name() or 'No name'})")
        except User.DoesNotExist:
            print(f"✗ User '{username}' not found!")
            return False
        
        # Check if user already has a teacher profile
        if hasattr(user, 'teacher_profile'):
            existing_teacher = user.teacher_profile
            print(f"✗ User already has a teacher profile: {existing_teacher.full_name} (NIP: {existing_teacher.nip})")
            
            response = input("Do you want to unlink the existing profile and link a new one? (yes/no): ")
            if response.lower() != 'yes':
                print("Operation cancelled.")
                return False
            
            # Unlink existing profile
            existing_teacher.user = None
            existing_teacher.save()
            print(f"✓ Unlinked existing profile: {existing_teacher.full_name}")
        
        # Get teacher
        try:
            teacher = Teacher.objects.get(nip=teacher_nip)
            print(f"✓ Found teacher: {teacher.full_name} (NIP: {teacher.nip})")
        except Teacher.DoesNotExist:
            print(f"✗ Teacher with NIP '{teacher_nip}' not found!")
            return False
        
        # Check if teacher already has a user
        if teacher.user:
            print(f"✗ Teacher already linked to user: {teacher.user.username}")
            
            response = input("Do you want to unlink and relink to the new user? (yes/no): ")
            if response.lower() != 'yes':
                print("Operation cancelled.")
                return False
        
        # Link teacher to user
        teacher.user = user
        teacher.save()
        
        print("\n" + "=" * 60)
        print("✓ SUCCESS! Teacher profile linked to user")
        print("=" * 60)
        print(f"User: {user.username}")
        print(f"Teacher: {teacher.full_name} (NIP: {teacher.nip})")
        print(f"Email: {teacher.email or 'N/A'}")
        print(f"Employment Status: {teacher.get_employment_status_display()}")
        print("\nThe user can now access teacher attendance features!")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def show_usage():
    """Show usage instructions"""
    print("=" * 60)
    print("LINK TEACHER TO USER")
    print("=" * 60)
    print("\nUsage:")
    print("  python link_teacher_user.py <username> <teacher_nip>")
    print("\nExample:")
    print("  python link_teacher_user.py ahmad_yusuf T001")
    print("\nTo see available users and teachers:")
    print("  python check_teacher_profile.py")
    print("=" * 60)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        show_usage()
        sys.exit(1)
    
    username = sys.argv[1]
    teacher_nip = sys.argv[2]
    
    success = link_teacher_to_user(username, teacher_nip)
    sys.exit(0 if success else 1)
